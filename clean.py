import mysql.connector
import os

db = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASS'),
    database=os.getenv('DB_NAME')
)
cursor = db.cursor()

# سڕینەوەی کلیلە بەسەرچووەکان
cursor.execute('DELETE FROM `keys` WHERE expires_at < NOW()')
db.commit()

# هێنانی کلیلە کاراکان بۆ فایلی Key.txt
cursor.execute('SELECT sha256_key FROM `keys` WHERE expires_at >= NOW()')
active_keys = cursor.fetchall()

with open('Key.txt', 'w') as f:
    for key in active_keys:
        f.write(key[0] + '\n')

cursor.close()
db.close()
print('Database cleaned and Key.txt updated successfully!')
