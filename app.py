from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime, timedelta
import math

app = Flask(__name__)

# Data storage files
DATA_DIR = 'data'
INVENTORY_FILE = os.path.join(DATA_DIR, 'inventory.json')
MACHINES_FILE = os.path.join(DATA_DIR, 'machines.json')
PRODUCTION_FILE = os.path.join(DATA_DIR, 'production.json')
SALES_FILE = os.path.join(DATA_DIR, 'sales.json')

# Initialize data files
def init_data_files():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    # Initialize inventory data
    if not os.path.exists(INVENTORY_FILE):
        inventory_data = {
            "raw_materials": [
                {"id": 1, "name": "Pulp Kayu", "stock": 15000, "unit": "kg", "min_stock": 5000},
                {"id": 2, "name": "Pulp Daur Ulang", "stock": 8000, "unit": "kg", "min_stock": 3000},
                {"id": 3, "name": "Bahan Kimia", "stock": 2000, "unit": "kg", "min_stock": 1000}
            ],
            "finished_products": [
                {"id": 1, "name": "Kertas HVS A4", "stock": 50000, "unit": "rim", "min_stock": 10000},
                {"id": 2, "name": "Kertas Koran", "stock": 30000, "unit": "rim", "min_stock": 8000},
                {"id": 3, "name": "Kertas Kemasan", "stock": 20000, "unit": "rim", "min_stock": 5000}
            ]
        }
        with open(INVENTORY_FILE, 'w') as f:
            json.dump(inventory_data, f, indent=4)
    
    # Initialize machines data
    if not os.path.exists(MACHINES_FILE):
        machines_data = {
            "machines": [
                {"id": 1, "name": "Mesin Paper Machine 1", "status": "running", "planned_production_time": 480, "downtime": 45},
                {"id": 2, "name": "Mesin Paper Machine 2", "status": "maintenance", "planned_production_time": 480, "downtime": 120},
                {"id": 3, "name": "Mesin Coating 1", "status": "running", "planned_production_time": 480, "downtime": 30}
            ]
        }
        with open(MACHINES_FILE, 'w') as f:
            json.dump(machines_data, f, indent=4)
    
    # Initialize production data
    if not os.path.exists(PRODUCTION_FILE):
        production_data = {
            "daily_production": [
                {"date": "2024-01-01", "machine_id": 1, "product_id": 1, "quantity": 12000, "defects": 120},
                {"date": "2024-01-01", "machine_id": 2, "product_id": 2, "quantity": 8000, "defects": 160},
                {"date": "2024-01-02", "machine_id": 1, "product_id": 1, "quantity": 11500, "defects": 115}
            ]
        }
        with open(PRODUCTION_FILE, 'w') as f:
            json.dump(production_data, f, indent=4)
    
    # Initialize sales data for forecasting
    if not os.path.exists(SALES_FILE):
        # Generate sample sales data for the past 12 months
        sales_data = {"sales": []}
        base_date = datetime(2023, 1, 1)
        base_sales = [12000, 12500, 13000, 13500, 14000, 14500, 15000, 15500, 16000, 16500, 17000, 17500]
        
        for i in range(12):
            month_date = base_date + timedelta(days=30*i)
            sales_data["sales"].append({
                "date": month_date.strftime("%Y-%m-%d"),
                "product_id": 1,
                "quantity": base_sales[i] + (i * 500)  # Trend dengan sedikit variasi
            })
        
        with open(SALES_FILE, 'w') as f:
            json.dump(sales_data, f, indent=4)

# Load data from JSON files
def load_data(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save data to JSON files
def save_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

# Calculate OEE for a machine
def calculate_oee(machine_id, production_data):
    machine_production = [p for p in production_data if p.get('machine_id') == machine_id]
    
    if not machine_production:
        return {"availability": 0, "performance": 0, "quality": 0, "oee": 0}
    
    # Load machine data
    machines_data = load_data(MACHINES_FILE)
    machine = next((m for m in machines_data.get('machines', []) if m['id'] == machine_id), None)
    
    if not machine:
        return {"availability": 0, "performance": 0, "quality": 0, "oee": 0}
    
    # Availability = (Planned Production Time - Downtime) / Planned Production Time
    planned_time = machine.get('planned_production_time', 480)
    downtime = machine.get('downtime', 0)
    availability = ((planned_time - downtime) / planned_time) * 100
    
    # Performance = (Total Pieces / Ideal Production Rate) / Operating Time
    # Simplified calculation for demo
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

# Simple forecasting using linear regression
def forecast_demand(sales_data, periods=3):
    if not sales_data:
        return []
    
    # Extract quantities and create time indices
    quantities = [sale['quantity'] for sale in sales_data]
    n = len(quantities)
    
    # Calculate linear regression
    sum_x = sum(range(n))
    sum_y = sum(quantities)
    sum_xy = sum(i * quantities[i] for i in range(n))
    sum_x2 = sum(i**2 for i in range(n))
    
    # Slope and intercept
    denominator = n * sum_x2 - sum_x**2
    if denominator == 0:
        slope = 0
    else:
        slope = (n * sum_xy - sum_x * sum_y) / denominator
    
    intercept = (sum_y - slope * sum_x) / n
    
    # Generate forecasts
    forecasts = []
    for i in range(n, n + periods):
        forecast = intercept + slope * i
        forecasts.append({
            "period": i - n + 1,
            "forecast": round(forecast)
        })
    
    return forecasts

# Routes
@app.route('/')
def dashboard():
    inventory_data = load_data(INVENTORY_FILE)
    machines_data = load_data(MACHINES_FILE)
    production_data = load_data(PRODUCTION_FILE).get('daily_production', [])
    
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
    inventory_data = load_data(INVENTORY_FILE)
    return render_template('inventory.html', inventory=inventory_data)

@app.route('/production')
def production():
    machines_data = load_data(MACHINES_FILE)
    production_data = load_data(PRODUCTION_FILE)
    
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
    sales_data = load_data(SALES_FILE).get('sales', [])
    forecasts = forecast_demand(sales_data)
    
    # Prepare data for charts
    sales_dates = [sale['date'] for sale in sales_data]
    sales_quantities = [sale['quantity'] for sale in sales_data]
    
    return render_template('analysis.html',
                         sales_data=sales_data,
                         forecasts=forecasts,
                         sales_dates=json.dumps(sales_dates),
                         sales_quantities=json.dumps(sales_quantities))

# API endpoints for data updates
@app.route('/api/update_inventory', methods=['POST'])
def update_inventory():
    data = request.json
    inventory_data = load_data(INVENTORY_FILE)
    
    # Update raw materials
    if 'raw_materials' in data:
        for updated_material in data['raw_materials']:
            for material in inventory_data['raw_materials']:
                if material['id'] == updated_material['id']:
                    material.update(updated_material)
                    break
    
    # Update finished products
    if 'finished_products' in data:
        for updated_product in data['finished_products']:
            for product in inventory_data['finished_products']:
                if product['id'] == updated_product['id']:
                    product.update(updated_product)
                    break
    
    save_data(INVENTORY_FILE, inventory_data)
    return jsonify({"status": "success"})

@app.route('/api/update_machine', methods=['POST'])
def update_machine():
    data = request.json
    machines_data = load_data(MACHINES_FILE)
    
    for updated_machine in data['machines']:
        for machine in machines_data['machines']:
            if machine['id'] == updated_machine['id']:
                machine.update(updated_machine)
                break
    
    save_data(MACHINES_FILE, machines_data)
    return jsonify({"status": "success"})

@app.route('/api/add_production', methods=['POST'])
def add_production():
    data = request.json
    production_data = load_data(PRODUCTION_FILE)
    
    # Add new production record
    new_record = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "machine_id": data['machine_id'],
        "product_id": data['product_id'],
        "quantity": data['quantity'],
        "defects": data.get('defects', 0)
    }
    
    production_data['daily_production'].append(new_record)
    save_data(PRODUCTION_FILE, production_data)
    
    return jsonify({"status": "success"})

if __name__ == '__main__':
    print("Initializing data files...")
    init_data_files()
    print("Starting Flask app...")
    app.run(debug=True)
