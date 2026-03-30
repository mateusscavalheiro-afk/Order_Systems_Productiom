# Database > Creation and configuration of SQLite database
import sqlite3

# Constant with name of the database
# The file will be created during the first execution
db_order = 'orders.bd'

def get_connection():
    '''
    Create and return a connection with SQLite database
    
    The property row_factory allows the access of the columns by name
    (Ex: order['product'] instead of index (Ex: order[1]))
    
    Return:
        sqlite3.Connection: Connection object with database
    '''
    
    conn = sqlite3.connect(db_order)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    '''
    Initialize database creating a table named 'orders' if does not exists. 
    Safe to call multiple times.
    '''
    
    conn = get_connection()
    
    # Cursor allows the execution of SQL commands
    cursor = conn.cursor()
    
    # 'IF NOT EXISTS' ensures the command don't fails if the table exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    status TEXT DEFAULT 'Pendente',
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
    )
    ''')
    
    # commit() Saves changes in .db file
    conn.commit()
    print("Database successfully initialized!")
    
init_db()
