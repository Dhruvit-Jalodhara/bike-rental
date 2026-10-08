-- DATABASE SETUP: Bike Rental Management System
DROP DATABASE IF EXISTS bike_rental;
CREATE DATABASE bike_rental;
USE bike_rental;

-- 1. ADMIN TABLE
CREATE TABLE Admin (
    admin_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

-- 2. CUSTOMER TABLE
CREATE TABLE Customer (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15) UNIQUE NOT NULL,
    license_no VARCHAR(30) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 3. BIKE TABLE
CREATE TABLE Bike (
    bike_id INT PRIMARY KEY AUTO_INCREMENT,
    model VARCHAR(50) NOT NULL,
    brand VARCHAR(50) NOT NULL,
    type VARCHAR(30) NOT NULL,
    registration_no VARCHAR(20) UNIQUE NOT NULL,
    price_per_hour DECIMAL(10,2) NOT NULL,
    status ENUM('Available', 'Rented', 'Maintenance') DEFAULT 'Available'
) ENGINE=InnoDB;

-- 4. RENTAL TABLE
CREATE TABLE Rental (
    rental_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    bike_id INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NULL,
    status ENUM('Active', 'Completed', 'Cancelled') DEFAULT 'Active',
    total_amount DECIMAL(10,2) DEFAULT 0.00,
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id) ON DELETE RESTRICT,
    FOREIGN KEY (bike_id) REFERENCES Bike(bike_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 5. PAYMENT TABLE
CREATE TABLE Payment (
    payment_id INT PRIMARY KEY AUTO_INCREMENT,
    rental_id INT UNIQUE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method ENUM('UPI', 'Card', 'Cash') NOT NULL,
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    payment_status ENUM('Pending', 'Paid', 'Failed') DEFAULT 'Pending',
    FOREIGN KEY (rental_id) REFERENCES Rental(rental_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 6. MAINTENANCE TABLE
CREATE TABLE Maintenance (
    maintenance_id INT PRIMARY KEY AUTO_INCREMENT,
    bike_id INT NOT NULL,
    description VARCHAR(255) NOT NULL,
    maintenance_date DATE NOT NULL,
    cost DECIMAL(10,2) DEFAULT 0.00,
    status ENUM('Pending', 'In Progress', 'Completed') DEFAULT 'Pending',
    FOREIGN KEY (bike_id) REFERENCES Bike(bike_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- DATA INSERTION

-- 1. SEED: 2 Admins
INSERT INTO Admin (admin_id, name, email, password) VALUES
(1, 'Admin1', 'admin1@bikerental.com', 'admin123'),
(2, 'Admin2', 'admin2@bikerental.com', 'admin123');

-- 2. SEED: 10 Bikes
INSERT INTO Bike (bike_id, model, brand, type, registration_no, price_per_hour, status) VALUES
(1,  'Classic 350',  'Royal Enfield', 'Cruiser',   'GJ05AB1001', 120.00, 'Available'),
(2,  'Hunter 350',   'Royal Enfield', 'Cruiser',   'GJ05AB1002', 110.00, 'Available'),
(3,  'R15 V4',       'Yamaha',        'Sports',    'GJ05CD2001', 150.00, 'Available'),
(4,  'MT-15',        'Yamaha',        'Sports',    'GJ05CD2002', 140.00, 'Available'),
(5,  'Duke 250',     'KTM',           'Sports',    'GJ05EF3001', 160.00, 'Available'),
(6,  'RC 200',       'KTM',           'Sports',    'GJ05EF3002', 155.00, 'Available'),
(7,  'Activa 6G',    'Honda',         'Scooter',   'GJ05GH4001',  60.00, 'Available'),
(8,  'Dio 125',      'Honda',         'Scooter',   'GJ05GH4002',  65.00, 'Available'),
(9,  'Access 125',   'Suzuki',        'Scooter',   'GJ05IJ5001',  70.00, 'Available'),
(10, 'Splendor Plus','Hero',          'Commuter',  'GJ05KL6001',  50.00, 'Available');

-- 3. SEED: 15 Customers (Normal Plain-Text Passwords)
INSERT INTO Customer (customer_id, name, email, phone, license_no, password, created_at) VALUES
(1,  'Rahul Sharma',      'rahul@example.com',     '9876543201', 'GJ0520210001001', 'rahul123',   '2026-08-01 10:15:00'),
(2,  'Priya Patel',       'priya@example.com',     '9876543202', 'GJ0520210001002', 'priya123',   '2026-08-05 11:30:00'),
(3,  'Amit Verma',        'amit@example.com',      '9876543203', 'GJ0520210001003', 'amit123',    '2026-08-10 14:00:00'),
(4,  'Sneha Mehta',       'sneha@example.com',     '9876543204', 'GJ0520210001004', 'sneha123',   '2026-08-12 16:20:00'),
(5,  'Dhruvit Jalodhara', 'dhruvit@example.com',   '9876543205', 'GJ0520210001005', 'dhruvit123', '2026-08-15 09:00:00'),
(6,  'Karan Joshi',       'karan@example.com',     '9876543206', 'GJ0520210001006', 'karan123',   '2026-08-18 12:45:00'),
(7,  'Ananya Desai',      'ananya@example.com',    '9876543207', 'GJ0520210001007', 'ananya123',  '2026-08-20 18:10:00'),
(8,  'Rohan Shah',        'rohan@example.com',     '9876543208', 'GJ0520210001008', 'rohan123',   '2026-08-22 15:30:00'),
(9,  'Bhavin Dave',       'bhavin@example.com',    '9876543209', 'GJ0520210001009', 'bhavin123',  '2026-08-25 11:20:00'),
(10, 'Nisha Trivedi',     'nisha@example.com',     '9876543210', 'GJ0520210001010', 'nisha123',   '2026-08-28 17:05:00'),
(11, 'Vikas Solanki',     'vikas@example.com',     '9876543211', 'GJ0520210001011', 'vikas123',   '2026-09-01 10:00:00'),
(12, 'Pooja Iyer',        'pooja@example.com',     '9876543212', 'GJ0520210001012', 'pooja123',   '2026-09-05 13:40:00'),
(13, 'Sanjay Rathod',     'sanjay@example.com',    '9876543213', 'GJ0520210001013', 'sanjay123',  '2026-09-10 16:50:00'),
(14, 'Tanvi Bhatt',       'tanvi@example.com',     '9876543214', 'GJ0520210001014', 'tanvi123',   '2026-09-12 19:15:00'),
(15, 'Hardik Chudasama',  'hardik@example.com',    '9876543215', 'GJ0520210001015', 'hardik123',  '2026-09-15 08:30:00');

-- 4. SEED: Rentals
INSERT INTO Rental (rental_id, customer_id, bike_id, start_time, end_time, status, total_amount) VALUES
(101, 1, 1, '2026-09-20 09:00:00', '2026-09-20 13:00:00', 'Completed', 480.00),
(102, 2, 7, '2026-09-21 10:00:00', '2026-09-21 12:00:00', 'Completed', 120.00),
(103, 3, 3, '2026-09-22 14:00:00', '2026-09-22 18:00:00', 'Completed', 600.00),
(104, 4, 9, '2026-09-23 11:00:00', '2026-09-23 15:00:00', 'Completed', 280.00),
(105, 5, 4, '2026-09-24 16:00:00', '2026-09-24 19:00:00', 'Completed', 420.00),
(106, 6, 2, '2026-09-04 16:00:00', '2026-09-24 19:00:00', 'Completed', 140.00),
(107, 5, 5, '2026-09-15 16:00:00', '2026-09-24 19:00:00', 'Completed', 260.00);

-- 5. SEED: Payments
INSERT INTO Payment (payment_id, rental_id, amount, payment_method, payment_date, payment_status) VALUES
(1, 101, 480.00, 'UPI',  '2026-09-20 13:05:00', 'Paid'),
(2, 102, 120.00, 'Cash', '2026-09-21 12:02:00', 'Paid'),
(3, 103, 600.00, 'Card', '2026-09-22 18:05:00', 'Paid'),
(4, 104, 280.00, 'UPI',  '2026-09-23 15:01:00', 'Paid'),
(5, 105, 420.00, 'UPI',  '2026-09-24 19:05:00', 'Paid');

-- 6. SEED: Maintenance
INSERT INTO Maintenance (maintenance_id, bike_id, description, maintenance_date, cost, status) VALUES
(1, 6, 'Brake pad and chain replacement', '2026-10-01', 1850.00, 'Completed'),
(2, 1, 'Regular engine oil and filter service', '2026-09-15', 750.00, 'Completed'),
(3, 7, 'Rear tyre puncture and general service', '2026-09-18', 450.00, 'Completed');