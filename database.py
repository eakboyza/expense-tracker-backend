import os
import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        # Render จะ inject DATABASE_URL environment variable
        db_url = os.environ.get('DATABASE_URL')
        
        if db_url:
            # ถ้ามี DATABASE_URL ให้ parse (รูปแบบ mysql://user:pass@host/db)
            import urllib.parse
            url = urllib.parse.urlparse(db_url)
            config = {
                'host': url.hostname,
                'user': url.username,
                'password': url.password,
                'database': url.path[1:],  # ตัด / ตัวแรกออก
                'port': url.port or 3306
            }
        else:
            # fallback สำหรับ local development
            config = {
                'host': os.getenv('MYSQL_HOST', 'localhost'),
                'user': os.getenv('MYSQL_USER', 'root'),
                'password': os.getenv('MYSQL_PASSWORD', ''),
                'database': os.getenv('MYSQL_DB', 'expense_tracker'),
                'port': int(os.getenv('MYSQL_PORT', 3306))
            }
        
        conn = mysql.connector.connect(**config)
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # สร้างตาราง users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # สร้างตาราง transactions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            type ENUM('income', 'expense') NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            description TEXT,
            category VARCHAR(50),
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()


    # ============================================
# ✅ ฟังก์ชันใหม่ที่ต้องเพิ่ม (สำหรับ UPDATE)
# ============================================

# ✅ 1. อัพเดท transaction
def update_transaction(transaction_id, user_id, transaction_data):
    try:
        conn = get_db_connection()
        if not conn:
            return False, "Database connection failed"
            
        cursor = conn.cursor()
        
        # ตรวจสอบว่า transaction นี้เป็นของ user นี้จริงๆ
        cursor.execute(
            "SELECT id FROM transactions WHERE id = %s AND user_id = %s",
            (transaction_id, user_id)
        )
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return False, "Transaction not found or unauthorized"
        
        # อัพเดทข้อมูล
        cursor.execute('''
            UPDATE transactions 
            SET type = %s, 
                amount = %s, 
                description = %s, 
                category = %s, 
                date = %s
            WHERE id = %s AND user_id = %s
        ''', (
            transaction_data.get('type'),
            transaction_data.get('amount'),
            transaction_data.get('desc'),
            transaction_data.get('category'),
            transaction_data.get('date'),
            transaction_id,
            user_id
        ))
        
        conn.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            return True, "Transaction updated successfully"
        else:
            return False, "No changes made"
            
    except Exception as e:
        print(f"Error updating transaction: {e}")
        return False, str(e)

# ✅ 2. ลบ transaction (optional)
def delete_transaction(transaction_id, user_id):
    try:
        conn = get_db_connection()
        if not conn:
            return False, "Database connection failed"
            
        cursor = conn.cursor()
        
        # ตรวจสอบและลบ
        cursor.execute(
            "DELETE FROM transactions WHERE id = %s AND user_id = %s",
            (transaction_id, user_id)
        )
        
        conn.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            return True, "Transaction deleted successfully"
        else:
            return False, "Transaction not found"
            
    except Exception as e:
        print(f"Error deleting transaction: {e}")
        return False, str(e)

# ✅ 3. ดึง transaction เดียว (optional)
def get_transaction(transaction_id, user_id):
    try:
        conn = get_db_connection()
        if not conn:
            return None, "Database connection failed"
            
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            "SELECT * FROM transactions WHERE id = %s AND user_id = %s",
            (transaction_id, user_id)
        )
        
        transaction = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if transaction:
            return transaction, "Success"
        else:
            return None, "Transaction not found"
            
    except Exception as e:
        print(f"Error getting transaction: {e}")
        return None, str(e)