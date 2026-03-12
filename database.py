python
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