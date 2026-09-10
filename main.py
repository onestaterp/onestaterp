import os
import base64
import hashlib
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone, timedelta
import requests
import telebot

# ==================== زانیارییە سەرەکییەکان (گۆڕین پێویستە) ====================
BOT_TOKEN = "8874156704:AAEJWnsJcUcAxvBbX4wyjo6luQHr4MofscI"
GITHUB_TOKEN = "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"
REPO_OWNER = "onestaterp"      # بۆ نموونە: onestaterp
REPO_NAME = "onestaterp"          # بۆ نموونە: onestaterp
FILE_PATH = "key.txt"                            # ناوی ئەو فایلەی کە کلیلەکانی تێدا پاشەکەوت دەکرێن

bot = telebot.TeleBot(BOT_TOKEN)

# ==================== وێب سەوڤەر بۆ ڕێندەر (Render Uptime) ====================
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is active and running!")

    def log_message(self, format, *args):
        return  # بۆ ئەوەی لۆگی وێب سەوڤەر ناوی لۆگی بۆتەکە تێک نەدات

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

# ==================== فەنکشنەکانی دروستکردنی کلیل ====================
def generate_vip_key(hwid, key_name):
    raw_data = f"{hwid}-{key_name}-SecretSalt".encode('utf-8')
    return hashlib.sha256(raw_data).hexdigest()[:16].upper()

# ==================== کۆدی سەرەکی بۆت و بەستنەوە بە گیتهەب ====================
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

    bot.reply_to(message, "باشە! ئێستا ماوەی کلیلەکە هەڵبژێرە (بۆ نموونە: 30 بۆ ڕۆژ، یان 60 بۆ خولەک):")
    bot.register_next_step_handler(message, get_duration, key_name)

def get_duration(message, key_name):
    try:
        duration_value = int(message.text.strip())
    except ValueError:
        bot.reply_to(message, "❌ تکایە تەنها ژمارە بنووسە:")
        bot.register_next_step_handler(message, get_duration, key_name)
        return

    bot.reply_to(message, "باشە! ئێستا کۆدی **HWID**ـی خۆت بنێرە (دەبێت پێک هاتبێت لە 16 پیت/ژمارە):")
    bot.register_next_step_handler(message, process_hwid_and_save, key_name, duration_value, False)

def process_hwid_and_save(message, key_name, duration_value, is_minutes):
    hwid = message.text.strip()
    
    if len(hwid) != 16:
        bot.reply_to(
            message,
            "❌ **هەڵە:** کۆدی HWID دەبێت **ڕێک 16 پیت/ژمارە** بێت!\n\nتکایە کۆدی ڕاستەقینەی HWID دووبارە بنێرەوە:",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(message, process_hwid_and_save, key_name, duration_value, is_minutes)
        return

    final_hashed_key = generate_vip_key(hwid, key_name)
    
    purchase_time = datetime.now(timezone.utc)
    purchase_str = purchase_time.strftime("%Y-%m-%d %H:%M:%S")
    expiry_time = purchase_time + timedelta(days=duration_value)
    expiry_str = expiry_time.strftime("%Y-%m-%d %H:%M:%S")
        
    new_entry = f"{final_hashed_key} | Expires: {expiry_str} | HWID: {hwid}"
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    # خوێندنەوەی فایلەکە لە گیتهەب
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        file_data = response.json()
        sha = file_data['sha']
        
        try:
            existing_content = base64.b64decode(file_data['content']).decode('utf-8')
        except Exception:
            existing_content = ""
            
        lines = existing_content.splitlines()
        valid_lines = [line.strip() for line in lines if line.strip()]
        
        valid_lines.append(new_entry)
        updated_content = "\n".join(valid_lines)
        
        encoded_content = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')
        
        data = {
            "message": f"Add new VIP key for {key_name}",
            "content": encoded_content,
            "sha": sha
        }
        
        # ناردنەوەی فایلە نوێکراوەکە بۆ گیتهەب
        update_response = requests.put(url, headers=headers, json=data)
        
        if update_response.status_code in [200, 201]:
            bot.reply_to(
                message, 
                f"✅ **پیرۆزە! کلیلەکەت بە سەرکەوتوویی دروست کرا.**\n\n"
                f"💻 **HWID:** `{hwid}`\n"
                f"🏷 **ناوی کلیل:** `{key_name}`\n"
                f"🔑 **کلیلەکەت (Hash Key):**\n`{final_hashed_key}`\n\n"
                f"⏳ **بەسەرچوون:** {expiry_str}",
                parse_mode="Markdown"
            )
        else:
            bot.reply_to(message, f"❌ هەەڵە لە نوێکردنەوەی گیتهەب: {update_response.status_code}")
    
    elif response.status_code == 404:
        # ئەگەر فایلەکە بوونی نەبوو، خۆکارانە دروستی دەکات
        encoded_content = base64.b64encode(new_entry.encode('utf-8')).decode('utf-8')
        data = {
            "message": "Create keys file and add first key",
            "content": encoded_content
        }
        create_response = requests.put(url, headers=headers, json=data)
        if create_response.status_code in [200, 201]:
            bot.reply_to(message, f"✅ فایل دروست کرا و کلیلەکە پاشەکەوت بوو:\n`{final_hashed_key}`", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ نەمتوانی فایلەکە لە گیتهەب دروست بکەم.")
    else:
        bot.reply_to(message, f"❌ ناتوانم پەیوەندی بە گیتهەبەوە بکەم (کۆدی هەڵە: {response.status_code}). دڵنیابە لە تووکن و ناوی ڕێپۆزیتۆری.")

if __name__ == '__main__':
    # هەڵکردنی وێب سەوڤەر لە پۆشتی سەرەکی بۆتدا
    server_thread = threading.Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()

    print("Bot is running with Web Server...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
