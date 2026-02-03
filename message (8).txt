"""
Server 1 - Python Flask Server pro správu nápojového lístku
Port: 8001
"""
import flask

from flask import Flask, jsonify, request, abort
import json

app = Flask(__name__)

def load_data():
    with open('db.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open('db.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@app.after_request
def header(response):
    response.headers["X-Server-ID"] = "1"
    return response
# 1
@app.route('/drinks', methods=['GET'])
def get_all_drinks():
    data = load_data()
    return jsonify(data), 200

# 2
@app.route("/drinks/<id>", methods = ["GET"])
def get_drink_by_id(id):
    data = load_data()["drinks"]
    for drink in data:
        if drink["id"] == int(id):
            return drink, 200

    return jsonify({"error": "not found"}), 400

# 3
@app.route('/drinks', methods=['POST'])
def create_drink():
    data = load_data()
    new_drink = request.json

    if not new_drink or 'name' not in new_drink:
        return jsonify({"error": "invalid json"}), 400

    new_drink['id'] = max(d['id'] for d in data['drinks']) + 1 if data['drinks'] else 1
    data['drinks'].append(new_drink)
    save_data(data)
    return jsonify({**new_drink, "server": 1}), 201

# 4
@app.route("/drinks/<id>", methods = ["PUT"])
def update_drink(id):
    data = load_data()
    up_drink = request.json
    for drink in data:
        if drink["id"] == int(id):
            drink["name"] = up_drink["name"]
            drink["category"] = up_drink["category"]
            drink["price"] = up_drink["price"]
            drink["available"] = up_drink["available"]

    save_data(data)
    return jsonify({**data, "server": 1}), 201



if __name__ == '__main__':
    app.run(port=8001, debug=True)