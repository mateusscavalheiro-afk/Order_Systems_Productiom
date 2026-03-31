# Back_end FLASK > API Rest's Routes
from flask import Flask, jsonify, request
from flask_cors import CORS
from database import init_db, get_connection

# Create an Flash's application instance
app = Flask(__name__, static_folder='static', static_url_path='')

# Habilitate CORS
CORS(app)

# Route Nº1 - Initial screen
@app.route('/')

def index():
    #FEED INDEX.HTML FILE IN STATIC FOLDER
    return app.send_static_file('index.html')

# Route Nº2 - API STATUS
@app.route('/status')
def status():
    '''
    API's VERIFICATION ROUTE (HEALTH)
    Returns JSON informing  server's active state
    '''

    return jsonify({
        "status": "online",
        "system": "Order System's Production",
        "version": "1.0.0",
        "message": "Hello Factory, API working!"
    })

#Route Nº3 - List all orders (GET)
@app.route('/orders', methods=['GET'])

def list_orders():
    '''
    LIST ALL REGISTEREDF PRODUCTION ORDERS
    METHODS HTTP: GET
    URL: https://localhost:5000/orders
    Returns: Orders and list in JSON format
    '''
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders ORDER BY id DESC')
    orders = cursor.fetchall()
    conn.close()
    
    # Converts every SQLite Row in Python dictionary to serialize in JSOn
    return jsonify([dict(o) for o in orders])

# STARTING POINT
if __name__== '__main__':
    init_db()
    
    app.run(debug=True, host='0.0.0.0', port=5000)