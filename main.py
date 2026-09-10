import os
import base64
import hashlib
from datetime import datetime, timezone, timedelta
import requests
from flask import Flask, request
import telebot

# ==================== زانیارییە سەرەکییەکان ====================
BOT_TOKEN = "8874156704:AAFtjfqvfSK1lDm5pKRsCLLE9dyd7Y_pHGM"
GITHUB_TOKEN = "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"
REPO_OWNER = "onestaterp"
REPO_NAME = "onestaterp"
FILE_PATH = "key.txt"                            

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

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
    return "Bot is active and running!"

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
    new_entry = f"{final_hashed_key} | Expires: {expiry_str} | HWID: {hwid}"
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        file_data = response.json()
        sha = file_data['sha']
        try:
            existing_content = base64.b64decode(file_data['content']).decode('utf-8')
        except Exception:
            existing_content = ""
            
        lines = [line.strip() for line in existing_content.splitlines() if line.strip()]
        lines.append(new_entry)
        updated_content = "\n".join(lines)
        encoded_content = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')
        
        data = {"message": f"Add key {key_name}", "content": encoded_content, "sha": sha}
        update_response = requests.put(url, headers=headers, json=data)
        
        if update_response.status_code in [200, 201]:
            bot.reply_to(message, f"✅ **پیرۆزە! کلیل دروست کرا:**\n`{final_hashed_key}`", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"❌ هەڵە لە نوێکردنەوەی گیتهەب. کۆد: {update_response.status_code}")
            
    elif response.status_code == 404:
        encoded_content = base64.b64encode(new_entry.encode('utf-8')).decode('utf-8')
        data = {"message": "Create keys file", "content": encoded_content}
        create_response = requests.put(url, headers=headers, json=data)
        if create_response.status_code in [200, 201]:
            bot.reply_to(message, f"✅ فایل دروست کرا و کلیل پاشەکەوت بوو:\n`{final_hashed_key}`", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"❌ نەمتوانی فایل دروست بکەم. کۆد: {create_response.status_code}")
    else:
        bot.reply_to(message, f"❌ هەڵەی گیتهەب! کۆدی هەڵە: {response.status_code}")

if __name__ == '__main__':
    # ڕێکخستنی وێب‌هۆک بۆ ڕێگریکردن لە کێشەی 409
    RENDER_URL = "https://onestaterp.onrender.com"
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{BOT_TOKEN}")
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
