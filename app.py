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
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
            
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, hashed_password)
            )
            conn.commit()
            return jsonify({"message": "Register successful"}), 201
        except mysql.connector.IntegrityError:
            return jsonify({"error": "Username already exists"}), 400
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"Register error: {e}")
        return jsonify({"error": str(e)}), 500

# API สำหรับ login
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        
        # ✅ ตรวจสอบว่ามีข้อมูลหรือไม่
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        # ✅ ตรวจสอบว่ามี username และ password หรือไม่
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
        
        # เข้ารหัส password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # เชื่อมต่อฐานข้อมูล
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, username FROM users WHERE username = %s AND password = %s",
            (username, hashed_password)
        )
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user:
            return jsonify({"message": "Login successful", "user": user}), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
            
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"error": str(e)}), 500

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

# ✅ เพิ่ม endpoint สำหรับแก้ไข transaction
@app.route('/api/transactions/<int:transaction_id>', methods=['PUT'])
def update_transaction(transaction_id):
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
            
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        
        # ตรวจสอบว่า transaction นี้เป็นของ user นี้หรือไม่
        cursor.execute(
            "SELECT id FROM transactions WHERE id = %s AND user_id = %s",
            (transaction_id, user_id)
        )
        if not cursor.fetchone():
            return jsonify({"error": "Transaction not found or unauthorized"}), 404
        
        # อัพเดทข้อมูล
        cursor.execute('''
            UPDATE transactions 
            SET type = %s, amount = %s, description = %s, category = %s, date = %s
            WHERE id = %s AND user_id = %s
        ''', (
            data.get('type'), data.get('amount'),
            data.get('desc'), data.get('category'),
            data.get('date'), transaction_id, user_id
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"message": "Transaction updated successfully"}), 200
        
    except Exception as e:
        print(f"Update transaction error: {e}")
        return jsonify({"error": str(e)}), 500
    
    # ✅ เพิ่ม endpoint สำหรับลบ transaction
@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
            
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        
        # ตรวจสอบสิทธิ์
        cursor.execute(
            "DELETE FROM transactions WHERE id = %s AND user_id = %s",
            (transaction_id, user_id)
        )
        
        conn.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            return jsonify({"message": "Transaction deleted successfully"}), 200
        else:
            return jsonify({"error": "Transaction not found"}), 404
            
    except Exception as e:
        print(f"Delete transaction error: {e}")
        return jsonify({"error": str(e)}), 500