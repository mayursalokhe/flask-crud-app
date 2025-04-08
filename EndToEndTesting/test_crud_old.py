import pytest
from flask import Flask
from crud_mysql import app,  initialize_db, get_db_connection
import json

# Fixture to initialize the Flask app for testing
@pytest.fixture(scope='module')
def client():
    app.config.from_object('config.TestingConfig') 

    with app.app_context():
        initialize_db() 

    with app.test_client() as client:
        yield client  

# Fixture for setting up and tearing down the database between tests
@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS items, users")
    initialize_db()  

    yield 

    cursor.close()
    conn.close()


# @pytest.fixture
# def client():
#     app.config['MYSQL_DB'] = 'ETE_DB'
#     with app.test_client() as client:
#         yield client


@pytest.fixture
def create_user(client):
    # Register the user to ensure they exist before login test
    register_data = {
        "username": "test_user",
        "password": "testpassword"
    }
    response = client.post('/register', json=register_data)

    assert response.status_code == 201
    assert response.json['message'] == 'User created successfully'
    assert response.json['user']['username'] == 'test_user'

    return response.json['user']['username']

@pytest.fixture
def test_login(client, create_user):
    # Now that we have created the user, attempt to log in
    login_data = {
        "username": "test_user",
        "password": "testpassword"
    }
    
    response = client.post('/login', json=login_data)

    assert response.status_code == 200
    assert 'access_token' in response.json
    assert response.json['access_token'] is not None

    return response.json['access_token']

#------------------------------------------------------ Create Item -------------------------------------------------#

# Test Create Item Route
def test_create_item(client, test_login):
    token = test_login
    
    item_data = {
        "name": "Test Item",
        "description": "This is a test item",
        "price": 19.99
    }
    
    response = client.post('/create_item', 
                           json=item_data, 
                           headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 201
    assert response.json['message'] == 'Item created successfully'

# Test Create Item Route with Invalid Data (Input Validation)
def test_create_item_invalid_data(client, test_login):
    token = test_login

    invalid_data = {
        "name": "Invalid Item",
        "description": "This item has no price"
    }
    response = client.post('/create_item', 
                           json=invalid_data, 
                           headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 400
    assert 'Invalid data' in response.json['message']
    assert 'price' in response.json['errors'][0]['loc']

#-------------------------------------------------- Update Item -------------------------------------------------#

def test_update_item(client, test_login):
    token = test_login

    item_data = {
        "name": "Test Item",
        "description": "This is a test item",
        "price": 19.99
    }
    
    create_response = client.post('/create_item', 
                                  json=item_data, 
                                  headers={'Authorization': f'Bearer {token}'})

    assert create_response.status_code == 201
    assert create_response.json['message'] == 'Item created successfully'
    
    item_id = create_response.json['item']['id']

    updated_data = {
        "name": "Updated Test Item",
        "description": "This is the updated description",
        "price": 25.99
    }

    update_response = client.put(f'/update_item/{item_id}', 
                                 json=updated_data, 
                                 headers={'Authorization': f'Bearer {token}'})

    assert update_response.status_code == 200
    assert update_response.json['message'] == 'Item updated successfully'

    get_response = client.get(f'/get_item_by_id/{item_id}', 
                              headers={'Authorization': f'Bearer {token}'})
    
    assert get_response.status_code == 200
    assert get_response.json['name'] == updated_data['name']
    assert get_response.json['description'] == updated_data['description']
    assert float(get_response.json['price']) == updated_data['price']


def test_update_item_invalid_data(client, test_login):
    token = test_login

    item_data = {
        "name": "Test Item",
        "description": "This is a test item",
        "price": 19.99
    }
    
    create_response = client.post('/create_item', 
                                  json=item_data, 
                                  headers={'Authorization': f'Bearer {token}'})

    assert create_response.status_code == 201
    assert create_response.json['message'] == 'Item created successfully'
    
    item_id = create_response.json['item']['id']


    invalid_data = {
        "name": "Updated Test Item",
        "description": "This is the updated description"
    }

    update_response = client.put(f'/update_item/{item_id}', 
                                 json=invalid_data, 
                                 headers={'Authorization': f'Bearer {token}'})

    assert update_response.status_code == 400
    assert 'Name and price are required (Optional: description)!' in update_response.json['message']

#-------------------------------------- Get Item -----------------------------------#

# Test for getting all items
def test_get_items(client, test_login):
    token = test_login

    item_data = {
        "name": "Test Item",
        "description": "This is a test item",
        "price": 19.99
    }
    create_response = client.post('/create_item', 
                                  json=item_data,
                                  headers={'Authorization': f'Bearer {token}'})
    
    assert create_response.status_code == 201
    assert create_response.json['message'] == 'Item created successfully'

    response = client.get('/get_items', headers={'Authorization': f'Bearer {token}'})
    
    assert response.status_code == 200
    assert isinstance(response.json['items'], list)
    assert len(response.json['items']) > 0  # Verify that at least one item exists

# Test for getting all items when no items exist
def test_get_items_no_items(client, test_login):
    token = test_login

    # Delete all items 
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM items')
    conn.commit()
    cursor.close()
    conn.close()

    response = client.get('/get_items', headers={'Authorization': f'Bearer {token}'})
    
    assert response.status_code == 404
    assert response.json['message'] == "No items found"

# Test for getting a single item by ID
def test_get_item_by_id(client, test_login):
    token = test_login

    item_data = {
        "name": "Test Item",
        "description": "This is a test item",
        "price": 19.99
    }
    create_response = client.post('/create_item', 
                                  json=item_data,
                                  headers={'Authorization': f'Bearer {token}'})
    
    assert create_response.status_code == 201
    assert create_response.json['message'] == 'Item created successfully'

    item_id = create_response.json['item']['id']

    response = client.get(f'/get_item_by_id/{item_id}', headers={'Authorization': f'Bearer {token}'})
    
    assert response.status_code == 200
    assert response.json['id'] == item_id
    assert response.json['name'] == "Test Item"
    assert response.json['description'] == "This is a test item"
    assert response.json['price'] == 19.99

# Test for getting a single item by an invalid ID (item does not exist)
def test_get_item_by_invalid_id(client, test_login):
    token = test_login

    response = client.get('/get_item_by_id/99999', headers={'Authorization': f'Bearer {token}'})
    
    assert response.status_code == 404
    assert response.json['message'] == "Item not found"
   
#-------------------------------------- Delete Item -----------------------------#

# Test for deleting an existing item
def test_delete_item(client, test_login):
    token = test_login
    

    item_data = {
        "name": "Test Item",
        "description": "This is a test item",
        "price": 19.99
    }
    create_response = client.post('/create_item', 
                                  json=item_data,
                                  headers={'Authorization': f'Bearer {token}'})
    
    assert create_response.status_code == 201
    assert create_response.json['message'] == 'Item created successfully'

    item_id = create_response.json['item']['id']

    delete_response = client.delete(f'/delete_item/{item_id}', 
                                    headers={'Authorization': f'Bearer {token}'})
    
    assert delete_response.status_code == 200
    assert delete_response.json['message'] == "Item deleted successfully"

    get_response = client.get(f'/get_item_by_id/{item_id}', headers={'Authorization': f'Bearer {token}'})
    assert get_response.status_code == 404
    assert get_response.json['message'] == "Item not found"


# Test for trying to delete a non-existent item
def test_delete_non_existent_item(client, test_login):
    token = test_login

    response = client.delete('/delete_item/99999', headers={'Authorization': f'Bearer {token}'})
    
    assert response.status_code == 404
    assert response.json['message'] == "Item not found"
