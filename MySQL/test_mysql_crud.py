import pytest
from mysql_crud import app, initialize_db, get_db_connection
from flask import jsonify
from flask_jwt_extended import create_access_token
import mysql.connector

# --- Test Setup ---
@pytest.fixture(scope="module")
def client():
    # Initialize the Flask app test client
    with app.test_client() as client:
        # Set up the test database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Drop the test database if exists, and create a new one
        cursor.execute("DROP DATABASE IF EXISTS test_db")
        cursor.execute("CREATE DATABASE test_db")
        
        initialize_db()  # Creates the necessary tables in the 'test_db'
        
        # Yield the test client to the tests
        yield client
        
        # Tear down 
        cursor.execute("DROP DATABASE IF EXISTS test_db")
        conn.commit()
        cursor.close()
        conn.close()

# --- Test Cases ---
def test_register(client):
    # Test user registration
    response = client.post('/register', json={'username': 'testuser', 'password': 'password123'})
    assert response.status_code == 201
    assert response.json['message'] == 'User registered successfully!'


def test_login(client):
    # Test login with correct credentials
    client.post('/register', json={'username': 'testuser1', 'password': 'password123'})
    response = client.post('/login', json={'username': 'testuser1', 'password': 'password123'})
    assert response.status_code == 200
    assert 'access_token' in response.json


def test_invalid_login(client):
    # Test invalid login with incorrect credentials
    response = client.post('/login', json={'username': 'testuser2', 'password': 'wrongpassword'})
    assert response.status_code == 401
    assert response.json['message'] == 'Invalid credentials'


def test_create_item(client):
    # Test creating an item with valid JWT token
    response = client.post('/register', json={'username': 'testuser3', 'password': 'password123'})
    login_response = client.post('/login', json={'username': 'testuser3', 'password': 'password123'})
    token = login_response.json['access_token']
    
    response = client.post('/create_item', json={'name': 'Test Item', 'description': 'Test description', 'price': 10.99},
                           headers={'Authorization': f'Bearer {token}'})
    
    assert response.status_code == 201
    assert response.json['message'] == 'Item created successfully!'
    assert 'id' in response.json
    assert isinstance(response.json['id'], int)


def test_get_item(client):
    # Test getting an item by ID
    response = client.post('/register', json={'username': 'testuser4', 'password': 'password123'})
    login_response = client.post('/login', json={'username': 'testuser4', 'password': 'password123'})
    token = login_response.json['access_token']

    item_response = client.post('/create_item', json={'name': 'Test Item 2', 'description': 'Test description 2', 'price': 10.99},
                                headers={'Authorization': f'Bearer {token}'})
    
    item_id = item_response.json['id']

    response = client.get(f'/get_item/{item_id}', headers={'Authorization': f'Bearer {token}'})
    
    assert response.status_code == 200
    assert response.json['name'] == 'Test Item 2'
    assert response.json['description'] == 'Test description 2'
    assert response.json['price'] == 10.99


def test_update_item(client):
    # Test updating an item
    response = client.post('/register', json={'username': 'testuser5', 'password': 'password123'})
    login_response = client.post('/login', json={'username': 'testuser5', 'password': 'password123'})
    token = login_response.json['access_token']
    
    item_response = client.post('/create_item', json={'name': 'Test Item 3', 'description': 'Test description 3', 'price': 10.99},
                                headers={'Authorization': f'Bearer {token}'})
    item_id = item_response.json['id']

    response = client.put(f'/update_item/{item_id}', json={'name': 'Updated Item', 'description': 'Updated description', 'price': 12.99},
                          headers={'Authorization': f'Bearer {token}'})
    
    assert response.status_code == 200
    assert response.json['message'] == 'Item updated successfully!'



def test_delete_item(client):
    # Test deleting an item

    response = client.post('/register', json={'username': 'testuser6', 'password': 'password123'})
    login_response = client.post('/login', json={'username': 'testuser6', 'password': 'password123'})
    token = login_response.json['access_token']

    item_response = client.post('/create_item', json={'name': 'Test Item 4', 'description': 'Test description 4', 'price': 10.99},
                                headers={'Authorization': f'Bearer {token}'})
    item_id = item_response.json['id']

    response = client.delete(f'/delete_item/{item_id}', headers={'Authorization': f'Bearer {token}'})
    
    assert response.status_code == 200
    assert response.json['message'] == 'Item deleted successfully!'

def test_get_all_items(client):
    # Test getting all items
    response = client.post('/register', json={'username': 'testuser7', 'password': 'password123'})
    login_response = client.post('/login', json={'username': 'testuser7', 'password': 'password123'})
    token = login_response.json['access_token']

    client.post('/create_item', json={'name': 'Test Item 5', 'description': 'Test description 5', 'price': 15.99},
                headers={'Authorization': f'Bearer {token}'})
    client.post('/create_item', json={'name': 'Test Item 6', 'description': 'Test description 6', 'price': 20.99},
                headers={'Authorization': f'Bearer {token}'})

    response = client.get('/all_items', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    assert isinstance(response.json['items'], list)
    assert len(response.json['items']) >= 2  
    assert 'id' in response.json['items'][0] 
    assert 'name' in response.json['items'][0] 
