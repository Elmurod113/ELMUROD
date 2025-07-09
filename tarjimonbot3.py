import telebot 
from telebot import types 
import fitz  # PyMuPDF 
from googletrans import Translator 
from reportlab.pdfgen import canvas 
import json 
import os

BOT_TOKEN = "7509516758:AAHG0KjB69S1IRH8H3X2DQsRBt7w9_KeQ8E"  # o'zingizning tokeningizni yozing 
bot = telebot.TeleBot(BOT_TOKEN) 
translator = Translator() 
user_data_file = "user_data.json"

#Foydalanuvchi ma'lumotlarini yuklash yoki yaratish

def load_user_data(): 
    if os.path.exists(user_data_file): 
        with open(user_data_file, "r") as f: 
            return json.load(f) 
    return {}

user_data = load_user_data()

#Foydalanuvchi ma'lumotlarini saqlash

def save_user_data(): 
    with open(user_data_file, "w") as f: 
        json.dump(user_data, f)

#PDF dan matn olish

def extract_text_from_pdf(file_path): 
    doc = fitz.open(file_path) 
    full_text = "" 
    for page in doc: 
        full_text += page.get_text() 
        return full_text.strip()

#Tarjimani Google orqali qilish

def translate_text(text, dest_lang): 
    try: 
        translated = translator.translate(text, dest=dest_lang) 
        return translated.text 
    except Exception as e: 
        return f"Tarjimada xatolik: {e}"

#Matnni PDFga saqlash

def save_text_as_pdf(text, filename="translated.pdf"): 
    c = canvas.Canvas(filename) 
    text_object = c.beginText(40, 800) 
    text_object.setFont("Helvetica", 14) 
    for line in text.split('\n'): 
        text_object.textLine(line) 
        if text_object.getY() < 40: 
            c.drawText(text_object) 
            c.showPage() 
            text_object = c.beginText(40, 800) 
            text_object.setFont("Helvetica", 14) 
    c.drawText(text_object) 
    c.save() 
    return filename


#/start komandasi

def handle_start(message): 
    user_id = str(message.from_user.id) 
    args = message.text.split()

    if user_id not in user_data:
        user_data[user_id] = {"count": 0, "lang": "", "format": "text", "invited": []}
        if len(args) > 1 and args[1].startswith("ref_"):
            inviter_id = args[1].replace("ref_", "")
            if inviter_id != user_id and inviter_id in user_data:
                if user_id not in user_data[inviter_id]["invited"]:
                   user_data[inviter_id]["count"] += 1
                   user_data[inviter_id]["invited"].append(user_id)
    save_user_data()

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("\ud83c\uddec\ud83c\uddf7 Inglizcha → O'zbekcha", callback_data="lang_en"))
    markup.add(types.InlineKeyboardButton("\ud83c\uddf7\ud83c\uddfa Ruscha → O'zbekcha", callback_data="lang_ru"))
    bot.send_message(message.chat.id, "Tilni tanlang:", reply_markup=markup)

#Til tanlash

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_")) 
def handle_language(call): 
    user_id = str(call.from_user.id) 
    lang = call.data.replace("lang_", "") 
    user_data[user_id]["lang"] = lang

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Matn holatida", callback_data="format_text"))
    markup.add(types.InlineKeyboardButton("PDF holatida", callback_data="format_pdf"))
    bot.send_message(call.message.chat.id, "Natijani qaysi shaklda olishni xohlaysiz?", reply_markup=markup)

#Format tanlash

@bot.callback_query_handler(func=lambda call: call.data.startswith("format_")) 
def handle_format(call): 
    user_id = str(call.from_user.id) 
    format_type = call.data.replace("format_", "") 
    user_data[user_id]["format"] = format_type 
    save_user_data() 
    bot.send_message(call.message.chat.id, "Iltimos, PDF faylni yuboring")

#PDF fayl qabul qilish

@bot.message_handler(content_types=["document"]) 
def handle_document(message): 
    user_id = str(message.from_user.id) 
    if user_data[user_id]["count"] >= 2: 
        bot.reply_to(message, "⛔ Siz bepul limitdan foydalandingiz. Referal havolangiz orqali do‘st chaqirsangiz qo‘shimcha imkoniyat olasiz.Buning botga /referal buyruqni bering") 
        return

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    file_path = f"{user_id}_uploaded.pdf"
    with open(file_path, "wb") as f:
        f.write(downloaded_file)

    text = extract_text_from_pdf(file_path)
    dest_lang = "uz"
    translated = translate_text(text, dest_lang)
    output_format = user_data[user_id]["format"]
    if output_format == "pdf":
       pdf_file = save_text_as_pdf(translated)
       with open(pdf_file, "rb") as f:
         bot.send_document(message.chat.id, f)
    else:
       bot.send_message(message.chat.id, translated)

    user_data[user_id]["count"] += 1
    save_user_data()
    os.remove(file_path)

#/referal komandasi

@bot.message_handler(commands=["referal"]) 
def referal_link(message): 
    user_id = str(message.from_user.id) 
    link = f"https://t.me/{bot.get_me().username}?start=ref_{user_id}" 
    bot.reply_to(message, f"\u2728 Do‘stlaringizni quyidagi havola orqali chaqiring {link}\n\nHar bir faol do‘st uchun 1 ta qo‘shimcha imkoniyat beriladi.")

#/users komandasi (admin uchun)

@bot.message_handler(commands=["users"]) 
def count_users(message): 
    user_id = str(message.from_user.id) 
    if user_id == "5582681341":  # Bu yerga o'zingizning Telegram ID ni yozing 
        bot.reply_to(message, f"Botdan foydalangan foydalanuvchilar soni: {len(user_data)}") 
    else: 
        bot.reply_to(message, "Sizda bu buyruqdan foydalanish huquqi yo'q.")

@bot.message_handler(commands=["start"])  
def start_handler(message): 
    handle_start(message)

print("Bot ishga tushdi...") 
bot.infinity_polling()