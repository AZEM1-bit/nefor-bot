import telebot
from telebot import types
import json
from datetime import datetime
import ssl
import certifi
import telebot.apihelper as apihelper
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# =================== SSL ФИКС ДЛЯ PYTHON 3.14 + Windows ===================
apihelper.REQUEST_TIMEOUT = 60
apihelper.LONG_POLLING_TIMEOUT = 60

session = requests.Session()
retry_strategy = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
session.mount("http://", adapter)
session.mount("https://", adapter)
session.verify = certifi.where()
apihelper._session = session

# ТОКЕН и АДМИНЫ - ОБЯЗАТЕЛЬНО ЗАМЕНИ!
BOT_TOKEN = "8720927581:AAF1b4DKxEKAQO35L8avAqc4-PpmYQVrw6s"
ADMIN_USERNAMES = ["studionefor", "Zegyrat_1"]

# СОЗДАЕМ БОТА ПЕРЕД ВСЕМИ ОБРАБОТЧИКАМИ
bot = telebot.TeleBot(BOT_TOKEN)

user_data = {}
applications = {}
admin_chat_ids = {}

# =================== КЛАВИАТУРЫ ===================
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("👩‍🎤 Модель", "🎥 Оператор")
    markup.row("📖 О нас")
    return markup

def submitted_keyboard():
    """Клавиатура для пользователя с отправленной анкетой"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("✏️ Изменить анкету")
    markup.row("🗑️ Удалить анкету")  # Кнопка удаления анкеты
    return markup

def admin_main_keyboard():
    """Основная клавиатура админа (только админ панель)"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🎛️ Админ панель")
    return markup

def admin_keyboard():
    """Админская клавиатура без кнопки главного меню"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⏳ Ожидающие", callback_data="admin_pending"),
        types.InlineKeyboardButton("✅ Принятые", callback_data="admin_accepted"),
        types.InlineKeyboardButton("❌ Отклоненные", callback_data="admin_rejected")
    )
    return markup

def back_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return markup

def preview_keyboard(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("📤 Отправить анкету", callback_data=f"submit_{user_id}"))
    markup.row(types.InlineKeyboardButton("➕ Добавить ответ", callback_data=f"add_more_{user_id}"))
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return markup

def admin_app_keyboard(app_id, status=None):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("✅ Принять", callback_data=f"accept_{app_id}"))
    markup.row(types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{app_id}"))
    # Кнопка "вернуть в ожидание" не нужна при проверке ожидающих анкет
    if status and status != 'pending':
        markup.row(types.InlineKeyboardButton("⏳ Вернуть в ожидание", callback_data=f"pending_{app_id}"))
    markup.row(types.InlineKeyboardButton("👀 Посмотреть", callback_data=f"view_{app_id}"))
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    return markup

def get_edit_keyboard():
    """Клавиатура для редактирования анкеты"""
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("➕ Добавить ответ", callback_data="add_answer"))
    markup.row(types.InlineKeyboardButton("📸 Добавить фото", callback_data="add_photo"))
    markup.row(types.InlineKeyboardButton("📤 Отправить изменения", callback_data="submit_changes"))
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return markup

# =================== ОРИГИНАЛЬНЫЕ ТЕКСТЫ ===================
ABOUT_TEXT = """❗️<b>Кто такие Nefor studios?</b>

- онлайн студия с многолетним опытом работы;
- дружная команда профессионалов;
- мы помогаем нашим моделям иметь хороший заработок буквально с первых дней;
- имеем уникальную систему благодаря которой для работы достаточно только мобильного телефона.

❗️<b>Что нужно от тебя?</b> 

- быть уникальной и яркой;
- иметь желание получать хороший заработок сидя дома;
- иметь мобильный телефон.

❗️<b>ты будешь занимать должность МОДЕЛИ</b>❗️

- В твои прямые обязанности входит ведение прямых трансляций (ты сама решаешь какого формата контент ты будешь создавать) 

❗️<b>Удобный график</b>

- 5/2 (ты сама выбираешь в какие дни ты хочешь взять выходной);
- смены по 6-7 часов (есть возможность работать утром, днём или ночь).

❗️<b>Ты переживаешь что у тебя нет опыта?</b>

- Наша команда состоит из опытных кураторов и операторов - мы обучим тебя всему.

❗️<b>Ты будешь работать с оператором</b>
- в его обязанности входит постановка шоу, модерация чатов и общение с пользователями. Он поможет заработать тебе как можно больше.

❗️<b>Переживаешь что у тебя нет оборудования?</b>

- для работы с нами тебе достаточно всего мобильного телефона. 

❗️<b>Заработная плата</b>  

- уже с первого дня ты будешь зарабатывать примерно 10.000 рублей за смену;
- первые 3 дня зп выплачивается каждый день;
- в дальнейшем раз в неделю;
- выплаты в крипте;
- от общего чека ты получаешь 50%.

❗️<b>Так же у нас есть реферальная программа</b> 

- Если у тебя есть подруги которые тоже хотят попробовать себя в этой сфере, ты можешь получить 10.000 за приведение каждой новой модели в нашу команду.

<b>Присоединяйся в нашу дружную команду и имей высокий заработок с первого дня🥰</b>"""

OPERATOR_QUESTIONS = """📋 <b>ВОПРОСЫ ОПЕРАТОРА:</b>

1️⃣ Работал ли ты раньше оператором в вебкам-студии?
2️⃣ С какими сайтами ты работал? 
3️⃣ Какой был средний доход у моделей, с которыми ты работал?
4️⃣ Как ты начинаешь диалог с новым пользователем в чате?
5️⃣ Как удержать пользователя в чате дольше?
6️⃣ Как перевести пользователя из бесплатного чата в приват?
7️⃣ Что ты пишешь пользователю, чтобы он начал донатить или покупать шоу?
8️⃣ Что делать, если зрители есть, но никто не платит?
9️⃣ Что делать, если у модели мало зрителей?
🔟 Как ты помогаешь модели увеличить доход?
1️⃣1️⃣ Что делать, если модель стесняется или не знает, как себя вести в эфире?
1️⃣2️⃣ Как ты придумываешь идеи для шоу?
1️⃣3️⃣ Как ты реагируешь, если мембер грубит модели?
1️⃣4️⃣ Что делать, если пользователь просит запрещённый контент?
1️⃣5️⃣ Сколько чатов одновременно ты можешь вести?
1️⃣6️⃣ Уровень английского?
1️⃣7️⃣ Работал ли ты с постоянными мемберами и как их удерживал?
1️⃣8️⃣ Почему ты ушёл с предыдущей студии?

<i>💡 Отвечай на ЛЮБЫЕ вопросы в ЛЮБОМ порядке! Даже 1 цифра = ответ!</i>"""

MODEL_QUESTIONS = """📋 <b>ВОПРОСЫ МОДЕЛИ:</b>

1️⃣ Как тебя зовут?
2️⃣ Сколько тебе лет?
3️⃣ Из какого ты города / страны?
4️⃣ Есть ли у тебя опыт работы в трансляциях или вебкаме?
5️⃣ Почему тебе интересна эта работа?
6️⃣ Что ты ожидаешь от этой работы?
7️⃣ Готова ли ты проводить прямые трансляции по 6–7 часов?
8️⃣ В какое время тебе удобнее работать (утро / день / ночь)?
9️⃣ Сколько дней в неделю ты планируешь выходить в эфир?
🔟 Какая техника есть для работы (Телефон, ПК)?
1️⃣1️⃣ Хороший ли у тебя интернет?
1️⃣2️⃣ Есть ли у тебя ограничения по формату контента?
1️⃣3️⃣ Когда ты готова начать работать?
1️⃣4️⃣ Прикрепи 2-3 своих фотографии 👉

<i>💡 Отвечай на ЛЮБЫЕ вопросы в ЛЮБОМ порядке! <b>📸 ОБЯЗАТЕЛЬНО 2+ ФОТО!</b></i>"""

# =================== ФУНКЦИИ ===================
def save_admin_chat_id(admin_username, chat_id):
    admin_chat_ids[admin_username] = chat_id

def get_user_role(user_id):
    """Проверяем есть ли уже ОТПРАВЛЕННАЯ анкета у пользователя"""
    if user_id in applications:
        return applications[user_id].get('role')
    return None

def get_status_text(status):
    statuses = {
        'pending': '⏳ На рассмотрении',
        'accepted': '✅ Принята',
        'rejected': '❌ Отклонена'
    }
    return statuses.get(status, '⏳ На рассмотрении')

def show_user_application(chat_id, user_id):
    """Показывает пользователю его анкету с фотографиями"""
    if user_id in applications:
        data = applications[user_id]
        text = f"<b>📋 ТВОЯ АНКЕТА ({data['role'].upper()})</b>\n\n"
        text += f"⏰ Отправлена: {data.get('time', 'неизвестно')}\n"
        text += f"📝 Статус: {get_status_text(data.get('status', 'pending'))}\n\n"
        
        text += "<b>Твои ответы:</b>\n"
        for time, answer in sorted(data['answers'].items()):
            text += f"[{time}] {answer}\n\n"
        
        bot.send_message(chat_id, text, parse_mode='HTML')
        
        # Отправляем все фотографии
        if data['role'] == 'model' and data.get('photos'):
            bot.send_message(chat_id, f"<b>📸 Твои фотографии ({len(data['photos'])} шт.):</b>", parse_mode='HTML')
            
            # Создаем клавиатуру для удаления фотографий
            for i, photo in enumerate(data['photos'], 1):
                markup = types.InlineKeyboardMarkup()
                markup.row(types.InlineKeyboardButton(f"🗑️ Удалить фото #{i}", 
                                                      callback_data=f"delete_photo_{user_id}_{i}"))
                try:
                    bot.send_photo(chat_id, photo['photo_id'], 
                                  caption=f"📸 Фото #{i} (от {photo['time']})",
                                  reply_markup=markup)
                except Exception as e:
                    print(f"Ошибка отправки фото: {e}")

def show_preview(user_id, chat_id):
    data = user_data[user_id]
    preview_text = (
        f"👀 <b>Предпросмотр анкеты</b>\n"
        f"Роль: <b>{data['role'].upper()}</b>\n\n"
    )
    
    preview_text += f"📝 <b>Ответы</b> ({len(data['answers'])}):\n"
    if data['answers']:
        for time, answer in sorted(data['answers'].items()):
            chunk = answer.strip().replace("\n", " ")
            preview_text += f"• <b>{time}</b>: {chunk[:120]}{'…' if len(chunk) > 120 else ''}\n"
    else:
        preview_text += "— пока нет текстовых ответов\n"
    
    if data['role'] == 'model' and data['photos']:
        preview_text += f"\n📸 <b>Фото</b>: {len(data['photos'])} шт.\n"
        for photo in data['photos']:
            preview_text += f"• <b>{photo['time']}</b>: ✅\n"
    
    preview_text += "\n<i>Проверь всё и выбери действие ниже.</i>"
    
    bot.send_message(chat_id, preview_text, reply_markup=preview_keyboard(user_id), parse_mode='HTML')

def notify_admin_new_application(user_id, data):
    """Уведомление о новой анкете"""
    text = f"🆕 <b>НОВАЯ АНКЕТА!</b>\n👤 @{data['username']}\n🆔 {user_id}\n"
    text += f"🎭 Роль: {data['role']}\n⏰ {datetime.now().strftime('%H:%M %d.%m.%Y')}\n\n"
    
    # Первые ответы
    text += "<b>Первые ответы:</b>\n"
    for i, (time, answer) in enumerate(sorted(data['answers'].items())[:3]):
        text += f"{i+1}. [{time}] {answer[:100]}...\n"
    
    if data['role'] == 'model' and data.get('photos'):
        text += f"\n📸 Фото: {len(data['photos'])} шт."
    
    for admin_username in ADMIN_USERNAMES:
        if admin_username in admin_chat_ids:
            try:
                # Отправляем текст
                bot.send_message(admin_chat_ids[admin_username], text, 
                               reply_markup=admin_app_keyboard(user_id), parse_mode='HTML')
                
                # Отправляем фото моделей
                if data['role'] == 'model' and data.get('photos'):
                    media_group = []
                    for photo in data['photos'][:5]:  # Максимум 5 фото
                        media_group.append(types.InputMediaPhoto(photo['photo_id']))
                    
                    if media_group:
                        bot.send_media_group(admin_chat_ids[admin_username], media_group)
                        
            except Exception as e:
                print(f"Ошибка отправки админу {admin_username}: {e}")

def notify_admin_deleted_application(user_id, data):
    """Уведомление об удалении анкеты"""
    text = f"🗑️ <b>Анкета удалена</b>\n👤 @{data['username']}\n🆔 {user_id}\n"
    text += f"🎭 Роль: {data['role']}\n⏰ Удалена: {datetime.now().strftime('%H:%M %d.%m.%Y')}"
    
    for admin_username in ADMIN_USERNAMES:
        if admin_username in admin_chat_ids:
            try:
                bot.send_message(admin_chat_ids[admin_username], text, parse_mode='HTML')
            except Exception as e:
                print(f"Ошибка отправки админу {admin_username}: {e}")

def notify_admins_about_change(user_id, data):
    """Уведомление админов об изменении анкеты"""
    text = f"✏️ <b>Анкета изменена</b>\n👤 @{data['username']}\n🆔 {user_id}\n\n"
    text += f"<b>Новые/измененные ответы:</b>\n"
    
    # Показываем последние 3 ответа
    answers = sorted(data['answers'].items())[-3:]
    for time, answer in answers:
        text += f"[{time}] {answer[:80]}...\n"
    
    if data['role'] == 'model' and data.get('photos'):
        text += f"\n📸 Фото: {len(data['photos'])} шт."
    
    for admin_username in ADMIN_USERNAMES:
        if admin_username in admin_chat_ids:
            try:
                bot.send_message(admin_chat_ids[admin_username], text, 
                               reply_markup=admin_app_keyboard(user_id), parse_mode='HTML')
            except Exception as e:
                print(f"Ошибка отправки админу {admin_username}: {e}")

def show_pending_applications(chat_id):
    pending = {k: v for k, v in applications.items() if v.get('status') not in ['accepted', 'rejected']}
    if pending:
        text = f"⏳ <b>ОЖИДАЮТ ({len(pending)}):</b>\n\n"
        markup = types.InlineKeyboardMarkup()
        for uid, data in list(pending.items())[:10]:
            text += f"👤 @{data.get('username', uid)} | {data['role']} | {data.get('time', '?')}\n"
            markup.row(types.InlineKeyboardButton(f"👀 @{data.get('username', uid)}", callback_data=f"view_{uid}"))
        bot.send_message(chat_id, text, parse_mode='HTML')
        bot.send_message(chat_id, "Выбери анкету для проверки:", reply_markup=markup, parse_mode='HTML')
        bot.send_message(chat_id, "Админ-меню:", reply_markup=admin_keyboard(), parse_mode='HTML')
    else:
        bot.send_message(chat_id, "⏳ Нет ожидающих анкет", reply_markup=admin_keyboard())

def show_accepted_applications(chat_id):
    accepted = {k: v for k, v in applications.items() if v.get('status') == 'accepted'}
    if accepted:
        text = f"✅ <b>ПРИНЯТЫЕ ({len(accepted)}):</b>\n\n"
        markup = types.InlineKeyboardMarkup()
        for uid, data in list(accepted.items())[:10]:
            text += f"👤 @{data.get('username', uid)} | {data['role']} | {data.get('time', '?')}\n"
            markup.row(types.InlineKeyboardButton(f"👀 @{data.get('username', uid)}", callback_data=f"view_{uid}"))
        bot.send_message(chat_id, text, parse_mode='HTML')
        bot.send_message(chat_id, "Выбери анкету для проверки:", reply_markup=markup, parse_mode='HTML')
        bot.send_message(chat_id, "Админ-меню:", reply_markup=admin_keyboard(), parse_mode='HTML')
    else:
        bot.send_message(chat_id, "✅ Нет принятых анкет", reply_markup=admin_keyboard())

def show_rejected_applications(chat_id):
    rejected = {k: v for k, v in applications.items() if v.get('status') == 'rejected'}
    if rejected:
        text = f"❌ <b>ОТКЛОНЕННЫЕ ({len(rejected)}):</b>\n\n"
        markup = types.InlineKeyboardMarkup()
        for uid, data in list(rejected.items())[:10]:
            text += f"👤 @{data.get('username', uid)} | {data['role']} | {data.get('time', '?')}\n"
            markup.row(types.InlineKeyboardButton(f"👀 @{data.get('username', uid)}", callback_data=f"view_{uid}"))
        bot.send_message(chat_id, text, parse_mode='HTML')
        bot.send_message(chat_id, "Выбери анкету для проверки:", reply_markup=markup, parse_mode='HTML')
        bot.send_message(chat_id, "Админ-меню:", reply_markup=admin_keyboard(), parse_mode='HTML')
    else:
        bot.send_message(chat_id, "❌ Нет отклоненных анкет", reply_markup=admin_keyboard())

def show_application_details(chat_id, app_id):
    if app_id in applications:
        data = applications[app_id]
        text = f"<b>📋 АНКЕТА @{data['username']} ({data['role']})</b>\n\n⏰ {data.get('time', 'нет времени')}\n\n"
        
        text += "<b>Все ответы:</b>\n"
        for time, answer in sorted(data['answers'].items()):
            text += f"[{time}] {answer}\n\n"
        
        markup = admin_app_keyboard(app_id, status=data.get('status', 'pending'))
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML')
        
        if data['role'] == 'model' and data.get('photos'):
            for photo in data['photos']:
                try:
                    bot.send_photo(chat_id, photo['photo_id'], f"📸 [{photo['time']}]")
                except Exception as e:
                    print(f"Ошибка отправки фото: {e}")

def submit_application(user_id, chat_id, username):
    """Отправка анкеты с уведомлением админов"""
    if user_id in user_data:
        # Валидация обязательных фото для модели
        if user_data[user_id].get('role') == 'model':
            photos_count = len(user_data[user_id].get('photos', []))
            if photos_count < 2:
                bot.send_message(
                    chat_id,
                    "❗️<b>Для анкеты модели нужно минимум 2 фотографии.</b>\nПришли ещё фото и попробуй снова.",
                    parse_mode='HTML'
                )
                return

        applications[user_id] = user_data[user_id].copy()
        applications[user_id]['time'] = datetime.now().strftime("%d.%m.%Y %H:%M")
        applications[user_id]['status'] = 'pending'
        
        # Уведомляем админов о новой анкете
        notify_admin_new_application(user_id, applications[user_id])
        
        bot.send_message(chat_id, 
                        "✅ <b>Анкета отправлена!</b>\nАдмины рассмотрят в ближайшее время.\nМожешь изменить её в любой момент!", 
                        reply_markup=submitted_keyboard(), parse_mode='HTML')
        del user_data[user_id]

# =================== ОБРАБОТЧИКИ ===================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    
    print(f"👤 {username} ({user_id}) /start")
    
    if username in ADMIN_USERNAMES:
        save_admin_chat_id(username, message.chat.id)
        bot.send_message(message.chat.id, "🎛️ <b>Админ‑панель NEFOR STUDIO</b>\n\nВыбери раздел ниже.", 
                        reply_markup=admin_main_keyboard(), parse_mode='HTML')
        return
    
    user_role = get_user_role(user_id)
    if user_role:
        bot.send_message(
            message.chat.id,
            f"✅ <b>Твоя анкета ({user_role.upper()}) уже отправлена!</b>\n\n"
            f"Что можно сделать дальше:\n"
            f"• ✏️ Изменить анкету\n"
            f"• 🗑️ Удалить анкету",
                        reply_markup=submitted_keyboard(), parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, 
                        "🎬 <b>NEFOR STUDIO</b>\n"
                        "Онлайн‑студия • обучение • поддержка\n\n"
                        "Хочешь зарабатывать на прямых эфирах, не выходя из дома?\n"
                        "Выбери роль — и начнём.",
                        reply_markup=main_keyboard(), parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text == "🎛️ Админ панель")
def admin_panel(message):
    username = message.from_user.username
    if username and username in ADMIN_USERNAMES:
        save_admin_chat_id(username, message.chat.id)
        bot.send_message(message.chat.id, "🎛️ <b>Админ‑панель</b>\n\nВыбери раздел:", 
                        reply_markup=admin_keyboard(), parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, "❌ Доступ запрещён!", reply_markup=main_keyboard())

@bot.message_handler(func=lambda message: message.text == "✏️ Изменить анкету")
def edit_application(message):
    user_id = message.from_user.id
    if user_id in applications:
        # Загружаем анкету обратно в user_data для редактирования
        user_data[user_id] = applications[user_id].copy()
        user_data[user_id]['preview_shown'] = False
        role = user_data[user_id]['role']
        
        # Отправляем анкету пользователю
        show_user_application(message.chat.id, user_id)
        
        questions = OPERATOR_QUESTIONS if role == 'operator' else MODEL_QUESTIONS
        bot.send_message(message.chat.id, f"✏️ <b>РЕДАКТИРОВАНИЕ АНКЕТЫ {role.upper()}</b>\n\n" + 
                        "Ты можешь добавлять новые ответы, удалять или добавлять фотографии.\n\n" + 
                        questions, 
                        reply_markup=get_edit_keyboard(), parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, "❌ Анкета не найдена!", reply_markup=submitted_keyboard())

@bot.message_handler(func=lambda message: message.text == "🗑️ Удалить анкету")
def delete_application(message):
    user_id = message.from_user.id
    if user_id in applications:
        data = applications[user_id].copy()
        
        # Уведомляем админов об удалении
        notify_admin_deleted_application(user_id, data)
        
        # Удаляем анкету
        del applications[user_id]
        # На всякий случай чистим черновик/редактирование
        if user_id in user_data:
            del user_data[user_id]
        
        bot.send_message(message.chat.id, 
                        "🗑️ <b>Анкета удалена</b>\nЕсли захочешь создать новую - нажми /start", 
                        reply_markup=main_keyboard(), parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, "❌ Анкета не найдена!")

@bot.message_handler(func=lambda message: message.text in ["👩‍🎤 Модель", "🎥 Оператор", "📖 О нас"])
def main_menu(message):
    user_id = message.from_user.id
    text = message.text
    user_role = get_user_role(user_id)
    
    if user_role and text in ["👩‍🎤 Модель", "🎥 Оператор"]:
        role_text = "модели" if text == "👩‍🎤 Модель" else "оператора"
        bot.send_message(message.chat.id, f"✅ Ты уже отправил анкету {role_text}! Используй '✏️ Изменить анкету'", 
                        reply_markup=submitted_keyboard())
        return
    
    if text == "📖 О нас":
        bot.send_message(message.chat.id, ABOUT_TEXT, reply_markup=back_keyboard(), parse_mode='HTML')
    
    elif text == "🎥 Оператор":
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("✅ Начать", callback_data="operator_start"))
        markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
        bot.send_message(message.chat.id,
                        "Мы ищем операторов для работы с моделями на прямых трансляциях.\n"
                        "<b>Готов начать? ✅</b>",
                        reply_markup=markup, parse_mode='HTML')
    
    elif text == "👩‍🎤 Модель":
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("✅ Начать", callback_data="model_start"))
        markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
        bot.send_message(message.chat.id,
                        "Ты попала в команду девушек, которые зарабатывают на прямых эфирах, не выходя из дома.\n\n"
                        "✨ <b>Готова показать, что ты крутая?</b>",
                        reply_markup=markup, parse_mode='HTML')

@bot.message_handler(func=lambda message: message.from_user.id in user_data)
def handle_answers(message):
    user_id = message.from_user.id
    if user_id in user_data and not user_data[user_id].get('preview_shown', False):
        now = datetime.now().strftime("%H:%M")
        user_data[user_id]['answers'][now] = message.text[:500]
        
        answers_count = len(user_data[user_id]['answers'])
        photos_count = len(user_data[user_id].get('photos', []))
        is_model = user_data[user_id]['role'] == 'model'
        
        if answers_count >= 1 or (is_model and photos_count >= 2):
            user_data[user_id]['preview_shown'] = True
            show_preview(user_id, message.chat.id)
        else:
            bot.reply_to(message, "✅ Ответ сохранен! Продолжай отвечать на вопросы 👇")

@bot.message_handler(content_types=['photo'], func=lambda message: message.from_user.id in user_data)
def handle_photos(message):
    user_id = message.from_user.id
    if user_id in user_data and user_data[user_id]['role'] == 'model':
        now = datetime.now().strftime("%H:%M")
        photo_id = message.photo[-1].file_id
        
        user_data[user_id]['photos'].append({
            'photo_id': photo_id,
            'time': now
        })

        # Если пользователь прислал фото с подписью — сохраняем подпись как ответ
        caption = getattr(message, 'caption', None)
        if caption:
            user_data[user_id].setdefault('answers', {})
            user_data[user_id]['answers'][now] = caption[:500]
        
        photos_count = len(user_data[user_id]['photos'])
        answers_count = len(user_data[user_id].get('answers', {}))
        previously_had_less_than_two = photos_count == 2
        
        # Показываем предпросмотр, как только выполнены минимальные условия.
        # Для модели — обязательно показать на 2-й фотографии, даже если предпросмотр уже показывался ранее.
        if (not user_data[user_id].get('preview_shown', False) and (answers_count >= 1 or photos_count >= 2)) or previously_had_less_than_two:
            user_data[user_id]['preview_shown'] = True
            show_preview(user_id, message.chat.id)
        else:
            bot.reply_to(message, f"✅ Фото #{photos_count} сохранено! Пришли еще или отвечай на вопросы 👇")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    username = call.from_user.username or f"user_{user_id}"
    chat_id = call.message.chat.id
    
    try:
        bot.answer_callback_query(call.id)
    except:
        pass
    
    if username in ADMIN_USERNAMES and call.data in ["back_main", "admin_back"]:
        bot.send_message(chat_id, "🎛️ <b>АДМИН-ПАНЕЛЬ</b>", reply_markup=admin_keyboard(), parse_mode='HTML')
        return
    
    if call.data == "back_main":
        user_role = get_user_role(user_id)
        if user_role:
            bot.send_message(chat_id, f"✅ <b>Твоя анкета {user_role} уже отправлена!</b>", 
                           reply_markup=submitted_keyboard(), parse_mode='HTML')
        else:
            bot.send_message(chat_id, "🎬 <b>NEFOR STUDIO</b> на связи!\nВыбери роль:", reply_markup=main_keyboard(), parse_mode='HTML')
        return
    
    if call.data == "operator_start":
        user_data[user_id] = {'role': 'operator', 'answers': {}, 'photos': [], 'preview_shown': False, 'username': username}
        bot.send_message(chat_id, OPERATOR_QUESTIONS, reply_markup=back_keyboard(), parse_mode='HTML')
        return
    
    if call.data == "model_start":
        user_data[user_id] = {'role': 'model', 'answers': {}, 'photos': [], 'preview_shown': False, 'username': username}
        bot.send_message(chat_id, MODEL_QUESTIONS, reply_markup=back_keyboard(), parse_mode='HTML')
        return
    
    # Обработка удаления фото
    if call.data.startswith("delete_photo_"):
        _, _, user_id_str, photo_idx_str = call.data.split('_', 3)
        target_user_id = int(user_id_str)
        
        if target_user_id in user_data and user_data[target_user_id]['role'] == 'model':
            # Удаляем фото из временных данных (по индексу, чтобы не превышать лимит callback_data)
            try:
                photo_idx = int(photo_idx_str) - 1
            except ValueError:
                photo_idx = -1

            if 0 <= photo_idx < len(user_data[target_user_id].get('photos', [])):
                user_data[target_user_id]['photos'].pop(photo_idx)
            
            bot.answer_callback_query(call.id, "✅ Фото удалено!")
            try:
                bot.edit_message_caption(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    caption="❌ Фото удалено"
                )
            except:
                pass
            
            # Показываем обновленную анкету
            show_user_application(call.message.chat.id, target_user_id)
        return
    
    # Обработка добавления ответа
    if call.data == "add_answer":
        if user_id in user_data:
            user_data[user_id]['preview_shown'] = False
            role = user_data[user_id]['role']
            questions = OPERATOR_QUESTIONS if role == 'operator' else MODEL_QUESTIONS
            bot.send_message(call.message.chat.id, 
                            f"➕ <b>ДОБАВЬ НОВЫЙ ОТВЕТ</b>\n\n" + questions, 
                            reply_markup=back_keyboard(), parse_mode='HTML')
        return
    
    # Обработка добавления фото
    if call.data == "add_photo":
        bot.send_message(call.message.chat.id, 
                        "📸 Отправь новую фотографию:", 
                        reply_markup=back_keyboard())
        return
    
    # Обработка отправки изменений
    if call.data == "submit_changes":
        if user_id in user_data:
            # Обновляем анкету
            old_data = applications.get(user_id, {})
            new_data = user_data[user_id]

            # Валидация обязательных фото для модели
            if new_data.get('role') == 'model':
                photos_count = len(new_data.get('photos', []))
                if photos_count < 2:
                    bot.send_message(
                        call.message.chat.id,
                        "❗️<b>Нужно минимум 2 фотографии для анкеты модели.</b>\nДобавь фото и отправь изменения ещё раз.",
                        parse_mode='HTML'
                    )
                    return
            
            # Сохраняем старый статус и время
            new_data['status'] = old_data.get('status', 'pending')
            new_data['time'] = datetime.now().strftime("%d.%m.%Y %H:%M")
            new_data['username'] = call.from_user.username or f"user_{user_id}"
            
            applications[user_id] = new_data
            
            # Уведомляем админов об изменении
            notify_admins_about_change(user_id, new_data)
            
            bot.send_message(call.message.chat.id, 
                            "✅ <b>Анкета обновлена!</b>\nИзменения сохранены.", 
                            reply_markup=submitted_keyboard(), parse_mode='HTML')
            
            del user_data[user_id]
        return
    
    # 📤 НОВАЯ КНОПКА "Отправить анкету"
    if call.data.startswith("submit_"):
        if user_id in user_data:
            submit_application(user_id, chat_id, username)
        return
    
    # ➕ НОВАЯ КНОПКА "Добавить ответ"
    if call.data.startswith("add_more_"):
        if user_id in user_data:
            user_data[user_id]['preview_shown'] = False
            role = user_data[user_id]['role']
            questions = OPERATOR_QUESTIONS if role == 'operator' else MODEL_QUESTIONS
            bot.send_message(chat_id, f"➕ <b>ДОБАВЬ ЕЩЁ ОТВЕТЫ</b>\n\n" + questions, reply_markup=back_keyboard(), parse_mode='HTML')
        return
    
    # (кнопка "Очистить" убрана)
    
    if call.data.startswith("edit_"):
        if user_id in user_data:
            user_data[user_id]['preview_shown'] = False
            questions = OPERATOR_QUESTIONS if user_data[user_id]['role'] == 'operator' else MODEL_QUESTIONS
            bot.send_message(chat_id, questions, reply_markup=back_keyboard(), parse_mode='HTML')
        return
    
    if username in ADMIN_USERNAMES:
        if call.data == "admin_pending":
            show_pending_applications(chat_id)
        elif call.data == "admin_accepted":
            show_accepted_applications(chat_id)
        elif call.data == "admin_rejected":
            show_rejected_applications(chat_id)
        elif call.data.startswith("accept_"):
            app_id = int(call.data.split("_")[1])
            if app_id in applications:
                applications[app_id]['status'] = 'accepted'
                bot.send_message(chat_id, f"✅ Анкета @{applications[app_id]['username']} принята!", 
                               reply_markup=admin_keyboard(), parse_mode='HTML')
        elif call.data.startswith("reject_"):
            app_id = int(call.data.split("_")[1])
            if app_id in applications:
                applications[app_id]['status'] = 'rejected'
                bot.send_message(chat_id, f"❌ Анкета @{applications[app_id]['username']} отклонена!", 
                               reply_markup=admin_keyboard(), parse_mode='HTML')
        elif call.data.startswith("pending_"):
            app_id = int(call.data.split("_")[1])
            if app_id in applications:
                applications[app_id]['status'] = 'pending'
                bot.send_message(chat_id, f"⏳ Анкета @{applications[app_id]['username']} возвращена в ожидание!", 
                               reply_markup=admin_keyboard(), parse_mode='HTML')
        elif call.data.startswith("view_"):
            app_id = int(call.data.split("_")[1])
            show_application_details(chat_id, app_id)

# =================== ЗАПУСК ===================
if __name__ == "__main__":
    print("🤖 Nefor Studio Bot запущен!")
    print("🌐 SSL фикс: ✅ | Таймаут: 60с | Ретраи: 5")
    print("👥 Админы:", ADMIN_USERNAMES)
    
    try:
        bot.polling(none_stop=True, interval=1, timeout=60, long_polling_timeout=60)
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("🔄 Перезапуск через 10 сек...")
        import time
        time.sleep(10)
        bot.polling(none_stop=True, interval=1, timeout=60)
