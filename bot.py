
import telebot
from telebot import types
import time
import re

# ТВОЙ ТОКЕН
TOKEN = '8720927581:AAF1b4DKxEKAQO35L8avAqc4-PpmYQVrw6s'

# Список админов (их username без @)
ADMIN_USERNAMES = ['studionefor', 'Zegyrat_1']

bot = telebot.TeleBot(TOKEN)

# Хранилища данных
admin_ids = {}
pending_quizzes = {}
approved_quizzes = {}
rejected_quizzes = {}
all_quizzes = {}
user_quizzes = {}          # связь user_id -> quiz_id
quiz_counter = 0
admin_states = {}          # состояния админов
user_survey_data = {}      # данные опроса пользователя

# Типы опросов
SURVEY_OPERATOR = "operator"
SURVEY_MODEL = "model"

# ВОПРОСЫ ДЛЯ ОПЕРАТОРА
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

# ВОПРОСЫ ДЛЯ МОДЕЛИ (только 13 вопросов, 14-й убран) - ЭТОТ КОММЕНТАРИЙ ТОЖЕ НУЖНО ИСПРАВИТЬ
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
    "14. Прикрепи 2-3 своих фотографии"
]

class QuizData:
    def __init__(self, quiz_id, user_id, username, answers, photos, survey_type):
        self.quiz_id = quiz_id
        self.user_id = user_id
        self.username = username
        self.answers = answers          # текстовые ответы
        self.photos = photos             # список file_id фотографий
        self.survey_type = survey_type
        self.status = 'pending'
        self.timestamp = time.time()
        self.reviewed_by = None
        self.reviewed_at = None

def format_user_link(user_id, username=None):
    if username:
        return f"@{username}"
    else:
        return f"<a href='tg://user?id={user_id}'>{user_id}</a>"

def is_admin(message):
    return message.chat.username in ADMIN_USERNAMES

def check_user_has_any_quiz(user_id):
    return user_id in user_quizzes

# ================== ПОЛЬЗОВАТЕЛЬСКАЯ ЧАСТЬ ==================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    username = message.chat.username

    if username in ADMIN_USERNAMES:
        admin_ids[username] = user_id
        bot.send_message(user_id, "✅ Вы зарегистрированы как администратор!")
        pending_count = len(pending_quizzes)
        if pending_count > 0:
            bot.send_message(user_id, f"📨 Ожидает проверки: {pending_count} заявок")
        show_admin_menu(user_id)
        return

    welcome_text = (
        "NEFOR STUDIO на связи! 📢\n\n"
        "Хочешь зарабатывать на прямых эфирах, не выходя из дома? "
        "Мы ищем и моделей, и операторов в нашу команду!"
    )
    bot.send_message(user_id, welcome_text)
    show_user_menu(user_id)

def show_user_menu(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if check_user_has_any_quiz(user_id):
        markup.add(types.InlineKeyboardButton("👤 Моя анкета", callback_data="my_quiz"))
    else:
        markup.add(
            types.InlineKeyboardButton("👨‍💼 Оператор", callback_data="choose_operator"),
            types.InlineKeyboardButton("👩 Модель", callback_data="choose_model")
        )
    
    markup.add(types.InlineKeyboardButton("ℹ️ О нас", callback_data="about_us"))
    bot.send_message(user_id, "📋 Главное меню\nВыберите действие:", reply_markup=markup)

def show_choice_confirmation(user_id, choice):
    if check_user_has_any_quiz(user_id):
        bot.send_message(user_id, "❌ У вас уже есть анкета. Вы можете посмотреть её в главном меню.")
        show_user_menu(user_id)
        return
    
    desc = {
        "operator": "Мы ищем операторов для работы с моделями на прямых трансляциях.\nБот задаст несколько вопросов о твоём опыте и навыках, чтобы подобрать подходящую роль.\n\nГотов начать? ✅",
        "model": "Ты попала в команду девушек, которые\nзарабатывают на прямых эфирах, не выходя из дома.\nБот задаст несколько вопросов.\n\nГотова показать, что ты крутая и заработать уже с первых дней?\n💃🔥"
    }
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Начать", callback_data=f"confirm_{choice}"),
        types.InlineKeyboardButton("◀ Назад", callback_data="back_to_user_menu")
    )
    bot.send_message(user_id, desc[choice], reply_markup=markup)

def show_my_quiz(user_id):
    if user_id not in user_quizzes:
        show_user_menu(user_id)
        return
    
    quiz_id = user_quizzes[user_id]
    quiz = (pending_quizzes.get(quiz_id) or 
            approved_quizzes.get(quiz_id) or 
            rejected_quizzes.get(quiz_id))
    
    if not quiz:
        return
    
    status_emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌"}[quiz.status]
    status_text = {"pending": "Ожидает проверки", "approved": "Принята", "rejected": "Отклонена"}[quiz.status]
    
    text = f"{status_emoji} Ваша анкета\n\n📌 Статус: {status_text}\n\n"
    
    for i, answer in enumerate(quiz.answers):
        text += f"{i+1}. {answer}\n"
    
    bot.send_message(user_id, text)
    
    if quiz.photos:
        bot.send_message(user_id, f"📸 Фотографии ({len(quiz.photos)} шт.):")
        for photo_id in quiz.photos:
            bot.send_photo(user_id, photo_id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    if quiz.status == 'pending':
        markup.add(
            types.InlineKeyboardButton("✏️ Редактировать", callback_data="edit_quiz"),
            types.InlineKeyboardButton("🗑 Удалить", callback_data="delete_quiz")
        )
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_user_menu"))
    
    bot.send_message(user_id, "Выберите действие:", reply_markup=markup)

def start_survey(user_id, survey_type):
    questions = operator_questions if survey_type == SURVEY_OPERATOR else model_questions
    bot.send_message(user_id, "📋 Вопросы:\n\n" + "\n".join(questions))
    bot.send_message(user_id, "✏️ Напиши ответы на вопросы (каждый ответ с новой строки).")
    
    user_survey_data[user_id] = {
        'type': survey_type,
        'questions': questions,
        'answers': [],
        'photos': [],
        'stage': 'waiting_answers',  # ИСПРАВЛЕНО: точно 'waiting_answers'
        'photo_count': 0
    }

def process_survey_answers(user_id, text):
    data = user_survey_data.get(user_id)
    if not data or data['stage'] != 'waiting_answers':
        return False

    answers = [line.strip() for line in text.strip().split('\n') if line.strip()]
    data['answers'].extend(answers)
    
    # Если это модель и собрали 13 ответов
    if data['type'] == SURVEY_MODEL and len(data['answers']) >= 13:
        # Переходим в режим ожидания фото
        bot.send_message(user_id, "📸 Теперь отправь фотографии (2-3 шт).\nОтправляй по одной. Когда закончишь, нажми 'Готово'.")
        
        data['stage'] = 'waiting_photos'  # ИСПРАВЛЕНО: меняем стадию
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Готово (фото отправлены)", callback_data="photos_done"))
        bot.send_message(user_id, "Отправляй фотографии:", reply_markup=markup)
        return True
    
    # Для оператора проверяем окончание
    if data['type'] == SURVEY_OPERATOR and len(data['answers']) >= len(data['questions']):
        show_confirmation(user_id, data)
        return True
    
    return True

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.chat.id
    
    if user_id not in user_survey_data:
        bot.send_message(user_id, "❌ Сейчас не время для фотографий. Используй меню.")
        return
    
    data = user_survey_data[user_id]
    
    # ИСПРАВЛЕНО: проверяем стадию waiting_photos
    if data['stage'] == 'waiting_photos':
        file_id = message.photo[-1].file_id
        data['photos'].append(file_id)
        data['photo_count'] += 1
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Готово (фото отправлены)", callback_data="photos_done"))
        
        bot.send_message(
            user_id, 
            f"✅ Фото {data['photo_count']} получено ({len(data['photos'])} всего).\nМожешь отправить ещё или нажать 'Готово'.",
            reply_markup=markup
        )
    else:
        bot.send_message(user_id, "❌ Сейчас жду текстовые ответы. Отправь их сначала.")

@bot.callback_query_handler(func=lambda call: call.data == "photos_done")
def photos_done_callback(call):
    user_id = call.message.chat.id
    
    if user_id not in user_survey_data:
        bot.answer_callback_query(call.id, "❌ Ошибка")
        return
    
    data = user_survey_data[user_id]
    
    if data['stage'] != 'waiting_photos':
        bot.answer_callback_query(call.id, "❌ Ошибка состояния")
        return
    
    if data['photo_count'] < 1:
        bot.answer_callback_query(call.id, "❌ Отправь хотя бы одно фото")
        return
    
    # Показываем подтверждение
    show_confirmation(user_id, data)
    try:
        bot.delete_message(user_id, call.message.message_id)
    except:
        pass
    bot.answer_callback_query(call.id)

def show_confirmation(user_id, data):
    # Формируем текст ответов
    answer_lines = []
    questions = data['questions']
    answers = data['answers'][:len(questions)]  # Берем только нужное количество
    for i, (q, a) in enumerate(zip(questions, answers)):
        answer_lines.append(f"{q}\n{a}")
    
    text = "📋 Ваши ответы:\n\n" + "\n\n".join(answer_lines)
    
    if data['photos']:
        text += f"\n\n📸 Фотографии: {len(data['photos'])} шт."
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_final"),
        types.InlineKeyboardButton("✏️ Изменить", callback_data="edit_survey"),
        types.InlineKeyboardButton("❌ Отмена", callback_data="back_to_user_menu")
    )
    
    data['stage'] = 'confirm'
    bot.send_message(user_id, text + "\n\nВсё верно?", reply_markup=markup)

def confirm_final(user_id):
    data = user_survey_data.get(user_id)
    if not data or data.get('stage') != 'confirm':
        return

    if check_user_has_any_quiz(user_id):
        bot.send_message(user_id, "❌ Ошибка: анкета уже существует")
        show_user_menu(user_id)
        del user_survey_data[user_id]
        return

    global quiz_counter
    quiz_counter += 1
    quiz_id = f"survey_{data['type']}_{quiz_counter}"

    # Получаем реальный username из Telegram
    try:
        chat = bot.get_chat(user_id)
        username = chat.username
    except:
        username = None

    quiz = QuizData(
        quiz_id=quiz_id,
        user_id=user_id,
        username=username,
        answers=data['answers'],
        photos=data.get('photos', []),
        survey_type=data['type']
    )
    
    pending_quizzes[quiz_id] = quiz
    all_quizzes[quiz_id] = quiz
    user_quizzes[user_id] = quiz_id

    bot.send_message(user_id, "✅ Спасибо! Анкета отправлена.")
    
    # Отправляем админам
    notify_admins_about_survey(quiz_id, user_id, username, data['type'], 
                              data['answers'], data.get('photos', []), data['questions'])
    
    show_user_menu(user_id)
    del user_survey_data[user_id]

def edit_quiz(user_id):
    if user_id not in user_quizzes:
        show_user_menu(user_id)
        return
    
    quiz_id = user_quizzes[user_id]
    quiz = (pending_quizzes.get(quiz_id) or 
            approved_quizzes.get(quiz_id) or 
            rejected_quizzes.get(quiz_id))
    
    if quiz and quiz.status == 'pending':
        survey_type = quiz.survey_type
        
        # Удаляем старую анкету
        for d in [pending_quizzes, approved_quizzes, rejected_quizzes, all_quizzes]:
            d.pop(quiz_id, None)
        del user_quizzes[user_id]
        
        # Начинаем новую
        start_survey(user_id, survey_type)

def delete_quiz(user_id):
    if user_id in user_quizzes:
        quiz_id = user_quizzes[user_id]
        for d in [pending_quizzes, approved_quizzes, rejected_quizzes, all_quizzes]:
            d.pop(quiz_id, None)
        del user_quizzes[user_id]
        bot.send_message(user_id, "✅ Анкета удалена")
    
    show_user_menu(user_id)

def show_about_us(user_id):
    about_text = (
        "❗Кто такие Nefor studios?\n\n"
        "- онлайн студия с многолетним опытом работы;\n"
        "- дружная команда профессионалов;\n"
        "- мы помогаем нашим моделям иметь хороший заработок буквально с первых дней;\n"
        "- имеем уникальную систему благодаря которой для работы достаточно только мобильного телефона.\n\n"
        "❗Что нужно от тебя? \n\n"
        "- быть уникальной и яркой;\n"
        "- иметь желание получать хороший заработок сидя дома;\n"
        "- иметь мобильный телефон.\n\n"
        "❗️ты будешь занимать должность МОДЕЛИ❗️\n\n"
        "- В твои прямые обязанности входит ведение прямых трансляций (ты сама решаешь какого формата контент ты будешь создавать) \n\n"
        "❗️Удобный график\n\n"
        "- 5/2 (ты сама выбираешь в какие дни ты хочешь взять выходной);\n"
        "- смены по 6-7 часов (есть возможность работать утром, днём или ночь).\n\n"
        "❗️Ты переживаешь что у тебя нет опыта?\n\n"
        "- Наша команда состоит из опытных кураторов и операторов - мы обучим тебя всему.\n\n"
        "❗️Ты будешь работать с оператором\n"
        "- в его обязанности входит постановка шоу, модерация чатов и общение с пользователями. Он поможет заработать тебе как можно больше.\n\n"
        "❗️Переживаешь что у тебя нет оборудования?\n\n"
        "- для работы с нами тебе достаточно всего мобильного телефона. \n\n"
        "❗️Заработная плата  \n\n"
        "- уже с первого дня ты будешь зарабатывать примерно 10.000 рублей за смену;\n"
        "- первые 3 дня зп выплачивается каждый день;\n"
        "- в дальнейшем раз в неделю;\n"
        "- выплаты в крипте;\n"
        "- от общего чека ты получаешь 50%.\n\n"
        "❗️Так же у нас есть реферальная программа \n\n"
        "- Если у тебя есть подруги которые тоже хотят попробовать себя в этой сфере, ты можешь получить 10.000 за приведение каждой новой модели в нашу команду.\n\n"
        "Присоединяйся в нашу дружную команду и имей высокий заработок с первого дня🥰"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="back_to_user_menu"))
    bot.send_message(user_id, about_text, reply_markup=markup)

# ================== АДМИНСКАЯ ЧАСТЬ ==================

def show_admin_menu(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    pending = len(pending_quizzes)
    markup.add(
        types.InlineKeyboardButton(f"📋 Ожидают проверки ({pending})" if pending else "📋 Ожидают проверки", 
                                  callback_data="pending"),
        types.InlineKeyboardButton("✅ Принятые", callback_data="approved"),
        types.InlineKeyboardButton("❌ Отклонённые", callback_data="rejected"),
        types.InlineKeyboardButton("📋 Все анкеты", callback_data="all_quizzes")
    )
    bot.send_message(user_id, "🔐 Админ-панель\nВыберите раздел:", reply_markup=markup)

def notify_admins_about_survey(quiz_id, user_id, username, survey_type, answers, photos, questions):
    if not admin_ids:
        return

    type_name = "Оператор" if survey_type == SURVEY_OPERATOR else "Модель"
    
    # Формируем кликабельную ссылку
    if username:
        user_display = f"@{username}"
    else:
        user_display = f"<a href='tg://user?id={user_id}'>{user_id}</a>"

    # Формируем текст ответов
    answers_text = ""
    for i, (q, a) in enumerate(zip(questions, answers)):
        answers_text += f"{q}\n{a}\n\n"
    
    for admin_id in admin_ids.values():
        try:
            # Отправляем текстовую часть
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
            
            # Если есть фото, отправляем их отдельно
            if photos:
                bot.send_message(admin_id, f"📸 Фотографии ({len(photos)} шт.):")
                for photo_id in photos:
                    bot.send_photo(admin_id, photo_id)
                    
        except Exception as e:
            print(f"Ошибка отправки админу: {e}")

# ================== ОБРАБОТЧИКИ ==================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    data = call.data

    # Админские кнопки
    if call.message.chat.username in ADMIN_USERNAMES:
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
        elif data.startswith("review_"):
            show_quiz_details(user_id, data[7:])
        elif data.startswith("manage_"):
            show_quiz_details(user_id, data[7:])
        elif data.startswith("approve_"):
            approve_quiz(user_id, data[8:])
        elif data.startswith("reject_"):
            reject_quiz(user_id, data[7:])
        elif data.startswith("change_to_pending_"):
            change_to_pending(user_id, data[18:])
        elif data.startswith("delete_quiz_admin_"):
            confirm_admin_delete(user_id, data[18:])
        elif data.startswith("confirm_admin_delete_"):
            admin_delete_quiz(user_id, data[21:])
    
    # Пользовательские кнопки
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
        elif data == "edit_survey":
            if user_id in user_survey_data:
                start_survey(user_id, user_survey_data[user_id]['type'])
        elif data == "confirm_final":
            confirm_final(user_id)

    try:
        bot.delete_message(user_id, call.message.message_id)
    except:
        pass
    bot.answer_callback_query(call.id)

# ИСПРАВЛЕНО: главный обработчик сообщений
@bot.message_handler(func=lambda message: True)
def message_handler(message):
    user_id = message.chat.id

    # Пропускаем админов
    if message.chat.username in ADMIN_USERNAMES:
        return

    # ИСПРАВЛЕНО: проверяем только текстовые сообщения для ответов
    if (user_id in user_survey_data and 
        message.content_type == 'text' and 
        user_survey_data[user_id].get('stage') == 'waiting_answers'):
        
        process_survey_answers(user_id, message.text)
    else:
        # Если не в режиме опроса, показываем меню
        if user_id not in user_survey_data:
            show_user_menu(user_id)

# ================== АДМИНСКИЕ ФУНКЦИИ ==================

def show_pending_quizzes(user_id):
    if not pending_quizzes:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
        bot.send_message(user_id, "📭 Нет анкет", reply_markup=markup)
        return
    
    text = f"📋 Ожидают проверки ({len(pending_quizzes)})\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    for qid, quiz in pending_quizzes.items():
        link = format_user_link(quiz.user_id, quiz.username)
        text += f"• {qid} - {link}\n"
        markup.add(types.InlineKeyboardButton(f"📋 {qid}", callback_data=f"review_{qid}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
    bot.send_message(user_id, text, reply_markup=markup, parse_mode='HTML')

def show_approved_quizzes(user_id):
    approved = {k: v for k, v in approved_quizzes.items()}
    if not approved:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
        bot.send_message(user_id, "📭 Нет принятых анкет", reply_markup=markup)
        return
    
    text = f"✅ Принятые ({len(approved)})\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    for qid, quiz in approved.items():
        link = format_user_link(quiz.user_id, quiz.username)
        text += f"• {qid} - {link}\n"
        markup.add(types.InlineKeyboardButton(f"📋 {qid}", callback_data=f"manage_{qid}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
    bot.send_message(user_id, text, reply_markup=markup, parse_mode='HTML')

def show_rejected_quizzes(user_id):
    rejected = {k: v for k, v in rejected_quizzes.items()}
    if not rejected:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
        bot.send_message(user_id, "📭 Нет отклонённых анкет", reply_markup=markup)
        return
    
    text = f"❌ Отклонённые ({len(rejected)})\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    for qid, quiz in rejected.items():
        link = format_user_link(quiz.user_id, quiz.username)
        text += f"• {qid} - {link}\n"
        markup.add(types.InlineKeyboardButton(f"📋 {qid}", callback_data=f"manage_{qid}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
    bot.send_message(user_id, text, reply_markup=markup, parse_mode='HTML')

def show_all_quizzes(user_id):
    all_q = list(pending_quizzes.values()) + list(approved_quizzes.values()) + list(rejected_quizzes.values())
    if not all_q:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
        bot.send_message(user_id, "📭 Нет анкет", reply_markup=markup)
        return
    
    text = f"📋 Все анкеты ({len(all_q)})\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    for quiz in sorted(all_q, key=lambda x: x.timestamp, reverse=True)[:20]:
        emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌"}[quiz.status]
        link = format_user_link(quiz.user_id, quiz.username)
        text += f"• {emoji} {quiz.quiz_id} - {link}\n"
        markup.add(types.InlineKeyboardButton(f"{emoji} {quiz.quiz_id}", callback_data=f"manage_{quiz.quiz_id}"))
    markup.add(types.InlineKeyboardButton("◀ Назад", callback_data="main_menu"))
    bot.send_message(user_id, text, reply_markup=markup, parse_mode='HTML')

def show_quiz_details(user_id, quiz_id):
    quiz = (pending_quizzes.get(quiz_id) or approved_quizzes.get(quiz_id) or rejected_quizzes.get(quiz_id))
    if not quiz:
        bot.send_message(user_id, "❌ Анкета не найдена")
        return
    
    link = format_user_link(quiz.user_id, quiz.username)
    status_emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌"}[quiz.status]
    
    text = f"{status_emoji} Анкета {quiz_id}\n\n👤 {link}\n📌 {quiz.status}\n"
    text += f"🕐 {time.strftime('%H:%M %d.%m.%Y', time.localtime(quiz.timestamp))}\n\n"
    
    # Текстовые ответы
    for i, answer in enumerate(quiz.answers):
        text += f"{i+1}. {answer}\n"
    
    bot.send_message(user_id, text, parse_mode='HTML')
    
    # Отправляем фото если есть
    if quiz.photos:
        bot.send_message(user_id, f"📸 Фотографии ({len(quiz.photos)} шт.):")
        for photo_id in quiz.photos:
            bot.send_photo(user_id, photo_id)

    markup = types.InlineKeyboardMarkup(row_width=2)
    if quiz.status == 'pending':
        markup.add(
            types.InlineKeyboardButton("✅ Принять", callback_data=f"approve_{quiz_id}"),
            types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{quiz_id}")
        )
    else:
        markup.add(types.InlineKeyboardButton("⏳ Вернуть", callback_data=f"change_to_pending_{quiz_id}"))
    markup.add(
        types.InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_quiz_admin_{quiz_id}"),
        types.InlineKeyboardButton("◀ Назад", callback_data="all_quizzes")
    )
    bot.send_message(user_id, "Выберите действие:", reply_markup=markup)

def approve_quiz(admin_id, quiz_id):
    quiz = pending_quizzes.pop(quiz_id, None) or rejected_quizzes.pop(quiz_id, None)
    if not quiz:
        bot.send_message(admin_id, "❌ Анкета не найдена")
        return
    
    quiz.status = 'approved'
    quiz.reviewed_by = admin_id
    quiz.reviewed_at = time.time()
    approved_quizzes[quiz_id] = quiz
    bot.send_message(admin_id, f"✅ Анкета {quiz_id} принята")
    show_all_quizzes(admin_id)

def reject_quiz(admin_id, quiz_id):
    quiz = pending_quizzes.pop(quiz_id, None) or approved_quizzes.pop(quiz_id, None)
    if not quiz:
        bot.send_message(admin_id, "❌ Анкета не найдена")
        return
    
    quiz.status = 'rejected'
    quiz.reviewed_by = admin_id
    quiz.reviewed_at = time.time()
    rejected_quizzes[quiz_id] = quiz
    
    bot.send_message(admin_id, f"❌ Анкета {quiz_id} отклонена")
    show_all_quizzes(admin_id)

def change_to_pending(admin_id, quiz_id):
    quiz = approved_quizzes.pop(quiz_id, None) or rejected_quizzes.pop(quiz_id, None)
    if not quiz:
        bot.send_message(admin_id, "❌ Анкета не найдена")
        return
    
    quiz.status = 'pending'
    quiz.reviewed_by = None
    quiz.reviewed_at = None
    pending_quizzes[quiz_id] = quiz
    bot.send_message(admin_id, f"⏳ Анкета {quiz_id} возвращена")
    show_all_quizzes(admin_id)

def confirm_admin_delete(user_id, quiz_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Да", callback_data=f"confirm_admin_delete_{quiz_id}"),
        types.InlineKeyboardButton("❌ Нет", callback_data=f"manage_{quiz_id}")
    )
    bot.send_message(user_id, f"🗑 Удалить анкету {quiz_id}?", reply_markup=markup)

def admin_delete_quiz(admin_id, quiz_id):
    quiz = (pending_quizzes.pop(quiz_id, None) or
            approved_quizzes.pop(quiz_id, None) or
            rejected_quizzes.pop(quiz_id, None))
    if quiz and quiz.user_id in user_quizzes:
        del user_quizzes[quiz.user_id]
    bot.send_message(admin_id, f"✅ Анкета {quiz_id} удалена")
    show_all_quizzes(admin_id)

@bot.message_handler(commands=['status'])
def status_command(message):
    if message.chat.username in ADMIN_USERNAMES:
        text = f"📊 Статус системы:\n\n"
        text += f"👥 Админов в сети: {len(admin_ids)}/{len(ADMIN_USERNAMES)}\n"
        text += f"📋 Ожидает проверки: {len(pending_quizzes)}\n"
        text += f"✅ Принято: {len(approved_quizzes)}\n"
        text += f"❌ Отклонено: {len(rejected_quizzes)}"
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, "❌ Эта команда только для администраторов")

# ================== ЗАПУСК ==================

if __name__ == '__main__':
    print("="*50)
    print("🚀 Бот NEFOR STUDIO запущен!")
    print("👥 Администраторы:", ', '.join(ADMIN_USERNAMES))
    print("📸 Поддержка фотографий включена!")
    print("="*50)
    bot.infinity_polling()
