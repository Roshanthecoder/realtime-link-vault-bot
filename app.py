import os
from flask import Flask, request
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db
import telebot
from telebot import types
from datetime import datetime

# ✅ Load .env variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")
DATABASE_URL = os.getenv("DATABASE_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 5000))

if not all([BOT_TOKEN, OWNER_ID, DATABASE_URL, WEBHOOK_URL]):
    print("❌ .env is missing required variables.")
    exit()

try:
    OWNER_ID = int(OWNER_ID)
except:
    print("❌ OWNER_ID must be numeric.")
    exit()

# ✅ Firebase Init
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        "databaseURL": DATABASE_URL
    })
    print("✅ Firebase connected.")
except Exception as e:
    print(f"❌ Firebase init error: {e}")
    exit()

# ✅ Flask & Telebot Init
app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)
user_state = {}

# 🔐 Owner check
def owner_only(func):
    def wrapper(message):
        if message.from_user.id != OWNER_ID:
            bot.send_message(message.chat.id, "⛔️ Access denied.")
            return
        return func(message)
    return wrapper

def get_greeting():
    hour = datetime.now().hour
    if 5 <= hour < 12: return "🌞 Good Morning!\n"
    elif 12 <= hour < 17: return "☀️ Good Afternoon!\n"
    elif 17 <= hour < 21: return "🌇 Good Evening!\n"
    return "🌙 Good Night!\n"

def exit_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ Exit", callback_data="exit"))
    return markup

def show_main_menu(chat_id, greeting=None):
    user_state[chat_id] = {"state": "ACTION"}
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ Add", callback_data="add"))
    markup.add(types.InlineKeyboardButton("📥 Get", callback_data="get"))
    markup.add(types.InlineKeyboardButton("🔄 Status", callback_data="status"))
    msg = f"{greeting}👋 Welcome Owner!\n\nChoose an option:" if greeting else "🔙 Back to main menu:"
    bot.send_message(chat_id, msg, reply_markup=markup)

# ✅ Command Handlers
@bot.message_handler(commands=["start"])
@owner_only
def start(message):
    show_main_menu(message.chat.id, get_greeting())

@bot.message_handler(commands=["exit"])
@owner_only
def exit_cmd(message):
    show_main_menu(message.chat.id)

@bot.message_handler(commands=["status"])
@owner_only
def status_cmd(message):
    now = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    bot.send_message(message.chat.id, f"✅ Bot is alive.\n🕒 {now}")

# ✅ Callback Handler
@bot.callback_query_handler(func=lambda call: True)
def handle_button(call):
    user_id = call.from_user.id
    if user_id != OWNER_ID:
        bot.answer_callback_query(call.id, "⛔️ Unauthorized.")
        return

    data = call.data
    chat_id = call.message.chat.id

    if data == "add":
        user_state[user_id] = {"state": "AWAIT_CONTENT_TYPE"}
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📂 What content type do you want?", callback_data="choose_content"))
        markup.add(types.InlineKeyboardButton("❌ Exit", callback_data="exit"))
        bot.send_message(chat_id, "📁 Choose an option:", reply_markup=markup)

    elif data == "choose_content":
        user_state[user_id] = {"state": "ADDING_CONTENT_TYPE"}
        bot.send_message(chat_id, "📝 Enter content type:")

    elif data == "add_more":
        state = user_state.get(user_id)
        if state and "content_type" in state and "category" in state:
            user_state[user_id] = {
                "state": "ADDING_LINK",
                "content_type": state["content_type"],
                "category": state["category"]
            }
            bot.send_message(chat_id, f"📎 Send another link for *{state['content_type']} → {state['category']}*", parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "❌ Info missing. Please start again.")
            show_main_menu(chat_id)

    elif data == "get":
        user_state[user_id] = {"state": "GET_CONTENT_TYPE"}
        bot.send_message(chat_id, "📁 Which content-type you want?", reply_markup=exit_markup())

    elif data.startswith("delete_link:"):
        _, idx = data.split(":")
        idx = int(idx)
        state = user_state.get(user_id)
        ctype = state.get("content_type")
        cat = state.get("category")
        ref = db.reference(f"links/{ctype}/{cat}")
        links = ref.get()
        if not links or idx >= len(links):
            bot.send_message(chat_id, "❌ Invalid index or link not found.")
            return
        deleted = links.pop(idx)
        ref.set(links)
        bot.send_message(chat_id, f"🗑️ Deleted:\n{deleted}")

    elif data == "exit":
        show_main_menu(chat_id)

    elif data == "status":
        now = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        bot.send_message(chat_id, f"✅ Bot is alive.\n🕒 {now}")

# ✅ Text Handlers
@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("state") == "ADDING_CONTENT_TYPE")
@owner_only
def receive_content_type(message):
    content_type = message.text.strip().lower()
    chat_id = message.chat.id
    user_state[chat_id] = {"state": "ADDING_CATEGORY", "content_type": content_type}
    bot.send_message(chat_id, f"📁 Enter category under *{content_type}*:", parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("state") == "ADDING_CATEGORY")
@owner_only
def receive_category(message):
    chat_id = message.chat.id
    category = message.text.strip().lower()
    content_type = user_state[chat_id]["content_type"]

    try:
        ref = db.reference(f"links/{content_type}/{category}")
        if not ref.get():
            ref.set([])
        user_state[chat_id] = {
            "state": "ADDING_LINK",
            "content_type": content_type,
            "category": category
        }
        bot.send_message(chat_id, f"📎 Send your link for *{content_type} → {category}*", parse_mode="Markdown")
    except:
        bot.send_message(chat_id, "❌ Failed to set category.")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("state") == "ADDING_LINK")
@owner_only
def receive_link(message):
    chat_id = message.chat.id
    state = user_state[chat_id]
    content_type = state["content_type"]
    category = state["category"]
    link = message.text.strip()

    try:
        ref = db.reference(f"links/{content_type}/{category}")
        data = ref.get() or []
        if any(link.lower() == l.lower() for l in data):
            bot.send_message(chat_id, "⚠️ This link already exists.")
        else:
            data.append(link)
            ref.set(data)
            bot.send_message(chat_id, "✅ Successfully added!")

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ Add more link", callback_data="add_more"))
        markup.add(types.InlineKeyboardButton("❌ Exit", callback_data="exit"))
        bot.send_message(chat_id, "Choose next action:", reply_markup=markup)

    except:
        bot.send_message(chat_id, "❌ Error while saving.")
        show_main_menu(chat_id)

    user_state[chat_id]["state"] = "ACTION"

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("state") == "GET_CONTENT_TYPE")
@owner_only
def get_content_type(message):
    content_type = message.text.strip().lower()
    chat_id = message.chat.id
    ref = db.reference(f"links/{content_type}")
    data = ref.get()
    if not data:
        bot.send_message(chat_id, "❌ Invalid content type. Try again:", reply_markup=exit_markup())
        return
    user_state[chat_id] = {"state": "AWAIT_GET_CATEGORY", "content_type": content_type}
    bot.send_message(chat_id, "📁 Enter category name:", reply_markup=exit_markup())

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("state") == "AWAIT_GET_CATEGORY")
@owner_only
def get_links(message):
    chat_id = message.chat.id
    category = message.text.strip().lower()
    ctype = user_state[chat_id]["content_type"]
    ref = db.reference(f"links/{ctype}/{category}")
    links = ref.get()

    if not links:
        bot.send_message(chat_id, "❌ Category doesn't exist. Please enter again:", reply_markup=exit_markup())
        return

    user_state[chat_id] = {"state": "READY_TO_DELETE", "content_type": ctype, "category": category}

    for i, link in enumerate(links):
        bot.send_message(chat_id, f"🔗 {link}")
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("▶️ Play", url=link),
            types.InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_link:{i}")
        )
        bot.send_message(chat_id, f"Options for link {i+1}:", reply_markup=markup)

    bot.send_message(chat_id, "⬅️ Done viewing? Press exit to return.", reply_markup=exit_markup())

# ✅ Webhook Route
@app.route('/')
def home():
    return "✅ Bot is live via webhook!"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

# ✅ Set webhook and run server
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    print(f"🚀 Webhook set to {WEBHOOK_URL}/webhook")

    try:
        bot.send_message(OWNER_ID, "✅ Bot is live on webhook!")
    except:
        print("⚠️ Couldn't notify owner.")

    app.run(host="0.0.0.0", port=PORT)
