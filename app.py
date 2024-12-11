import sqlite3
import telebot
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# SQLite3 Connection
conn = sqlite3.connect('telegram_bot.db', check_same_thread=False)
cursor = conn.cursor()

# Create table if not exists
cursor.execute('''
CREATE TABLE IF NOT EXISTS groups (
    group_id TEXT PRIMARY KEY,
    group_link TEXT,
    title TEXT,
    type TEXT,
    is_main INTEGER DEFAULT 0
)
''')
conn.commit()

bot =TeleBot('7681890390:AAHwYCk-8QG_JvBZrBPJ9QLB_hF00NICeUI') 

# Keyboard setup
reply_keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
group_buttons = [KeyboardButton('AddGroup'), KeyboardButton('RemoveGroup'), KeyboardButton('ShowGroups')]
main_group_buttons = [KeyboardButton('ShowMainGroup'), KeyboardButton('SetMainGroup')]
reply_keyboard.add(KeyboardButton('Groups'), KeyboardButton('MainGroup'), KeyboardButton('SendToAll'))

group_keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
group_keyboard.add(*group_buttons, KeyboardButton('Back'))

main_group_keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
main_group_keyboard.add(*main_group_buttons, KeyboardButton('Back'))

@bot.message_handler(commands=['start', 'Start'])
def welcome(message):
    bot.reply_to(message, "Welcome! Choose an option:", reply_markup=reply_keyboard)

@bot.message_handler(func=lambda message: message.text == 'Groups')
def show_group_options(message):
    bot.reply_to(message, "Choose an option for groups:", reply_markup=group_keyboard)

@bot.message_handler(func=lambda message: message.text == 'MainGroup')
def show_main_group_options(message):
    bot.reply_to(message, "Choose an option for the main group:", reply_markup=main_group_keyboard)

@bot.message_handler(func=lambda message: message.text == 'Back')
def go_back(message):
    bot.reply_to(message, "Choose an option:", reply_markup=reply_keyboard)

@bot.message_handler(func=lambda message: message.text == 'AddGroup')
def add_group(message):
    msg = bot.reply_to(message, "Please send the group link:")
    bot.register_next_step_handler(msg, process_group_link)

def process_group_link(message):
    try:
        group_link = message.text.strip()
        
        try:
            if 'joinchat' in group_link or '+' in group_link:
                chat_info = bot.get_chat(group_link)
                group_id = str(chat_info.id)
                username = group_link
            else:
                if group_link.startswith('https://t.me/'):
                    username = group_link.split('/')[-1]
                elif group_link.startswith('t.me/'):
                    username = group_link.split('/')[-1]
                elif group_link.startswith('@'):
                    username = group_link[1:]
                else:
                    username = group_link

                username = username.split('?')[0]
                chat_info = bot.get_chat(f"@{username}")
                group_id = str(chat_info.id)

            try:
                chat_member = bot.get_chat_member(chat_info.id, bot.get_me().id)
                if chat_member.status not in ['administrator', 'member']:
                    bot.reply_to(message, "Bot is not a member of this group. Please add the bot to the group first!")
                    return
            except telebot.apihelper.ApiException as e:
                bot.reply_to(message, "Cannot verify bot membership. Please make sure the bot is in the group.")
                return

            # SQLite insert/update
            cursor.execute('''
            INSERT OR REPLACE INTO groups (group_id, group_link, title, type)
            VALUES (?, ?, ?, ?)
            ''', (group_id, group_link, chat_info.title, chat_info.type))
            conn.commit()

            bot.reply_to(message, f"""
Group successfully added!
Group ID: {group_id}
Title: {chat_info.title}
Type: {chat_info.type}
Link: {group_link}
""")

        except telebot.apihelper.ApiException as e:
            bot.reply_to(message, f"""
Failed to add group. Please make sure:
1. The link is correct
2. The bot is already added to the group
3. The bot is an admin in the group
4. For private groups, use the full invite link

Error: {str(e)}
""")

    except Exception as e:
        bot.reply_to(message, f"General error: {str(e)}")

@bot.message_handler(func=lambda message: message.text == 'RemoveGroup')
def remove_group(message):
    msg = bot.reply_to(message, "Please send the group link to remove:")
    bot.register_next_step_handler(msg, process_remove_group)

def process_remove_group(message):
    try:
        group_link = message.text
        cursor.execute('DELETE FROM groups WHERE group_link = ?', (group_link,))
        conn.commit()
        if cursor.rowcount > 0:
            bot.reply_to(message, "Group removed successfully!")
        else:
            bot.reply_to(message, "Group not found!")
    except Exception as e:
        bot.reply_to(message, f"Error removing group: {str(e)}")

@bot.message_handler(func=lambda message: message.text == 'ShowGroups')
def show_groups(message):
    try:
        cursor.execute('SELECT group_link, title FROM groups')
        groups = cursor.fetchall()
        if groups:
            group_list = "\n".join([f"{group[1]} - {group[0]}" for group in groups])
            bot.reply_to(message, f"Registered groups:\n{group_list}")
        else:
            bot.reply_to(message, "No groups registered yet!")
    except Exception as e:
        bot.reply_to(message, f"Error showing groups: {str(e)}")

@bot.message_handler(func=lambda message: message.text == 'ShowMainGroup')
def show_main_group(message):
    try:
        cursor.execute('SELECT group_link, title FROM groups WHERE is_main = 1')
        main_group = cursor.fetchone()
        if main_group:
            bot.reply_to(message, f"Main group:\n{main_group[1]} - {main_group[0]}")
        else:
            bot.reply_to(message, "No main group set!")
    except Exception as e:
        bot.reply_to(message, f"Error showing main group: {str(e)}")

@bot.message_handler(func=lambda message: message.text == 'SetMainGroup')
def set_main_group(message):
    msg = bot.reply_to(message, "Please send the group link to set as main group:")
    bot.register_next_step_handler(msg, process_set_main_group)

def process_set_main_group(message):
    try:
        group_link = message.text
        cursor.execute('UPDATE groups SET is_main = 0')
        cursor.execute('UPDATE groups SET is_main = 1 WHERE group_link = ?', (group_link,))
        conn.commit()
        if cursor.rowcount > 0:
            bot.reply_to(message, "Main group set successfully!")
        else:
            bot.reply_to(message, "Group not found!")
    except Exception as e:
        bot.reply_to(message, f"Error setting main group: {str(e)}")

@bot.message_handler(func=lambda message: message.text == 'SendToAll')
def send_to_all(message):
    msg = bot.reply_to(message, "Please send the message to broadcast:")
    bot.register_next_step_handler(msg, process_broadcast_message)

def process_broadcast_message(message):
    try:
        cursor.execute('SELECT group_id FROM groups')
        groups = cursor.fetchall()

        for group in groups:
            try:
                if message.content_type == 'text':
                    bot.send_message(group[0], message.text)
                elif message.content_type == 'photo':
                    bot.send_photo(group[0], message.photo[-1].file_id, caption=message.caption)
                elif message.content_type == 'video':
                    bot.send_video(group[0], message.video.file_id, caption=message.caption)
                elif message.content_type == 'document':
                    bot.send_document(group[0], message.document.file_id, caption=message.caption)
                elif message.content_type == 'audio':
                    bot.send_audio(group[0], message.audio.file_id, caption=message.caption)
                elif message.content_type == 'voice':
                    bot.send_voice(group[0], message.voice.file_id, caption=message.caption)
                elif message.content_type == 'sticker':
                    bot.send_sticker(group[0], message.sticker.file_id)
                elif message.content_type == 'location':
                    bot.send_location(group[0], message.location.latitude, message.location.longitude)
                elif message.content_type == 'contact':
                    bot.send_contact(group[0], message.contact.phone_number, message.contact.first_name, message.contact.last_name)
            except Exception as e:
                print(f"Error sending to group {group[0]}: {str(e)}")
                
        bot.reply_to(message, "Message broadcasted successfully!")
    except Exception as e:
        bot.reply_to(message, f"Error broadcasting message: {str(e)}")
        
@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker', 'location', 'contact'])
def handle_forwarded_message(message):
    try:
        cursor.execute('SELECT group_id FROM groups WHERE is_main = 1')
        main_group = cursor.fetchone()
        if main_group and str(message.chat.id) == main_group[0]:
            cursor.execute('SELECT group_id FROM groups WHERE is_main = 0')
            groups = cursor.fetchall()

            for group in groups:
                try:
                    if message.content_type == 'text':
                        bot.send_message(group[0], message.text)
                    elif message.content_type == 'photo':
                        bot.send_photo(group[0], message.photo[-1].file_id, caption=message.caption)
                    elif message.content_type == 'video':
                        bot.send_video(group[0], message.video.file_id, caption=message.caption)
                    elif message.content_type == 'document':
                        bot.send_document(group[0], message.document.file_id, caption=message.caption)
                    elif message.content_type == 'audio':
                        bot.send_audio(group[0], message.audio.file_id, caption=message.caption)
                    elif message.content_type == 'voice':
                        bot.send_voice(group[0], message.voice.file_id, caption=message.caption)
                    elif message.content_type == 'sticker':
                        bot.send_sticker(group[0], message.sticker.file_id)
                    elif message.content_type == 'location':
                        bot.send_location(group[0], message.location.latitude, message.location.longitude)
                    elif message.content_type == 'contact':
                        bot.send_contact(group[0], message.contact.phone_number, message.contact.first_name, message.contact.last_name)
                except Exception as e:
                    print(f"Error sending to group {group[0]}: {str(e)}")
                    
    except Exception as e:
        print(f"Error in forwarded message handler: {str(e)}")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "I don't understand this command.")

@bot.my_chat_member_handler()
def handle_new_chat_member(message):
    try:
        if message.new_chat_member.status == 'administrator':
            chat_info = bot.get_chat(message.chat.id)
            group_id = str(chat_info.id)
            group_link = f"https://t.me/{chat_info.username}" if chat_info.username else "Private Group"
            
            # SQLite insert/update
            cursor.execute('''
            INSERT OR REPLACE INTO groups (group_id, group_link, title, type)
            VALUES (?, ?, ?, ?)
            ''', (group_id, group_link, chat_info.title, chat_info.type))
            conn.commit()

            bot.send_message(message.chat.id, f"""
Group successfully added!
Group ID: {group_id}
Title: {chat_info.title}
Type: {chat_info.type}
Link: {group_link}
""")
    except Exception as e:
        print(f"Error adding group: {str(e)}")

if __name__ == "__main__":
    print("Bot started...")
    bot.polling(none_stop=True)
    app = bot

