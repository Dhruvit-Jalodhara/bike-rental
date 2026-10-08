from flask import Flask, render_template, request, redirect, url_for, session, flash
import math
from datetime import datetime
from database import get_db_connection, SQL

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
            cursor.execute(SQL["check_admin_login"], (email, password))
            admin = cursor.fetchone()
            cursor.close()
            db.close()

            if admin:
                session["admin_id"] = admin["admin_id"]
                session["admin_name"] = admin["name"]
                return redirect(url_for("admin_dashboard"))

            flash("Invalid admin credentials.", "danger")
            return redirect(url_for("login"))

        cursor.execute(SQL["check_customer_login"], (email, password))
        customer = cursor.fetchone()
        cursor.close()
        db.close()

        if customer:
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

    db = get_db_connection()
    if not db:
        flash("Database connection failed", "danger")
        return redirect(url_for("login"))

    cursor = db.cursor()
    try:
        cursor.execute(SQL["register_customer"], (name, email, phone, license_no, password))
        db.commit()
        flash("Registration successful! Please log in.", "success")
    except Exception:
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
    if not db:
        flash("Database connection failed", "danger")
        return redirect(url_for("login"))

    cursor = db.cursor(dictionary=True)
    cursor.execute(SQL["get_available_bikes"])
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
    if not db:
        flash("Database connection failed", "danger")
        return redirect(url_for("bikes"))

    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(SQL["get_bike_for_rental_lock"], (bike_id,))
        bike = cursor.fetchone()

        if not bike or bike["status"] != "Available":
            db.rollback()
            flash("Sorry, this bike is no longer available.", "danger")
            return redirect(url_for("bikes"))

        cursor.execute(SQL["insert_rental"], (customer_id, bike_id))
        cursor.execute(SQL["set_bike_rented"], (bike_id,))

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

    cursor.execute(SQL["get_customer_profile"], (customer_id,))
    customer = cursor.fetchone()

    if customer and "customer_name" not in session:
        session["customer_name"] = customer["name"]

    cursor.execute(SQL["get_customer_rentals"], (customer_id,))
    my_rentals = cursor.fetchall()
    cursor.close()
    db.close()

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
    if not db:
        flash("Database connection failed", "danger")
        return redirect(url_for("rentals"))

    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(SQL["get_active_rental_for_return_lock"], (rental_id,))
        rental = cursor.fetchone()

        if not rental:
            db.rollback()
            flash("Active rental record not found.", "danger")
            return redirect(url_for("rentals"))

        end_time = datetime.now()
        start_time = rental["start_time"]
        duration_seconds = max((end_time - start_time).total_seconds(), 60)
        hours = max(1, math.ceil(duration_seconds / 3600))
        total_amount = float(hours * float(rental["price_per_hour"]))

        cursor.execute(SQL["complete_rental"], (end_time, total_amount, rental_id))
        cursor.execute(SQL["insert_payment"], (rental_id, total_amount, payment_method))
        cursor.execute(SQL["set_bike_available"], (rental["bike_id"],))

        db.commit()
        flash(f"Bike returned successfully! Total Amount: ₹{total_amount:.2f} (Duration: {hours} hr).", "success")

    except Exception as e:
        db.rollback()
        flash(f"Error returning bike: {str(e)}", "danger")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for("rentals"))


# ----------------- ROUTE 9: ADMIN DASHBOARD -----------------
@app.route("/admin")
def admin_dashboard():
    if "admin_id" not in session:
        flash("Admin login required.", "warning")
        return redirect(url_for("login"))

    db = get_db_connection()
    if not db:
        flash("Database connection failed", "danger")
        return redirect(url_for("login"))

    cursor = db.cursor(dictionary=True)

    cursor.execute(SQL["admin_stat_total_bikes"])
    total_bikes = cursor.fetchone()["count"]

    cursor.execute(SQL["admin_stat_available_bikes"])
    available_bikes = cursor.fetchone()["count"]

    cursor.execute(SQL["admin_stat_active_rentals"])
    active_rentals = cursor.fetchone()["count"]

    cursor.execute(SQL["admin_stat_total_customers"])
    total_customers = cursor.fetchone()["count"]

    cursor.execute(SQL["admin_stat_revenue"])
    revenue = cursor.fetchone()["total"]

    cursor.execute(SQL["admin_get_all_bikes"])
    all_bikes = cursor.fetchall()

    cursor.execute(SQL["admin_get_all_rentals"])
    all_rentals = cursor.fetchall()

    cursor.execute(SQL["admin_get_all_customers"])
    all_customers = cursor.fetchall()

    cursor.execute(SQL["admin_get_maintenance"])
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
    if not db:
        flash("Database connection failed", "danger")
        return redirect(url_for("admin_dashboard"))

    cursor = db.cursor()
    try:
        cursor.execute(SQL["admin_add_bike"], (model, brand, bike_type, registration_no, price_per_hour))
        db.commit()
        flash("New bike added successfully!", "success")
    except Exception:
        db.rollback()
        flash("Error adding bike: Registration number must be unique.", "danger")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for("admin_dashboard"))


# ----------------- ROUTE 11: ADMIN DELETE BIKE -----------------
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
        cursor.execute(SQL["get_bike_status"], (bike_id,))
        bike = cursor.fetchone()

        if not bike:
            flash("Bike not found.", "danger")
            return redirect(url_for("admin_dashboard"))

        if bike["status"] == "Rented":
            flash("Cannot delete bike while it is currently rented out!", "danger")
            return redirect(url_for("admin_dashboard"))

        cursor.execute(SQL["check_bike_rental_history_count"], (bike_id,))
        rental_count = cursor.fetchone()["count"]

        if rental_count > 0:
            flash("Cannot delete bike: Historical rental records exist for this vehicle (Foreign Key integrity).", "danger")
            return redirect(url_for("admin_dashboard"))

        cursor.execute(SQL["delete_bike"], (bike_id,))
        db.commit()
        flash("Bike deleted successfully from inventory!", "success")

    except Exception as e:
        db.rollback()
        flash(f"Error deleting bike: {str(e)}", "danger")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for("admin_dashboard"))

# ----------------- ROUTE 12: ADMIN SEND BIKE TO MAINTENANCE -----------------
@app.route("/admin/send-maintenance", methods=["POST"])
def send_maintenance():
    if "admin_id" not in session:
        return redirect(url_for("login"))

    bike_id = request.form.get("bike_id")
    description = request.form.get("description", "").strip()
    cost = request.form.get("cost", 0.0)
    service_date = request.form.get("maintenance_date") or datetime.now().strftime("%Y-%m-%d")

    if not bike_id or not description:
        flash("Bike and description are required for maintenance.", "danger")
        return redirect(url_for("admin_dashboard"))

    db = get_db_connection()
    if not db:
        flash("Database connection failed", "danger")
        return redirect(url_for("admin_dashboard"))

    cursor = db.cursor(dictionary=True)
    try:
        # Verify bike is Available before sending
        cursor.execute(SQL["get_bike_status"], (bike_id,))
        bike = cursor.fetchone()

        if not bike or bike["status"] != "Available":
            flash("Only 'Available' bikes can be put under maintenance.", "danger")
            return redirect(url_for("admin_dashboard"))

        # Atomic Transaction: Log maintenance & update bike status
        cursor.execute(SQL["insert_maintenance"], (bike_id, description, service_date, cost))
        cursor.execute(SQL["set_bike_maintenance"], (bike_id,))
        
        db.commit()
        flash("Bike moved to Maintenance successfully!", "success")
    except Exception as e:
        db.rollback()
        flash(f"Error logging maintenance: {str(e)}", "danger")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for("admin_dashboard"))


# ----------------- ROUTE 13: ADMIN COMPLETE MAINTENANCE -----------------
@app.route("/admin/complete-maintenance/<int:maintenance_id>", methods=["POST"])
def complete_maintenance(maintenance_id):
    if "admin_id" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()
    if not db:
        flash("Database connection failed", "danger")
        return redirect(url_for("admin_dashboard"))

    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(SQL["get_maintenance_record"], (maintenance_id,))
        m = cursor.fetchone()

        if not m or m["status"] == "Completed":
            flash("Maintenance record already completed or invalid.", "warning")
            return redirect(url_for("admin_dashboard"))

        # Atomic Transaction: Mark maintenance Completed & release bike to Available
        cursor.execute(SQL["complete_maintenance_record"], (maintenance_id,))
        cursor.execute(SQL["set_bike_available"], (m["bike_id"],))

        db.commit()
        flash("Maintenance completed! Bike is now Available for rent.", "success")
    except Exception as e:
        db.rollback()
        flash(f"Error completing maintenance: {str(e)}", "danger")
    finally:
        cursor.close()
        db.close()

    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)