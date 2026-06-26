from telebot import TeleBot , types
from dotenv import load_dotenv
from flask import Flask , request
from schema import create_tables
import os
import query







create_tables()
load_dotenv()
bot_token = os.getenv("BOT_TOKEN")


bot = TeleBot(bot_token , threaded=False)

app = Flask(__name__)


user_state = {}



ADMINS = ["8733201207"]

# Handle Start 
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "N/A"
    
    # ثبت کاربر در دیتابیس از طریق query.py
    query.insert_user(user_id, username)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Book Appointment 📅")
    btn2 = types.KeyboardButton("My Appointments 📋")
    
    if user_id in ADMINS:
        btn3 = types.KeyboardButton("➕ Add Service")
        markup.add(btn3)
        
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "Welcome! How can I help you today?", reply_markup=markup)



@bot.message_handler(func=lambda m: m.text == "Book Appointment 📅")
def show_services(message):
    services = query.get_services()
    markup = types.InlineKeyboardMarkup()
    for sid, name in services:
        markup.add(types.InlineKeyboardButton(name, callback_data=f"service_{sid}"))
    bot.send_message(message.chat.id, "Choose a service:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("service_"))
def choose_date(call):
    service_id = int(call.data.split("_")[1])
    user_state[call.from_user.id] = {"service_id": service_id}
    dates = query.get_dates(service_id)
    markup = types.InlineKeyboardMarkup()
    for d in dates:
        markup.add(types.InlineKeyboardButton(d, callback_data=f"date_{d}"))
    bot.send_message(call.message.chat.id, "Choose a date:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("date_"))
def choose_time(call):
    date = call.data.split("_")[1]
    user_state[call.from_user.id]["date"] = date
    service_id = user_state[call.from_user.id]["service_id"]
    times = query.get_times(service_id, date)
    markup = types.InlineKeyboardMarkup()
    for slot_id, time in times:
        markup.add(types.InlineKeyboardButton(time, callback_data=f"time_{slot_id}"))
    bot.send_message(call.message.chat.id, "Choose a time:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("time_"))
def confirm(call):
    slot_id = int(call.data.split("_")[1])
    user_id = str(call.from_user.id)
    query.book_appointment(user_id, slot_id)
    query.update_slot_status(slot_id)
    bot.send_message(call.message.chat.id, "✅ Appointment booked and time reserved!")
    user_state.pop(call.from_user.id, None)


@bot.message_handler(func=lambda m: m.text == "My Appointments 📋")
def show_appointments(message):
    user_id = str(message.from_user.id)

    if user_id in ADMINS:
        appointments = query.get_admin_appointments(user_id)
        if not appointments:
            bot.send_message(message.chat.id, "📭 No appointments have been booked for your services yet.")
            return
        text = "📋 Appointments booked by users:\n\n"
        for date, time, service, username in appointments:
            text += f"• {service} on {date} at {time} — booked by @{username}\n"
        bot.send_message(message.chat.id, text)

    else:
        appointments = query.get_user_appointments(user_id)
        if not appointments:
            bot.send_message(message.chat.id, "📭 You have no appointments yet.")
            return
        text = "📅 Your Appointments:\n\n"
        for date, time, service in appointments:
            text += f"• {service} on {date} at {time}\n"
        bot.send_message(message.chat.id, text)


# Admin Flow
@bot.message_handler(func=lambda m: m.text == "➕ Add Service")
def ask_service_name(message):
    user_id = str(message.from_user.id)
    if user_id not in ADMINS:
        bot.send_message(message.chat.id, "❌ You are not authorized to add services.")
        return
    user_state[user_id] = {"step": "service_name", "dates": [], "slots": []}
    bot.send_message(message.chat.id, "📝 Enter the name of the new service:")



@bot.message_handler(func=lambda m: str(m.from_user.id) in user_state)
def handle_admin_input(message):
    user_id = str(message.from_user.id)
    state = user_state[user_id]
    step = state["step"]

    if step == "service_name":
        state["service_name"] = message.text.strip()
        state["step"] = "add_date"
        bot.send_message(message.chat.id, "📅 Enter a date (YYYY-MM-DD), or type 'done' when finished:")

    elif step == "add_date":
        text = message.text.strip()
        if text.lower() == "done":
            if not state["dates"]:
                bot.send_message(message.chat.id, "⚠️ You must enter at least one date.")
                return
            state["date_index"] = 0
            state["step"] = "add_times"
            bot.send_message(message.chat.id, f"⏰ Enter times for {state['dates'][0]} (comma-separated):")
        else:
            state["dates"].append(text)
            bot.send_message(message.chat.id, "✅ Date added. Enter another date or type 'done':")

    elif step == "add_times":
        times = [t.strip() for t in message.text.split(",") if t.strip()]
        date = state["dates"][state["date_index"]]
        state["slots"].append((date, times))
        state["date_index"] += 1
        if state["date_index"] < len(state["dates"]):
            next_date = state["dates"][state["date_index"]]
            bot.send_message(message.chat.id, f"⏰ Enter times for {next_date} (comma-separated):")
        else:
            service_id = query.insert_service(state["service_name"], user_id)
            for date, times in state["slots"]:
                query.insert_slots(service_id, date, times)
            bot.send_message(message.chat.id, f"✅ Service '{state['service_name']}' added with {len(state['dates'])} dates.")
            user_state.pop(user_id)








@app.route(f"/{bot_token}" , methods=["POST"])
def webhook():
    raw = request.get_data().decode("utf-8")
    print(f"Raw Update: {raw}")
    update = types.Update.de_json(raw)
    print(f"Parsed Update: {update}")
    bot.process_new_updates([update])
    return "0k" , 200


@app.route("/")
def index():
    return "Bot Is Runing!" , 200




if __name__ == "__main__":
    app.run(host="0.0.0.0" , port=8080)
