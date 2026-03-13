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
    # ========== 🆕 ตารางใหม่ที่ต้องเพิ่ม ==========
    
    # 1. 🏦 ตาราง accounts (บัญชี)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            name VARCHAR(100) NOT NULL,
            type ENUM('savings', 'cash', 'credit', 'investment') DEFAULT 'savings',
            icon VARCHAR(10) DEFAULT '🏦',
            initial_balance DECIMAL(10,2) DEFAULT 0,
            is_default BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # 2. 📂 ตาราง categories (หมวดหมู่)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            type ENUM('income', 'spending', 'investment') NOT NULL,
            name VARCHAR(50) NOT NULL,
            icon VARCHAR(10) NOT NULL,
            is_default BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # 3. 🎯 ตาราง budgets (งบประมาณ)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            month_key VARCHAR(7) NOT NULL,
            category_id INT NOT NULL,
            target_value DECIMAL(10,2),
            target_mode ENUM('percentage', 'fixed') DEFAULT 'percentage',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    
    # 4. 💳 ตาราง debts (หนี้สิน)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS debts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            name VARCHAR(200) NOT NULL,
            category_id INT NOT NULL,
            tag VARCHAR(50),
            total_amount DECIMAL(10,2) NOT NULL,
            monthly_payment DECIMAL(10,2) NOT NULL,
            interest_rate DECIMAL(5,2) DEFAULT 0,
            due_date INT,
            start_date DATE NOT NULL,
            status ENUM('open', 'closed') DEFAULT 'open',
            closed_at DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    
    # 5. 💸 ตาราง debt_payments (การชำระหนี้)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS debt_payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            debt_id INT NOT NULL,
            account_id INT,
            amount DECIMAL(10,2) NOT NULL,
            payment_date DATE NOT NULL,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (debt_id) REFERENCES debts(id),
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Database initialized with all tables")


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