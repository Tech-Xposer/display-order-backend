from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId
import os
from datetime import datetime, timezone, timedelta
import pytz

load_dotenv()
app = Flask(__name__)

FRONT_END_ORIGIN = os.getenv('FRONTEND_ORIGIN', 'http://localhost:3000')
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')

CORS(app, resources={r"/*": {"origins": FRONT_END_ORIGIN}})
socketio = SocketIO(app, cors_allowed_origins=FRONT_END_ORIGIN)

# MongoDB setup
client = MongoClient(MONGODB_URI)
db = client['order_management']
orders_collection = db['orders']
trash_collection = db['trash']

def convert_to_ist(utc_time_str):
    utc_time = datetime.strptime(utc_time_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    ist_time = utc_time.astimezone(timezone(timedelta(hours=5, minutes=30)))  # IST is UTC+5:30
    return ist_time.strftime('%Y-%m-%d %H:%M:%S')

# Logging
print('frontend url:', FRONT_END_ORIGIN)
print('mongodb url:', MONGODB_URI)

@socketio.on('connect')
def on_connect():
    print('Client connected')

@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected')

@app.route('/')
def index():
    return render_template('marketing.html')

timezone = pytz.timezone("Asia/Kolkata")
current_time = datetime.now(timezone)

@app.route('/time')
def get_current_time_and_date():
    return get_current_time().strftime('%Y-%m-%d %H:%M:%S %Z%z')
def get_current_time():
    timezone = pytz.timezone("Asia/Kolkata")
    return datetime.now(timezone)

@app.route('/add_order', methods=['GET', 'POST'])
def add_order():
    try:
        if request.method == 'POST':
            data = request.form
            count = orders_collection.count_documents({})
            order = {
                'order_number': count + 1,
                'party_name': data.get('party_name'),
                'station_name': data.get('station_name'),
                'division': data.get('division'),
                'order_by': data.get('order_by'),
                'transport': data.get('transport'),
                'promotional_material': data.get('promotional_material'),
                'date_and_time': get_current_time().strftime('%Y-%m-%d %H:%M:%S %Z%z'),
                'status': 'marketing'
            }
            result = orders_collection.insert_one(order)
            order['_id'] = str(result.inserted_id)  # Convert ObjectId to string
            socketio.emit('update', order)
            return render_template('marketing.html', message="Order added successfully!")
        return render_template('marketing.html')
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/update_packaging', methods=['GET', 'POST'])
def update_packaging():
    try:
        if request.method == 'POST':
            data = request.form
            order_number = data.get('order_number')
            order_number = int(order_number)
            total_shipper = data.get('total_shipper')
            packed = data.get('packed')
            packed_time = get_current_time().strftime('%Y-%m-%d %H:%M:%S %Z%z') if packed == 'yes' else None

            order = orders_collection.find_one({'order_number': order_number})
            print(order)
            if order:
                orders_collection.update_one(
                    {'order_number': order_number},
                    {'$set': {
                        'total_shipper': total_shipper,
                        'packed': packed,
                        'packed_time': packed_time,
                        'status': 'packaging'
                    }}
                )
                updated_order = orders_collection.find_one({'order_number': order_number})
                updated_order['_id'] = str(updated_order['_id'])  # Convert ObjectId to string
                socketio.emit('update', updated_order)
                return render_template('packaging.html', message="Packaging details updated successfully!")
            return jsonify({'status': 'Order not found'}), 404
        return render_template('packaging.html')
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/update_billing', methods=['GET', 'POST'])
def update_billing():
    try:
        if request.method == 'POST':
            data = request.form
            order_number = data.get('order_number')
            order_number = int(order_number)
            billed = data.get('billed')
            billed_time = get_current_time().strftime('%Y-%m-%d %H:%M:%S %Z%z') if billed == 'yes' else None

            order = orders_collection.find_one({'order_number': order_number})
            if order:
                orders_collection.update_one(
                    {'order_number': order_number},
                    {'$set': {
                        'billed': billed,
                        'billed_time': billed_time,
                        'status': 'billing'
                    }}
                )
                updated_order = orders_collection.find_one({'order_number': order_number})
                updated_order['_id'] = str(updated_order['_id'])  # Convert ObjectId to string
                socketio.emit('update', updated_order)
                return render_template('billing.html', message="Billing details updated successfully!")
            return jsonify({'status': 'Order not found'}), 404
        return render_template('billing.html')
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/update_dispatch', methods=['GET', 'POST'])
def update_dispatch():
    try:
        if request.method == 'POST':
            data = request.form
            order_number = data.get('order_number')
            order_number = int(order_number)
            dispatched = data.get('dispatched')
            dispatched_time = get_current_time().strftime('%Y-%m-%d %H:%M:%S %Z%z') if dispatched == 'yes' else None

            order = orders_collection.find_one({'order_number': order_number})
            if order:
                orders_collection.update_one(
                    {'order_number': order_number},
                    {'$set': {
                        'dispatched': dispatched,
                        'dispatched_time': dispatched_time,
                        'status': 'dispatch'
                    }}
                )
                updated_order = orders_collection.find_one({'order_number': order_number})
                updated_order['_id'] = str(updated_order['_id'])  # Convert ObjectId to string
                socketio.emit('update', updated_order)
                return render_template('dispatch.html', message="Dispatch details updated successfully!")
            return jsonify({'status': 'Order not found'}), 404
        return render_template('dispatch.html')
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/orders', methods=['GET'])
def get_orders():
    try:
        all_orders = list(orders_collection.find())
        for order in all_orders:
            order['_id'] = str(order['_id'])  # Convert ObjectId to string
        return jsonify(all_orders)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/deleted_orders', methods=['GET'])
def get_trash_items():
    try:
        all_trashed_orders = list(trash_collection.find())
        for order in all_trashed_orders:
            order['_id'] = str(order['_id'])  # Convert ObjectId to string
        return jsonify(all_trashed_orders)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/clear_orders', methods=['POST'])
def clear_orders():
    try:
        orders = orders_collection.find()
        trash_collection.insert_many(orders)
        orders_collection.delete_many({})  # Clear all orders from MongoDB
        return jsonify({'status': 'All orders cleared'}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

#restore orders from trash
@app.route('/restore_orders', methods=['POST'])
def restore_orders():
    try:
        orders = list(trash_collection.find())
        if not orders:
            return jsonify({'status': 'error', 'message': 'No orders to restore'}), 404

        orders_collection.insert_many(orders)
        trash_collection.delete_many({})  # Clear all orders from MongoDB

        # Convert ObjectId to string for JSON serialization
        for order in orders:
            order['_id'] = str(order['_id'])

        # Emit the restored orders via Socket.IO
        socketio.emit('update', orders)
        
        return jsonify({'status': 'All orders restored', 'restored_orders': len(orders)}), 200
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    return render_template('notfound.html'), 404



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 5001)), debug=True)
