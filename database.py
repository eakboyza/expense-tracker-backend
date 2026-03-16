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
    
    # ============================================
    # 1. CREATE TABLES
    # ============================================
    
    # 👤 ตาราง users (มีอยู่แล้ว)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 🏦 ตาราง accounts (ใหม่)
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
    
    # 📂 ตาราง categories (ใหม่)
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
    
    # 🏷️ ตาราง tags (ใหม่)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            name VARCHAR(50) NOT NULL,
            color VARCHAR(20) DEFAULT '#6366f1',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_tag_per_user (user_id, name),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
      # 💰 transactions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            type ENUM('income', 'expense', 'transfer') NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            description TEXT,
            category VARCHAR(50),
            tag VARCHAR(50),
            icon VARCHAR(10) DEFAULT '📝',
            date DATE NOT NULL,
            month_key VARCHAR(7),
            account_id INT,
            transfer_to_account_id INT,
            is_debt_payment BOOLEAN DEFAULT FALSE,
            original_debt_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (account_id) REFERENCES accounts(id),
            FOREIGN KEY (transfer_to_account_id) REFERENCES accounts(id)
        )
    ''')
    
    # 🏷️ ตาราง transaction_tags (เชื่อม transactions กับ tags สำหรับหลาย tags ต่อรายการ)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaction_tags (
            transaction_id INT NOT NULL,
            tag_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (transaction_id, tag_id),
            FOREIGN KEY (transaction_id) REFERENCES transactions(id),
            FOREIGN KEY (tag_id) REFERENCES tags(id)
        )
    ''')
    
    # 🎯 ตาราง budgets (ใหม่)
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
    
    # 💳 ตาราง debts (ใหม่)
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
    
    # 💸 ตาราง debt_payments (ใหม่)
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


  # ============================================
    # 2. MIGRATION: เพิ่ม column ที่ขาดหายไป
    # ============================================
    
    print("🔧 Running database migrations...")
    
    # รายการ migrations
    migrations = [
        {
            'table': 'transactions',
            'column': 'tag',
            'definition': 'VARCHAR(50) AFTER category'
        },
        {
            'table': 'transactions',
            'column': 'icon',
            'definition': "VARCHAR(10) DEFAULT '📝' AFTER tag"
        },
        {
            'table': 'transactions',
            'column': 'month_key',
            'definition': 'VARCHAR(7) AFTER date'
        },
        {
            'table': 'transactions',
            'column': 'account_id',
            'definition': 'INT AFTER month_key'
        },
        {
            'table': 'transactions',
            'column': 'transfer_to_account_id',
            'definition': 'INT AFTER account_id'
        },
        {
            'table': 'transactions',
            'column': 'is_debt_payment',
            'definition': "BOOLEAN DEFAULT FALSE AFTER transfer_to_account_id"
        },
        {
            'table': 'transactions',
            'column': 'original_debt_id',
            'definition': 'INT AFTER is_debt_payment'
        }
    ]
    
    for mig in migrations:
        try:
            # ตรวจสอบว่ามี column นี้หรือยัง
            cursor.execute(f"SHOW COLUMNS FROM {mig['table']} LIKE '{mig['column']}'")
            if not cursor.fetchone():
                print(f"➕ Adding {mig['column']} to {mig['table']}...")
                cursor.execute(f"ALTER TABLE {mig['table']} ADD COLUMN {mig['column']} {mig['definition']}")
                print(f"✅ Added {mig['column']}")
        except Exception as e:
            print(f"⚠️  {mig['column']}: {e}")

    
    
    # ============================================
    # 2. CREATE INDEXES (ใช้ TRY-EXCEPT เพื่อป้องกัน error)
    # ============================================
    
    print("Creating indexes for better performance...")
    
    # 🔍 INDEXES สำหรับ transactions
    indexes = [
        "CREATE INDEX idx_transactions_user_month ON transactions(user_id, month_key)",
        "CREATE INDEX idx_transactions_date ON transactions(user_id, date)",
        "CREATE INDEX idx_transactions_category ON transactions(user_id, category)",
        "CREATE INDEX idx_transactions_tag ON transactions(user_id, tag)",
        "CREATE INDEX idx_transactions_type ON transactions(user_id, type)",
        "CREATE INDEX idx_transactions_account ON transactions(user_id, account_id)",
        
        # 🔍 INDEXES สำหรับ accounts
        "CREATE INDEX idx_accounts_user ON accounts(user_id)",
        
        # 🔍 INDEXES สำหรับ categories
        "CREATE INDEX idx_categories_user ON categories(user_id)",
        
        # 🔍 INDEXES สำหรับ tags
        "CREATE INDEX idx_tags_user ON tags(user_id)",
        
        # 🔍 INDEXES สำหรับ transaction_tags
        "CREATE INDEX idx_transaction_tags_trans ON transaction_tags(transaction_id)",
        "CREATE INDEX idx_transaction_tags_tag ON transaction_tags(tag_id)",
        
        # 🔍 INDEXES สำหรับ budgets
        "CREATE INDEX idx_budgets_user_month ON budgets(user_id, month_key)",
        "CREATE INDEX idx_budgets_category ON budgets(category_id)",
        
        # 🔍 INDEXES สำหรับ debts
        "CREATE INDEX idx_debts_user ON debts(user_id)",
        "CREATE INDEX idx_debts_status ON debts(user_id, status)",
        
        # 🔍 INDEXES สำหรับ debt_payments
        "CREATE INDEX idx_debt_payments_debt ON debt_payments(debt_id)",
        "CREATE INDEX idx_debt_payments_date ON debt_payments(payment_date)"
    ]
    
    for index_sql in indexes:
        try:
            cursor.execute(index_sql)
            print(f"  ✅ Created: {index_sql[:50]}...")
        except Exception as e:
            # ถ้า index มีอยู่แล้ว หรือ error อื่นๆ ให้ข้ามไป
            print(f"  ⚠️  Skipped: {index_sql[:50]}... ({e})")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Database initialized with all tables and indexes")

# ============================================
# 3. CRUD FUNCTIONS สำหรับ transactions (ที่มีอยู่แล้ว)
# ============================================

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
                tag = %s,
                icon = %s,
                date = %s,
                month_key = %s,
                account_id = %s
            WHERE id = %s AND user_id = %s
        ''', (
            transaction_data.get('type'),
            transaction_data.get('amount'),
            transaction_data.get('desc'),
            transaction_data.get('category'),
            transaction_data.get('tag'),
            transaction_data.get('icon'),
            transaction_data.get('date'),
            transaction_data.get('month_key'),
            transaction_data.get('account_id'),
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

def delete_transaction(transaction_id, user_id):
    try:
        conn = get_db_connection()
        if not conn:
            return False, "Database connection failed"
            
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
            return True, "Transaction deleted successfully"
        else:
            return False, "Transaction not found"
            
    except Exception as e:
        print(f"Error deleting transaction: {e}")
        return False, str(e)

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