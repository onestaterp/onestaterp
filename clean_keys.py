import pymysql
import base64
import urllib.request
import json
from datetime import datetime

# زانیارییەکانی داتابەیسەکەت
DB_HOST = 'localhost'
DB_USER = 'u129582972_ewanmod'
DB_PASSWORD = 'Ewan1999@'
DB_NAME = 'u129582972_ewanmod'

# زانیارییەکانی گیتهاب (بۆ نوێکردنەوەی Key.txt)
GITHUB_TOKEN = "GHS_TOKEN_HERE"  # ئەگەر پێویست بکات تۆکنی گیتهاب دەنوسیت، یان ئەگەر نا دەتوانین بە ڕێگەیەکی تر بکەین
REPO_NAME = "onestaterp/onestaterp"
FILE_PATH = "Key.txt"

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
            # 1. هێنانی کلیلە بەسەرچووەکان
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("SELECT sha256_key FROM `keys` WHERE expires_at < %s AND sha256_key IS NOT NULL", (now,))
            expired_rows = cursor.fetchall()
            
            if not expired_rows:
                print("هیچ کلیلێکی بەسەرچوو لە داتابەیس نەدۆزراوەتەوە.")
                connection.close()
                return

            expired_keys = {row[0] for row in expired_rows}
            print(f"دۆزراوەتەوە: {len(expired_keys)} کلیلی بەسەرچوو.")

            # 2. سڕینەوەی کلیلە بەسەرچووەکان لە داتابەیس
            cursor.execute("DELETE FROM `keys` WHERE expires_at < %s AND sha256_key IS NOT NULL", (now,))
            connection.commit()
            print("سڕینەوە لە داتابەیس سەرکەوتوو بوو.")

        connection.close()
        
    except Exception as e:
        print(f"هەڵە لە داتابەیس: {e}")

if __name__ == "__main__":
    clean_expired_keys()
