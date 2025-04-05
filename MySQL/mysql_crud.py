from datetime import timedelta
from flask import Flask, jsonify, request 
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
from typing import List

load_dotenv()

app = Flask(__name__)

# Load configuration from environment variables
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
# app.config['MYSQL_DB'] = 'test_db'

# Initialize the JWT manager
jwt = JWTManager(app)

# Function to create MySQL connection
def get_db_connection():
    return mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB']
    )

# Function to create the database and table if they don't exist
def initialize_db():
    conn = mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD']
    )
    cursor = conn.cursor()

    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {app.config['MYSQL_DB']}")
    
    conn.database = app.config['MYSQL_DB']
    
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

# Pydantic models for user and item data validation
class RegisterUser(BaseModel):
    username: str = Field(..., min_length=8, max_length=10)
    password: str = Field(..., min_length=6)

class LoginUser(BaseModel):
    username: str
    password: str

class CreateItem(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=3)
    price: float = Field(..., ge=0)

class UpdateItem(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=3)
    price: float = Field(..., ge=0)

class ItemResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    created_at: str

class GetAllItems(BaseModel):
    items: List[ItemResponse]

# User registration endpoint
@app.route('/register', methods=['POST'])
def register():
    try:
        data = RegisterUser.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify(errors=e.errors()), 400

    hashed_password = generate_password_hash(data.password)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (data.username, hashed_password))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify(message="User registered successfully!"), 201

# User login endpoint (generate JWT token)
@app.route('/login', methods=['POST'])
def login():
    try:
        data = LoginUser.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify(errors=e.errors()), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM users WHERE username = %s", (data.username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[2], data.password):  
            access_token = create_access_token(identity=data.username, fresh=True, expires_delta=timedelta(minutes=30))
            return jsonify(access_token=access_token), 200
        else:
            return jsonify(message="Invalid credentials"), 401
    except mysql.connector.Error as e:
        return jsonify(message=f"Database error: {str(e)}"), 500
    finally:
        cursor.close()
        conn.close()

# Protected route (requires JWT token)
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    return jsonify(message="You have access to this route!")

# Create Item
@app.route('/create_item', methods=['POST'])
@jwt_required()
def create_item():
    try:
        data = CreateItem.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify(errors=e.errors()), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO items (name, description, price) VALUES (%s, %s, %s)", 
                   (data.name, data.description, data.price))
    conn.commit()

    # Get the ID of the newly created item
    cursor.execute("SELECT LAST_INSERT_ID()")
    item_id = cursor.fetchone()[0]  # Fetch the generated ID

    cursor.close()
    conn.close()

    return jsonify(id=item_id, message="Item created successfully!"), 201


# Get Item by ID
@app.route('/get_item/<int:id>', methods=['GET'])
@jwt_required()
def get_item(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE id = %s", (id,))
    item = cursor.fetchone()
    cursor.close()
    conn.close()

    if item:
        item_data = ItemResponse(id=item[0], name=item[1], description=item[2], price=item[3], created_at=item[4].isoformat())
        return jsonify(item_data.model_dump()), 200
    else:
        return jsonify(message="Item not found"), 404

# Update Item by ID
@app.route('/update_item/<int:id>', methods=['PUT'])
@jwt_required()
def update_item(id):
    try:
        data = UpdateItem.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify(errors=e.errors()), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE items SET name = %s, description = %s, price = %s WHERE id = %s", 
                   (data.name, data.description, data.price, id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify(message="Item updated successfully!"), 200

# Delete Item by ID
@app.route('/delete_item/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_item(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify(message="Item deleted successfully!"), 200

# Get all items
@app.route('/all_items', methods=['GET'])
@jwt_required()
def get_all_items():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM items")  
        items = cursor.fetchall()

        if items:
            items_list = [ItemResponse(id=item[0], name=item[1], description=item[2], price=item[3], created_at=item[4].isoformat()) for item in items]
            response = GetAllItems(items=items_list)
            return jsonify(response.model_dump()), 200
        else:
            return jsonify(message="No items found"), 404
    except Exception as e:
        return jsonify(message=f"Error: {str(e)}"), 500
    finally:
        cursor.close()
        conn.close()

# Initialize the database before the application runs
initialize_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
