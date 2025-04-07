from flask import Flask, request, jsonify
import mysql.connector
import jwt
import datetime
import bcrypt
from functools import wraps
from mysql.connector import Error
from pydantic import ValidationError
from models  import CreateItemRequest, UpdateItemRequest, ItemResponse, GetAllItems

# Initialize Flask app
app = Flask(__name__)


app.config['SECRET_KEY'] = 'fc3e90f3c184d87568ba60c8dcddcc30'

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",  
            user="root", 
            password="user@123", 
            database="TestDB"
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def initialize_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f"CREATE DATABASE IF NOT EXISTS TestDB")
    
    
    # Create the items table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        price DECIMAL(10, 2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create the users table for login
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100) NOT NULL,
        password VARCHAR(255) NOT NULL
    )
    """)

    cursor.close()
    conn.close()

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1] 
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"], options={"verify_exp": True})
            current_user = data['username']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 403
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 403
        
        return f(current_user, *args, **kwargs)
    
    return decorated_function


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data.get('username') or not data.get('password'):
        return jsonify({"message": "Username and password are required!"}), 400

    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Failed to connect to the database!"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({"message": "User already exists"}), 400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, hashed_password))
        conn.commit()

        return jsonify({
            "message": "User created successfully",
            "user": {
                "username": username
            }
        }), 201
    except Error as e:
        return jsonify({"message": f"Database error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

# Route for user login (Generate JWT Token)
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data.get('username') or not data.get('password'):
        return jsonify({"message": "Username and password are required!"}), 400

    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Failed to connect to the database!"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            # Generate JWT token
            token = jwt.encode({'username': username, 'exp': datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(hours=1)},
                               app.config['SECRET_KEY'], algorithm="HS256")
            return jsonify({"access_token": token}), 200
        else:
            return jsonify({"message": "Invalid credentials"}), 401
    except Error as e:
        return jsonify({"message": f"Database error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

# Route to create an item (Protected by JWT)
@app.route('/create_item', methods=['POST'])
@token_required
def create_item(current_user):
    try:
        data = CreateItemRequest.model_validate(request.get_json())
        print(data)

    except ValidationError as e:
        return jsonify({"message": "Invalid data", "errors": e.errors()}), 400
    
    # data = request.get_json()

    name = data.name
    description = data.description
    price = data.price

    # Handle database connection
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Failed to connect to the database!"}), 500

    cursor = conn.cursor()
    try:
        # Insert item into the database
        cursor.execute('INSERT INTO items (name, description, price) VALUES (%s, %s, %s)',
                       (name, description, price))
        conn.commit()

        item_id = cursor.lastrowid
        # Return success message with item details
        return jsonify({
            "message": "Item created successfully",
            "item": {
                "id":item_id,
                "name": name,
                "description": description,
                "price": str(price) 
            }
        }), 201
    except Error as e:
        return jsonify({"message": f"Database error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

# Route to get all items (Protected by JWT)
@app.route('/get_items', methods=['GET'])
@token_required
def get_items(current_user):
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Failed to connect to the database!"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM items')
        items = cursor.fetchall()
        if items:
            items_list = [ItemResponse(id=item[0], name=item[1], description=item[2], price=item[3], created_at=item[4].isoformat()) for item in items]
            response = GetAllItems(items=items_list)
            return jsonify(response.model_dump()), 200
        else:
            return jsonify(message="No items found"), 404
    except Error as e:
        return jsonify({"message": f"Database error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/get_item_by_id/<int:item_id>', methods=['GET'])
@token_required
def get_item_by_id(current_user, item_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Failed to connect to the database!"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM items WHERE id = %s', (item_id,))
        item = cursor.fetchone()

        if item:
            item_data = ItemResponse(id=item[0], name=item[1], description=item[2], price=item[3], created_at=item[4].isoformat())
            return jsonify(item_data.model_dump()), 200
        else:
            return jsonify(message="Item not found"), 404

    except Error as e:
        return jsonify({"message": f"Database error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


# Route to update an item (Protected by JWT)
@app.route('/update_item/<int:item_id>', methods=['PUT'])
@token_required
def update_item(current_user, item_id):
    try:
        data = UpdateItemRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"message": "Invalid data", "errors": e.errors()}), 400
    
    data = request.get_json()
    print(data)

    if not data.get('name') or not data.get('price'):
        return jsonify({"message": "Name and price are required (Optional: description)!"}), 400
        
    name = data.get('name')
    description = data.get('description') 
    price = data.get('price')

    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Failed to connect to the database!"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE items SET name = %s, description = %s, price = %s WHERE id = %s',
                       (name, description, price, item_id))
        conn.commit()
        return jsonify({"message": "Item updated successfully"}), 200
    except Error as e:
        return jsonify({"message": f"Database error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

# Route to delete an item (Protected by JWT)
@app.route('/delete_item/<int:item_id>', methods=['DELETE'])
@token_required
def delete_item(current_user, item_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Failed to connect to the database!"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM items WHERE id = %s', (item_id,))
        item = cursor.fetchone()

        if not item:
            return jsonify({"message": "Item not found"}), 404  

        cursor.execute('DELETE FROM items WHERE id = %s', (item_id,))
        conn.commit()
        return jsonify({"message": "Item deleted successfully"}), 200

    except Error as e:
        return jsonify({"message": f"Database error: {str(e)}"}), 500

    finally:
        cursor.close()
        conn.close()

initialize_db()

if __name__ == '__main__':
    app.run(debug=True,port=3000)
