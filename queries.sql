-- name: check_admin_login
SELECT * 
FROM Admin 
WHERE email = %s AND password = %s;

-- name: check_customer_login
SELECT * 
FROM Customer 
WHERE email = %s AND password = %s;

-- name: register_customer
INSERT INTO Customer (name, email, phone, license_no, password)
VALUES (%s, %s, %s, %s, %s);

-- name: get_available_bikes
SELECT * 
FROM Bike 
WHERE status = 'Available';

-- name: get_bike_for_rental_lock
SELECT * 
FROM Bike 
WHERE bike_id = %s 
FOR UPDATE;

-- name: insert_rental
INSERT INTO Rental (customer_id, bike_id, start_time, status, total_amount)
VALUES (%s, %s, NOW(), 'Active', 0.00);

-- name: set_bike_rented
UPDATE Bike 
SET status = 'Rented' 
WHERE bike_id = %s;

-- name: get_customer_profile
SELECT customer_id, name, email, phone, license_no, created_at 
FROM Customer 
WHERE customer_id = %s;

-- name: get_customer_rentals
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
ORDER BY r.start_time DESC;

-- name: get_active_rental_for_return_lock
SELECT r.*, b.price_per_hour, b.bike_id 
FROM Rental r
JOIN Bike b ON r.bike_id = b.bike_id
WHERE r.rental_id = %s AND r.status = 'Active' 
FOR UPDATE;

-- name: complete_rental
UPDATE Rental 
SET end_time = %s, status = 'Completed', total_amount = %s
WHERE rental_id = %s;

-- name: insert_payment
INSERT INTO Payment (rental_id, amount, payment_method, payment_status)
VALUES (%s, %s, %s, 'Paid');

-- name: set_bike_available
UPDATE Bike 
SET status = 'Available' 
WHERE bike_id = %s;

-- name: admin_stat_total_bikes
SELECT COUNT(*) AS count FROM Bike;

-- name: admin_stat_available_bikes
SELECT COUNT(*) AS count FROM Bike WHERE status = 'Available';

-- name: admin_stat_active_rentals
SELECT COUNT(*) AS count FROM Rental WHERE status = 'Active';

-- name: admin_stat_total_customers
SELECT COUNT(*) AS count FROM Customer;

-- name: admin_stat_revenue
SELECT COALESCE(SUM(amount), 0) AS total FROM Payment WHERE payment_status = 'Paid';

-- name: admin_get_all_bikes
SELECT * FROM Bike ORDER BY bike_id DESC;

-- name: admin_get_all_rentals
SELECT 
    r.rental_id, 
    c.name AS customer_name, 
    b.brand, 
    b.model,
    r.start_time, 
    r.end_time, 
    r.status, 
    r.total_amount
FROM Rental r
JOIN Customer c ON r.customer_id = c.customer_id
JOIN Bike b ON r.bike_id = b.bike_id
ORDER BY r.rental_id DESC;

-- name: admin_get_all_customers
SELECT customer_id, name, email, phone, license_no, created_at 
FROM Customer 
ORDER BY customer_id DESC;

-- name: admin_get_maintenance
SELECT m.*, b.brand, b.model 
FROM Maintenance m 
JOIN Bike b ON m.bike_id = b.bike_id
ORDER BY m.maintenance_id DESC;

-- name: admin_add_bike
INSERT INTO Bike (model, brand, type, registration_no, price_per_hour, status)
VALUES (%s, %s, %s, %s, %s, 'Available');

-- name: get_bike_status
SELECT status FROM Bike WHERE bike_id = %s;

-- name: check_bike_rental_history_count
SELECT COUNT(*) AS count FROM Rental WHERE bike_id = %s;

-- name: delete_bike
DELETE FROM Bike WHERE bike_id = %s;

-- name: insert_maintenance
INSERT INTO Maintenance (bike_id, description, maintenance_date, cost, status)
VALUES (%s, %s, %s, %s, 'In Progress');

-- name: set_bike_maintenance
UPDATE Bike 
SET status = 'Maintenance' 
WHERE bike_id = %s;

-- name: get_maintenance_record
SELECT maintenance_id, bike_id, status 
FROM Maintenance 
WHERE maintenance_id = %s;

-- name: complete_maintenance_record
UPDATE Maintenance 
SET status = 'Completed' 
WHERE maintenance_id = %s;