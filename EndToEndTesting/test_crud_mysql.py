import pytest
import requests
from models import ItemResponse, GetAllItems, CreateItemRequest, UpdateItemRequest
# import mysql.connector
# from mysql.connector import Error

BASE_URL = "http://localhost:3000"


@pytest.fixture
def create_user():
    register_data = {
        "username": "test_user",
        "password": "testpassword"
    }
    response = requests.post(f'{BASE_URL}/register', json=register_data)

    assert response.status_code == 201
    assert response.json()['message'] == 'User created successfully'
    assert response.json()['user']['username'] == 'test_user'

    return response.json()['user']['username']


@pytest.fixture
def test_login():
    login_data = {
        "username": "test_user",
        "password": "testpassword"
    }
    
    response = requests.post(f'{BASE_URL}/login', json=login_data)

    assert response.status_code == 200
    json_data = response.json()  
    assert 'access_token' in json_data
    assert json_data['access_token'] is not None

    return json_data['access_token']


#------------------------------------------------------ Create Item -------------------------------------------------#

def test_create_item(test_login):
    token = test_login
    
    item_data = {
        "name": "Test Item",
        "description": "This is a test item",
        "price": 19.99
    }
    
    response = requests.post(f'{BASE_URL}/create_item',
                             json=item_data, 
                             headers={'Authorization': f'Bearer {token}'})

    json_data = response.json()
    assert response.status_code == 201
    assert json_data['message'] == 'Item created successfully'
    
    # Extract the 'item' field from the response
    item_data_from_response = json_data['item']
    
    # Validate response using ItemResponse Pydantic model
    item = ItemResponse(**item_data_from_response)
    
    assert item.name == item_data['name']
    assert item.description == item_data['description']
    assert item.price == item_data['price']



def test_create_item_invalid_data(test_login):
    token = test_login

    invalid_data = {
        "name": "Invalid Item",
        "description": "This item has no price"
    }
    response = requests.post(f'{BASE_URL}/create_item', 
                           json=invalid_data, 
                           headers={'Authorization': f'Bearer {token}'})


    json_data = response.json()
    assert response.status_code == 400
    assert 'Invalid data' in json_data['message']
    assert 'price' in json_data['errors'][0]['loc']

# Edge test case: Empty request body
def test_create_item_empty_body(test_login):
    token = test_login
    
    response = requests.post(f'{BASE_URL}/create_item',
                             json={},  # Empty body
                             headers={'Authorization': f'Bearer {token}'})
    
    assert response.status_code == 400  # Bad Request
    json_data = response.json()
    assert 'message' in json_data
    assert json_data['message'] == 'Invalid data'



#-------------------------------------------------- Update Item -------------------------------------------------#

def test_update_item(test_login):
    token = test_login

    item_data = {
        "name": "Test Item",
        "description": "This is a test item",
        "price": 19.99
    }
    
    create_response = requests.post(f'{BASE_URL}/create_item', 
                                  json=item_data, 
                                  headers={'Authorization': f'Bearer {token}'})


    json_data = create_response.json()
    assert create_response.status_code == 201
    assert json_data['message'] == 'Item created successfully'
    
    item_id = json_data['item']['id']

    updated_data = {
        "name": "Updated Test Item",
        "description": "This is the updated description",
        "price": 25.99
    }

    update_response = requests.put(f'{BASE_URL}/update_item/{item_id}', 
                                 json=updated_data, 
                                 headers={'Authorization': f'Bearer {token}'})


    json_update_data = update_response.json()
    assert update_response.status_code == 200
    assert json_update_data['message'] == 'Item updated successfully'

    get_response = requests.get(f'{BASE_URL}/get_item_by_id/{item_id}', 
                              headers={'Authorization': f'Bearer {token}'})


    json_get_data = get_response.json()
    assert get_response.status_code == 200
    # Validate the response using the ItemResponse model
    item = ItemResponse(**json_get_data)
    assert item.name == updated_data['name']
    assert item.description == updated_data['description']
    assert item.price == updated_data['price']

def test_update_item_invalid_data(test_login):
    token = test_login

    item_data = {
        "name": "Test Item",
        "description": "This is a test item",
        "price": 19.99
    }
    
    create_response = requests.post(f'{BASE_URL}/create_item', 
                                  json=item_data, 
                                  headers={'Authorization': f'Bearer {token}'})


    json_create_data = create_response.json()
    assert create_response.status_code == 201
    assert json_create_data['message'] == 'Item created successfully'
    
    item_id = json_create_data['item']['id']


    invalid_data = {
        "name": "Updated Test Item",
        "description": "This is the updated description"
    }

    update_response = requests.put(f'{BASE_URL}/update_item/{item_id}', 
                                 json=invalid_data, 
                                 headers={'Authorization': f'Bearer {token}'})


    json_update_data = update_response.json()

    assert update_response.status_code == 400
    assert 'Name and price are required (Optional: description)!' in json_update_data['message']


#-------------------------------------- Get Item -----------------------------------#

# Test for getting all items
def test_get_items(test_login):
    token = test_login

    item_data = {
        "name": "Test Item",
        "description": "This is a test item",
        "price": 19.99
    }
    create_response = requests.post(f'{BASE_URL}/create_item', 
                                  json=item_data,
                                  headers={'Authorization': f'Bearer {token}'})


    json_create_data = create_response.json()
    
    assert create_response.status_code == 201
    assert json_create_data['message'] == 'Item created successfully'

    get_response = requests.get(f'{BASE_URL}/get_items', headers={'Authorization': f'Bearer {token}'})


    json_get_data = get_response.json()
    items = GetAllItems(**json_get_data)

    assert get_response.status_code == 200
    assert isinstance(items.items, list)
    assert len(items.items) > 0  # Verify that at least one item exists

# Test for getting a single item by ID
def test_get_item_by_id(test_login):
    token = test_login

    item_data = {
        "name": "Test Item",
        "description": "This is a test item",
        "price": 19.99
    }
    create_response = requests.post(f'{BASE_URL}/create_item', 
                                  json=item_data,
                                  headers={'Authorization': f'Bearer {token}'})


    json_create_data = create_response.json()
    assert create_response.status_code == 201
    assert json_create_data['message'] == 'Item created successfully'

    item_id = json_create_data['item']['id']

    get_response = requests.get(f'{BASE_URL}/get_item_by_id/{item_id}', headers={'Authorization': f'Bearer {token}'})


    item = ItemResponse(**get_response.json())

    assert get_response.status_code == 200
    assert item.id == item_id
    assert item.name == item_data['name']
    assert item.description == item_data['description']
    assert item.price == item_data['price']

# Test for getting a single item by an invalid ID (item does not exist)
def test_get_item_by_invalid_id(test_login):
    token = test_login

    response = requests.get(f'{BASE_URL}/get_item_by_id/99999', headers={'Authorization': f'Bearer {token}'})


    json_data = response.json()

    assert response.status_code == 404
    assert json_data['message'] == "Item not found"

#-------------------------------------- Delete Item -----------------------------#

# Test for deleting an existing item
def test_delete_item(test_login):
    token = test_login

    item_data = {
        "name": "Test Item",
        "description": "This is a test item",
        "price": 19.99
    }
    create_response = requests.post(f'{BASE_URL}/create_item', 
                                  json=item_data,
                                  headers={'Authorization': f'Bearer {token}'})


    json_create_data = create_response.json()

    assert create_response.status_code == 201
    assert json_create_data['message'] == 'Item created successfully'

    item_id = json_create_data['item']['id']

    delete_response = requests.delete(f'{BASE_URL}/delete_item/{item_id}', 
                                    headers={'Authorization': f'Bearer {token}'})


    json_delete_data = delete_response.json()

    assert delete_response.status_code == 200
    assert json_delete_data['message'] == "Item deleted successfully"

    get_response = requests.get(f'{BASE_URL}/get_item_by_id/{item_id}', headers={'Authorization': f'Bearer {token}'})


    json_get_data = get_response.json()
    assert get_response.status_code == 404
    assert json_get_data['message'] == "Item not found"

def test_delete_non_existent_item(test_login):
    token = test_login

    response = requests.delete(f'{BASE_URL}/delete_item/99999', headers={'Authorization': f'Bearer {token}'})


    json_data = response.json()

    assert response.status_code == 404
    assert json_data['message'] == "Item not found"
