import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import get_db_connection, init_database
import hashlib
import json
from datetime import datetime
import mysql.connector

app = Flask(__name__)
CORS(app)  # ให้ Frontend เรียก API ได้

# เรียกตอนเริ่มระบบ
init_database()

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Expense Tracker API is running"})



def format_transaction_response(transaction):
    return {
        'id': str(transaction['id']),
        'amount': float(transaction['amount']),
        'type': transaction['type'],
        'category': transaction['category'],
        'icon': transaction['icon'] or '📝',
        'desc': transaction['description'] or transaction['category'],
        'tag': transaction['tag'] or '',
        'rawDate': transaction['date'].strftime('%Y-%m-%d') if hasattr(transaction['date'], 'strftime') else transaction['date'],
        'date': transaction['date'].strftime('%Y-%m-%d') if hasattr(transaction['date'], 'strftime') else transaction['date'],
        'monthKey': transaction['month_key'],
        'accountId': transaction['account_id'],
        'transferToAccountId': transaction['transfer_to_account_id'],  # ✅ เพิ่ม
        'transferType': transaction['transfer_type'],  # ✅ เพิ่ม
        'createdAt': transaction['created_at'].isoformat() if transaction['created_at'] else None,
        'updatedAt': transaction['updated_at'].isoformat() if transaction['updated_at'] else None
    }

def create_default_user_data(user_id):
    """สร้าง accounts และ categories เริ่มต้นให้ user (ไม่ใช่ route)"""
    try:
        conn = get_db_connection()
        if not conn:
            return False, "Database connection failed"
            
        cursor = conn.cursor()
        
        # สร้างบัญชีเริ่มต้น
        default_accounts = [
            ('บัญชีหลัก', 'savings', '🏦', 0, True),
            ('เงินสด', 'cash', '💰', 0, False)
        ]
        
        for name, acc_type, icon, balance, is_default in default_accounts:
            cursor.execute('''
                INSERT INTO accounts (user_id, name, type, icon, initial_balance, is_default)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, name, acc_type, icon, balance, is_default))
        
        # สร้างหมวดหมู่เริ่มต้น
        default_categories = [
            ('income', 'เงินเดือน', '💰'),
            ('income', 'โบนัส', '🎁'),
            ('income', 'กำไรลงทุน', '💹'),
            ('income', 'อื่นๆ', '🏦'),
            ('spending', 'กิน', '🍱'),
            ('spending', 'น้ำมัน', '⛽'),
            ('spending', 'สังคม', '🤝'),
            ('spending', 'ครอบครัว', '👨‍👩‍👧‍👦'),
            ('spending', 'ของใช้', '🧺'),
            ('spending', 'สิ่งบันเทิง', '🎬'),
            ('spending', 'ท่องเที่ยว', '✈️'),
            ('spending', 'สุขภาพ', '🏥'),
            ('spending', 'รถยนต์', '🚗'),
            ('investment', 'เงินเก็บลูก', '👶'),
            ('investment', 'สำรองระยะสั้น', '🛡️'),
            ('investment', 'เก็บเตรียมลงทุน', '💎')
        ]
        
        for cat_type, name, icon in default_categories:
            cursor.execute('''
                INSERT INTO categories (user_id, type, name, icon, is_default)
                VALUES (%s, %s, %s, %s, %s)
            ''', (user_id, cat_type, name, icon, True))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True, "User data created"
        
    except Exception as e:
        print(f"Error creating user data: {e}")
        return False, str(e)

@app.route('/api/init-user-data/<int:user_id>', methods=['POST'])
def init_user_data(user_id):
    """สร้างข้อมูลเริ่มต้นให้ user ใหม่ (accounts + categories)"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()

        
        
        # ============================================
        # 1. สร้างบัญชีเริ่มต้น (accounts)
        # ============================================
        default_accounts = [
            ('บัญชีหลัก', 'savings', '🏦', 0, True),
            ('เงินสด', 'cash', '💰', 0, False)
        ]
        
        for name, acc_type, icon, balance, is_default in default_accounts:
            cursor.execute('''
                INSERT INTO accounts (user_id, name, type, icon, initial_balance, is_default)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, name, acc_type, icon, balance, is_default))
        
        # ============================================
        # 2. สร้างหมวดหมู่เริ่มต้น (categories)
        # ============================================
        default_categories = [
            # income
            ('income', 'เงินเดือน', '💰'),
            ('income', 'โบนัส', '🎁'),
            ('income', 'กำไรลงทุน', '💹'),
            ('income', 'อื่นๆ', '🏦'),
            # spending
            ('spending', 'กิน', '🍱'),
            ('spending', 'น้ำมัน', '⛽'),
            ('spending', 'สังคม', '🤝'),
            ('spending', 'ครอบครัว', '👨‍👩‍👧‍👦'),
            ('spending', 'ของใช้', '🧺'),
            ('spending', 'สิ่งบันเทิง', '🎬'),
            ('spending', 'ท่องเที่ยว', '✈️'),
            ('spending', 'สุขภาพ', '🏥'),
            ('spending', 'รถยนต์', '🚗'),
            # investment
            ('investment', 'เงินเก็บลูก', '👶'),
            ('investment', 'สำรองระยะสั้น', '🛡️'),
            ('investment', 'เก็บเตรียมลงทุน', '💎')
        ]
        
        for cat_type, name, icon in default_categories:
            cursor.execute('''
                INSERT INTO categories (user_id, type, name, icon, is_default)
                VALUES (%s, %s, %s, %s, %s)
            ''', (user_id, cat_type, name, icon, True))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "message": "User data initialized successfully",
            "accounts_created": 2,
            "categories_created": 16
        }), 201
        
    except Exception as e:
        print(f"Error initializing user data: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================
# AUTHENTICATION API (มีอยู่แล้ว)
# ============================================

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
            user_id = cursor.lastrowid
            cursor.close()
            conn.close()
            
            # ✅ แก้ไข: เรียก function helper แทน
            success, message = create_default_user_data(user_id)
            
            if not success:
                print(f"Warning: {message}")
                # ไม่ต้อง return error แค่ log ไว้
            
            return jsonify({
                "message": "Register successful",
                "user_id": user_id
            }), 201
            
        except mysql.connector.IntegrityError:
            return jsonify({"error": "Username already exists"}), 400
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
            
    except Exception as e:
        print(f"Register error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
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

# ============================================
# TRANSACTIONS API (ปรับปรุง)
# ============================================

@app.route('/api/transactions/<int:user_id>', methods=['GET'])
def get_transactions(user_id):
    """โหลด transactions ทั้งหมดของผู้ใช้"""
    try:
        month = request.args.get('month')
        account = request.args.get('account')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM transactions WHERE user_id = %s"
        params = [user_id]
        
        if month:
            query += " AND month_key = %s"
            params.append(month)
        
        query += " ORDER BY date DESC, created_at DESC"
        
        cursor.execute(query, params)
        transactions = cursor.fetchall()
        
        # ✅ แปลงข้อมูลให้ตรงกับ frontend
        result = []
        for t in transactions:
            try:
                date_str = t['date'].strftime('%Y-%m-%d') if t['date'] else ''
                created_str = t['created_at'].isoformat() if t['created_at'] else None
                
                result.append({
                    'id': str(t['id']),
                    'amount': float(t['amount']) if t['amount'] else 0,
                    'type': t['type'] or 'expense',
                    'category': t['category'] or 'อื่นๆ',
                    'icon': t['icon'] or '📝',
                    'desc': t['description'] or t['category'] or '',
                    'tag': t['tag'] or '',
                    'rawDate': date_str,
                    'date': date_str,
                    'monthKey': t['month_key'] or '',
                    'accountId': str(t['account_id']) if t['account_id'] else None,
                    'transferToAccountId': str(t['transfer_to_account_id']) if t['transfer_to_account_id'] else None,
                    'transferType': t['transfer_type'],
                    'createdAt': created_str,
                    'updatedAt': None
                })
            except Exception as e:
                print(f"Error formatting transaction {t.get('id')}: {e}")
                continue
        
        cursor.close()
        conn.close()
        
        print(f"✅ ส่งข้อมูล {len(result)} รายการกลับไป")
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error getting transactions: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    """เพิ่ม transaction ใหม่"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        
        # ✅ แปลง account_id เป็น string
        account_id = data.get('accountId')
        if account_id is not None:
            account_id = str(account_id)
        
        # ✅ แปลง transfer_to_account_id เป็น string
        transfer_to_account_id = data.get('transferToAccountId')
        if transfer_to_account_id is not None:
            transfer_to_account_id = str(transfer_to_account_id)
        
        # ✅ รับ transfer_type
        transfer_type = data.get('transferType')
        
        # ✅ Debug log
        print(f"📝 add_transaction - account_id: {account_id}")
        print(f"📝 add_transaction - transfer_to_account_id: {transfer_to_account_id}")
        print(f"📝 add_transaction - transfer_type: {transfer_type}")
        print(f"📝 add_transaction - type: {data.get('type')}")
        
        cursor.execute('''
            INSERT INTO transactions 
            (user_id, type, amount, description, category, tag, icon, date, month_key, 
             account_id, transfer_to_account_id, transfer_type, is_debt_payment, original_debt_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            user_id,
            data.get('type'),
            data.get('amount'),
            data.get('desc'),
            data.get('category'),
            data.get('tag', ''),
            data.get('icon', '📝'),
            data.get('rawDate') or data.get('date'),
            data.get('month_key'),
            account_id,
            transfer_to_account_id,
            transfer_type,
            data.get('isDebtPayment', False),
            data.get('originalDebtId')
        ))
        
        conn.commit()
        transaction_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        print(f"✅ Transaction added: id={transaction_id}, transfer_to_account_id={transfer_to_account_id}, transfer_type={transfer_type}")
        
        return jsonify({
            "message": "Transaction added",
            "id": transaction_id
        }), 201
        
    except Exception as e:
        print(f"Error adding transaction: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/debug/transactions/<int:user_id>', methods=['GET'])
def debug_transactions(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # ดู transactions ทั้งหมด
        cursor.execute("SELECT * FROM transactions WHERE user_id = %s", (user_id,))
        all_tx = cursor.fetchall()
        
        # ดู structure
        cursor.execute("DESCRIBE transactions")
        structure = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'transactions': all_tx,
            'count': len(all_tx),
            'structure': structure
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        
        # ✅ แปลง account_id เป็น string ถ้ามี
        account_id = data.get('account_id')
        if account_id is not None:
            account_id = str(account_id)
        

        transfer_to_account_id = data.get('transfer_to_account_id')
        if transfer_to_account_id is not None:
            transfer_to_account_id = str(transfer_to_account_id)

        transfer_type = data.get('transfer_type')

        cursor.execute('''
            UPDATE transactions 
            SET type = %s, amount = %s, description = %s, category = %s,
                tag = %s, icon = %s, date = %s, month_key = %s, 
                account_id = %s, transfer_to_account_id = %s, transfer_type = %s
            WHERE id = %s AND user_id = %s
        ''', (
            data.get('type'), 
            data.get('amount'),
            data.get('desc'), 
            data.get('category'),
            data.get('tag', ''),
            data.get('icon'),
            data.get('date'), 
            data.get('month_key'),
            account_id,
            transfer_to_account_id,
            transfer_type,
            transaction_id, 
            user_id
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"message": "Transaction updated successfully"}), 200
        
    except Exception as e:
        print(f"Update transaction error: {e}")
        return jsonify({"error": str(e)}), 500

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

# ============================================
# ACCOUNTS API
# ============================================

@app.route('/api/accounts/<int:user_id>', methods=['GET'])
def get_accounts(user_id):
    """โหลดบัญชีทั้งหมดของผู้ใช้"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT * FROM accounts 
            WHERE user_id = %s 
            ORDER BY is_default DESC, created_at ASC
        ''', (user_id,))
        
        accounts = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # แปลงข้อมูลให้ตรงกับ frontend
        result = []
        for acc in accounts:
            result.append({
                'id': str(acc['id']),
                'name': acc['name'],
                'type': acc['type'],
                'icon': acc['icon'],
                'initialBalance': float(acc['initial_balance']),
                'isDefault': bool(acc['is_default']),
                'createdAt': acc['created_at'].isoformat() if acc['created_at'] else None,
                'updatedAt': acc['updated_at'].isoformat() if acc['updated_at'] else None
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error getting accounts: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/accounts', methods=['POST'])
def add_account():
    """เพิ่มบัญชีใหม่"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id or not data.get('name'):
            return jsonify({"error": "User ID and account name required"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO accounts 
            (user_id, name, type, icon, initial_balance, is_default)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            user_id,
            data.get('name'),
            data.get('type', 'savings'),
            data.get('icon', '🏦'),
            data.get('initialBalance', 0),
            data.get('isDefault', False)
        ))
        
        conn.commit()
        account_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return jsonify({
            "message": "Account added",
            "id": account_id
        }), 201
        
    except Exception as e:
        print(f"Error adding account: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/accounts/<int:account_id>', methods=['PUT'])
def update_account(account_id):
    """แก้ไขบัญชี"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE accounts 
            SET name = %s, type = %s, icon = %s, is_default = %s
            WHERE id = %s AND user_id = %s
        ''', (
            data.get('name'),
            data.get('type'),
            data.get('icon'),
            data.get('isDefault', False),
            account_id,
            user_id
        ))
        
        conn.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            return jsonify({"message": "Account updated"}), 200
        else:
            return jsonify({"error": "Account not found"}), 404
            
    except Exception as e:
        print(f"Error updating account: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    """ลบบัญชี พร้อม transactions ที่เกี่ยวข้องทั้งหมด"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        
        # ✅ นับจำนวน transaction ที่จะถูกลบ (เพื่อแสดงผล)
        cursor.execute('''
            SELECT COUNT(*) FROM transactions 
            WHERE (account_id = %s OR transfer_to_account_id = %s) 
            AND user_id = %s
        ''', (str(account_id), str(account_id), user_id))
        
        transaction_count = cursor.fetchone()[0]
        
        # ✅ ลบ transactions ที่เกี่ยวข้องทั้งหมด
        cursor.execute('''
            DELETE FROM transactions 
            WHERE (account_id = %s OR transfer_to_account_id = %s) 
            AND user_id = %s
        ''', (str(account_id), str(account_id), user_id))
        
        # ✅ ลบ debt_payments ที่เกี่ยวข้อง (ถ้ามี)
        cursor.execute('''
            DELETE FROM debt_payments 
            WHERE account_id = %s
        ''', (str(account_id),))
        
        # ✅ ลบ account
        cursor.execute(
            "DELETE FROM accounts WHERE id = %s AND user_id = %s",
            (account_id, user_id)
        )
        
        conn.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            return jsonify({
                "message": "Account and related transactions deleted",
                "deleted_account": affected_rows,
                "deleted_transactions": transaction_count
            }), 200
        else:
            return jsonify({"error": "Account not found"}), 404
            
    except Exception as e:
        print(f"Error deleting account: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ============================================
# CATEGORIES API
# ============================================
# เพิ่มใน app.py หลังจาก register สำเร็จ
@app.route('/api/init-categories/<int:user_id>', methods=['POST'])
def init_categories(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # สร้าง categories เริ่มต้น
        default_cats = [
            # income
            ('income', 'เงินเดือน', '💰'),
            ('income', 'โบนัส', '🎁'),
            ('income', 'กำไรลงทุน', '💹'),
            ('income', 'อื่นๆ', '🏦'),
            
            # spending
            ('spending', 'กิน', '🍱'),
            ('spending', 'น้ำมัน', '⛽'),
            ('spending', 'สังคม', '🤝'),
            ('spending', 'ครอบครัว', '👨‍👩‍👧‍👦'),
            ('spending', 'ของใช้', '🧺'),
            ('spending', 'สิ่งบันเทิง', '🎬'),
            ('spending', 'ท่องเที่ยว', '✈️'),
            ('spending', 'สุขภาพ', '🏥'),
            ('spending', 'รถยนต์', '🚗'),
            
            # investment
            ('investment', 'เงินเก็บลูก', '👶'),
            ('investment', 'สำรองระยะสั้น', '🛡️'),
            ('investment', 'เก็บเตรียมลงทุน', '💎')
        ]
        
        for cat_type, name, icon in default_cats:
            cursor.execute('''
                INSERT INTO categories (user_id, type, name, icon, is_default)
                VALUES (%s, %s, %s, %s, %s)
            ''', (user_id, cat_type, name, icon, True))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"message": "Categories initialized"}), 201
        
    except Exception as e:
        print(f"Error init categories: {e}")
        return jsonify({"error": str(e)}), 500
@app.route('/api/categories/<int:user_id>', methods=['GET'])
def get_categories(user_id):
    """โหลดหมวดหมู่ทั้งหมดของผู้ใช้"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT * FROM categories 
            WHERE user_id = %s 
            ORDER BY type, name
        ''', (user_id,))
        
        categories = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # จัดกลุ่มตาม type
        result = {
            'income': [],
            'spending': [],
            'investment': []
        }
        
        for cat in categories:
            result[cat['type']].append({
                'id': str(cat['id']),
                'label': cat['name'],
                'icon': cat['icon'],
                'default': None
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error getting categories: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/categories', methods=['POST'])
def add_category():
    """เพิ่มหมวดหมู่ใหม่"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id or not data.get('name') or not data.get('type'):
            return jsonify({"error": "Missing required fields"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO categories 
            (user_id, type, name, icon, is_default)
            VALUES (%s, %s, %s, %s, %s)
        ''', (
            user_id,
            data.get('type'),
            data.get('name'),
            data.get('icon', '📝'),
            data.get('is_default', False)
        ))
        
        conn.commit()
        category_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return jsonify({
            "message": "Category added",
            "id": category_id
        }), 201
        
    except Exception as e:
        print(f"Error adding category: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """แก้ไขหมวดหมู่"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE categories 
            SET name = %s, icon = %s
            WHERE id = %s AND user_id = %s
        ''', (
            data.get('name'),
            data.get('icon'),
            category_id,
            user_id
        ))
        
        conn.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            return jsonify({"message": "Category updated"}), 200
        else:
            return jsonify({"error": "Category not found"}), 404
            
    except Exception as e:
        print(f"Error updating category: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """ลบหมวดหมู่"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM categories WHERE id = %s AND user_id = %s",
            (category_id, user_id)
        )
        
        conn.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            return jsonify({"message": "Category deleted"}), 200
        else:
            return jsonify({"error": "Category not found"}), 404
            
    except Exception as e:
        print(f"Error deleting category: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================
# TAGS API
# ============================================

@app.route('/api/tags/<int:user_id>', methods=['GET'])
def get_tags(user_id):
    """โหลด tags ทั้งหมดของผู้ใช้"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT * FROM tags 
            WHERE user_id = %s 
            ORDER BY name
        ''', (user_id,))
        
        tags = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify(tags), 200
        
    except Exception as e:
        print(f"Error getting tags: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tags', methods=['POST'])
def add_tag():
    """เพิ่ม tag ใหม่"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id or not data.get('name'):
            return jsonify({"error": "User ID and tag name required"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tags (user_id, name, color)
            VALUES (%s, %s, %s)
        ''', (
            user_id,
            data.get('name'),
            data.get('color', '#6366f1')
        ))
        
        conn.commit()
        tag_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return jsonify({
            "message": "Tag added",
            "id": tag_id
        }), 201
        
    except Exception as e:
        print(f"Error adding tag: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tags/<int:tag_id>', methods=['DELETE'])
def delete_tag(tag_id):
    """ลบ tag"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM tags WHERE id = %s AND user_id = %s",
            (tag_id, user_id)
        )
        
        conn.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            return jsonify({"message": "Tag deleted"}), 200
        else:
            return jsonify({"error": "Tag not found"}), 404
            
    except Exception as e:
        print(f"Error deleting tag: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================
# BUDGETS API
# ============================================

@app.route('/api/budgets/<int:user_id>/<string:month_key>', methods=['GET'])
def get_budgets(user_id, month_key):
    """โหลดงบประมาณของเดือนที่ระบุ"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT b.*, c.name as category_name, c.icon as category_icon
            FROM budgets b
            JOIN categories c ON b.category_id = c.id
            WHERE b.user_id = %s AND b.month_key = %s
        ''', (user_id, month_key))
        
        budgets = cursor.fetchall()
        cursor.close()
        conn.close()
        
        result = {}
        for b in budgets:
            result[str(b['category_id'])] = {
                'value': float(b['target_value']) if b['target_value'] else 0,
                'mode': b['target_mode']
            }
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error getting budgets: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/budgets', methods=['POST'])
def save_budgets():
    """บันทึกงบประมาณทั้งเดือน"""
    try:
        data = request.json
        user_id = data.get('user_id')
        month_key = data.get('month_key')
        budgets = data.get('budgets', {})
        
        if not user_id or not month_key:
            return jsonify({"error": "User ID and month key required"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        
        # ลบของเก่าก่อน
        cursor.execute('''
            DELETE FROM budgets 
            WHERE user_id = %s AND month_key = %s
        ''', (user_id, month_key))
        
        # เพิ่มของใหม่
        for category_id, target in budgets.items():
            cursor.execute('''
                INSERT INTO budgets 
                (user_id, month_key, category_id, target_value, target_mode)
                VALUES (%s, %s, %s, %s, %s)
            ''', (
                user_id,
                month_key,
                int(category_id),
                target.get('value'),
                target.get('mode', 'percentage')
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"message": "Budgets saved"}), 200
        
    except Exception as e:
        print(f"Error saving budgets: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================
# DEBTS API
# ============================================

@app.route('/api/debts/<int:user_id>', methods=['GET'])
def get_debts(user_id):
    """โหลดหนี้ทั้งหมดของผู้ใช้"""
    try:
        status = request.args.get('status', 'all')  # open, closed, all
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        query = '''
            SELECT d.*, c.name as category_name, c.icon as category_icon
            FROM debts d
            JOIN categories c ON d.category_id = c.id
            WHERE d.user_id = %s
        '''
        params = [user_id]
        
        if status != 'all':
            query += " AND d.status = %s"
            params.append(status)
        
        query += " ORDER BY d.created_at DESC"
        
        cursor.execute(query, params)
        debts = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # แปลงข้อมูล
        result = []
        for debt in debts:
            result.append({
                'id': str(debt['id']),
                'name': debt['name'],
                'categoryId': str(debt['category_id']),
                'categoryName': debt['category_name'],
                'categoryIcon': debt['category_icon'],
                'tag': debt['tag'],
                'totalAmount': float(debt['total_amount']),
                'monthlyPayment': float(debt['monthly_payment']),
                'interestRate': float(debt['interest_rate']),
                'dueDate': debt['due_date'],
                'startDate': debt['start_date'].isoformat() if debt['start_date'] else None,
                'status': debt['status'],
                'closedAt': debt['closed_at'].isoformat() if debt['closed_at'] else None,
                'createdAt': debt['created_at'].isoformat() if debt['created_at'] else None,
                'updatedAt': debt['updated_at'].isoformat() if debt['updated_at'] else None
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error getting debts: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/debts', methods=['POST'])
def add_debt():
    """เพิ่มหนี้ใหม่"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id or not data.get('name') or not data.get('categoryId'):
            return jsonify({"error": "Missing required fields"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO debts 
            (user_id, name, category_id, tag, total_amount, monthly_payment, 
             interest_rate, due_date, start_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            user_id,
            data.get('name'),
            data.get('categoryId'),
            data.get('tag'),
            data.get('totalAmount'),
            data.get('monthlyPayment'),
            data.get('interestRate', 0),
            data.get('dueDate'),
            data.get('startDate'),
            data.get('status', 'open')
        ))
        
        conn.commit()
        debt_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return jsonify({
            "message": "Debt added",
            "id": debt_id
        }), 201
        
    except Exception as e:
        print(f"Error adding debt: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/debts/<int:debt_id>', methods=['PUT'])
def update_debt(debt_id):
    """แก้ไขหนี้"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE debts 
            SET name = %s, category_id = %s, tag = %s, total_amount = %s,
                monthly_payment = %s, interest_rate = %s, due_date = %s,
                start_date = %s, status = %s, closed_at = %s
            WHERE id = %s AND user_id = %s
        ''', (
            data.get('name'),
            data.get('categoryId'),
            data.get('tag'),
            data.get('totalAmount'),
            data.get('monthlyPayment'),
            data.get('interestRate', 0),
            data.get('dueDate'),
            data.get('startDate'),
            data.get('status'),
            data.get('closedAt'),
            debt_id,
            user_id
        ))
        
        conn.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            return jsonify({"message": "Debt updated"}), 200
        else:
            return jsonify({"error": "Debt not found"}), 404
            
    except Exception as e:
        print(f"Error updating debt: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/debts/<int:debt_id>', methods=['DELETE'])
def delete_debt(debt_id):
    """ลบหนี้"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM debts WHERE id = %s AND user_id = %s",
            (debt_id, user_id)
        )
        
        conn.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            return jsonify({"message": "Debt deleted"}), 200
        else:
            return jsonify({"error": "Debt not found"}), 404
            
    except Exception as e:
        print(f"Error deleting debt: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================
# DEBT PAYMENTS API
# ============================================

@app.route('/api/debts/<int:debt_id>/payments', methods=['GET'])
def get_debt_payments(debt_id):
    """โหลดประวัติการชำระหนี้"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT p.*, a.name as account_name, a.icon as account_icon
            FROM debt_payments p
            LEFT JOIN accounts a ON p.account_id = a.id
            WHERE p.debt_id = %s
            ORDER BY p.payment_date DESC, p.created_at DESC
        ''', (debt_id,))
        
        payments = cursor.fetchall()
        cursor.close()
        conn.close()
        
        result = []
        for p in payments:
            result.append({
                'id': str(p['id']),
                'debtId': str(p['debt_id']),
                'accountId': str(p['account_id']) if p['account_id'] else None,
                'accountName': p['account_name'],
                'accountIcon': p['account_icon'],
                'amount': float(p['amount']),
                'date': p['payment_date'].isoformat() if p['payment_date'] else None,
                'note': p['note'],
                'createdAt': p['created_at'].isoformat() if p['created_at'] else None
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error getting debt payments: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/debt-payments', methods=['POST'])
def add_debt_payment():
    """บันทึกการชำระหนี้"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id or not data.get('debtId') or not data.get('amount'):
            return jsonify({"error": "Missing required fields"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO debt_payments 
            (debt_id, account_id, amount, payment_date, note)
            VALUES (%s, %s, %s, %s, %s)
        ''', (
            data.get('debtId'),
            data.get('accountId'),
            data.get('amount'),
            data.get('payment_date'),
            data.get('note')
        ))
        
        conn.commit()
        payment_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return jsonify({
            "message": "Payment added",
            "id": payment_id
        }), 201
        
    except Exception as e:
        print(f"Error adding payment: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/debt-payments/<int:payment_id>', methods=['PUT'])
def update_debt_payment(payment_id):
    """แก้ไขการชำระหนี้"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE debt_payments 
            SET account_id = %s, amount = %s, payment_date = %s, note = %s
            WHERE id = %s
        ''', (
            data.get('accountId'),
            data.get('amount'),
            data.get('payment_date'),
            data.get('note'),
            payment_id
        ))
        
        conn.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            return jsonify({"message": "Payment updated"}), 200
        else:
            return jsonify({"error": "Payment not found"}), 404
            
    except Exception as e:
        print(f"Error updating payment: {e}")
        return jsonify({"error": str(e)}), 500

        

@app.route('/api/debt-payments/<int:payment_id>', methods=['DELETE'])
def delete_debt_payment(payment_id):
    """ลบการชำระหนี้"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "User ID required"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM debt_payments WHERE id = %s",
            (payment_id,)
        )
        
        conn.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            return jsonify({"message": "Payment deleted"}), 200
        else:
            return jsonify({"error": "Payment not found"}), 404
            
    except Exception as e:
        print(f"Error deleting payment: {e}")
        return jsonify({"error": str(e)}), 500
    
    

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

