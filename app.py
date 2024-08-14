from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)

frontend_origin = os.getenv('FRONTEND_ORIGIN', 'http://localhost:3000')


CORS(app, resources={r"/*": {"origins": frontend_origin}})
socketio = SocketIO(app, cors_allowed_origins=frontend_origin)

# Directory for storing order details
ORDER_FILES_DIR = 'backend/files'
if not os.path.exists(ORDER_FILES_DIR):
    os.makedirs(ORDER_FILES_DIR)

orders = []

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
        orders.append(order)
        save_order_to_file(order)  # Save order details to file
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

        for order in orders:
            if order['order_number'] == order_number:
                order['total_shipper'] = total_shipper
                order['packed'] = packed
                if packed_time:
                    order['packed_time'] = packed_time
                order['status'] = 'packaging'  # Update status to packaging
                save_order_to_file(order)  # Save updated order details to file
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

        for order in orders:
            if order['order_number'] == order_number:
                order['billed'] = billed
                if billed_time:
                    order['billed_time'] = billed_time
                order['status'] = 'billing'  # Update status to billing
                save_order_to_file(order)  # Save updated order details to file
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

        for order in orders:
            if order['order_number'] == order_number:
                order['dispatched'] = dispatched
                if dispatched_time:
                    order['dispatched_time'] = dispatched_time
                order['status'] = 'dispatch'  # Update status to dispatch
                save_order_to_file(order)  # Save updated order details to file
                socketio.emit('update', order)
                return render_template('dispatch.html', message="Dispatch details updated successfully!")
        return jsonify({'status': 'Order not found'}), 404
    return render_template('dispatch.html')

@app.route('/orders', methods=['GET'])
def get_orders():
    return jsonify(orders)

def save_order_to_file(order):
    filename = os.path.join(ORDER_FILES_DIR, f"{order['order_number']}.txt")
    with open(filename, 'w') as f:
        for key, value in order.items():
            f.write(f"{key}: {value}\n")
        f.write("\n")  # Add an extra newline for separation

@app.route('/clear_orders', methods=['POST'])
def clear_orders():
    global orders
    orders = []  # Clear the orders list
    # Optionally, clear the files as well
    for filename in os.listdir(ORDER_FILES_DIR):
        file_path = os.path.join(ORDER_FILES_DIR, filename)
        os.remove(file_path)
    return jsonify({'status': 'All orders cleared'}), 200

if __name__ == '__main__':
    socketio.run(app, debug=True)
    app.run(host='localhost', debug=True)
