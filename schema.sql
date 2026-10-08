-- NestHub Apartment Management — Database Schema
-- Run this in MySQL Workbench to create the database and tables manually.
-- (Your Flask app can also create these automatically via init_db(), so this
--  file is optional — use it if you'd rather set things up from Workbench.)

CREATE DATABASE IF NOT EXISTS apartment_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE apartment_db;

CREATE TABLE IF NOT EXISTS user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150),
    phone VARCHAR(30),
    status VARCHAR(20) NOT NULL DEFAULT 'approved',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS unit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    unit_number VARCHAR(20) UNIQUE NOT NULL,
    floor INT NOT NULL,
    unit_type VARCHAR(50) NOT NULL,
    monthly_rent DECIMAL(10,2) NOT NULL,
    description TEXT,
    amenities TEXT,
    is_occupied TINYINT(1) DEFAULT 0,
    tenant_id INT,
    occupancy_start DATE,
    monthly_due_day INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES user(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS rent_record (
    id INT AUTO_INCREMENT PRIMARY KEY,
    unit_id INT NOT NULL,
    tenant_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    due_date DATE NOT NULL,
    paid_date DATE,
    is_paid TINYINT(1) DEFAULT 0,
    month_year VARCHAR(20) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (unit_id) REFERENCES unit(id),
    FOREIGN KEY (tenant_id) REFERENCES user(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS message (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    subject VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    message_type VARCHAR(30) DEFAULT 'general',
    unit_id INT,
    is_read TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES user(id),
    FOREIGN KEY (receiver_id) REFERENCES user(id),
    FOREIGN KEY (unit_id) REFERENCES unit(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS notification (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    notif_type VARCHAR(30) DEFAULT 'info',
    is_read TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
) ENGINE=InnoDB;