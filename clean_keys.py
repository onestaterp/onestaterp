import pymysql
from datetime import datetime

# زانیارییەکانی داتابەیسەکەت
DB_HOST = 'localhost'
DB_USER = 'u129582972_ewanmod'
DB_PASSWORD = 'Ewan1999@'
DB_NAME = 'u129582972_ewanmod'

def clean_expired_keys():
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 1. هێنانی هەموو ئەو کلیلانەی کە بەسەرچوون یان کاتیان تێپەڕیوە
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("SELECT sha256_key FROM `keys` WHERE expires_at < %s AND sha256_key IS NOT NULL", (now,))
            expired_rows = cursor.fetchall()
            
            if not expired_rows:
                print("هیچ کلیلێکی بەسەرچوو نەدۆزراوەتەوە.")
                return

            expired_keys = [row[0] for row in expired_rows]

            # 2. سڕینەوەی کلیلە بەسەرچووەکان لە داتابەیس
            cursor.execute("DELETE FROM `keys` WHERE expires_at < %s AND sha256_key IS NOT NULL", (now,))
            connection.commit()
            print(f"سڕینەوەی {len(path := len(expired_keys))} کلیل لە داتابەیس سەرکەوتوو بوو.")

        connection.close()
        
    except Exception as e:
        print(f"هەڵە ڕووی دا: {e}")

if __name__ == "__main__":
    clean_expired_keys()
