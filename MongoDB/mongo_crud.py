from flask import Flask, request, jsonify
# from flask_pymongo import PyMongo
from bson import ObjectId
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# app.config["MONGO_URI"] = "mongodb://localhost:27017/TestDataBase"

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')

client = MongoClient(MONGO_URI)
db = client.mydatabase # Database name
collection = db.mycollection # Collection name


# CREATE
@app.route('/add', methods=['POST'])
def add_data():
    data = request.json 
    if not data:
        return jsonify(message="No data provided"), 400
    
    result = collection.insert_one(data)
    return jsonify(message="Data added successfully", id=str(result.inserted_id)), 201

# READ
@app.route('/get_all', methods=['GET'])
def get_all_data():
    data = list(collection.find())
    for item in data:
        item['_id'] = str(item['_id'])
    return jsonify(data=data)

# READ by ID
@app.route('/get/<id>', methods=['GET'])
def get_data_by_id(id):
    try:
        data = collection.find_one({"_id": ObjectId(id)})  
        if data:
            data['_id'] = str(data['_id']) 
            return jsonify(data=data)
        else:
            return jsonify(message="Data not found"), 404
    except Exception as e:
        return jsonify(message=f"Invalid ID format: {str(e)}"), 400

# UPDATE
@app.route('/update/<id>', methods=['PUT'])
def update_data(id):
    data = request.json 
    if not data:
        return jsonify(message="No data provided"), 400
    
    try:
        result = collection.update_one({"_id": ObjectId(id)}, {"$set": data})
        if result.matched_count == 0:
            return jsonify(message="No matching document found"), 404
        return jsonify(message="Data updated successfully")
    except Exception as e:
        return jsonify(message=f"Invalid ID format: {str(e)}"), 400

# DELETE
@app.route('/delete/<id>', methods=['DELETE'])
def delete_data(id):
    try:
        result = collection.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            return jsonify(message="No matching document found"), 404
        return jsonify(message="Data deleted successfully")
    except Exception as e:
        return jsonify(message=f"Invalid ID format: {str(e)}"), 400

# Index
@app.route('/')
def index():
    return jsonify(message="Welcome to the Flask MongoDB CRUD App!")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)