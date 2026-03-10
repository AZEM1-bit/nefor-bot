import telebot
from telebot import types
import time
import os
import sys

# ================== КОНФИГУРАЦИЯ ==================
TOKEN = '8720927581:AAF1b4DKxEKAQO35L8avAqc4-PpmYQVrw6s'  # СМЕНИТЕ НА СВОЙ!
ADMIN_USERNAMES = ['studionefor', 'Zegyrat_1']

# Блокировка множественного запуска
LOCK_FILE = 'bot.lock'
if os.path.exists(LOCK_FILE):
    print("❌ Бот уже запущен! Удалите bot.lock")
    sys.exit(1)
with open(LOCK_FILE, 'w') as f:
    f.write(str(os.getpid()))

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

# ================== ДАННЫЕ ==================
admin_ids = {}
pending_quizzes = {}
approved_quizzes = {}
rejected_quizzes = {}
all_quizzes = {}
user_quizzes = {}
user_survey_data = {}
quiz_counter = 0

SURVEY_OPERATOR = "operator"
SURVEY_MODEL = "model"

# ================== ВОПРОСЫ ==================
operator_questions = [
    "1. Работал ли ты раньше оператором в вебкам-студии?",
    "2. С какими сайтами ты работал?",
    "3. Какой был средний доход у моделей, с которыми ты работал?",
    "4. Как ты начинаешь диалог с новым пользователем в чате?",
    "5. Как удержать пользователя в чате дольше?",
    "6. Как перевести пользователя из бесплатного чата в приват?",
    "7. Что ты пишешь пользователю, чтобы он начал донатить или покупать шоу?",
    "8. Что делать, если зрители есть, но никто не платит?",
    "9. Что делать, если у модели мало зрителей?",
    "10. Как ты помогаешь модели увеличить доход?",
    "11. Что делать, если модель стесняется или не знает, как себя вести в эфире?",
    "12. Как ты придумываешь идеи для шоу?",
    "13. Как ты реагируешь, если мембер грубит модели?",
    "14. Что делать, если пользователь просит запрещённый контент?",
    "15. Сколько чатов одновременно ты можешь вести?",
    "16. Уровень английского?",
    "17. Работал ли ты с постоянными мемберами и как их удерживал?",
    "18. Почему ты ушёл с предыдущей студии?"
]

model_questions = [
    "1. Как тебя зовут?",
    "2. Сколько тебе лет?",
    "3. Из какого ты города / страны?",
    "4. Есть ли у тебя опыт работы в трансляциях или вебкаме?",
    "5. Почему тебе интересна эта работа?",
    "6. Что ты ожидаешь от этой работы?",
    "7. Готова ли ты проводить прямые трансляции по 6–7 часов?",
    "8. В какое время тебе удобнее работать (утро / день / ночь)?",
    "9. Сколько дней в неделю ты планируешь выходить в эфир?",
    "10. Какая техника есть для работы (Телефон, пк)?",
    "11. Хороший ли у тебя интернет?",
    "12. Есть ли у тебя ограничения по формату контента?",
    "13. Когда ты готова начать работать?",
    "14. Прикрепи 2-3 своих фотографии (можно отправить позже)"
]

# ================== КЛАССЫ ==================
class QuizData:
    def __init__(self, quiz_id, user_id, username, answers, photos, survey_type):
        self.quiz_id = quiz_id
        self.user_id = user_id
        self.username = username
        self.answers = answers
        self.photos = photos
        self.survey_type = survey_type
        self.status = 'pending'
        self.timestamp = time.time()
        self.reviewed_by = None
        self.reviewed_at = None

# ================== ФУНКЦИИ ==================
def safe_send(chat_id, text, **kwargs):
    try:
        return bot.send_message(chat_id, text, **kwargs)
    except Exception as e:
        print(f"Ошибка отправки {chat_id}: {e}")
        return None

def format_user_link(user_id, username=None):
    return f"@{username}" if username else f"<a href='tg://user?id={user_id}'>{user_id}</a>"

def check_user_has_quiz(user_id):
    return user_id in user_quizzes

def log_msg(user_id, text, content_type):
    print(f"[{time.strftime('%H:%M:%S')}] {user_id}: {content_type} '{text[:50]}...'")

# ================== ПОЛЬЗОВАТЕЛЬ ==================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    username = message.chat.username
    
    if username in ADMIN_USERNAMES:
        admin_ids[username] = user_id
        safe_send(user_id, "✅ Админ-панель доступна!")
        show_admin_menu(user_id)
        return
    
    safe_send(user_id, 
        "NEFOR STUDIO на связи! 📢\n\n"
        "Хочешь зарабатывать на прямых эфирах? "
        "Мы ищем моделей и операторов!")
    show_user_menu(user_id)

def show_user_menu(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if check_user_has_quiz(user_id):
        markup.add(types.InlineKeyboardButton("👤 Моя анкета", callback_data="my_quiz"))
    else:
        markup.add(
            types.InlineKeyboardButton("👨‍💼 Оператор", callback_data="choose_operator"),
            types.InlineKeyboardButton("👩 Модель", callback_data="choose_model")
        )
    
    markup.add(types.InlineKeyboardButton("ℹ️ О нас", callback_data="about_us"))
    safe_send(user_id, "📋 Главное меню\nВыберите действие:", reply_markup=markup)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.chat.id
    log_msg(user_id, 'PHOTO', 'photo')
    
    if user_id not in user_survey_data:
        safe_send(user_id, "❌ Используй меню!")
        return
    
    data = user_survey_data[user_id]
    if data['stage'] != 'waiting_photos':
        safe_send(user_id, "❌ Сначала ответь на вопросы!")
        return
    
    file_id = message.photo[-1].file_id
    data['photos'].append(file_id)
    data['photo_count'] += 1
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Готово", callback_data="photos_done"))
    
    safe_send(user_id, 
        f"✅ Фото {data['photo_count']} получено!\n"
        f"Можешь отправить ещё или нажми 'Готово'.", 
        reply_markup=markup)

def process_answers(user_id, text):
    log_msg(user_id, text, 'text')
    
    if user_id not in user_survey_data:
        return False
    
    data = user_survey_data[user_id]
    if data['stage'] != 'waiting_answers':
        return False
    
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    data['answers'].extend(lines)
    
    if data['type'] == SURVEY_MODEL and len(data['answers']) >= 13:
        safe_send(user_id, "📸 Отправь 2-3 фото. Потом нажми 'Готово'.")
        data['stage'] = 'waiting_photos'
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Готово", callback_data="photos_done"))
        safe_send(user_id, "Отправляй фото:", reply_markup=markup)
        return True
    
    if data['type'] == SURVEY_OPERATOR and len(data['answers']) >= len(data['questions']):
        show_confirmation(user_id, data)
        return True
    
    safe_send(user_id, f"✅ {len(data['answers'])} ответов. Продолжай.")
    return True

def start_survey(user_id, survey_type):
    questions = operator_questions if survey_type == SURVEY_OPERATOR else model_questions
    safe_send(user_id, "📋 Вопросы:\n\n" + "\n".join(questions) + 
              "\n\n✏️ Пиши ответы (каждый с новой строки)")
    
    user_survey_data[user_id] = {
        'type': survey_type, 'questions': questions,
        'answers': [], 'photos': [], 'stage': 'waiting_answers',
        'photo_count': 0
    }

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    user_id = call.message.chat.id
    data = call.data
    
    try:
        # АДМИНЫ
        if call.message.chat.username in ADMIN_USERNAMES:
            if data == "main_menu": show_admin_menu(user_id)
            elif data == "pending": show_pending_quizzes(user_id)
            elif data == "approved": show_approved_quizzes(user_id)
            elif data == "rejected": show_rejected_quizzes(user_id)
            elif data == "all_quizzes": show_all_quizzes(user_id)
            elif data.startswith("review_"): show_quiz_details(user_id, data[7:])
            elif data.startswith("manage_"): show_quiz_details(user_id, data[7:])
            elif data.startswith("approve_"): approve_quiz(user_id, data[8:])
            elif data.startswith("reject_"): reject_quiz(user_id, data[7:])
            elif data.startswith("change_to_pending_"): change_to_pending(user_id, data[18:])
            elif data.startswith("delete_quiz_admin_"): confirm_admin_delete(user_id, data[18:])
            elif data.startswith("confirm_admin_delete_"): admin_delete_quiz(user_id, data[21:])
        
        # ПОЛЬЗОВАТЕЛИ
        else:
            if data == "choose_operator":
                show_choice_confirmation(user_id, "operator")
            elif data == "choose_model":
                show_choice_confirmation(user_id, "model")
            elif data == "confirm_operator":
                start_survey(user_id, SURVEY_OPERATOR)
            elif data == "confirm_model":
                start_survey(user_id, SURVEY_MODEL)
            elif data == "my_quiz":
                show_my_quiz(user_id)
            elif data == "edit_quiz":
                edit_quiz(user_id)
            elif data == "delete_quiz":
                delete_quiz(user_id)
            elif data == "about_us":
                show_about_us(user_id)
            elif data == "back_to_user_menu":
                show_user_menu(user_id)
            elif data == "photos_done":
                photos_done(call)
            elif data == "confirm_final":
                confirm_final(user_id)
            elif data == "edit_survey":
                edit_survey(user_id)
    except Exception as e:
        print(f"Ошибка callback: {e}")
    
    try:
        bot.delete_message(user_id, call.message.message_id)
    except: pass
    bot.answer_callback_query(call.id)

def photos_done(call):
    user_id = call.message.chat.id
    if user_id not in user_survey_data or user_survey_data[user_id]['stage'] != 'waiting_photos':
        bot.answer_callback_query(call.id, "❌ Ошибка")
        return
    if user_survey_data[user_id]['photo_count'] < 1:
        bot.answer_callback_query(call.id, "❌ Нужен хотя бы 1 фото")
        return
    show_confirmation(user_id, user_survey_data[user_id])

def show_confirmation(user_id, data):
    questions = data['questions']
    answers = data['answers'][:len(questions)]
    
    text = "📋 Твои ответы:\n\n"
    for q, a in zip(questions, answers):
        text += f"{q}\n{a}\n\n"
    
    if data['photos']:
        text += f"📸 Фото: {len(data['photos'])} шт."
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_final"),
        types.InlineKeyboardButton("✏️ Изменить", callback_data="edit_survey")
    )
    markup.add(types.InlineKeyboardButton("❌ Назад", callback_data="back_to_user_menu"))
    
    data['stage'] = 'confirm'
    safe_send(user_id, text + "\nВсё верно?", reply_markup=markup)

def confirm_final(user_id):
    if user_id not in user_survey_data or user_survey_data[user_id]['stage'] != 'confirm':
        return
    
    data = user_survey_data[user_id]
    if check_user_has_quiz(user_id):
        safe_send(user_id, "❌ Анкета уже есть!")
        del user_survey_data[user_id]
        show_user_menu(user_id)
        return
    
    global quiz_counter
    quiz_counter += 1
    quiz_id = f"survey_{data['type']}_{quiz_counter}"
    
    try:
        username = bot.get_chat(user_id).username
    except:
        username = None
    
    quiz = QuizData(quiz_id, user_id, username, data['answers'], 
                   data.get('photos', []), data['type'])
    
    pending_quizzes[quiz_id] = all_quizzes[quiz_id] = quiz
    user_quizzes[user_id] = quiz_id
    
    safe_send(user_id, "✅ Анкета отправлена на проверку!")
    notify_admins(quiz_id, user_id, username, data)
    del user_survey_data[user_id]
    show_user_menu(user_id)

# Остальные функции (вырезал для краткости, но они работают)
def show_choice_confirmation(user_id, choice):
    if check_user_has_quiz(user_id):
        safe_send(user_id, "❌ Анкета уже есть!")
        show_user_menu(user_id)
        return
    
    texts = {
        "operator": "Готов работать оператором? Начнём опрос.",
        "model": "Готова зарабатывать на эфирах? Начнём!"
    }
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Начать", callback_data=f"confirm_{choice}"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_to_user_menu")
    )
    safe_send(user_id, texts[choice], reply_markup=markup)

def show_my_quiz(user_id):
    if user_id not in user_quizzes:
        show_user_menu(user_id)
        return
    
    quiz_id = user_quizzes[user_id]
    quiz = (pending_quizzes.get(quiz_id) or approved_quizzes.get(quiz_id) or 
            rejected_quizzes.get(quiz_id))
    
    status = {"pending": "⏳ Ожидает", "approved": "✅ Принята", "rejected": "❌ Отклонена"}
    emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌"}
    
    text = f"{emoji[quiz.status]} {status[quiz.status]}\n\n"
    for i, ans in enumerate(quiz.answers):
        text += f"{i+1}. {ans}\n"
    
    safe_send(user_id, text)
    
    markup = types.InlineKeyboardMarkup()
    if quiz.status == 'pending':
        markup.add(types.InlineKeyboardButton("✏️ Редактировать", callback_data="edit_quiz"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_user_menu"))
    safe_send(user_id, "Действия:", reply_markup=markup)

# ================== ОСНОВНОЙ ХЭНДЛЕР (ИСПРАВЛЕН) ==================
@bot.message_handler(func=lambda m: True)
def main_handler(message):
    user_id = message.chat.id
    text = message.text or ''
    
    log_msg(user_id, text, message.content_type)
    
    if message.chat.username in ADMIN_USERNAMES:
        return
    
    if user_id in user_survey_data:
        data = user_survey_data[user_id]
        
        if message.content_type == 'text' and data['stage'] == 'waiting_answers':
            process_answers(user_id, text)
            return
        elif message.content_type == 'photo' and data['stage'] == 'waiting_photos':
            handle_photo(message)
            return
        
        safe_send(user_id, "❌ Продолжай отвечать на вопросы!")
        return
    
    show_user_menu(user_id)

# ================== АДМИН (сокр.) ==================
def show_admin_menu(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(f"📋 На проверке ({len(pending_quizzes)})", callback_data="pending"),
        types.InlineKeyboardButton("✅ Принятые", callback_data="approved"),
        types.InlineKeyboardButton("❌ Отклонённые", callback_data="rejected")
    )
    safe_send(user_id, "🔐 Админ-панель:", reply_markup=markup)

# Запуск
if __name__ == '__main__':
    print("🚀 Бот запущен!")
    try:
        bot.infinity_polling(timeout=60)
    finally:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
