from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
from database import db
import config
from config import SECTIONS_CONFIG
from scheduler import scheduler
from datetime import time
from database_couples import DatabaseCouples  # ← НОВАЯ БАЗА ДЛЯ ПАР
# Хранилище для задач отправки рекомендаций



# Создаем экземпляр базы для пар
db_couples = DatabaseCouples()

# Хранилище для задач
recommendation_jobs = {}
movie_jobs = {}
book_jobs = {}
question_jobs = {}

async def stop_recommendation_job(user_id: int, application):
    """Останавливает задачу отправки рекомендаций"""
    if user_id in recommendation_jobs:
        recommendation_jobs[user_id].schedule_removal()
        del recommendation_jobs[user_id]

async def stop_movie_job(user_id: int, application):
    """Останавливает задачу отправки фильмов"""
    if user_id in movie_jobs:
        movie_jobs[user_id].schedule_removal()
        del movie_jobs[user_id]

async def stop_question_job(user_id: int, application):
    """Останавливает задачу отправки фильмов"""
    if user_id in question_jobs:
        question_jobs[user_id].schedule_removal()
        del question_jobs[user_id]

async def stop_book_job(user_id: int, application):
    """Останавливает задачу отправки книг"""
    if user_id in book_jobs:
        book_jobs[user_id].schedule_removal()
        del book_jobs[user_id]

async def show_gender_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает выбор пола"""
    user_id = update.effective_user.id
    
    # Проверяем, не выбрал ли уже пользователь пол
    current_gender = db.get_gender(user_id)
    if current_gender:
        print(f"🔍 Пользователь {user_id} уже выбрал пол: {current_gender}")
        # Если пол уже выбран, переходим к главному меню
        await back_to_main(update, context)
        return
    
    text = "👫 *Выберите ваш пол*\n\n"
    text += "Это поможет нам подобрать наиболее подходящие рекомендации."
    
    keyboard = [
        [InlineKeyboardButton("👨 Мужской", callback_data="gender_male")],
        [InlineKeyboardButton("👩 Женский", callback_data="gender_female")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')


async def show_gender_selection1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает выбор пола"""
    user_id = update.effective_user.id
    
    # Проверяем, не выбрал ли уже пользователь пол
    current_gender = db.get_gender(user_id)
    if current_gender:
        print(f"🔍 Пользователь {user_id} уже выбрал пол: {current_gender}")
        # Если пол уже выбран, переходим к главному меню
        await back_to_main(update, context)
        return
    
    text = "👫 *Выберите ваш пол*\n\n"
    text += "Это поможет нам подобрать наиболее подходящие рекомендации."
    
    keyboard = [
        [InlineKeyboardButton("👨 Мужской", callback_data="g1ender_male1")],
        [InlineKeyboardButton("👩 Женский", callback_data="g1ender_female")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')


async def handle_gender_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор пола"""
    if not update.callback_query:
        return
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    gender = query.data.replace("gender_", "")
    username = update.effective_user.username
    user = db.get_user(user_id)
    db.create_user(user_id, username)
    print(f"🔍 Пользователь {user_id} выбрал пол: {gender}")
    
    # Сохраняем пол пользователя
    result = db.update_gender(user_id, gender)
    print(f"🔍 Результат сохранения пола: {result.modified_count if result else 'None'}")
    
    # Проверяем, сохранился ли пол
    current_gender = db.get_gender(user_id)
    print(f"🔍 Текущий пол пользователя: {current_gender}")
    
    # Начинаем опросник
    from survey_handlers import survey_manager
    await back_to_main(update, context)

# rec_handlers.py

async def handle_gender_selection1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор пола"""
    if not update.callback_query:
        return
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    gender = query.data.replace("g1ender_", "")
    username = update.effective_user.username
    user = db.get_user(user_id)
    db.create_user(user_id, username)
    print(f"🔍 Пользователь {user_id} выбрал пол: {gender}")
    
    # Сохраняем пол пользователя
    result = db.update_gender(user_id, gender)
    print(f"🔍 Результат сохранения пола: {result.modified_count if result else 'None'}")
    
    # Проверяем, сохранился ли пол
    current_gender = db.get_gender(user_id)
    print(f"🔍 Текущий пол пользователя: {current_gender}")

    if update.callback_query:
        await update.callback_query.edit_message_text(text="вы успешно выбрали пол, подтвердите участие в паре", parse_mode='Markdown')


# rec_handlers.py


async def show_recommendations_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню рекомендаций С ПРОВЕРКОЙ ПАРТНЕРА"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
    else:
        user_id = update.effective_user.id
    
    # 🔥 ИСПРАВЛЕНИЕ: используем db_couples вместо db
    partner_id = db_couples.get_partner_id(user_id)  # ← ТУТ ИСПРАВЛЕНИЕ
    
    if partner_id:
        partner_completed = db_couples.has_completed_survey(partner_id)  # ← И ЗДЕСЬ
        print(partner_completed)
        print("partner_completed")
        if not partner_completed:
            partner_info = db_couples.get_user_info(partner_id)  # ← И ЗДЕСЬ
            partner_name = partner_info.get('first_name', 'Ваш партнер') if partner_info else 'Ваш партнер'
            
            text = f"👫 *Ожидание партнера*\n\n"
            text += f"⏳ {partner_name} еще не завершил(а) опросник.\n\n"
            text += "Для получения парных рекомендаций необходимо, чтобы оба партнера прошли диагностику."
            
            keyboard = [
                [InlineKeyboardButton("👫 Проверить статус пары", callback_data="start_couple_menu")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            return
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
    else:
        user_id = update.effective_user.id
    
    # Проверяем, прошел ли пользователь все опросники
    if not db.has_completed_survey(user_id):
        text = "📝 *Сначала пройдите опросники*\n\n"
        text += "Для получения персонализированных рекомендаций необходимо пройти опросники по ключевым разделам отношений."
        
        keyboard = [
            [InlineKeyboardButton("📋 Пройти опросники", callback_data="start_survey")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        return
    
    # Проверяем подписку
    if not db.is_subscription_active(user_id):
        await show_premium_offer(update, context)
        return
    
    # Получаем статистику по разделам
    priority_section = db.get_section_priority(user_id)
    total_recommendations = db.get_recommendation_count(user_id)
    remaining_recommendations = db.get_remaining_recommendations_count(user_id)
    
    # Статистика по разделам
    remaining_comm = db.get_remaining_recommendations_count_by_section(user_id, 'communication')
    remaining_intimacy = db.get_remaining_recommendations_count_by_section(user_id, 'intimacy')
    
    text = "💫 *Ваши персонализированные рекомендации*\n\n"
 ##   text += f"📊 Всего рекомендаций: {total_recommendations}\n"
 ##   text += f"🆕 Новых рекомендаций: {remaining_recommendations}\n\n"
    text += f"💬 Рекомендаций по общению: {remaining_comm}\n"
    text += f"💕 Рекомендаций по близости: {remaining_intimacy}\n\n"
    
    if priority_section == 'communication':
        text += "💡 *Приоритет:* Рекомендации по улучшению общения\n\n"
    else:
        text += "💡 *Приоритет:* Рекомендации по укреплению близости\n\n"
    
    text += "🎯 Рекомендации будут приходить по одной каждые 10 секунд.\n"
    text += "Сначала будут показаны рекомендации из приоритетного раздела."
    
    keyboard = []
    
    if remaining_intimacy > 0:
        keyboard.append([InlineKeyboardButton("📖 Начать чтение рекомендаций", callback_data="start_reading_recommendations")])
    
    if total_recommendations > 0 and remaining_recommendations == 0:
        text += "\n\n✅ Вы уже прочитали все рекомендации. Пройдите опросники заново для получения новых."
        keyboard.append([InlineKeyboardButton("📋 Пройти опросники заново", callback_data="restart_survey")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
async def stop_recommendation_job(user_id: int, application):
    """Останавливает задачу отправки рекомендаций"""
    if user_id in recommendation_jobs:
        recommendation_jobs[user_id].schedule_removal()
        del recommendation_jobs[user_id]

async def show_premium_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает предложение о подписке"""
    if not update.callback_query:
        return
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Получаем примеры рекомендаций которые будут доступны
    recommendations = db.get_personalized_recommendations(user_id)
    preview_count = min(3, len(recommendations))
    
    text = "💎 *Персонализированные рекомендации*\n\n"
    text += "📊 На основе ваших ответов мы подготовили рекомендации:\n\n"
    
    if recommendations:
        for i, rec in enumerate(recommendations[:preview_count], 1):
            text += f"• *{rec['title']}* - {rec['description']}\n"
        
        if len(recommendations) > preview_count:
            text += f"• *...и еще {len(recommendations) - preview_count} рекомендаций*\n\n"
    else:
        text += "🎯 Рекомендации по улучшению общения, разрешению конфликтов и укреплению отношений\n\n"
    
    text += f"💰 Подписка: {config.SUBSCRIPTION_PRICE} руб. в месяц"
    
    keyboard = [
        [InlineKeyboardButton("💳 Оформить подписку", callback_data="buy_subscription")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# rec_handlers.py
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возвращает в главное меню С ПРОВЕРКОЙ ПАРЫ"""
    user_id = update.effective_user.id
    current_gender = db.get_gender(user_id)
    
    if not current_gender:
        print(f"🔍 Пользователь {user_id} еще не выбрал пол")
        await show_gender_selection(update, context)
        return
    
    # 🔥 ПРОВЕРКА ПАРЫ - ПРОСТО И ЭФФЕКТИВНО
    from database_couples import DatabaseCouples
    db_couples = DatabaseCouples()
    couple_completed = db_couples.has_both_partners_completed_survey(user_id)
    
    text = "💑 *Бот по семейным отношениям*\n\n"
    
    if db.has_completed_survey(user_id):
        if db.is_subscription_active(user_id):
            current_schedule = scheduler.get_user_schedule(user_id)
            
            text += f"✅ Подписка активна\n"
            if current_schedule:
                text += f"⏰ Расписание: "
                text += ", ".join([t.strftime('%H:%M') for t in current_schedule]) + "\n\n"
            else:
                text += "⏰ Расписание не настроено\n\n"
            
            # 🔥 ПРОВЕРЯЕМ: ЕСЛИ В ПАРЕ И ПАРА НЕ ЗАВЕРШИЛА - БЛОКИРУЕМ РЕКОМЕНДАЦИИ
            partner_id = db_couples.get_partner_id(user_id)
            if partner_id and not couple_completed:
                partner_info = db_couples.get_user_info(partner_id)
                partner_name = partner_info.get('first_name', 'Партнер') if partner_info else 'Партнер'
                
                text += f"👫 *Ожидание партнера*\n"
                text += f"⏳ {partner_name} еще не завершил(а) опросник\n\n"
                
                keyboard = [
                    [InlineKeyboardButton("👫 Статус пары", callback_data="couple_profile")],
                    [InlineKeyboardButton("⏰ Настроить расписание", callback_data="schedule_settings")],
                    [InlineKeyboardButton("👤 Профиль", callback_data="my_profile")],
                    [InlineKeyboardButton("🎬 Рекомендация фильма", callback_data="request_movie")],
                    [InlineKeyboardButton("📚 Рекомендация книги", callback_data="request_book")]
                ]
            else:
                # 🔥 ПАРА ЗАВЕРШИЛА ИЛИ НЕТ ПАРЫ - показываем рекомендации
                keyboard = [
                    [InlineKeyboardButton("💫 Мои рекомендации", callback_data="show_recommendations")],
                    [InlineKeyboardButton("⏰ Настроить расписание", callback_data="schedule_settings")],
                    [InlineKeyboardButton("👤 Профиль", callback_data="my_profile")],
                    [InlineKeyboardButton("🎬 Рекомендация фильма", callback_data="request_movie")],
                    [InlineKeyboardButton("📚 Рекомендация книги", callback_data="request_book")]
                ]
            
            if db.is_female(user_id):
                # Аналогичная логика для женского меню
                keyboard = [k for k in keyboard if k[0].callback_data != "🎬 Рекомендация фильма"]
                keyboard = [k for k in keyboard if k[0].callback_data != "📚 Рекомендация книги"]
                keyboard.append([InlineKeyboardButton("🔥 Либидо", callback_data="show_libido_menu")])

        else:
            text += "📊 Опросник пройден\n"
            
            # 🔥 ПРОВЕРЯЕМ ПАРУ
            partner_id = db_couples.get_partner_id(user_id)
            if partner_id and not couple_completed:
                partner_info = db_couples.get_user_info(partner_id)
                partner_name = partner_info.get('first_name', 'Партнер') if partner_info else 'Партнер'
                
                text += f"⏳ Ожидаем завершения опроса {partner_name}\n\n"
                keyboard = [
                    [InlineKeyboardButton("👫 Статус пары", callback_data="couple_profile")],
                    [InlineKeyboardButton("👤 Профиль", callback_data="my_profile")]
                ]
            else:
                text += "💎 Персональные рекомендации готовы\n\n"
                keyboard = [
                    [InlineKeyboardButton("💳 Получить рекомендации", callback_data="get_recommendations")],
                    [InlineKeyboardButton("👤 Профиль", callback_data="my_profile")]
                ]
    else:
        text += "🎯 Персонализированные рекомендации по вашим отношениям\n\n"
        text += "Для начала пройдите небольшой опросник:"
        keyboard = [
         #   [InlineKeyboardButton("📋 Начать опросник", callback_data="start_survey")],
            [InlineKeyboardButton("👫 Парный опросник", callback_data="start_couple_menu")],
            [InlineKeyboardButton("👤 Профиль", callback_data="my_profile")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')


async def show_my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает профиль пользователя с обработкой ошибок"""
    if not update.callback_query:
        return
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user = db.get_user(user_id)
    
    # 🔧 ИСПРАВЛЕНИЕ: Проверяем, что пользователь существует
    if not user:
        # Создаем пользователя, если его нет
        username = query.from_user.username or "Не указано"
        db.create_user(user_id, username)
        user = db.get_user(user_id)
    
    # 🔧 ИСПРАВЛЕНИЕ: Безопасное получение username
    username = user.get('username') if user else "Не указано"
    if not username or username == "None":
        username = "Не указано"
    
    text = f"👤 *Ваш профиль*\n\n"
    text += f"📛 Имя: @{username}\n"
    text += f"🆔 ID: {user_id}\n"
    
    # 🔧 ИСПРАВЛЕНИЕ: Безопасное получение пола
    gender = user.get('gender', 'Не указан') if user else 'Не указан'
    gender_text = "👨 Мужской" if gender == "male" else "👩 Женский" if gender == "female" else "❓ Не указан"
    text += f"🚻 Пол: {gender_text}\n"
    
    # 🔧 ИСПРАВЛЕНИЕ: Безопасное получение даты регистрации
    created_at = user.get('created_at') if user else None
    if created_at:
        text += f"📅 Регистрация: {created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
    else:
        text += f"📅 Регистрация: Неизвестно\n\n"
    
    # 🔧 ИСПРАВЛЕНИЕ: Безопасная проверка опросника
    survey_completed = user.get('survey_completed', False) if user else False
    if survey_completed:
        text += "✅ Опросник пройден\n"
        survey_date = user.get('survey_completed_at')
        if survey_date:
            text += f"📅 Дата прохождения: {survey_date.strftime('%d.%m.%Y %H:%M')}\n\n"
        else:
            text += f"📅 Дата прохождения: Неизвестно\n\n"
    else:
        text += "❌ Опросник не пройден\n\n"
    
    # 🔧 ИСПРАВЛЕНИЕ: Безопасная проверка подписки
    subscription_active = db.is_subscription_active(user_id)
    if subscription_active:
        time_left = db.get_subscription_time_left(user_id)
        text += f"💎 Подписка активна\n"
        text += f"⏰ Осталось: {time_left}\n"
        
        
        # 🔧 ИСПРАВЛЕНИЕ: Безопасная проверка раздела либидо
        try:
            if db.is_female(user_id):
                remaining_libido = db.get_remaining_libido_content_count(user_id)
                print("внутри libido!!")
                total_libido = len(db.get_libido_content())
                text +=db.get_libido_content()
                print(db.get_libido_content())
                print("total_libido")
                print(total_libido)
                text += f"🌺 Материалов либидо изучено: {total_libido - remaining_libido}/{total_libido}"
        except Exception as e:
            text += f"🌺 Либидо: Ошибка загрузки"
    else:
        text += "🔒 Подписка не активна\n"
        text += "💡 Пройдите опросник и оформите подписку для доступа к рекомендациям"
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')


async def send_single_recommendation_old(context: CallbackContext):
    """Отправляет одну рекомендацию с учетом приоритета 8 разделов"""
    job = context.job
    user_id = job.data['user_id']
    chat_id = job.data['chat_id']
    
    # Проверяем активна ли подписка
    if not db.is_subscription_active(user_id):
        await stop_recommendation_job(user_id, context.application)
        keyboard = [
        [InlineKeyboardButton("💳 Оформить подписку", callback_data="buy_subscription")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            reply_markup=reply_markup,
            chat_id=chat_id,
            text="❌ *Подписка истекла*\n\nДля продолжения чтения рекомендаций необходимо продлить подписку.",
            parse_mode='Markdown'
        )
        return
    
    # Получаем приоритетные разделы пользователя
    priority_sections = db_couples.get_couple_priority_sections(user_id)
    
    # Ищем рекомендации в порядке приоритета
    recommendation = None
    for section_id in priority_sections:
        recommendation = db.get_next_section_recommendation_by_category(user_id, section_id)
        if recommendation:
            break
    
    # Если в приоритетных разделах нет рекомендаций, ищем в других
    if not recommendation:
        all_sections = list(SECTIONS_CONFIG.keys())
        remaining_sections = [s for s in all_sections if s not in priority_sections]
        
        for section_id in remaining_sections:
            recommendation = db.get_next_section_recommendation_by_category(user_id, section_id)
            if recommendation:
                break
    
    # Если все рекомендации закончились
    if not recommendation:
        await stop_recommendation_job(user_id, context.application)
        await context.bot.send_message(
            chat_id=chat_id,
            text="🎉 *Все рекомендации прочитаны!*\n\n"
                 "Вы ознакомились со всеми персонализированными рекомендациями. "
                 "Для получения новых рекомендаций пройдите опросник заново.",
            parse_mode='Markdown'
        )
        return
    
    # Форматируем рекомендацию
    section_config = SECTIONS_CONFIG[recommendation.get('section', 'communication')]
    
    text = f"{section_config['name']} *Рекомендация*\n\n"
    text += f"**{recommendation['title']}**\n"
    text += f"🏷️ {recommendation['category']}\n\n"
    text += f"📝 *Описание:* {recommendation['description']}\n\n"
    text += f"**Содержание:**\n{recommendation['content']}\n\n"
    
    # Показываем прогресс по разделам
    remaining_by_section = {}
    for section_id in SECTIONS_CONFIG.keys():
        remaining = db.get_remaining_recommendations_count_by_section(user_id, section_id)
        if remaining > 0:
            remaining_by_section[section_id] = remaining
    
    if remaining_by_section:
        text += "📊 *Осталось рекомендаций по разделам:*\n"
        for section_id, count in list(remaining_by_section.items())[:4]:  # Показываем первые 4
            section_name = SECTIONS_CONFIG[section_id]['name']
            text += f"{section_name}: {count}\n"
    
    text += "\n⏰ Следующая рекомендация через 10 секунд..."
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode='Markdown'
    )

async def send_single_recommendation(context: CallbackContext):
    """Отправляет одну рекомендацию с учетом приоритета 8 разделов (работает со старой и новой структурой)"""
    job = context.job
    user_id = job.data['user_id']
    chat_id = job.data['chat_id']
    
    # Проверяем активна ли подписка
    if not db.is_subscription_active(user_id):
        await stop_recommendation_job(user_id, context.application)
        keyboard = [
        [InlineKeyboardButton("💳 Оформить подписку", callback_data="buy_subscription")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            reply_markup=reply_markup,
            chat_id=chat_id,
            text="❌ *Подписка истекла*\n\nДля продолжения чтения рекомендаций необходимо продлить подписку.",
            parse_mode='Markdown'
        )
        return
    
    # Получаем приоритетные разделы пользователя
    priority_sections = db_couples.get_couple_priority_sections(user_id)
    
    # Сначала пробуем получить рекомендацию из НОВОЙ структуры (activities)
    recommendation = None
    used_new_structure = True
    
    # Ищем в приоритетных разделах (новая структура)
    # for section_id in priority_sections:
    #     if hasattr(db, 'get_next_section_recommendation_by_category'):
    #         recommendation = db.get_next_section_recommendation_by_category(user_id, section_id)
    #         if recommendation:
    #             break


    # # Ищем рекомендации в порядке приоритета
    # recommendation = None
    # for section_id in priority_sections:
    #     recommendation = db.get_next_section_recommendation_by_category(user_id, section_id)
    #     if recommendation:
    #         break
    
    # # Если в приоритетных разделах нет рекомендаций, ищем в других
    # if not recommendation:
    #     all_sections = list(SECTIONS_CONFIG.keys())
    #     remaining_sections = [s for s in all_sections if s not in priority_sections]
        
    #     for section_id in remaining_sections:
    #         recommendation = db.get_next_section_recommendation_by_category(user_id, section_id)
    #         if recommendation:
    #             break
    
    recommendation = None
    for section_id in priority_sections:
        recommendation = db.get_next_recommendation_from_any_collection(user_id, section_id)
        if recommendation:
            break

# Если в приоритетных разделах нет рекомендаций, ищем в других
    if not recommendation:
        all_sections = list(SECTIONS_CONFIG.keys())
        remaining_sections = [s for s in all_sections if s not in priority_sections]
        
        for section_id in remaining_sections:
            recommendation = db.get_next_recommendation_from_any_collection(user_id, section_id)
            if recommendation:
                break
    
    # Если в приоритетных разделах нет рекомендаций в новой структуре, ищем в других
    # if not recommendation and hasattr(db, 'get_next_section_recommendation_by_category'):
    #     all_sections = list(SECTIONS_CONFIG.keys())
    #     remaining_sections = [s for s in all_sections if s not in priority_sections]
        
    #     for section_id in remaining_sections:
    #         recommendation = db.get_next_section_recommendation_by_category(user_id, section_id)
    #         if recommendation:
    #             break
    
    # Если в новой структуре не нашли, пробуем СТАРУЮ структуру
    # if not recommendation and hasattr(db, 'get_next_recommendation_by_section'):
    #     used_new_structure = False
        
    #     # Ищем в приоритетных разделах (старая структура)
    #     for section_id in priority_sections:
    #         recommendation = db.get_next_recommendation_by_section(user_id, section_id)
    #         if recommendation:
    #             break
        
    #     # Если в приоритетных разделах нет рекомендаций, ищем в других
    #     if not recommendation:
    #         all_sections = list(SECTIONS_CONFIG.keys())
    #         remaining_sections = [s for s in all_sections if s not in priority_sections]
            
    #         for section_id in remaining_sections:
    #             recommendation = db.get_next_recommendation_by_section(user_id, section_id)
    #             if recommendation:
    #                 break
    
    # Если все рекомендации закончились
    if not recommendation:
        await stop_recommendation_job(user_id, context.application)
        await context.bot.send_message(
            chat_id=chat_id,
            text="🎉 *Все рекомендации прочитаны!*\n\n"
                 "Вы ознакомились со всеми персонализированными рекомендациями. "
                 "Для получения новых рекомендаций пройдите опросник заново.",
            parse_mode='Markdown'
        )
        return
    
    # Форматируем рекомендацию в зависимости от структуры
    collection_type = recommendation.get('collection', 'cinema')

    if collection_type == 'activities':
        # Форматирование для activities (уже есть)
        section_config = SECTIONS_CONFIG[recommendation.get('section', 'communication')]
        text = f"{section_config['name']} *Рекомендация*\n\n"
        text += f"**{recommendation['title']}**\n"
        if recommendation.get('goal'):
            text += f"🎯 *Цель:* {recommendation['goal']}\n\n"
        
        # Форматируем шаги
        steps = recommendation.get('steps', [])
        if steps:
            text += "**Шаги выполнения:**\n"
            for i, step in enumerate(steps, 1):
                text += f"{i}. {step}\n"
            text += "\n"

    elif collection_type == 'literature':
        section_config = SECTIONS_CONFIG[recommendation.get('section', 'literature')]
        text = f"{section_config['name']} *Литература*\n\n"
        text += f"**{recommendation['title']}**\n"
        text += f"✍️ *Автор:* {recommendation.get('author', '')}\n\n"
        text += f"📖 *Описание:* {recommendation.get('description', '')}\n\n"
        
        benefits = recommendation.get('benefits', [])
        if benefits:
            text += "🌟 *Что вы получите:*\n"
            for benefit in benefits:
                text += f"• {benefit}\n"
            text += "\n"

    elif collection_type == 'cinema':
        section_config = SECTIONS_CONFIG[recommendation.get('section', 'cinema')]
        text = f"{section_config['name']} *Кино*\n\n"
        
        # Берем первый фильм из массива (или можно выбрать случайный)
        if recommendation.get('movies') and len(recommendation['movies']) > 0:
            film = recommendation['movies'][0]
            text += f"🎬 **{film.get('title', '')}** ({film.get('year', '')})\n"
            text += f"🌍 *Страна:* {film.get('country', '')}\n\n"
            text += f"📝 *О чем фильм:* {film.get('about_what', '')}\n\n"
            text += f"🎯 *Что можно понять:* {film.get('what_to_learn', '')}\n\n"
        
        if recommendation.get('prescribe'):
            text += f"💡 *Тема подборки:* {recommendation['prescribe']}\n"
        if recommendation.get('as_result'):
            text += f"📈 *Результат:* {recommendation['as_result']}\n"

    elif collection_type == 'questions_new':
        section_config = SECTIONS_CONFIG[recommendation.get('section', 'questions_new')]
        text = f"{section_config['name']} *Вопросы для обсуждения*\n\n"
        
        text += f"❓ **{recommendation.get('text', '')}**\n\n"
        
        tags = recommendation.get('tags', [])
        if tags:
            text += "🏷️ *Темы:* " + ", ".join([f"#{tag}" for tag in tags]) + "\n"
        
        difficulty = recommendation.get('difficulty', '')
        if difficulty:
            text += f"📊 *Сложность:* {difficulty}\n"

    # Общая часть для всех типов (прогресс)
    if hasattr(db, 'get_remaining_section_recommendations_by_category'):
        remaining_by_section = {}
        for section_id in SECTIONS_CONFIG.keys():
            remaining = db.get_remaining_section_recommendations_by_category(user_id, section_id)
            if remaining > 0:
                remaining_by_section[section_id] = remaining
        
        if remaining_by_section:
            text += "\n📊 *Осталось рекомендаций по разделам:*\n"
            for section_id, count in list(remaining_by_section.items())[:4]:
                section_name = SECTIONS_CONFIG[section_id]['name']
                text += f"{section_name}: {count}\n"

    text += "\n⏰ Следующая рекомендация через 10 секунд..."
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode='Markdown'
    )
async def start_reading_recommendations(update: Update, context: ContextTypes):
    """Начинает пошаговую отправку рекомендаций"""
    if not update.callback_query:
        return
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    
    application = context.application
    if not application:
        await query.edit_message_text("❌ Ошибка: приложение не найдено")
        return
    
    await stop_recommendation_job(user_id, application)
    
    job = application.job_queue.run_repeating(
        send_single_recommendation,
        interval=10,
        first=0,
        data={'user_id': user_id, 'chat_id': chat_id, 'message_id': query.message.message_id}
    )
    job = application.job_queue.run_repeating(
        request_movie_recommendation,
        interval=15,
        first=2,
        data={'user_id': user_id, 'chat_id': chat_id, 'message_id': query.message.message_id}
    )
    
    recommendation_jobs[user_id] = job
    
    text = "📖 *Начинаем отправку рекомендаций*\n\n"
    text += "⏰ Рекомендации будут приходить каждые 10 секунд.\n"
    text += "💡 Внимательно читайте и применяйте на практике!\n\n"
    text += "🛑 Чтобы остановить отправку, нажмите кнопку ниже."
    
    keyboard = [
        [InlineKeyboardButton("⏸️ Остановить отправку", callback_data="stop_recommendations")],
        [InlineKeyboardButton("⬅️ В меню", callback_data="show_recommendations")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
async def stop_recommendations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Останавливает отправку рекомендаций"""
    if not update.callback_query:
        return
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    application = context.application
    
    if application:
        await stop_recommendation_job(user_id, application)
    
    text = "⏸️ *Отправка рекомендаций остановлена*\n\n"
    text += "Вы можете продолжить чтение в любое время."
    
    keyboard = [
        [InlineKeyboardButton("📖 Продолжить чтение", callback_data="start_reading_recommendations")],
        [InlineKeyboardButton("⬅️ В меню", callback_data="show_recommendations")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_schedule_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает настройки расписания"""
    if not update.callback_query:
        return
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Проверяем подписку
    if not db.is_subscription_active(user_id):
        await show_premium_offer(update, context)
        return
    
    current_schedule = scheduler.get_user_schedule(user_id)
    is_active = scheduler.is_user_scheduled(user_id)
    
    text = "⏰ *Настройка расписания рекомендаций*\n\n"
    
    if is_active and current_schedule:
        text += "✅ *Расписание активно:*\n"
        for i, t in enumerate(current_schedule, 1):
            text += f"{i}. {t.strftime('%H:%M')}\n"
        text += f"\nВсего рекомендаций в день: {len(current_schedule)}\n"
    else:
        text += "❌ *Расписание не настроено*\n"
    
    text += "\nВыберите вариант расписания:"
    
    keyboard = [
        [InlineKeyboardButton("🌅 Утро (9:00)", callback_data="schedule_morning")],
        [InlineKeyboardButton("🌞 День (14:00)", callback_data="schedule_afternoon")],
        [InlineKeyboardButton("🌙 Вечер (19:00)", callback_data="schedule_evening")],
       #[InlineKeyboardButton("📅 Комбинированное (9:00, 14:00, 19:00)", callback_data="schedule_combined")],
        [InlineKeyboardButton("⚙️ Настроить свое время", callback_data="schedule_custom")],
    ]
    
    if is_active:
        keyboard.append([InlineKeyboardButton("⏸️ Остановить расписание", callback_data="schedule_stop")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="show_recommendations")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_schedule_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор расписания"""
    if not update.callback_query:
        return
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    schedule_type = query.data
    
    # Определяем время по типу расписания
    schedule_times = {
        'schedule_morning': [time(9, 0)],
        'schedule_afternoon': [time(14, 0)],
        'schedule_evening': [time(19, 0)],
        'schedule_combined': [time(9, 0), time(14, 0), time(19, 0)]
    }
    
    if schedule_type in schedule_times:
        times = schedule_times[schedule_type]
        count = await scheduler.setup_user_schedule(user_id, chat_id, context.application, times)
        
        text = f"✅ *Расписание настроено!*\n\n"
        text += f"Рекомендации будут приходить:\n"
        for t in times:
            text += f"• {t.strftime('%H:%M')}\n"
        text += f"\nВсего рекомендаций в день: {count}"
        
    elif schedule_type == 'schedule_custom':
        await show_custom_schedule_settings(update, context)
        return
    elif schedule_type == 'schedule_stop':
        await scheduler.stop_user_schedule(user_id, context.application)
        text = "⏸️ *Расписание остановлено*\n\nРекомендации больше не будут приходить по расписанию."
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад к настройкам", callback_data="schedule_settings")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_custom_schedule_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает настройку кастомного расписания"""
    if not update.callback_query:
        return
    
    query = update.callback_query
    await query.answer()
    
    text = "⚙️ *Настройка своего расписания*\n\n"
    text += "Введите время в формате ЧЧ:ММ через запятую\n"
    text += "*Пример:* 9:00, 14:30, 20:00\n\n"
    text += "Максимум 5 временных слотов в день"
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="schedule_settings")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    # Сохраняем состояние для обработки текстового ввода
    context.user_data['waiting_for_schedule'] = True

async def handle_custom_schedule_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод кастомного расписания"""
    if not update.message or not context.user_data.get('waiting_for_schedule'):
        return
    
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.text
    
    try:
        # Парсим введенное время
        time_strings = [t.strip() for t in text.split(',')]
        times = []
        
        for time_str in time_strings:
            if ':' in time_str:
                hours, minutes = map(int, time_str.split(':'))
                if 0 <= hours <= 23 and 0 <= minutes <= 59:
                    times.append(time(hours, minutes))
                else:
                    raise ValueError("Некорректное время")
            else:
                raise ValueError("Некорректный формат")
        
        if len(times) > 5:
            await update.message.reply_text("❌ Максимум 5 временных слотов в день")
            return
        
        if not times:
            await update.message.reply_text("❌ Не указано ни одного времени")
            return
        
        # Настраиваем расписание
        count = await scheduler.setup_user_schedule(user_id, chat_id, context.application, times)
        
        # Очищаем состояние
        context.user_data.pop('waiting_for_schedule', None)
        
        text = f"✅ *Кастомное расписание настроено!*\n\n"
        text += f"Рекомендации будут приходить:\n"
        for t in times:
            text += f"• {t.strftime('%H:%M')}\n"
        text += f"\nВсего рекомендаций в день: {count}"
        
        keyboard = [[InlineKeyboardButton("⬅️ В меню", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except ValueError as e:
        await update.message.reply_text(
            "❌ *Ошибка формата*\n\n"
            "Пожалуйста, введите время в формате ЧЧ:ММ через запятую\n"
            "*Пример:* 9:00, 14:30, 20:00",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text("❌ Произошла ошибка при настройке расписания")

# В recommendation_handlers.py добавляем:
async def send_scheduled_movie(context: ContextTypes.DEFAULT_TYPE):
    """Отправляет фильм по расписанию"""
    job = context.job
    user_id = job.data['user_id']
    chat_id = job.data['chat_id']
    
    # Проверяем активна ли подписка
    if not db.is_subscription_active(user_id):
        await stop_movie_job(user_id, context.application)
        return
    
    movies = db.get_movie_recommendations(user_id, 1)
    if not movies:
        return
    
    movie = movies[0]
    text = "🎬 *Рекомендация фильма*\n\n"
    text += f"*{movie['title']}* ({movie.get('year', 'N/A')})\n\n"
    text += f"📝 *Описание:* {movie['description']}\n\n"
    
    if movie.get('genre'):
        text += f"🎭 *Жанр:* {movie['genre']}\n"
    if movie.get('duration'):
        text += f"⏱ *Продолжительность:* {movie['duration']}\n"
    if movie.get('why_recommend'):
        text += f"💡 *Почему смотреть:* {movie['why_recommend']}\n"
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode='Markdown'
    )

async def send_scheduled_book(context: ContextTypes.DEFAULT_TYPE):
    """Отправляет книгу по расписанию"""
    job = context.job
    user_id = job.data['user_id']
    chat_id = job.data['chat_id']
    
    # Проверяем активна ли подписка
    if not db.is_subscription_active(user_id):
        await stop_book_job(user_id, context.application)
        return
    
    books = db.get_book_recommendations(user_id, 1)
    if not books:
        return
    
    book = books[0]
    text = "📚 *Рекомендация книги*\n\n"
    text += f"*{book['title']}* - {book.get('author', 'Неизвестный автор')}\n\n"
    text += f"📝 *Описание:* {book['description']}\n\n"
    
    if book.get('pages'):
        text += f"📖 *Страниц:* {book['pages']}\n"
    if book.get('genre'):
        text += f"🏷️ *Жанр:* {book['genre']}\n"
    if book.get('why_recommend'):
        text += f"💡 *Почему читать:* {book['why_recommend']}\n"
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode='Markdown'
    )
async def start_reading_recommendations(update: Update, context: ContextTypes):
    """Начинает пошаговую отправку рекомендаций, фильмов и книг"""
    if not update.callback_query:
        return
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    
    application = context.application
    if not application:
        await query.edit_message_text("❌ Ошибка: приложение не найдено")
        return
    
    # Останавливаем старые задачи
    await stop_recommendation_job(user_id, application)
    await stop_movie_job(user_id, application)
    await stop_book_job(user_id, application)
    
    # Запускаем задачу для основных рекомендаций (каждые 10 секунд)
    rec_job = application.job_queue.run_repeating(
        send_single_recommendation,
        interval=10,
        first=0,
        data={'user_id': user_id, 'chat_id': chat_id}
    )
    recommendation_jobs[user_id] = rec_job
    
    # Запускаем задачу для фильмов (каждые 15 секунд)
    movie_job = application.job_queue.run_repeating(
        send_scheduled_cinema,
        interval=15,
        first=2,  # начинаем через 2 секунды
        data={'user_id': user_id, 'chat_id': chat_id}
    )
    movie_jobs[user_id] = movie_job
    
    # Запускаем задачу для книг (каждые 20 секунд)
    book_job = application.job_queue.run_repeating(
        send_scheduled_literature,
        interval=20,
        first=4,  # начинаем через 4 секунды
        data={'user_id': user_id, 'chat_id': chat_id}
    )
    book_jobs[user_id] = book_job

    question_job = application.job_queue.run_repeating(
    send_scheduled_question,  # questions_new
    interval=25,
    first=6,
    data={'user_id': user_id, 'chat_id': chat_id}
    )
    question_jobs[user_id] = question_job
    text = "📖 *Начинаем отправку рекомендаций*\n\n"
    text += "⏰ Основные рекомендации: каждые 10 секунд\n"
    text += "🎬 Рекомендации фильмов: каждые 15 секунд\n"
    text += "📚 Рекомендации книг: каждые 20 секунд\n\n"
    text += "💡 Внимательно читайте и применяйте на практике!\n\n"
    text += "🛑 Чтобы остановить отправку, нажмите кнопку ниже."
    
    keyboard = [
        [InlineKeyboardButton("⏸️ Остановить отправку", callback_data="stop_recommendations")],
        [InlineKeyboardButton("⬅️ В меню", callback_data="show_recommendations")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')


async def request_movie_recommendation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ручной запрос рекомендации фильма"""
    user_id = update.effective_user.id
    
    if not db.is_subscription_active(user_id):
        text = "❌ Эта функция доступна только для подписчиков"
        
        if update.message:
            await update.message.reply_text(text)
        elif update.callback_query:
            await update.callback_query.answer(text, show_alert=True)
        return
    
    movies = db.get_movie_recommendations(user_id, 1)
    if not movies:
        text = "🎬 На данный момент нет рекомендаций фильмов"
        
        if update.message:
            await update.message.reply_text(text)
        elif update.callback_query:
            await update.callback_query.message.edit_text(text)
        return
    
    movie = movies[0]
    text = "🎬 *Рекомендация фильма*\n\n"
    text += f"*{movie['title']}* ({movie.get('year', 'N/A')})\n\n"
    text += f"📝 *Описание:* {movie['description']}\n\n"
    
    if movie.get('genre'):
        text += f"🎭 *Жанр:* {movie['genre']}\n"
    if movie.get('duration'):
        text += f"⏱ *Продолжительность:* {movie['duration']}\n"
    if movie.get('why_recommend'):
        text += f"💡 *Почему смотреть:* {movie['why_recommend']}\n"
    
    if update.message:
        await update.message.reply_text(text, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode='Markdown')
        await update.callback_query.answer()

async def request_book_recommendation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ручной запрос рекомендации книги"""
    user_id = update.effective_user.id
    
    if not db.is_subscription_active(user_id):
        text = "❌ Эта функция доступна только для подписчиков"
        
        if update.message:
            await update.message.reply_text(text)
        elif update.callback_query:
            await update.callback_query.answer(text, show_alert=True)
        return
    
    books = db.get_book_recommendations(user_id, 1)
    if not books:
        text = "📚 На данный момент нет рекомендаций книг"
        
        if update.message:
            await update.message.reply_text(text)
        elif update.callback_query:
            await update.callback_query.message.edit_text(text)
        return
    
    book = books[0]
    text = "📚 *Рекомендация книги*\n\n"
    text += f"*{book['title']}* - {book.get('author', 'Неизвестный автор')}\n\n"
    text += f"📝 *Описание:* {book['description']}\n\n"
    
    if book.get('pages'):
        text += f"📖 *Страниц:* {book['pages']}\n"
    if book.get('genre'):
        text += f"🏷️ *Жанр:* {book['genre']}\n"
    if book.get('why_recommend'):
        text += f"💡 *Почему читать:* {book['why_recommend']}\n"
    
    if update.message:
        await update.message.reply_text(text, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode='Markdown')
        await update.callback_query.answer()
    

async def stop_recommendations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Останавливает отправку всех рекомендаций"""
    if not update.callback_query:
        return
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    application = context.application
    
    if application:
        await stop_recommendation_job(user_id, application)
        await stop_movie_job(user_id, application)
        await stop_book_job(user_id, application)
    
    text = "⏸️ *Отправка рекомендаций остановлена*\n\n"
    text += "Вы можете продолжить чтение в любое время."
    
    keyboard = [
        [InlineKeyboardButton("📖 Продолжить чтение", callback_data="start_reading_recommendations")],
        [InlineKeyboardButton("⬅️ В меню", callback_data="show_recommendations")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')


async def start_reading_recommendations(update: Update, context: ContextTypes):
    """Начинает пошаговую отправку рекомендаций, фильмов и книг"""
    if not update.callback_query:
        return
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    
    application = context.application
    if not application:
        await query.edit_message_text("❌ Ошибка: приложение не найдено")
        return
    
    # Останавливаем старые задачи
    await stop_recommendation_job(user_id, application)
    await stop_movie_job(user_id, application)
    await stop_book_job(user_id, application)
    
    # Запускаем задачу для основных рекомендаций (каждые 10 секунд)
    rec_job = application.job_queue.run_repeating(
        send_single_recommendation,
        interval=10,
        first=0,
        data={'user_id': user_id, 'chat_id': chat_id}
    )
    recommendation_jobs[user_id] = rec_job
    
    # Запускаем задачу для фильмов (каждые 15 секунд)
    movie_job = application.job_queue.run_repeating(
        send_scheduled_cinema,
        interval=30,
        first=2,  # начинаем через 2 секунды
        data={'user_id': user_id, 'chat_id': chat_id}
    )
    movie_jobs[user_id] = movie_job
    
    # Запускаем задачу для книг (каждые 20 секунд)
    book_job = application.job_queue.run_repeating(
        send_scheduled_literature,
        interval=60,
        first=4,  # начинаем через 4 секунды
        data={'user_id': user_id, 'chat_id': chat_id}
    )
    book_jobs[user_id] = book_job

    question_job = application.job_queue.run_repeating(
    send_scheduled_question,  # questions_new
    interval=25,
    first=6,
    data={'user_id': user_id, 'chat_id': chat_id}
    )
    question_jobs[user_id] = question_job
    
    text = "📖 *Начинаем отправку рекомендаций*\n\n"
    text += "⏰ Основные рекомендации: каждые 10 секунд\n"
    text += "🎬 Рекомендации фильмов: каждые 15 секунд\n"
    text += "📚 Рекомендации книг: каждые 20 секунд\n\n"
    text += "💡 Внимательно читайте и применяйте на практике!\n\n"
    text += "🛑 Чтобы остановить отправку, нажмите кнопку ниже."
    
    keyboard = [
        [InlineKeyboardButton("⏸️ Остановить отправку", callback_data="stop_recommendations")],
        [InlineKeyboardButton("⬅️ В меню", callback_data="show_recommendations")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')


def format_couple_recommendation(recommendation, user1_id, user2_id):
    """Форматирует парную рекомендацию"""
    user1_name = db.get_user_info(user1_id).get('first_name', 'Партнер 1')
    user2_name = db.get_user_info(user2_id).get('first_name', 'Партнер 2')
    
    text = f"👫 *Рекомендация для пары*\n\n"
    text += f"💑 *{user1_name}* и *{user2_name}*\n\n"
    text += f"**{recommendation['title']}**\n\n"
    text += f"📝 {recommendation['description']}\n\n"
    text += f"💡 *Совместное задание:* {recommendation['couple_task']}\n\n"
    text += "💞 Работайте над отношениями вместе!"
    
    return text

async def send_scheduled_cinema(context: CallbackContext):
    """Отправляет фильмы из коллекции cinema"""
    job = context.job
    user_id = job.data['user_id']
    chat_id = job.data['chat_id']
    
    # Проверяем активна ли подписка
    if not db.is_subscription_active(user_id):
        await stop_movie_job(user_id, context.application)
        return
    
    # Получаем приоритетные разделы пользователя
    priority_sections = db_couples.get_couple_priority_sections(user_id)
    
    # Ищем фильм в приоритетных разделах
    movie = None
    for section_id in priority_sections:
        movie = db.get_next_cinema_recommendation(user_id, section_id)
        if movie:
            break
    
    # Если в приоритетных разделах нет фильмов, ищем в других
    if not movie:
        all_sections = list(SECTIONS_CONFIG.keys())
        remaining_sections = [s for s in all_sections if s not in priority_sections]
        
        for section_id in remaining_sections:
            movie = db.get_next_cinema_recommendation(user_id, section_id)
            if movie:
                break
    
    if not movie:
        await stop_movie_job(user_id, context.application)
        return
    
    # Форматируем фильм
    section_config = SECTIONS_CONFIG[movie.get('section', 'communication')]
    text = f"{section_config['name']} *Кино*\n\n"
    
    if movie.get('movies') and len(movie['movies']) > 0:
        film = movie['movies'][0]
        text += f"🎬 **{film.get('title', '')}** ({film.get('year', '')})\n"
        text += f"🌍 *Страна:* {film.get('country', '')}\n\n"
        text += f"📝 *О чем фильм:* {film.get('about_what', '')}\n\n"
        text += f"🎯 *Что можно понять:* {film.get('what_to_learn', '')}\n\n"
    
    if movie.get('prescribe'):
        text += f"💡 *Тема подборки:* {movie['prescribe']}\n"
    if movie.get('as_result'):
        text += f"📈 *Результат:* {movie['as_result']}\n"
    
    text += "\n⏰ Следующий фильм через 15 секунд..."
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode='Markdown'
    )

async def send_scheduled_literature(context: CallbackContext):
    """Отправляет книги из коллекции literature"""
    job = context.job
    user_id = job.data['user_id']
    chat_id = job.data['chat_id']
    
    # Проверяем активна ли подписка
    if not db.is_subscription_active(user_id):
        await stop_book_job(user_id, context.application)
        return
    
    # Получаем приоритетные разделы пользователя
    priority_sections = db_couples.get_couple_priority_sections(user_id)
    
    # Ищем книгу в приоритетных разделах
    book = None
    for section_id in priority_sections:
        book = db.get_next_literature_recommendation(user_id, section_id)
        if book:
            break
    
    # Если в приоритетных разделах нет книг, ищем в других
    if not book:
        all_sections = list(SECTIONS_CONFIG.keys())
        remaining_sections = [s for s in all_sections if s not in priority_sections]
        
        for section_id in remaining_sections:
            book = db.get_next_literature_recommendation(user_id, section_id)
            if book:
                break
    
    if not book:
        await stop_book_job(user_id, context.application)
        return
    
    # Форматируем книгу
    section_config = SECTIONS_CONFIG[book.get('section', 'communication')]
    text = f"{section_config['name']} *Литература*\n\n"
    text += f"**{book['title']}**\n"
    text += f"✍️ *Автор:* {book.get('author', '')}\n\n"
    text += f"📖 *Описание:* {book.get('description', '')}\n\n"
    
    benefits = book.get('benefits', [])
    if benefits:
        text += "🌟 *Что вы получите:*\n"
        for benefit in benefits:
            text += f"• {benefit}\n"
    
    text += "\n⏰ Следующая книга через 20 секунд..."
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode='Markdown'
    )

async def send_scheduled_question(context: CallbackContext):
    """Отправляет вопросы из коллекции questions_new"""
    job = context.job
    user_id = job.data['user_id']
    chat_id = job.data['chat_id']
    
    # Проверяем активна ли подписка
    if not db.is_subscription_active(user_id):
        await stop_question_job(user_id, context.application)
        return
    
    # Получаем приоритетные разделы пользователя
    priority_sections = db_couples.get_couple_priority_sections(user_id)
    
    # Ищем вопрос в приоритетных разделах
    question = None
    for section_id in priority_sections:
        question = db.get_next_question_recommendation(user_id, section_id)
        if question:
            break
    
    # Если в приоритетных разделах нет вопросов, ищем в других
    if not question:
        all_sections = list(SECTIONS_CONFIG.keys())
        remaining_sections = [s for s in all_sections if s not in priority_sections]
        
        for section_id in remaining_sections:
            question = db.get_next_question_recommendation(user_id, section_id)
            if question:
                break
    
    if not question:
        await stop_question_job(user_id, context.application)
        return
    
    # Форматируем вопрос
    section_config = SECTIONS_CONFIG[question.get('section', 'communication')]
    text = f"{section_config['name']} *Вопросы для обсуждения*\n\n"
    text += f"❓ **{question.get('text', '')}**\n\n"
    
    tags = question.get('tags', [])
    if tags:
        text += "🏷️ *Темы:* " + ", ".join([f"#{tag}" for tag in tags]) + "\n"
    
    difficulty = question.get('difficulty', '')
    if difficulty:
        text += f"📊 *Сложность:* {difficulty}\n"
    
    text += "\n⏰ Следующий вопрос через 25 секунд..."
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode='Markdown'
    )