from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import math
from datetime import datetime
from database import get_db_connection

app = Flask(__name__)
app.secret_key = "super_secret_dbms_project_key"

# ----------------- ROUTE 1: HOME -----------------
@app.route("/")
def index():
    return render_template("index.html")

# ----------------- ROUTE 2: AUTH (LOGIN) -----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "customer")

        db = get_db_connection()
        if not db:
            flash("Database connection failed", "danger")
            return redirect(url_for("login"))

        cursor = db.cursor(dictionary=True)

        if role == "admin":
            cursor.execute("SELECT * FROM Admin WHERE email = %s", (email,))
            admin = cursor.fetchone()
            cursor.close()
            db.close()

            # Plaintext fallback check for seed data or hashed
            if admin and (admin["password"] == password or check_password_hash(admin["password"], password)):
                session["admin_id"] = admin["admin_id"]
                session["admin_name"] = admin["name"]
                return redirect(url_for("admin_dashboard"))
            flash("Invalid admin credentials.", "danger")
            return redirect(url_for("login"))

        # Customer Login
        cursor.execute("SELECT * FROM Customer WHERE email = %s", (email,))
        customer = cursor.fetchone()
        cursor.close()
        db.close()

        if customer and check_password_hash(customer["password"], password):
            session["customer_id"] = customer["customer_id"]
            session["customer_name"] = customer["name"]
            return redirect(url_for("bikes"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for("login"))

    return render_template("auth.html")

# ----------------- ROUTE 3: REGISTER -----------------
@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    license_no = request.form.get("license_no", "").strip()
    password = request.form.get("password", "").strip()

    if not all([name, email, phone, license_no, password]):
        flash("All fields are required.", "danger")
        return redirect(url_for("login"))

    hashed_pw = generate_password_hash(password)

    db = get_db_connection()
    if not db:
        flash("Database connection failed", "danger")
        return redirect(url_for("login"))

    cursor = db.cursor()
    try:
        query = """
            INSERT INTO Customer (name, email, phone, license_no, password)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, email, phone, license_no, hashed_pw))
        db.commit()
        flash("Registration successful! Please log in.", "success")
    except Exception as e:
        db.rollback()
        flash("Registration failed: Email, Phone, or License Number already exists.", "danger")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for("login"))

# ----------------- ROUTE 4: LOGOUT -----------------
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

# ----------------- ROUTE 5: BIKES -----------------
@app.route("/bikes")
def bikes():
    if "customer_id" not in session:
        flash("Please log in to view and rent bikes.", "warning")
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Bike WHERE status = 'Available'")
    available_bikes = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template("bikes.html", bikes=available_bikes)

# ----------------- ROUTE 6: RENT BIKE (TRANSACTION) -----------------
@app.route("/rent/<int:bike_id>", methods=["POST"])
def rent_bike(bike_id):
    if "customer_id" not in session:
        return redirect(url_for("login"))

    customer_id = session["customer_id"]
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Step 1: Check availability with row locking
        cursor.execute("SELECT * FROM Bike WHERE bike_id = %s FOR UPDATE", (bike_id,))
        bike = cursor.fetchone()

        if not bike or bike["status"] != "Available":
            db.rollback()
            flash("Sorry, this bike is no longer available.", "danger")
            return redirect(url_for("bikes"))

        # Step 2: Insert into Rental
        cursor.execute(
            """
            INSERT INTO Rental (customer_id, bike_id, start_time, status, total_amount)
            VALUES (%s, %s, NOW(), 'Active', 0.00)
            """,
            (customer_id, bike_id)
        )

        # Step 3: Update Bike status
        cursor.execute("UPDATE Bike SET status = 'Rented' WHERE bike_id = %s", (bike_id,))

        # Commit transaction atomically
        db.commit()
        flash(f"Successfully rented {bike['brand']} {bike['model']}! 🚀", "success")
        return redirect(url_for("rentals"))

    except Exception as e:
        db.rollback()
        flash(f"Transaction failed: {str(e)}", "danger")
        return redirect(url_for("bikes"))
    finally:
        cursor.close()
        db.close()

# ----------------- ROUTE 7: CUSTOMER DASHBOARD / RENTALS -----------------
@app.route("/rentals")
def rentals():
    if "customer_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))

    customer_id = session["customer_id"]
    db = get_db_connection()
    if not db:
        flash("Database connection failed", "danger")
        return redirect(url_for("bikes"))

    cursor = db.cursor(dictionary=True)

    # 1. Fetch Customer Profile Details
    cursor.execute(
        """
        SELECT customer_id, name, email, phone, license_no, created_at 
        FROM Customer 
        WHERE customer_id = %s
        """, 
        (customer_id,)
    )
    customer = cursor.fetchone()

    # 2. Fetch Rental History with Bike & Payment Data
    query = """
        SELECT 
            r.rental_id,
            b.brand,
            b.model,
            b.type AS bike_type,
            b.registration_no,
            b.price_per_hour,
            r.start_time,
            r.end_time,
            r.status AS rental_status,
            r.total_amount,
            p.payment_method,
            p.payment_status
        FROM Rental r
        JOIN Bike b ON r.bike_id = b.bike_id
        LEFT JOIN Payment p ON r.rental_id = p.rental_id
        WHERE r.customer_id = %s
        ORDER BY r.start_time DESC
    """
    cursor.execute(query, (customer_id,))
    my_rentals = cursor.fetchall()
    cursor.close()
    db.close()

    # 3. Compute Summary Statistics for the KPI Cards
    total_trips = len(my_rentals)
    active_count = sum(1 for r in my_rentals if r["rental_status"] == "Active")
    total_spent = sum(float(r["total_amount"] or 0) for r in my_rentals if r["rental_status"] == "Completed")

    stats = {
        "total_trips": total_trips,
        "active_count": active_count,
        "total_spent": total_spent
    }

    return render_template("rentals.html", customer=customer, rentals=my_rentals, stats=stats)

# ----------------- ROUTE 8: RETURN BIKE (TRANSACTION) -----------------
@app.route("/return/<int:rental_id>", methods=["POST"])
def return_bike(rental_id):
    if "customer_id" not in session:
        return redirect(url_for("login"))

    payment_method = request.form.get("payment_method", "UPI")
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Step 1: Fetch active rental
        cursor.execute(
            """
            SELECT r.*, b.price_per_hour, b.bike_id 
            FROM Rental r
            JOIN Bike b ON r.bike_id = b.bike_id
            WHERE r.rental_id = %s AND r.status = 'Active' FOR UPDATE
            """,
            (rental_id,)
        )
        rental = cursor.fetchone()

        if not rental:
            db.rollback()
            flash("Active rental record not found.", "danger")
            return redirect(url_for("rentals"))

        end_time = datetime.now()
        start_time = rental["start_time"]
        duration_seconds = max((end_time - start_time).total_seconds(), 60)
        # Billable hours (minimum 1 hour, rounded up)
        hours = max(1, math.ceil(duration_seconds / 3600))
        total_amount = float(hours * float(rental["price_per_hour"]))

        # Step 2: Update Rental
        cursor.execute(
            """
            UPDATE Rental 
            SET end_time = %s, status = 'Completed', total_amount = %s
            WHERE rental_id = %s
            """,
            (end_time, total_amount, rental_id)
        )

        # Step 3: Insert Payment (Simulated)
        cursor.execute(
            """
            INSERT INTO Payment (rental_id, amount, payment_method, payment_status)
            VALUES (%s, %s, %s, 'Paid')
            """,
            (rental_id, total_amount, payment_method)
        )

        # Step 4: Reset Bike status
        cursor.execute(
            "UPDATE Bike SET status = 'Available' WHERE bike_id = %s",
            (rental["bike_id"],)
        )

        db.commit()
        flash(f"Bike returned successfully! Total Amount: ₹{total_amount:.2f} (Duration: {hours} hr).", "success")

    except Exception as e:
        db.rollback()
        flash(f"Error returning bike: {str(e)}", "danger")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for("rentals"))

# ----------------- ROUTE 9: ADMIN DASHBOARD (AGGREGATIONS) -----------------
@app.route("/admin")
def admin_dashboard():
    if "admin_id" not in session:
        flash("Admin login required.", "warning")
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Metrics
    cursor.execute("SELECT COUNT(*) AS count FROM Bike")
    total_bikes = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) AS count FROM Bike WHERE status = 'Available'")
    available_bikes = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) AS count FROM Rental WHERE status = 'Active'")
    active_rentals = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) AS count FROM Customer")
    total_customers = cursor.fetchone()["count"]

    cursor.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM Payment WHERE payment_status = 'Paid'")
    revenue = cursor.fetchone()["total"]

    # Tables Data
    cursor.execute("SELECT * FROM Bike ORDER BY bike_id DESC")
    all_bikes = cursor.fetchall()

    cursor.execute("""
        SELECT 
            r.rental_id, c.name AS customer_name, b.brand, b.model,
            r.start_time, r.end_time, r.status, r.total_amount
        FROM Rental r
        JOIN Customer c ON r.customer_id = c.customer_id
        JOIN Bike b ON r.bike_id = b.bike_id
        ORDER BY r.rental_id DESC
    """)
    all_rentals = cursor.fetchall()

    cursor.execute("SELECT customer_id, name, email, phone, license_no, created_at FROM Customer")
    all_customers = cursor.fetchall()

    cursor.execute("""
        SELECT m.*, b.brand, b.model 
        FROM Maintenance m 
        JOIN Bike b ON m.bike_id = b.bike_id
    """)
    maintenance_records = cursor.fetchall()

    cursor.close()
    db.close()

    stats = {
        "total_bikes": total_bikes,
        "available_bikes": available_bikes,
        "active_rentals": active_rentals,
        "total_customers": total_customers,
        "revenue": revenue
    }

    return render_template(
        "admin.html",
        stats=stats,
        bikes=all_bikes,
        rentals=all_rentals,
        customers=all_customers,
        maintenance=maintenance_records
    )

# ----------------- ROUTE 10: ADMIN ADD BIKE -----------------
@app.route("/admin/add-bike", methods=["POST"])
def add_bike():
    if "admin_id" not in session:
        return redirect(url_for("login"))

    model = request.form.get("model", "").strip()
    brand = request.form.get("brand", "").strip()
    bike_type = request.form.get("type", "").strip()
    registration_no = request.form.get("registration_no", "").strip().upper()
    price_per_hour = request.form.get("price_per_hour", 0.0)

    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO Bike (model, brand, type, registration_no, price_per_hour, status)
            VALUES (%s, %s, %s, %s, %s, 'Available')
            """,
            (model, brand, bike_type, registration_no, price_per_hour)
        )
        db.commit()
        flash("New bike added successfully!", "success")
    except Exception as e:
        db.rollback()
        flash("Error adding bike: Registration number must be unique.", "danger")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for("admin_dashboard"))

# ----------------- ROUTE 11 ADMIN: ADD CUSTOMER -----------------
@app.route("/admin/add-customer", methods=["POST"])
def admin_add_customer():
    if "admin_id" not in session:
        return redirect(url_for("login"))

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    license_no = request.form.get("license_no", "").strip()
    password = request.form.get("password", "").strip()

    if not all([name, email, phone, license_no, password]):
        flash("All fields are required to register a customer.", "danger")
        return redirect(url_for("admin_dashboard"))

    hashed_pw = generate_password_hash(password)

    db = get_db_connection()
    if not db:
        flash("Database connection failed", "danger")
        return redirect(url_for("admin_dashboard"))

    cursor = db.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO Customer (name, email, phone, license_no, password)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (name, email, phone, license_no, hashed_pw)
        )
        db.commit()
        flash(f"Customer '{name}' registered successfully!", "success")
    except Exception:
        db.rollback()
        flash("Error: Email, Phone, or License Number already exists.", "danger")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for("admin_dashboard"))


# ----------------- ROUTE 12 ADMIN: DELETE BIKE -----------------
@app.route("/admin/delete-bike/<int:bike_id>", methods=["POST"])
def delete_bike(bike_id):
    if "admin_id" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()
    if not db:
        flash("Database connection failed", "danger")
        return redirect(url_for("admin_dashboard"))

    cursor = db.cursor(dictionary=True)

    try:
        # Check if the bike is currently rented
        cursor.execute("SELECT status FROM Bike WHERE bike_id = %s", (bike_id,))
        bike = cursor.fetchone()

        if not bike:
            flash("Bike not found.", "danger")
            return redirect(url_for("admin_dashboard"))

        if bike["status"] == "Rented":
            flash("Cannot delete bike while it is currently rented out!", "danger")
            return redirect(url_for("admin_dashboard"))

        # Check for Foreign Key constraints (Rental history or Maintenance)
        cursor.execute("SELECT COUNT(*) AS count FROM Rental WHERE bike_id = %s", (bike_id,))
        rental_count = cursor.fetchone()["count"]

        if rental_count > 0:
            flash("Cannot delete bike: Historical rental records exist for this vehicle (Foreign Key integrity).", "danger")
            return redirect(url_for("admin_dashboard"))

        # Safe to delete
        cursor.execute("DELETE FROM Bike WHERE bike_id = %s", (bike_id,))
        db.commit()
        flash("Bike deleted successfully from inventory!", "success")

    except Exception as e:
        db.rollback()
        flash(f"Error deleting bike: {str(e)}", "danger")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)