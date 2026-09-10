
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import telebot
from telebot import types
import hashlib
import base64
from datetime import datetime, timedelta, timezone

# زانیارییە سەرەکییەکان
TELEGRAM_BOT_TOKEN = "8874156704:AAEJWnsJcUcAxvBbX4wyjo6luQHr4MofscI"
GITHUB_TOKEN = "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"
REPO_OWNER = "onestaterp"
REPO_NAME = "onestaterp"
FILE_PATH = "Key.txt"
CHANNEL_USERNAME = "@Ewan1999Kurd"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# --- وێب سەوڤەرێکی بچووک بۆ ڕێندەر (بۆ گرتنی پۆرت) ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active and running!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    print(f"Web server running on port {port}")
    server.serve_forever()
# ----------------------------------------------------

# فەنکشن بۆ دروستکردنی SHA256 Hash
def generate_vip_key(hwid, key_name):
    raw_string = f"605348db2ce3c473{key_name}EWN2026VIP"
    sha256_output = hashlib.sha256(raw_string.encode('utf-8')).hexdigest()
    return sha256_output

# فەرمانی /start و پشکنینی چەناڵ
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user_lang = message.from_user.language_code
    
    try:
        chat_member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if chat_member.status in ['left', 'kicked']:
            markup = types.InlineKeyboardMarkup()
            btn_channel = types.InlineKeyboardButton(text="📢 جۆینی چەناڵ بکە", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")
            btn_check = types.InlineKeyboardButton(text="✅ پشکنین / دووبارە پشکەنەوە", callback_data="check_sub")
            markup.add(btn_channel)
            markup.add(btn_check)
            
            bot.reply_to(
                message, 
                f"سڵاو! (زمانت: {user_lang})\nبۆ بەکارهێنانی ئەم بۆتە، دەبێت سەرەتا لە چەناڵەکەمان ئەندام بیت:\n{CHANNEL_USERNAME}\n\nتکایە جۆین بکە و پاشان دوگمەی پشکنین بگرە.", 
                reply_markup=markup
            )
            return
    except Exception as e:
        print(f"Error checking channel: {e}")

    show_duration_menu(message.chat.id)

# نیشاندانی لیستی ماوەکان
def show_duration_menu(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_1min = types.InlineKeyboardButton(text="⏱ 1 خولەک (تاقیکردنەوە)", callback_data="dur_1min")
    btn_1d = types.InlineKeyboardButton(text="📅 1 ڕۆژ (24 کاتژمێر)", callback_data="dur_1")
    btn_7d = types.InlineKeyboardButton(text="📅 7 ڕۆژ (هەفتەیەک)", callback_data="dur_7")
    btn_15d = types.InlineKeyboardButton(text="📅 15 ڕۆژ", callback_data="dur_15")
    btn_30d = types.InlineKeyboardButton(text="📅 30 ڕۆژ (مانگێک)", callback_data="dur_30")
    markup.add(btn_1min, btn_1d, btn_7d, btn_15d, btn_30d)
    
    bot.send_message(
        chat_id, 
        "⭐ فەرموو ماوەی کلیلەکەت هەڵبژێرە لە ڕێگەی دوگمەکانی خوارەوە:", 
        reply_markup=markup
    )

# پشکنینی دووبارەی جۆین بوون
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_check_sub(call):
    user_id = call.from_user.id
    try:
        chat_member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if chat_member.status in ['left', 'kicked']:
            bot.answer_callback_query(call.id, "تۆ هێشتا جۆینی چەناڵ نەکردووە!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "سوپاس، جۆین بوونت سەرکەوتوو بوو!")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            show_duration_menu(call.message.chat.id)
    except Exception as e:
        bot.answer_callback_query(call.id, "هەڵەیەک ڕووی دا، دووبارە هەوڵ بدەرەوە.", show_alert=True)

# وەرگرتنی ماوەی هەڵبژاردراو
@bot.callback_query_handler(func=lambda call: call.data.startswith("dur_"))
def handle_duration_selection(call):
    data_val = call.data.split("_")[1]
    
    if data_val == "1min":
        is_minutes = True
        duration_value = 1
        duration_text = "1 خولەک"
    else:
        is_minutes = False
        duration_value = int(data_val)
        duration_text = f"{duration_value} ڕۆژ"

    bot.answer_callback_query(call.id, f"ماوەی {duration_text} هەڵبژێرا.")
    
    msg = bot.send_message(
        call.message.chat.id, 
        f"✅ ماوەی دیاریکراو: **{duration_text}**.\n\n"
        "⚠️ **تێبینی:** ناوی کلیل دەبێت تەنها پیتە ئینگلیزیەکان و **بە کەپیتەڵ (Uppercase)** بێت (نموونە: `EWAN`).\n\n"
        "تکایە **ناوی کلیلەکەت** بنێرە:", 
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, get_key_name, duration_value, is_minutes)

# وەرگرتنی ناوی کلیل
def get_key_name(message, duration_value, is_minutes):
    key_name = message.text.strip()
    
    if not key_name.isupper() or not key_name.isalpha():
        msg = bot.reply_to(
            message, 
            "❌ **هەڵە:** ناوەکە هەڵەیە!\n"
            "• دەبێت تەنها پیتە ئینگلیزیەکان بن.\n"
            "• دەبێت هەموو پیتەکان **کەپیتەڵ (Uppercase)** بن.\n\n"
            "تکایە ناوەکە دووبارە بە ڕاستی بنێرە:",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, get_key_name, duration_value, is_minutes)
        return

    msg = bot.reply_to(message, "باشە! ئێستا کۆدی **HWID**ـی خۆت بنێرە (دەبێت **ڕێک 16 پیت/ژمارە** بێت):")
    bot.register_next_step_handler(msg, process_hwid_and_save, key_name, duration_value, is_minutes)

# وەرگرتنی HWID و پاشەکەوتکردن لە گیتهەب
def process_hwid_and_save(message, key_name, duration_value, is_minutes):
    hwid = message.text.strip()
    
    if len(hwid) != 16 or not hwid.isalnum():
        msg = bot.reply_to(
            message, 
            "❌ **هەڵە:** کۆدی HWID هەڵەیە!\n"
            "• دەبێت **ڕێک 16** پیت یان ژمارە بێت.\n"
            "• تەنها پیت و ژمارە قبوڵ دەکرێت.\n\n"
            "تکایە کۆدی ڕاستەقینەی HWID دووبارە بنێرەوە:",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, process_hwid_and_save, key_name, duration_value, is_minutes)
        return

    final_hashed_key = generate_vip_key(hwid, key_name)
    
    purchase_time = datetime.now(timezone.utc)
    purchase_str = purchase_time.strftime("%Y-%m-%d %H:%M:%S")
    
    if is_minutes:
        expiry_time = purchase_time + timedelta(minutes=duration_value)
    else:
        expiry_time = purchase_time + timedelta(days=duration_value)
        
    expiry_str = expiry_time.strftime("%Y-%m-%d %H:%M:%S")
    
    new_entry = f"{final_hashed_key} | Expires: {expiry_str}"
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        file_data = response.json()
        sha = file_data['sha']
        
        existing_content = base64.b64decode(file_data['content']).decode('utf-8')
        lines = existing_content.splitlines()
        
        valid_lines = []
        now = datetime.now(timezone.utc)
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            if " | Expires: " in line_stripped:
                try:
                    parts = line_stripped.split(" | Expires: ")
                    exp_str = parts[1].strip()
                    exp_time = datetime.strptime(exp_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                    
                    if exp_time > now:
                        valid_lines.append(line_stripped)
                except Exception as e:
                    print(f"Error parsing line: {e}")
            else:
                continue
                    
        valid_lines.append(new_entry)
        updated_content = "\n".join(valid_lines)
        
        encoded_content = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')
        
        data = {
            "message": f"Clean expired keys and add new for {key_name}",
            "content": encoded_content,
            "sha": sha
        }
        
        update_response = requests.put(url, headers=headers, json=data)
        if update_response.status_code == 200:
            bot.reply_to(
                message, 
                f"✅ **پیرۆزە! کلیلەکەت بە سەرکەوتوویی دروست کرا.**\n\n"
                f"💻 **کۆدی HWIDی داخڵکراو:**\n`{hwid}`\n\n"
                f"🏷 **ناوی کلیل:** `{key_name}`\n\n"
                f"🔑 **کلیلەکەت (Hash Key):**\n`{final_hashed_key}`\n\n"
                f"📅 **بەرواری کڕین:** {purchase_str}\n"
                f"⏳ **بەرواری بەسەرچوون:** {expiry_str}",
                parse_mode="Markdown"
            )
        else:
            bot.reply_to(message, "❌ هەەڵەیەک ڕووی دا لە نوێکردنەوەی فایلەکە لە گیتهەب.")
    else:
        bot.reply_to(message, "❌ ناتوانم پەیوەندی بە گیتهەبەوە بکەم.")

if __name__ == '__main__':
    # دەستپێکردنی وێب سەوڤەر لە تەنیشت بۆتەوە (بە پرۆسەیەک کە پێشلی پۆرت نەگرێت)
    server_thread = threading.Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()

    print("Bot is running with Web Server...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
