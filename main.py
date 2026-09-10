import os
import base64
import hashlib
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone, timedelta
import requests
import telebot

# ==================== زانیارییە سەرەکییەکان ====================
BOT_TOKEN = "8874156704:AAEJWnsJcUcAxvBbX4wyjo6luQHr4MofscI"
GITHUB_TOKEN = "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"
REPO_OWNER = "onestaterp"
REPO_NAME = "onestaterp"
FILE_PATH = "key.txt"                            

bot = telebot.TeleBot(BOT_TOKEN)

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is active and running!")
    def log_message(self, format, *args):
        return

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

def generate_vip_key(hwid, key_name):
    raw_data = f"{hwid}-{key_name}-SecretSalt".encode('utf-8')
    return hashlib.sha256(raw_data).hexdigest()[:16].upper()

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
    purchase_str = purchase_time.strftime("%Y-%m-%d %H:%M:%S")
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
            bot.reply_to(message, f"❌ هەڵە لە نوێکردنەوەی گیتهەب. کۆد: {update_response.status_code}\nوەڵام: {update_response.text}")
            
    elif response.status_code == 404:
        encoded_content = base64.b64encode(new_entry.encode('utf-8')).decode('utf-8')
        data = {"message": "Create keys file", "content": encoded_content}
        create_response = requests.put(url, headers=headers, json=data)
        if create_response.status_code in [200, 201]:
            bot.reply_to(message, f"✅ فایل دروست کرا و کلیل پاشەکەوت بوو:\n`{final_hashed_key}`", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"❌ نەمتوانی فایل دروست بکەم. کۆد: {create_response.status_code}\nوەڵام: {create_response.text}")
    else:
        # لێرەدا کۆدی وردی هەڵەکە دەبینین
        bot.reply_to(message, f"❌ هەڵەی گیتهەب! کۆدی هەڵە: {response.status_code}\nوەڵام: {response.text}")

if __name__ == '__main__':
    server_thread = threading.Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
