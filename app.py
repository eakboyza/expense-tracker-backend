import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import get_db_connection, init_database
import hashlib

app = Flask(__name__)
CORS(app)  # ให้ Frontend เรียก API ได้

# เรียกตอนเริ่มระบบ
init_database()

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Expense Tracker API is running"})

# API สำหรับสมัครสมาชิก
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = hashlib.sha256(data.get('password').encode()).hexdigest()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, password)
        )
        conn.commit()
        return jsonify({"message": "Register successful"}), 201
    except mysql.connector.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400
    finally:
        cursor.close()
        conn.close()

# API สำหรับ login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = hashlib.sha256(data.get('password').encode()).hexdigest()
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        "SELECT id, username FROM users WHERE username = %s AND password = %s",
        (username, password)
    )
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if user:
        return jsonify({"message": "Login successful", "user": user}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# API สำหรับบันทึกรายการ
@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    data = request.json
    user_id = data.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO transactions (user_id, type, amount, description, category, date)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (
        user_id, data.get('type'), data.get('amount'),
        data.get('description'), data.get('category'), data.get('date')
    ))
    
    conn.commit()
    transaction_id = cursor.lastrowid
    cursor.close()
    conn.close()
    
    return jsonify({"message": "Transaction added", "id": transaction_id}), 201

# API สำหรับดึงรายการ
@app.route('/api/transactions/<int:user_id>', methods=['GET'])
def get_transactions(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        "SELECT * FROM transactions WHERE user_id = %s ORDER BY date DESC",
        (user_id,)
    )
    transactions = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify(transactions)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)