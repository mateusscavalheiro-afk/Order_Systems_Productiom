# Back_end FLASK > API Rest's Routes
from flask import Flask, jsonify, request
from flask_cors import CORS
from database import init_db, get_connection
import datetime 
import os
from dotenv import load_dotenv as ldv
from functools import wraps

# Flask defines the server-side logic and endpoints, while Flask-CORS bypasses browser security restrictions to 
# let different domains (like a React frontend and a Python backend) interact

# Create an Flash's application instance
app = Flask(__name__, static_folder='static', static_url_path='')

# Enable CORS
CORS(app)

# ── Safe Config. ────────────────────────────
# In production: use enviroment variable (os.environ.get('API_KEY'))
# Import .env safe key
ldv()

API_KEY = os.environ.get('API_KEY')

def aut_need(f):
    """
    Formatter protects routes, requiring a valid API key.
    
    Client must send header:
        X-API-Key: <API_KEY value set>
        
    If key is incorret or apsent, returns 401 Unauthorized.
    If correct, execute normally route.
    
    Uses:
        @app.route('/route')
        @aut_need
        def my_route():
        ...
    """
    
    @wraps(f) # Preserve name and docstring from original function

    def formatter(*args, **kwargs):
        # Read X-API-Key require
        rcv_key = request.headers.get('X-API-Key')
        if not rcv_key:
            return jsonify({
            'error': 'Authenticate needed.',
            'instruction': 'Send X-API-Key header with your safe key.'}), 401
        if rcv_key != API_KEY:
            return jsonify({
            'error': 'Chave de API invalida ou expirada.'}), 403
        # Correct key: execute route
        return f(*args, **kwargs)
    return formatter

#In Python, decorators are special functions that “wrap” other functions, 
# adding extra behavior without altering the original code. In APIs, 
# they are essential for reusing common logic such as authentication, permission control, logging, timing, and error handling,
# applied using the @ syntax

# Route Nº1 - Initial screen
@app.route('/')

def index():
    #FEED INDEX.HTML FILE IN STATIC FOLDER
    return app.send_static_file('index.html')

# Route Nº2 - API STATUS
@app.route('/status')
@aut_need
def status():
    '''
    API's VERIFICATION ROUTE (HEALTH)
    Returns JSON informing  server's active state
    '''
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as total FROM orders')
    result = cursor.fetchone()

    return jsonify({
        "status": "online",
        "system": "Order System's Production",
        "version": "1.0.0",
        "total_orders": result["total"],
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d / %H:%M:%S"),
        "message": "Hello Factory, API working!"
    })


# Route Nº3 - List all orders (GET)
@app.route('/orders', methods=['GET'])
@aut_need
def list_orders():
    '''
    LIST ALL REGISTERED PRODUCTION ORDERS (Supports filtering by status)
    METHODS HTTP: GET
    URL: http://localhost:5000/orders?status=Pending
    Returns: Orders and list in JSON format
    '''
    status_filter = request.args.get('status')
    
    conn = get_connection()
    cursor = conn.cursor()
    
    if status_filter:
        # Added a comma after status_filter to make it a valid tuple
        cursor.execute(
            'SELECT * FROM orders WHERE status = ? ORDER BY id DESC', (status_filter,)
        )
    else:
        cursor.execute('SELECT * FROM orders ORDER BY id DESC')
        
    orders = cursor.fetchall()
    conn.close()
    
    return jsonify([dict(o) for o in orders])

# Route Nº4 - Get a specific order by ID (GET)
@app.route('/orders/<int:order_id>', methods=['GET'])
@aut_need
def search_order(order_id):
    """
    Search a unique production order.
    URL parameters:
        order_id (int): ID of the order to be searched.
    Returns:
        200 + JSON of order, if found.
        404 + error message, if it does not exist.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # The '?' switches the id in a safe way
    cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
    order = cursor.fetchone() 
    conn.close()
    
    # If ID doesn't exist, we show an error
    if order is None:
        return jsonify({'error': f'Order {order_id} not found.'}), 404
        
    return jsonify(dict(order)), 200

# Route Nº5 - Create a new order (POST)
@app.route('/orders', methods=['POST'])
@aut_need
def create_order():
    """
    Create a new production order from sended JSON data 
    
    Spected body (JSON):
        product (str): Product Name, Obligatory
        quantity (int): Pieces quantity. Obligatory, > 0.
        status (str): Optional. Standard: 'Pending'.
    Returns:
        201 + Created JSON order, in successfully cases.
        400 + error message, if invalid data.
    """
    
    data = request.get_json()
    # ── Input validation ── 
    
    # Verify if body was sended and the JSON is valid
    if not data:
        return jsonify({'error': 'Missing or invalid request body.'}), 400
    
    # Verify obligatory field 'product'
    product = data.get('product', '').strip()
    if not product:
        return jsonify({'error': 'Field "product" its obligatory and cannot be empty.'}), 400
    
    # Verify obligatory field 'quantity'
    quantity = data.get('quantity')
    if quantity is None:
        return jsonify({'error': 'Field "quantity" its obligatory and cannot be empty.'}), 400
    
    # Verify if quantity is a positive number
    try:
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({'error': 'Field "quantity" must be a positive number.'}), 400
    
    # Status it's optional; use 'Pending' if not informed
    valid_status = ['Pending', 'In progress', 'Complete']
    status = data.get('status', 'Pending')
    if status not in valid_status:
        return jsonify({'error': f'Invalid status. Use: {valid_status}'}), 400
    
    # ── Database insert ── 
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
    'INSERT INTO orders (product, quantity, status) VALUES (?, ?, ?)', (product, quantity, status))
    conn.commit()
    
    # We get the ID automatic generated by the database
    new_id = cursor.lastrowid
    conn.close()
    
    # We search the new-born register to return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders WHERE id = ?', (new_id,))
    new_order = cursor.fetchone()
    conn.close()
    
    # Returns 201 Created with complete register
    return jsonify(dict(new_order)), 201

# Route Nº6 - Order status update (PUT)
@app.route('/orders/<int:order_id>', methods=['PUT'])
@aut_need
def update_order(order_id):
    """
    Update an existent production order
    URL parameters:
        order_id (int): ID of order and update.
        Spected body (JSON):
        status (str): New status. Accepted values:
        'Pending', 'In progress', 'Complete'.
    Returns:
        200 + JSON updated order.
        400 + error if invalid status.
        404 + error if order not found.
    """
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing or invalid request body.'}), 400
    
    # Verify status field
    valid_status = ['Pending', 'In progress', 'Complete']
    new_status = data.get('status', '').strip()
    if not new_status:
        return jsonify({'error': 'Field "status" is obligatory.'}), 400
    if new_status not in valid_status:
        return jsonify({'error': f'Invalid status. Allowed values: {valid_status}'}), 400
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verify existent order before try visualize it 
    cursor.execute('SELECT id FROM orders WHERE id = ?', (order_id,))
    if cursor.fetchone() is None:
        conn.close()
        return jsonify({'error': f'Order {order_id} not found.'}),404
    # Update
    cursor.execute(
        'UPDATE orders SET status = ? WHERE id = ?', (new_status, order_id))
    conn.commit()
    conn.close()
    # Return the updated register
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
    updated_order = cursor.fetchone()
    conn.close()
    return jsonify(dict(updated_order)), 200

# Route Nº7 - Edit order (PUT)
@app.route('/orders/<int:order_id>/edit', methods=['PUT'])
@aut_need
def edit_order(order_id):
    """
    Edit an existent production order
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing or invalid request body.'}), 400
    
    # Verify product name and quantity field
    new_product = data.get('product', '').strip()
    if not new_product:
        return jsonify({'error': 'Field "product" is obligatory.'}), 400
    
    new_quantity = data.get('quantity')
    if new_quantity is None:
        return jsonify({'error': 'Field "quantity" its obligatory and cannot be empty.'}), 400
    
    # Verify if quantity is a positive number
    try:
        quantity = int(new_quantity)
        if quantity <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({'error': 'Field "quantity" must be a positive number.'}), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verify existent order before try visualize it 
    cursor.execute('SELECT id FROM orders WHERE id = ?', (order_id,))
    if cursor.fetchone() is None:
        conn.close()
        return jsonify({'error': f'Order {order_id} not found.'}), 404
    
    # ── Database update ──
    cursor.execute(
        'UPDATE orders SET product = ?, quantity = ? WHERE id = ?', 
        (new_product, quantity, order_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'message': f'Order {order_id} updated successfully.'}), 200
    
# Route Nº7 - Remove an order (DELETE) 
@app.route('/orders/<int:order_id>', methods=['DELETE'])
@aut_need
def remove_order(order_id):
    """
    Remove permanently an order searched by ID
    URL parameters:
        order_id (int): removed ID order
    Returns:
        200 + confirmation message.
        404 + error if order not found.
    """
    
    conn = get_connection()
    cursor = conn.cursor()
    # Verify the existance before DELETE
    cursor.execute('SELECT id, product FROM orders WHERE id = ?',(order_id,))
    order = cursor.fetchone()
    if order is None:
        conn.close()
        return jsonify({'error': f'Order {order_id} not found.'}), 404

    # Save the prodcut name to use in confirmation message
    name_product = order['product']
    
    # Remove
    cursor.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    conn.commit()
    conn.close()
    return jsonify({
        'message': f'Order {order_id} ({name_product}) removed with success.', 'id_removed': order_id}), 200
    
# STARTING POINT
if __name__== '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)