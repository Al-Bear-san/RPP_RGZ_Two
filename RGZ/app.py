from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from Db.models import Items
from Db import db
from sqlalchemy.exc import IntegrityError
import csv
import os

app = Flask(__name__)


app.secret_key = '123'
user_db = 'postgres'
host_ip = '127.0.0.1'
host_port = '5432'
database_name = 'rpp_rgz'
password = 'postgres'

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{user_db}:{password}@{host_ip}:{host_port}/{database_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


@app.route('/items', methods=['POST'])
def add_item():
    data = request.get_json()
    try:
        if data['quantity'] < 0 or data['price'] <= 0:
            return jsonify({"error": "Invalid quantity or price."}), 400
        new_item = Items(
            name=data['name'],
            quantity=data['quantity'],
            price=data['price'],
            category=data['category']
        )
        db.session.add(new_item)
        db.session.commit()
        return jsonify({"message": "Item added successfully."}), 201
    except KeyError as e:
        return jsonify({"error": f"Missing field: {str(e)}"}), 400


@app.route('/items', methods=['GET'])
def get_items():
    category = request.args.get('category')
    query = Items.query
    if category:
        query = query.filter_by(category=category)
    items = query.all()
    return jsonify([
        {
            "id": item.id,
            "name": item.name,
            "quantity": item.quantity,
            "price": item.price,
            "category": item.category
        } for item in items
    ])

@app.route('/items/<int:item_id>', methods=['PUT']) 
def update_item(item_id):
    data = request.get_json()
    item = Items.query.get(item_id)
    
    if item is None:
        return jsonify({"error": "Item not found."}), 404 
    try:
        if 'quantity' in data and data['quantity'] < 0:
            return jsonify({"error": "Quantity cannot be negative."}), 400
        if 'price' in data and data['price'] <= 0:
            return jsonify({"error": "Price must be greater than zero."}), 400
        item.name = data.get('name', item.name)
        item.quantity = data.get('quantity', item.quantity)
        item.price = data.get('price', item.price)
        item.category = data.get('category', item.category)
        db.session.commit()
        return jsonify({"message": "Item updated successfully."}), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Database error."}), 500

@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = Items.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Item deleted successfully."}), 200

@app.route('/reports/summary', methods=['GET'])
def generate_report():
    items = Items.query.all()
    total_value = sum(item.price * item.quantity for item in items)
    category_summary = {}
    zero_or_negative = []

    for item in items:
        if item.quantity <= 0:
            zero_or_negative.append({"name": item.name, "quantity": item.quantity})
        if item.category not in category_summary:
            category_summary[item.category] = {"count": 0, "value": 0}
        category_summary[item.category]["count"] += item.quantity
        category_summary[item.category]["value"] += item.price * item.quantity

    report = {
        "total_value": total_value,
        "category_summary": category_summary,
        "zero_or_negative_items": zero_or_negative
    }

    if request.args.get('format') == 'csv':
        csv_file = 'report.csv'
        with open(csv_file, 'w', newline='') as csvfile:
            fieldnames = ['category', 'count', 'value']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for category, summary in category_summary.items():
                writer.writerow({"category": category, "count": summary["count"], "value": summary["value"]})
        return jsonify({"message": f"CSV report generated at {os.path.abspath(csv_file)}"})

    return jsonify(report)


with app.app_context():
        db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
