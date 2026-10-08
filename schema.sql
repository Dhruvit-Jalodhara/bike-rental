-- Create database
CREATE DATABASE IF NOT EXISTS bike_rental;
USE bike_rental;

-- 1. Customer Table
CREATE TABLE IF NOT EXISTS Customer (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15) UNIQUE NOT NULL,
    license_no VARCHAR(30) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Bike Table
CREATE TABLE IF NOT EXISTS Bike (
    bike_id INT PRIMARY KEY AUTO_INCREMENT,
    model VARCHAR(50) NOT NULL,
    brand VARCHAR(50) NOT NULL,
    type VARCHAR(30) NOT NULL,
    registration_no VARCHAR(20) UNIQUE NOT NULL,
    price_per_hour DECIMAL(10,2) NOT NULL,
    status ENUM('Available', 'Rented', 'Maintenance') DEFAULT 'Available'
) ENGINE=InnoDB;

-- 3. Rental Table
CREATE TABLE IF NOT EXISTS Rental (
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

-- 4. Payment Table
CREATE TABLE IF NOT EXISTS Payment (
    payment_id INT PRIMARY KEY AUTO_INCREMENT,
    rental_id INT UNIQUE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method ENUM('UPI', 'Card', 'Cash') NOT NULL,
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    payment_status ENUM('Pending', 'Paid', 'Failed') DEFAULT 'Pending',
    FOREIGN KEY (rental_id) REFERENCES Rental(rental_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 5. Maintenance Table
CREATE TABLE IF NOT EXISTS Maintenance (
    maintenance_id INT PRIMARY KEY AUTO_INCREMENT,
    bike_id INT NOT NULL,
    description VARCHAR(255) NOT NULL,
    maintenance_date DATE NOT NULL,
    cost DECIMAL(10,2) DEFAULT 0.00,
    status ENUM('Pending', 'In Progress', 'Completed') DEFAULT 'Pending',
    FOREIGN KEY (bike_id) REFERENCES Bike(bike_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- 6. Admin Table
CREATE TABLE IF NOT EXISTS Admin (
    admin_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

-- Sample Seed Data
INSERT INTO Admin (name, email, password) 
VALUES ('System Admin', 'admin@bikerental.com', 'admin123')
ON DUPLICATE KEY UPDATE name=name;

INSERT INTO Bike (model, brand, type, registration_no, price_per_hour, status) VALUES
('Classic 350', 'Royal Enfield', 'Cruiser', 'GJ05AB1234', 120.00, 'Available'),
('R15 V4', 'Yamaha', 'Sports', 'GJ05CD5678', 150.00, 'Available'),
('Activa 6G', 'Honda', 'Scooter', 'GJ05EF9012', 60.00, 'Available'),
('Duke 250', 'KTM', 'Sports', 'GJ05GH3456', 160.00, 'Available'),
('Access 125', 'Suzuki', 'Scooter', 'GJ05IJ7890', 65.00, 'Available')
ON DUPLICATE KEY UPDATE registration_no=registration_no;