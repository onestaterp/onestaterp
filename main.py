import os
import hashlib
from datetime import datetime, timezone, timedelta
from flask import Flask, request
import telebot
import pymysql

# ==================== زانیارییە سەرەکییەکان ====================
BOT_TOKEN = "8874156704:AAFtjfqvfSK1lDm5pKRsCLLE9dyd7Y_pHGM"

# زانیارییەکانی داتابەیسی MySQLـەکەت لە هۆستینگەر
DB_HOST = "localhost"
DB_USER = "u129582972_ewanaligian"
DB_PASSWORD = "Ewan1999@"
DB_NAME = "u129582972_ewanaligian"

bot = telebot.TeleBot(BOT_TOKEN, thr"eaded=False)
app = Flask(__name__)

# دروستکردنی خشتە لە داتابەیس ئەگەر بوونی نەبێت
def init_db():
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vip_keys (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    key_name VARCHAR(255),
                    vip_key VARCHAR(255),
                    expiry VARCHAR(255),
                    hwid VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            connection.commit()
        connection.close()
    except Exception as e:
        print(f"Database Initialization Error: {e}")

init_db()

def generate_vip_key(hwid, key_name):
    raw_data = f"{hwid}-{key_name}-SecretSalt".encode('utf-8')
    return hashlib.sha256(raw_data).hexdigest()[:16].upper()

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def receive_message():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route('/')
def index():
    return "Bot with MySQL is active and running!"

# فەنکشنەکانی گفتوگۆی تلگرام
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "بە خیر بێیت بۆ بۆتی بەڕێوەبردنی کلیلی VIP!\nتکایە ناوی کلیلەکەت بنێرە:")
    bot.register_next_step_handler(message, get_key_name)

def get_key_name(message):
    key_name = message.text.strip()
    if not key_name.isalnum():
        bot.reply_to(message, "❌ هەڵە: ناوەکە دەبێت تەنها پیت و ژمارەی ئینگلیزی بێت.")
        bot.register_next_step_handler(message, get_key_name)
        return
    bot.reply_to(message, "باشە! ئێستا ماوەی کلیلەکە بە ڕۆژ بنووسە (ژمارە):")
    bot.register_next_step_handler(message, get_duration, key_name)

def get_duration(message, key_name):
    try:
        duration_value = int(message.text.strip())
    except ValueError:
        bot.reply_to(message, "❌ تکایە تەنها ژمارە بنووسە:")
        bot.register_next_step_handler(message, get_duration, key_name)
        return
    bot.reply_to(message, "باشە! ئێستا کۆدی **HWID**ـی خۆت بنێرە (16 پیت/ژمارە):")
    bot.register_next_step_handler(message, process_hwid_and_save, key_name, duration_value)

def process_hwid_and_save(message, key_name, duration_value):
    hwid = message.text.strip()
    if len(hwid) != 16:
        bot.reply_to(message, "❌ هەڵە: کۆدی HWID دەبێت ڕێک 16 پیت بێت. دووبارە بنێرە:")
        bot.register_next_step_handler(message, process_hwid_and_save, key_name, duration_value)
        return

    final_hashed_key = generate_vip_key(hwid, key_name)
    purchase_time = datetime.now(timezone.utc)
    expiry_time = purchase_time + timedelta(days=duration_value)
    expiry_str = expiry_time.strftime("%Y-%m-%d %H:%M:%S")
    
    # پاشەکەوتکردن لە داتابەیسی MySQL
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            sql = "INSERT INTO vip_keys (key_name, vip_key, expiry, hwid) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (key_name, final_hashed_key, expiry_str, hwid))
            connection.commit()
        connection.close()
        
        bot.reply_to(message, f"✅ **پیرۆزە! کلیل لە داتابەیس پاشەکەوت بوو:**\n`{final_hashed_key}`", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ هەڵە لە پاشەکەوتکردن لە داتابەیس: {str(e)}")

if __name__ == '__main__':
    RENDER_URL = "https://onestaterp.onrender.com"
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{BOT_TOKEN}")
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
