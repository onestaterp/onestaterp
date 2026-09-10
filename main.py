import os
import hashlib
from datetime import datetime, timezone, timedelta
from flask import Flask, request
import telebot
import pymysql

BOT_TOKEN = "8874156704:AAFtjfqvfSK1lDm5pKRsCLLE9dyd7Y_pHGM"

DB_HOST = "localhost"
DB_USER = "u129582972_ewanaligian"
DB_PASSWORD = "Ewan1999@"
DB_NAME = "u129582972_ewanaligian"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

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
        print(f"Database Error: {e}")

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
    return "Bot is running!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "بە خیر بێیت بۆ بۆتی بەڕێوەبردنی کلیلی VIP!\nتکایە ناوی کلیلەکەت بنێرە:")
    bot.register_next_step_handler(message, get_key_name)

def get_key_name(message):
    key_name = message.text.strip()
    bot.reply_to(message, "باشە! ئێستا ماوەی کلیلەکە بە ڕۆژ بنووسە (ژمارە):")
    bot.register_next_step_handler(message, get_duration, key_name)

def get_duration(message, key_name):
    try:
        duration_value = int(message.text.strip())
    except ValueError:
        bot.reply_to(message, "❌ تکایە تەنها ژمارە بنووسە:")
        bot.register_next_step_handler(message, get_duration, key_name)
        return
    bot.reply_to(message, "باشە! ئێستا کۆدی HWID بنێرە (16 پیت):")
    bot.register_next_step_handler(message, process_hwid_and_save, key_name, duration_value)

def process_hwid_and_save(message, key_name, duration_value):
    hwid = message.text.strip()
    if len(hwid) != 16:
        bot.reply_to(message, "❌ هەڵە: کۆدی HWID دەبێت ڕێک 16 پیت بێت:")
        bot.register_next_step_handler(message, process_hwid_and_save, key_name, duration_value)
        return

    final_hashed_key = generate_vip_key(hwid, key_name)
    expiry_str = (datetime.now(timezone.utc) + timedelta(days=duration_value)).strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        connection = pymysql.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME, cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO vip_keys (key_name, vip_key, expiry, hwid) VALUES (%s, %s, %s, %s)", 
                           (key_name, final_hashed_key, expiry_str, hwid))
            connection.commit()
        connection.close()
        bot.reply_to(message, f"✅ **کلیل لە داتابەیس پاشەکەوت بوو:**\n`{final_hashed_key}`", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ هەڵە لە داتابەیس: {str(e)}")

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=f"https://onestaterp.onrender.com/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
