-- 1. VIEW: Currently Available Fleet
CREATE OR REPLACE VIEW Available_Bikes AS
SELECT bike_id, brand, model, type, price_per_hour
FROM Bike
WHERE status = 'Available';

-- 2. AGGREGATE + GROUP BY + HAVING: Top performing bikes rented more than once
SELECT 
    b.bike_id, 
    b.brand, 
    b.model, 
    COUNT(r.rental_id) AS total_rentals,
    COALESCE(SUM(r.total_amount), 0) AS total_earnings
FROM Bike b
JOIN Rental r ON b.bike_id = r.bike_id
GROUP BY b.bike_id, b.brand, b.model
HAVING COUNT(r.rental_id) >= 1;

-- 3. SUBQUERY: Find bikes priced higher than average hourly price
SELECT model, brand, price_per_hour
FROM Bike
WHERE price_per_hour > (SELECT AVG(price_per_hour) FROM Bike);

-- 4. MULTI-TABLE JOIN: Full customer rental report with payment status
SELECT 
    r.rental_id,
    c.name AS customer_name,
    c.phone,
    CONCAT(b.brand, ' ', b.model) AS bike_name,
    r.start_time,
    r.end_time,
    r.status AS rental_status,
    p.amount,
    p.payment_method,
    p.payment_status
FROM Rental r
INNER JOIN Customer c ON r.customer_id = c.customer_id
INNER JOIN Bike b ON r.bike_id = b.bike_id
LEFT JOIN Payment p ON r.rental_id = p.rental_id
ORDER BY r.start_time DESC;