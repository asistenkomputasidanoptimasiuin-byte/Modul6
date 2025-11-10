-- Buat database
CREATE DATABASE pabrik_kertas;
USE pabrik_kertas;

-- Tabel bahan baku
CREATE TABLE raw_materials (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    stock DECIMAL(10,2) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    min_stock DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabel produk jadi
CREATE TABLE finished_products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    stock DECIMAL(10,2) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    min_stock DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabel mesin
CREATE TABLE machines (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    status ENUM('running', 'maintenance', 'stopped') NOT NULL,
    planned_production_time INT NOT NULL,
    downtime INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabel produksi harian
CREATE TABLE daily_production (
    id INT PRIMARY KEY AUTO_INCREMENT,
    date DATE NOT NULL,
    machine_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    defects DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (machine_id) REFERENCES machines(id),
    FOREIGN KEY (product_id) REFERENCES finished_products(id)
);

-- Tabel penjualan
CREATE TABLE sales (
    id INT PRIMARY KEY AUTO_INCREMENT,
    date DATE NOT NULL,
    product_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES finished_products(id)
);

-- Insert data awal
INSERT INTO raw_materials (name, stock, unit, min_stock) VALUES
('Pulp Kayu', 15000, 'kg', 5000),
('Pulp Daur Ulang', 8000, 'kg', 3000),
('Bahan Kimia', 2000, 'kg', 1000);

INSERT INTO finished_products (name, stock, unit, min_stock) VALUES
('Kertas HVS A4', 50000, 'rim', 10000),
('Kertas Koran', 30000, 'rim', 8000),
('Kertas Kemasan', 20000, 'rim', 5000);

INSERT INTO machines (name, status, planned_production_time, downtime) VALUES
('Mesin Paper Machine 1', 'running', 480, 45),
('Mesin Paper Machine 2', 'maintenance', 480, 120),
('Mesin Coating 1', 'running', 480, 30);

INSERT INTO daily_production (date, machine_id, product_id, quantity, defects) VALUES
('2024-01-01', 1, 1, 12000, 120),
('2024-01-01', 2, 2, 8000, 160),
('2024-01-02', 1, 1, 11500, 115);

-- Insert data penjualan contoh
INSERT INTO sales (date, product_id, quantity) VALUES
('2023-01-01', 1, 12000),
('2023-02-01', 1, 12500),
('2023-03-01', 1, 13000),
('2023-04-01', 1, 13500),
('2023-05-01', 1, 14000),
('2023-06-01', 1, 14500),
('2023-07-01', 1, 15000),
('2023-08-01', 1, 15500),
('2023-09-01', 1, 16000),
('2023-10-01', 1, 16500),
('2023-11-01', 1, 17000),
('2023-12-01', 1, 17500);
