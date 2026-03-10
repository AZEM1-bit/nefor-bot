import telebot
from telebot import types
import time
import os

# ================== КОНФИГУРАЦИЯ ==================
TOKEN = '8720927581:AAF1b4DKxEKAQO35L8avAqc4-PpmYQVrw6s'  # Замените на свой токен!
ADMIN_USERNAMES = ['studionefor', 'Zegyrat_1']

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

# ================== ДАННЫЕ ==================
admin_ids = {}
pending_quizzes = {}
approved_quizzes = {}
rejected_quizzes = {}
all_quizzes = {}
user_quizzes = {}  # Одна анкета на пользователя
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

# ================== УТИЛИТЫ ==================
def safe_send(chat_id, text, **kwargs):
    try:
        return bot.send_message(chat_id, text, **kwargs)
    except Exception as e:
        print(f"Ошибка отправки {chat_id}: {e}")

def has_quiz(user_id):
    return user_id in user_quizzes

def format_user_link(user_id, username):
    return f"@{username}" if username else f"<a href='tg://user?id={user_id}'>{user_id}</a>"

def back_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
    return markup

# ================== ПОЛЬЗОВАТЕЛЬ ==================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    username = message.chat.username
    
    if username in ADMIN_USERNAMES:
        if username not in admin_ids:
            admin_ids[username] = user_id
        safe_send(user_id, "✅ Добро пожаловать в админ-панель!")
        show_admin_menu(user_id)
        return
    
    text = """🎬 NEFOR STUDIO на связи! 📢

Хочешь зарабатывать на прямых эфирах, не выходя из дома? 
Мы ищем и моделей, и операторов в нашу команду!"""
    safe_send(user_id, text)
    show_user_menu(user_id)

def show_user_menu(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if has_quiz(user_id):
        markup.add(types.InlineKeyboardButton("👤 Моя анкета", callback_data="my_quiz"))
    else:
        markup.add(
            types.InlineKeyboardButton("👨‍💼 Оператор", callback_data="choose_operator"),
            types.InlineKeyboardButton("👩 Модель", callback_data="choose_model")
        )
    
    markup.add(types.InlineKeyboardButton("ℹ️ О нас", callback_data="about_us"))
    safe_send(user_id, "📋 Главное меню\nВыберите действие:", reply_markup=markup)

def show_choice_confirmation(user_id, choice):
    if has_quiz(user_id):
        safe_send(user_id, "❌ У вас уже есть анкета. Посмотрите её в меню.")
        show_user_menu(user_id)
        return
    
    desc = {
        "operator": """Мы ищем операторов для работы с моделями на прямых трансляциях.
Бот задаст несколько вопросов о твоём опыте и навыках, чтобы подобрать подходящую роль.

Готов начать? ✅""",
        "model": """Ты попала в команду девушек, которые
зарабатывают на прямых эфирах, не выходя из дома.
Бот задаст несколько вопросов.

Готова показать, что ты крутая и заработать уже с первых дней?
💃🔥"""
    }
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Начать", callback_data=f"confirm_{choice}"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_to_user_menu")
    )
    safe_send(user_id, desc[choice], reply_markup=markup)

def start_survey(user_id, survey_type):
    questions = operator_questions if survey_type == SURVEY_OPERATOR else model_questions
    text = "📋 Вопросы:\n\n" + "\n".join(questions) + "\n\n✏️ Напиши ответы на вопросы (каждый ответ с новой строки).\nМожешь ответить на все сразу!"
    
    user_survey_data[user_id] = {
        'type': survey_type,
        'questions': questions,
        'answers': [],
        'photos': [],
        'stage': 'waiting_answers'
    }
    safe_send(user_id, text)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.chat.id
    
    if user_id not in user_survey_data or user_survey_data[user_id]['stage'] != 'waiting_photos':
        safe_send(user_id, "❌ Сейчас не время для фотографий. Сначала ответь на вопросы!")
        return
    
    data = user_survey_data[user_id]
    file_id = message.photo[-1].file_id
    data['photos'].append(file_id)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Готово (фото отправлены)", callback_data="photos_done"))
    safe_send(user_id, f"✅ Фото {len(data['photos'])} получено!\nМожешь отправить ещё или нажать 'Готово'.", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    user_id = message.chat.id
    text = message.text
    
    if message.chat.username in ADMIN_USERNAMES:
        return
    
    if user_id in user_survey_data:
        data = user_survey_data[user_id]
        
        if data['stage'] == 'waiting_answers':
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            data['answers'] = lines
            
            safe_send(user_id, f"✅ Получено {len(lines)} ответов.")
            
            if data['type'] == SURVEY_MODEL:
                safe_send(user_id, "📸 Теперь отправь фотографии (2-3 шт). Отправляй по одной. Когда закончишь, нажми 'Готово'.")
                data['stage'] = 'waiting_photos'
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("✅ Готово (фото отправлены)", callback_data="photos_done"))
                safe_send(user_id, "Отправляй фотографии:", reply_markup=markup)
            else:
                # Оператор сразу на предпросмотр
                show_confirmation(user_id, data)
            return
        
        elif data['stage'] == 'waiting_photos':
            safe_send(user_id, "❌ Отправляй фото или нажми 'Готово'!")
            return
    
    show_user_menu(user_id)

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    user_id = call.message.chat.id
    data = call.data
    
    try:
        # АДМИН
        if call.message.chat.username in ADMIN_USERNAMES:
            handle_admin_callbacks(user_id, data)
        # ПОЛЬЗОВАТЕЛЬ
        else:
            handle_user_callbacks(user_id, data)
    except Exception as e:
        print(f"Ошибка callback: {e}")
    
    try:
        bot.delete_message(user_id, call.message.message_id)
    except: pass
    bot.answer_callback_query(call.id)

def handle_user_callbacks(user_id, data):
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
        if user_id in user_survey_data and user_survey_data[user_id]['stage'] == 'waiting_photos':
            show_confirmation(user_id, user_survey_data[user_id])
    elif data == "confirm_final":
        confirm_final(user_id)
    elif data == "edit_survey":
        survey_type = user_survey_data[user_id]['type']
        del user_survey_data[user_id]
        start_survey(user_id, survey_type)

def show_confirmation(user_id, data):
    questions = data['questions']
    answers = data['answers']
    
    text = "📋 Ваши ответы:\n\n"
    for i, (q, a) in enumerate(zip(questions, answers)):
        text += f"{q}\n{a}\n\n"
    
    if data['photos']:
        text += f"📸 Фотографии: {len(data['photos'])} шт."
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_final"),
        types.InlineKeyboardButton("✏️ Изменить", callback_data="edit_survey")
    )
    markup.add(types.InlineKeyboardButton("❌ Отмена", callback_data="back_to_user_menu"))
    
    data['stage'] = 'confirm'
    safe_send(user_id, text + "\n\nВсё верно?", reply_markup=markup)

def confirm_final(user_id):
    if user_id not in user_survey_data:
        return
    
    data = user_survey_data[user_id]
    if has_quiz(user_id):
        safe_send(user_id, "❌ У вас уже есть анкета!")
        show_user_menu(user_id)
        return
    
    global quiz_counter
    quiz_counter += 1
    quiz_id = f"survey_{data['type']}_{quiz_counter}"
    
    try:
        username = bot.get_chat(user_id).username
    except:
        username = None
    
    quiz = QuizData(quiz_id, user_id, username, data['answers'], data['photos'], data['type'])
    
    pending_quizzes[quiz_id] = quiz
    all_quizzes[quiz_id] = quiz
    user_quizzes[user_id] = quiz_id
    
    safe_send(user_id, "✅ Спасибо! Анкета отправлена на проверку!")
    notify_admins_about_survey(quiz_id, user_id, username, data['type'], data['answers'], data['photos'], data['questions'])
    del user_survey_data[user_id]
    show_user_menu(user_id)

def show_my_quiz(user_id):
    if not has_quiz(user_id):
        show_user_menu(user_id)
        return
    
    quiz_id = user_quizzes[user_id]
    quiz = (pending_quizzes.get(quiz_id) or approved_quizzes.get(quiz_id) or rejected_quizzes.get(quiz_id))
    
    status_emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌"}
    status_text = {"pending": "Ожидает проверки", "approved": "Принята", "rejected": "Отклонена"}
    
    text = f"{status_emoji[quiz.status]} Ваша анкета\n\n📌 Статус: {status_text[quiz.status]}\n\n"
    for i, answer in enumerate(quiz.answers):
        text += f"{i+1}. {answer}\n"
    
    safe_send(user_id, text)
    
    if quiz.photos:
        safe_send(user_id, f"📸 Фотографии ({len(quiz.photos)} шт.):")
        for photo_id in quiz.photos:
            try:
                bot.send_photo(user_id, photo_id)
            except:
                pass
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    if quiz.status == 'pending':
        markup.add(
            types.InlineKeyboardButton("✏️ Редактировать", callback_data="edit_quiz"),
            types.InlineKeyboardButton("🗑 Удалить", callback_data="delete_quiz")
        )
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_user_menu"))
    
    safe_send(user_id, "Выберите действие:", reply_markup=markup)

def edit_quiz(user_id):
    if not has_quiz(user_id):
        show_user_menu(user_id)
        return
    
    quiz_id = user_quizzes[user_id]
    quiz = pending_quizzes.get(quiz_id)
    
    if quiz and quiz.status == 'pending':
        for storage in [pending_quizzes, approved_quizzes, rejected_quizzes, all_quizzes]:
            storage.pop(quiz_id, None)
        del user_quizzes[user_id]
        safe_send(user_id, "✏️ Редактирование анкеты. Начнём заново.")
        start_survey(user_id, quiz.survey_type)
    else:
        show_user_menu(user_id)

def delete_quiz(user_id):
    if has_quiz(user_id):
        quiz_id = user_quizzes[user_id]
        for storage in [pending_quizzes, approved_quizzes, rejected_quizzes, all_quizzes]:
            storage.pop(quiz_id, None)
        del user_quizzes[user_id]
        safe_send(user_id, "✅ Анкета удалена")
    show_user_menu(user_id)

def show_about_us(user_id):
    about_text = """❗Кто такие Nefor studios?

- онлайн студия с многолетним опытом работы;
- дружная команда профессионалов;
- мы помогаем нашим моделям иметь хороший заработок буквально с первых дней;
- имеем уникальную систему благодаря которой для работы достаточно только мобильного телефона.

❗Что нужно от тебя? 
- быть уникальной и яркой;
- иметь желание получать хороший заработок сидя дома;
- иметь мобильный телефон.

❗️Удобный график
- 5/2 (ты сама выбираешь в какие дни ты хочешь взять выходной);
- смены по 6-7 часов (есть возможность работать утром, днём или ночь).

❗️Заработная плата  
- уже с первого дня ты будешь зарабатывать примерно 10.000 рублей за смену;
- первые 3 дня зп выплачивается каждый день;
- в дальнейшем раз в неделю;
- выплаты в крипте;
- от общего чека ты получаешь 50%.

Присоединяйся в нашу дружную команду и имей высокий заработок с первого дня🥰"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_user_menu"))
    safe_send(user_id, about_text, reply_markup=markup)

# ================== АДМИН ==================
def show_admin_menu(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(f"📋 Ожидают проверки ({len(pending_quizzes)})", callback_data="pending"),
        types.InlineKeyboardButton("✅ Принятые", callback_data="approved")
    )
    markup.add(
        types.InlineKeyboardButton("❌ Отклонённые", callback_data="rejected"),
        types.InlineKeyboardButton(f"📊 Все анкеты ({len(all_quizzes)})", callback_data="all_quizzes")
    )
    safe_send(user_id, "🔐 Админ-панель\nВыберите раздел:", reply_markup=markup)

def notify_admins_about_survey(quiz_id, user_id, username, survey_type, answers, photos, questions):
    if not admin_ids:
        return

    type_name = "Оператор" if survey_type == SURVEY_OPERATOR else "Модель"
    
    if username:
        user_display = f"@{username}"
    else:
        user_display = f"<a href='tg://user?id={user_id}'>{user_id}</a>"

    answers_text = ""
    for i, (q, a) in enumerate(zip(questions, answers)):
        answers_text += f"{q}\n{a}\n\n"
    
    for admin_id in admin_ids.values():
        try:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📋 Проверить", callback_data=f"review_{quiz_id}"))
            
            bot.send_message(
                admin_id,
                f"🔔 Новая анкета {type_name}!\n\n"
                f"📋 Номер: {quiz_id}\n"
                f"👤 Пользователь: {user_display}\n\n"
                f"{answers_text}",
                reply_markup=markup,
                parse_mode='HTML'
            )
            
            if photos:
                bot.send_message(admin_id, f"📸 Фотографии ({len(photos)} шт.):")
                for photo_id in photos:
                    bot.send_photo(admin_id, photo_id)
                    
        except Exception as e:
            print(f"Ошибка отправки админу: {e}")

def handle_admin_callbacks(user_id, data):
    if data == "main_menu":
        show_admin_menu(user_id)
    elif data == "pending":
        show_pending_quizzes(user_id)
    elif data == "approved":
        show_approved_quizzes(user_id)
    elif data == "rejected":
        show_rejected_quizzes(user_id)
    elif data == "all_quizzes":
        show_all_quizzes(user_id)
    elif data.startswith("review_") or data.startswith("manage_"):
        quiz_id = data.split('_')[-1]
        show_quiz_details(user_id, quiz_id)
    elif data.startswith("approve_"):
        approve_quiz(user_id, data[7:])
    elif data.startswith("reject_"):
        reject_quiz(user_id, data[6:])
    elif data.startswith("delete_quiz_admin_"):
        delete_quiz_admin(user_id, data[17:])

def show_pending_quizzes(user_id):
    if not pending_quizzes:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
        safe_send(user_id, "📭 Нет анкет на проверке", reply_markup=markup)
        return
    
    text = f"📋 Ожидают проверки ({len(pending_quizzes)})\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    for qid, quiz in list(pending_quizzes.items())[:10]:
        link = format_user_link(quiz.user_id, quiz.username)
        text += f"• {qid} - {link}\n"
        markup.add(types.InlineKeyboardButton(f"📋 {qid}", callback_data=f"review_{qid}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
    safe_send(user_id, text, reply_markup=markup, parse_mode='HTML')

def show_quiz_details(user_id, quiz_id):
    quiz = (pending_quizzes.get(quiz_id) or approved_quizzes.get(quiz_id) or rejected_quizzes.get(quiz_id))
    if not quiz:
        safe_send(user_id, "❌ Анкета не найдена")
        return
    
    link = format_user_link(quiz.user_id, quiz.username)
    status_emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌"}
    
    text = f"{status_emoji[quiz.status]} Анкета {quiz_id}\n\n👤 {link}\n📌 {quiz.status}\n🕐 {time.strftime('%H:%M %d.%m.%Y', time.localtime(quiz.timestamp))}\n\n"
    
    for i, answer in enumerate(quiz.answers):
        text += f"{i+1}. {answer}\n"
    
    safe_send(user_id, text, parse_mode='HTML')
    
    if quiz.photos:
        safe_send(user_id, f"📸 Фотографии ({len(quiz.photos)} шт.):")
        for photo_id in quiz.photos:
            try:
                bot.send_photo(user_id, photo_id)
            except:
                pass

    markup = types.InlineKeyboardMarkup(row_width=2)
    if quiz.status == 'pending':
        markup.add(
            types.InlineKeyboardButton("✅ Принять", callback_data=f"approve_{quiz_id}"),
            types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{quiz_id}")
        )
    else:
        markup.add(types.InlineKeyboardButton("⏳ Вернуть на проверку", callback_data=f"change_to_pending_{quiz_id}"))
    markup.add(
        types.InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_quiz_admin_{quiz_id}"),
        types.InlineKeyboardButton("◀ Назад", callback_data="main_menu")
    )
    safe_send(user_id, "Выберите действие:", reply_markup=markup)

def approve_quiz(user_id, quiz_id):
    quiz = pending_quizzes.pop(quiz_id, None)
    if quiz:
        quiz.status = 'approved'
        quiz.reviewed_by = user_id
        quiz.reviewed_at = time.time()
        approved_quizzes[quiz_id] = quiz
        safe_send(user_id, f"✅ Анкета {quiz_id} принята")
    show_admin_menu(user_id)

def reject_quiz(user_id, quiz_id):
    quiz = pending_quizzes.pop(quiz_id, None)
    if quiz:
        quiz.status = 'rejected'
        quiz.reviewed_by = user_id
        quiz.reviewed_at = time.time()
        rejected_quizzes[quiz_id] = quiz
        safe_send(user_id, f"❌ Анкета {quiz_id} отклонена")
    show_admin_menu(user_id)

def delete_quiz_admin(user_id, quiz_id):
    quiz = (pending_quizzes.pop(quiz_id, None) or
            approved_quizzes.pop(quiz_id, None) or
            rejected_quizzes.pop(quiz_id, None))
    if quiz and quiz.user_id in user_quizzes:
        del user_quizzes[quiz.user_id]
    safe_send(user_id, f"✅ Анкета {quiz_id} удалена")
    show_admin_menu(user_id)

def show_approved_quizzes(user_id):
    count = len(approved_quizzes)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
    safe_send(user_id, f"✅ Принятых анкет: {count}", reply_markup=markup)

def show_rejected_quizzes(user_id):
    count = len(rejected_quizzes)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
    safe_send(user_id, f"❌ Отклонённых анкет: {count}", reply_markup=markup)

def show_all_quizzes(user_id):
    count = len(all_quizzes)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
    safe_send(user_id, f"📊 Всего анкет: {count}", reply_markup=markup)

# ================== ЗАПУСК ==================
if __name__ == '__main__':
    print("🚀 Nefor Studio Bot запущен!")
    print("👥 Админы:", ', '.join(ADMIN_USERNAMES))
    print("📸 Поддержка фотографий включена!")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
