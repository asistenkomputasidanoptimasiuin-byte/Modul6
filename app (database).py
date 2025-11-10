from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime, timedelta
import math
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# Konfigurasi database MySQL
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  
    'password': '',  
    'database': 'pabrik_kertas'
}

def get_db_connection():
    """Membuat koneksi ke database MySQL"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Fungsi-fungsi untuk membaca data dari MySQL
def load_inventory_data():
    """Memuat data inventory dari MySQL"""
    connection = get_db_connection()
    if not connection:
        return {"raw_materials": [], "finished_products": []}
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Ambil data raw materials
        cursor.execute("SELECT * FROM raw_materials")
        raw_materials = cursor.fetchall()
        
        # Konversi decimal ke float untuk JSON serialization
        for material in raw_materials:
            material['stock'] = float(material['stock'])
            material['min_stock'] = float(material['min_stock'])
        
        # Ambil data finished products
        cursor.execute("SELECT * FROM finished_products")
        finished_products = cursor.fetchall()
        
        # Konversi decimal ke float untuk JSON serialization
        for product in finished_products:
            product['stock'] = float(product['stock'])
            product['min_stock'] = float(product['min_stock'])
        
        return {
            "raw_materials": raw_materials,
            "finished_products": finished_products
        }
    except Error as e:
        print(f"Error loading inventory data: {e}")
        return {"raw_materials": [], "finished_products": []}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def load_machines_data():
    """Memuat data mesin dari MySQL"""
    connection = get_db_connection()
    if not connection:
        return {"machines": []}
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM machines")
        machines = cursor.fetchall()
        
        return {"machines": machines}
    except Error as e:
        print(f"Error loading machines data: {e}")
        return {"machines": []}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def load_production_data():
    """Memuat data produksi dari MySQL"""
    connection = get_db_connection()
    if not connection:
        return {"daily_production": []}
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM daily_production")
        daily_production = cursor.fetchall()
        
        # Konversi decimal ke float
        for production in daily_production:
            production['quantity'] = float(production['quantity'])
            production['defects'] = float(production['defects'])
            # Konversi date ke string
            production['date'] = production['date'].isoformat()
        
        return {"daily_production": daily_production}
    except Error as e:
        print(f"Error loading production data: {e}")
        return {"daily_production": []}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def load_sales_data():
    """Memuat data penjualan dari MySQL"""
    connection = get_db_connection()
    if not connection:
        return {"sales": []}
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM sales ORDER BY date")
        sales = cursor.fetchall()
        
        # Konversi decimal ke float dan date ke string
        for sale in sales:
            sale['quantity'] = float(sale['quantity'])
            sale['date'] = sale['date'].isoformat()
        
        return {"sales": sales}
    except Error as e:
        print(f"Error loading sales data: {e}")
        return {"sales": []}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Fungsi OEE tetap sama
def calculate_oee(machine_id, production_data):
    machine_production = [p for p in production_data if p.get('machine_id') == machine_id]
    
    if not machine_production:
        return {"availability": 0, "performance": 0, "quality": 0, "oee": 0}
    
    # Load machine data
    machines_data = load_machines_data()
    machine = next((m for m in machines_data.get('machines', []) if m['id'] == machine_id), None)
    
    if not machine:
        return {"availability": 0, "performance": 0, "quality": 0, "oee": 0}
    
    # Availability = (Planned Production Time - Downtime) / Planned Production Time
    planned_time = machine.get('planned_production_time', 480)
    downtime = machine.get('downtime', 0)
    availability = ((planned_time - downtime) / planned_time) * 100
    
    # Performance = (Total Pieces / Ideal Production Rate) / Operating Time
    total_quantity = sum(p.get('quantity', 0) for p in machine_production)
    ideal_rate = 1000  # pieces per hour (example)
    operating_time = planned_time - downtime
    performance = (total_quantity / (ideal_rate * (operating_time / 60))) * 100
    performance = min(performance, 100)  # Cap at 100%
    
    # Quality = Good Pieces / Total Pieces
    total_defects = sum(p.get('defects', 0) for p in machine_production)
    quality = ((total_quantity - total_defects) / total_quantity) * 100 if total_quantity > 0 else 0
    
    # OEE = Availability × Performance × Quality
    oee = (availability / 100) * (performance / 100) * (quality / 100) * 100
    
    return {
        "availability": round(availability, 2),
        "performance": round(performance, 2),
        "quality": round(quality, 2),
        "oee": round(oee, 2)
    }

# Fungsi forecasting tetap sama
def forecast_demand(sales_data, periods=3):
    if not sales_data:
        return []
    
    quantities = [sale['quantity'] for sale in sales_data]
    n = len(quantities)
    
    sum_x = sum(range(n))
    sum_y = sum(quantities)
    sum_xy = sum(i * quantities[i] for i in range(n))
    sum_x2 = sum(i**2 for i in range(n))
    
    denominator = n * sum_x2 - sum_x**2
    if denominator == 0:
        slope = 0
    else:
        slope = (n * sum_xy - sum_x * sum_y) / denominator
    
    intercept = (sum_y - slope * sum_x) / n
    
    forecasts = []
    for i in range(n, n + periods):
        forecast = intercept + slope * i
        forecasts.append({
            "period": i - n + 1,
            "forecast": round(forecast)
        })
    
    return forecasts

# Routes - Diperbarui untuk menggunakan fungsi MySQL
@app.route('/')
def dashboard():
    inventory_data = load_inventory_data()
    machines_data = load_machines_data()
    production_data = load_production_data().get('daily_production', [])
    
    # Calculate OEE for each machine
    oee_data = {}
    for machine in machines_data.get('machines', []):
        oee_data[machine['id']] = calculate_oee(machine['id'], production_data)
    
    # Check low stock alerts
    low_stock_alerts = []
    for material in inventory_data.get('raw_materials', []):
        if material['stock'] < material['min_stock']:
            low_stock_alerts.append(f"{material['name']} stock rendah: {material['stock']} {material['unit']}")
    
    for product in inventory_data.get('finished_products', []):
        if product['stock'] < product['min_stock']:
            low_stock_alerts.append(f"{product['name']} stock rendah: {product['stock']} {product['unit']}")
    
    return render_template('dashboard.html', 
                         inventory=inventory_data,
                         machines=machines_data.get('machines', []),
                         oee_data=oee_data,
                         alerts=low_stock_alerts)

@app.route('/inventory')
def inventory():
    inventory_data = load_inventory_data()
    return render_template('inventory.html', inventory=inventory_data)

@app.route('/production')
def production():
    machines_data = load_machines_data()
    production_data = load_production_data()
    
    # Calculate OEE for each machine
    oee_data = {}
    for machine in machines_data.get('machines', []):
        oee_data[machine['id']] = calculate_oee(machine['id'], production_data.get('daily_production', []))
    
    return render_template('production.html', 
                         machines=machines_data.get('machines', []),
                         production=production_data.get('daily_production', []),
                         oee_data=oee_data)

@app.route('/analysis')
def analysis():
    sales_data = load_sales_data().get('sales', [])
    forecasts = forecast_demand(sales_data)
    
    # Prepare data for charts
    sales_dates = [sale['date'] for sale in sales_data]
    sales_quantities = [sale['quantity'] for sale in sales_data]
    
    return render_template('analysis.html',
                         sales_data=sales_data,
                         forecasts=forecasts,
                         sales_dates=json.dumps(sales_dates),
                         sales_quantities=json.dumps(sales_quantities))

# API endpoints - Diperbarui untuk MySQL
@app.route('/api/update_inventory', methods=['POST'])
def update_inventory():
    data = request.json
    connection = get_db_connection()
    if not connection:
        return jsonify({"status": "error", "message": "Database connection failed"})
    
    try:
        cursor = connection.cursor()
        
        # Update raw materials
        if 'raw_materials' in data:
            for material in data['raw_materials']:
                cursor.execute(
                    "UPDATE raw_materials SET stock = %s, min_stock = %s WHERE id = %s",
                    (material['stock'], material['min_stock'], material['id'])
                )
        
        # Update finished products
        if 'finished_products' in data:
            for product in data['finished_products']:
                cursor.execute(
                    "UPDATE finished_products SET stock = %s, min_stock = %s WHERE id = %s",
                    (product['stock'], product['min_stock'], product['id'])
                )
        
        connection.commit()
        return jsonify({"status": "success"})
        
    except Error as e:
        connection.rollback()
        return jsonify({"status": "error", "message": str(e)})
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/update_machine', methods=['POST'])
def update_machine():
    data = request.json
    connection = get_db_connection()
    if not connection:
        return jsonify({"status": "error", "message": "Database connection failed"})
    
    try:
        cursor = connection.cursor()
        
        for machine in data['machines']:
            cursor.execute(
                "UPDATE machines SET status = %s, planned_production_time = %s, downtime = %s WHERE id = %s",
                (machine['status'], machine['planned_production_time'], machine['downtime'], machine['id'])
            )
        
        connection.commit()
        return jsonify({"status": "success"})
        
    except Error as e:
        connection.rollback()
        return jsonify({"status": "error", "message": str(e)})
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/add_production', methods=['POST'])
def add_production():
    data = request.json
    connection = get_db_connection()
    if not connection:
        return jsonify({"status": "error", "message": "Database connection failed"})
    
    try:
        cursor = connection.cursor()
        
        cursor.execute(
            "INSERT INTO daily_production (date, machine_id, product_id, quantity, defects) VALUES (%s, %s, %s, %s, %s)",
            (datetime.now().strftime("%Y-%m-%d"), data['machine_id'], data['product_id'], data['quantity'], data.get('defects', 0))
        )
        
        connection.commit()
        return jsonify({"status": "success"})
        
    except Error as e:
        connection.rollback()
        return jsonify({"status": "error", "message": str(e)})
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    print("Starting Flask app with MySQL...")
    app.run(debug=True)
