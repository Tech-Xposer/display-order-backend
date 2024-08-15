from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from datetime import datetime
import os
from pymongo import MongoClient

app = Flask(__name__)

frontend_origin = os.getenv('FRONTEND_ORIGIN', 'http://localhost:3000')
port = os.getenv('PORT')

CORS(app, resources={r"/*": {"origins": frontend_origin}})
socketio = SocketIO(app, cors_allowed_origins=frontend_origin)

# MongoDB setup
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['order_db']
orders_collection = db['orders']

@app.route('/')
def index():
    return render_template('marketing.html')

@app.route('/add_order', methods=['GET', 'POST'])
def add_order():
    if request.method == 'POST':
        data = request.form
        order = {
            'order_number': data.get('order_number'),
            'party_name': data.get('party_name'),
            'station_name': data.get('station_name'),
            'division': data.get('division'),
            'transport': data.get('transport'),
            'promotional_material': data.get('promotional_material'),
            'date_and_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'marketing'  # Mark as marketing
        }
        orders_collection.insert_one(order)  # Save order to MongoDB
        socketio.emit('update', order)
        return render_template('marketing.html', message="Order added successfully!")
    return render_template('marketing.html')

@app.route('/update_packaging', methods=['GET', 'POST'])
def update_packaging():
    if request.method == 'POST':
        data = request.form
        order_number = data.get('order_number')
        total_shipper = data.get('total_shipper')
        packed = data.get('packed')
        packed_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if packed == 'yes' else None

        order = orders_collection.find_one({'order_number': order_number})
        if order:
            order['total_shipper'] = total_shipper
            order['packed'] = packed
            if packed_time:
                order['packed_time'] = packed_time
            order['status'] = 'packaging'  # Update status to packaging
            orders_collection.update_one({'_id': order['_id']}, {"$set": order})  # Save updated order to MongoDB
            socketio.emit('update', order)
            return render_template('packaging.html', message="Packaging details updated successfully!")
        return jsonify({'status': 'Order not found'}), 404
    return render_template('packaging.html')

@app.route('/update_billing', methods=['GET', 'POST'])
def update_billing():
    if request.method == 'POST':
        data = request.form
        order_number = data.get('order_number')
        billed = data.get('billed')
        billed_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if billed == 'yes' else None

        order = orders_collection.find_one({'order_number': order_number})
        if order:
            order['billed'] = billed
            if billed_time:
                order['billed_time'] = billed_time
            order['status'] = 'billing'  # Update status to billing
            orders_collection.update_one({'_id': order['_id']}, {"$set": order})  # Save updated order to MongoDB
            socketio.emit('update', order)
            return render_template('billing.html', message="Billing details updated successfully!")
        return jsonify({'status': 'Order not found'}), 404
    return render_template('billing.html')

@app.route('/update_dispatch', methods=['GET', 'POST'])
def update_dispatch():
    if request.method == 'POST':
        data = request.form
        order_number = data.get('order_number')
        dispatched = data.get('dispatched')
        dispatched_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if dispatched == 'yes' else None

        order = orders_collection.find_one({'order_number': order_number})
        if order:
            order['dispatched'] = dispatched
            if dispatched_time:
                order['dispatched_time'] = dispatched_time
            order['status'] = 'dispatch'  # Update status to dispatch
            orders_collection.update_one({'_id': order['_id']}, {"$set": order})  # Save updated order to MongoDB
            socketio.emit('update', order)
            return render_template('dispatch.html', message="Dispatch details updated successfully!")
        return jsonify({'status': 'Order not found'}), 404
    return render_template('dispatch.html')

@app.route('/orders', methods=['GET'])
def get_orders():
    orders = list(orders_collection.find({}))
    for order in orders:
        order['_id'] = str(order['_id'])  # Convert ObjectId to string for JSON serialization
    return jsonify(orders)

@app.route('/clear_orders', methods=['POST'])
def clear_orders():
    orders_collection.delete_many({})  # Clear all orders from MongoDB
    return jsonify({'status': 'All orders cleared'}), 200
