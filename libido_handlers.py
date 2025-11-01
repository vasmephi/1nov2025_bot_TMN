from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
from database import db
from recommendation_handlers import show_premium_offer
from database_libido import Database_lib


# Хранилище для задач отправки контента либидо
libido_jobs = {}

async def show_libido_menu___(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню раздела либидо"""

    if not update.callback_query:
        return
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if not db.is_subscription_active(user_id):
        await show_premium_offer(update, context)
        return
          
    
    # Проверяем, что пользователь - женщина
    if not db.is_female(user_id):
        await query.edit_message_text("❌ Этот раздел доступен только для женщин")
        return
    
    total_content = len(db.get_libido_content())
    remaining_content = db.get_remaining_libido_content_count(user_id)
    
    text = "🌺 *Раздел: Женское либидо и чувственность*\n\n"
    text += "Здесь вы найдете практики и упражнения для:\n"
    text += "• 🌿 Усиления сексуального желания\n"
    text += "• 💪 Укрепления интимных мышц\n"
    text += "• 🧘‍♀️ Развития чувственности\n"
    text += "• 🌙 Баланса гормональной системы\n\n"
    
    text += f"📚 Всего материалов: {total_content}\n"
    
    if remaining_content > 0:
        text += f"🆕 Новых материалов: {remaining_content}\n\n"
        text += "Материалы будут приходить по одному каждые 10 секунд."
    else:
        text += "\n✅ Вы уже изучили все материалы. Можете повторить их изучение."
    
    keyboard = []
    
    if remaining_content > 0:
        keyboard.append([InlineKeyboardButton("📖 Начать изучение", callback_data="start_reading_libido")])
    
    if total_content > 0 and remaining_content == 0:
        keyboard.append([InlineKeyboardButton("🔄 Изучить заново", callback_data="restart_libido")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def start_reading_libido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает пошаговую отправку контента либидо"""
    if not update.callback_query:
        return
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    
    # Проверяем, что пользователь - женщина
    if not db.is_female(user_id):
        await query.edit_message_text("❌ Этот раздел доступен только для женщин")
        return
    
    application = context.application
    if not application:
        await query.edit_message_text("❌ Ошибка: приложение не найдено")
        return
    
    # Останавливаем предыдущие задачи если есть
    await stop_libido_job(user_id, application)
    
    # Запускаем новую задачу
    job = application.job_queue.run_repeating(
        send_single_libido_content,
        interval=10,  # 10 секунд
        first=0,
        data={'user_id': user_id, 'chat_id': chat_id, 'message_id': query.message.message_id}
    )
    
    libido_jobs[user_id] = job
    
    text = "🌺 *Начинаем изучение раздела либидо*\n\n"
    text += "⏰ Материалы будут приходить каждые 10 секунд.\n"
    text += "💡 Внимательно изучайте и применяйте практики!\n\n"
    text += "🛑 Чтобы остановить отправку, нажмите кнопку ниже."
    
    keyboard = [
        [InlineKeyboardButton("⏸️ Остановить отправку", callback_data="stop_libido")],
        [InlineKeyboardButton("⬅️ В меню либидо", callback_data="show_libido_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def send_single_libido_content(context: CallbackContext):
    """Отправляет один элемент контента либидо"""
    job = context.job
    user_id = job.data['user_id']
    chat_id = job.data['chat_id']
    
    # Проверяем, что пользователь - женщина
    if not db.is_female(user_id):
        await stop_libido_job(user_id, context.application)
        return
    
    # Получаем следующий контент
    content = db.get_next_libido_content(user_id)
    
    if not content:
        # Контент закончился
        await stop_libido_job(user_id, context.application)
        await context.bot.send_message(
            chat_id=chat_id,
            text="🎉 *Все материалы изучены!*\n\n"
                 "Вы ознакомились со всем контентом раздела либидо. "
                 "Рекомендуем регулярно повторять практики для достижения лучших результатов.",
            parse_mode='Markdown'
        )
        return
    
    # Форматируем контент
    text = f"🌺 *{content['title']}*\n"
    text += f"🏷️ {content['category']}\n\n"
    text += f"{content['content']}\n\n"
    
    # Показываем сколько контента осталось
    remaining = db.get_remaining_libido_content_count(user_id)
    if remaining > 0:
        text += f"📚 Осталось материалов: {remaining}\n"
        text += "⏰ Следующий материал через 10 секунд..."
    
    if db.is_subscription_active(user_id):
        time_left = db.get_subscription_time_left(user_id)
        text += f"💎 Подписка активна\n"
        text += f"⏰ Осталось: {time_left}\n"
       # Для женщин показываем прогресс по разделу либидо
        if db.is_female(user_id):
            remaining_libido = db.get_remaining_libido_content_count(user_id)
            total_libido = len(db.get_libido_content())
            text += f"\n🌺 Материалов либидо изучено: {total_libido - remaining_libido}/{total_libido}"
        await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode='Markdown'
    )

    else:
        text = "🔒 Подписка не активна\n"
        text += "💡 Оформите подписку для доступа к следующим разделам модуля Либидо "
        await stop_libido_job(user_id, context.application)
        keyboard = [
        [InlineKeyboardButton("💳 Оформить подписку", callback_data="buy_subscription")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            reply_markup=reply_markup,
            text=text,
            chat_id=chat_id,
            parse_mode='Markdown'
    )


async def stop_libido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Останавливает отправку контента либидо"""
    if not update.callback_query:
        return
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    application = context.application
    
    if application:
        await stop_libido_job(user_id, application)
    
    text = "⏸️ *Отправка материалов остановлена*\n\n"
    text += "Вы можете продолжить изучение в любое время."
    
    keyboard = [
        [InlineKeyboardButton("📖 Продолжить изучение", callback_data="start_reading_libido")],
        [InlineKeyboardButton("⬅️ В меню либидо", callback_data="show_libido_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def restart_libido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перезапускает контент либидо"""
    if not update.callback_query:
        return
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Сбрасываем прогресс
    db.reset_libido_content(user_id)
    
    text = "🔄 *Прогресс сброшен!*\n\n"
    text += "Теперь вы можете изучить материалы раздела либидо заново."
    
    keyboard = [
        [InlineKeyboardButton("📖 Начать изучение", callback_data="start_reading_libido")],
        [InlineKeyboardButton("⬅️ В меню либидо", callback_data="show_libido_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def stop_libido_job(user_id: int, application):
    """Останавливает задачу отправки контента либидо"""
    if user_id in libido_jobs:
        libido_jobs[user_id].schedule_removal()
        del libido_jobs[user_id]

Database_lib1=Database_lib()

class LibidoHandlers:
    def __init__(self):
        self.db = Database_lib1
       
    async def show_libido_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Главное меню модуля либидо"""
        keyboard = [
            [InlineKeyboardButton("Упражнения по дням фазы", callback_data="libido_exercises")],
            [InlineKeyboardButton("Полезные статьи", callback_data="libido_content")],
            [InlineKeyboardButton("Опросники", callback_data="libido_questionnaires")],
            [InlineKeyboardButton("Упражнения перед близостью", callback_data="l1ibido_pre_intimacy")],
            [InlineKeyboardButton("Назад в главное меню", callback_data="libido_back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text(
                "Модуль либидо и отношений. Выберите опцию:",
                reply_markup=reply_markup
            )
        else:
            await update.callback_query.edit_message_text(
                "Модуль либидо и отношений. Выберите опцию:",
                reply_markup=reply_markup
            )
    
    async def handle_libido_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора в меню либидо"""
        query = update.callback_query
        await query.answer()
        
        option = query.data.split('_')[1]
        
        if option == "exercises":
            await self.handle_libido_exercises(update, context)
        elif option == "content":
            await self.handle_libido_content(update, context)
        elif option == "questionnaires":
            await self.show_libido_questionnaires(update, context)
        elif option == "pre-intimacy":
            await self.handle_libido_pre_intimacy(update, context)
        elif option == "back":
            await self.show_libido_menu(update, context)


    async def handle_day_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода дня цикла вручную"""
        # Если это callback от кнопки "Ввести день вручную"
        if update.callback_query :
            await update.callback_query.answer()
            context.user_data["waiting_for_day"] = True
            await update.callback_query.edit_message_text(
                text="Пожалуйста, введите день цикла (число от 1 до 28):"
            )
            return
        
        # Если это текстовое сообщение с днём
        if update.message and context.user_data.get("waiting_for_day"):
            try:
                day = int(update.message.text)
                print("_________day___________")
                print(day)
                if 1 <= day <= 28:
                    print("_________day___________")
                    print(day)
                    await self.show_libido_day_exercises(update, context, day)
                    context.user_data.pop("waiting_for_day", None)
                else:
                    await update.message.reply_text("Пожалуйста, введите число от 1 до 28")
            except ValueError:
                await update.message.reply_text("Пожалуйста, введите число")
            return

    async def handle_libido_exercises(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора упражнений по дням фазы"""
        keyboard = [
            [InlineKeyboardButton("Ввести день вручную", callback_data="libido_enter_day")],
            [InlineKeyboardButton("Текущий день цикла", callback_data="libido_current_day")],
            [InlineKeyboardButton("Назад", callback_data="libido_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text="Выберите способ определения дня цикла:",
            reply_markup=reply_markup
        )

    async def request_day_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запрос у пользователя ввода дня (обработка кнопки 'Ввести день вручную')"""
        query = update.callback_query
        await query.answer()
        
        # Устанавливаем флаг, что ожидаем ввод дня
        context.user_data["waiting_for_day"] = True
        
        await query.edit_message_text(
            text="Пожалуйста, введите день цикла (число от 1 до 28):"
        )

    async def process_day_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка введенного пользователем дня"""
        try:
            day = int(update.message.text)
            print(day)

            print(day)
            if not 1 <= day <= 28:
                await update.message.reply_text("День должен быть числом от 1 до 28. Попробуйте еще раз.")
                return
            
            # Сбрасываем флаг ожидания ввода
            context.user_data.pop("waiting_for_day", None)
            
            # Показываем упражнения для введенного дня
            await self.show_libido_day_exercises(update, context, day)
            
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите число от 1 до 28.")


    async def show_libido_day_exercises(self, update, context, day):
        exercise = self.db.get_libido_exercise(day)["exercises"]

        keyboard = []
        nav_buttons = []
        
        if day > 1:
             nav_buttons.append(InlineKeyboardButton("⬅️ Предыдущий день", callback_data=f"libido_prev_day_{day}"))
        if day < 28:
             nav_buttons.append(InlineKeyboardButton(f"Следующий день ➡️", callback_data=f"libido_next_day_{day}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton("В меню", callback_data="libido_back")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if exercise:
            # Преобразуем список упражнений в строку
            exercises_text = "\n".join([f"• {ex}" for ex in exercise])
            
            message = (
                f"📅 <b>День {day}:</b>\n\n"
                f"<b>Упражнения:</b>\n{exercises_text}\n\n"
                f"<i>{self.db.get_libido_exercise(day).get('description', '')}</i>"
            )
        else:
            message = f"❌ Упражнения для дня {day} не найдены"
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=message,
                parse_mode="HTML",
                reply_markup=reply_markup
                )
        else:
        # Если это текстовое сообщение, отправляем новое сообщение
            await update.message.reply_text(
                text=message,
                parse_mode="HTML",
                reply_markup=reply_markup
                )
        
               
    # async def show_libido_day_exercises(self, update: Update, context: ContextTypes.DEFAULT_TYPE, day: int):
    #     """Показать упражнения для конкретного дня"""
    #     exercise = self.db.get_libido_exercise(day)
    #     print("exercise")
    #     print(exercise)
    #     keyboard = []
    #     nav_buttons = []
        
    #     if day > 1:
    #         nav_buttons.append(InlineKeyboardButton("⬅️ Предыдущий день", callback_data=f"libido_prev_day_{day}"))
    #     if day < 28:
    #         nav_buttons.append(InlineKeyboardButton(f"Следующий день ➡️", callback_data=f"libido_next_day_{day}"))
        
    #     if nav_buttons:
    #         keyboard.append(nav_buttons)
        
    #     keyboard.append([InlineKeyboardButton("В меню", callback_data="libido_back")])
        
    #     reply_markup = InlineKeyboardMarkup(keyboard)
        
    #     if exercise:
    #         message = f"📅 <b>День {day}:</b>\n{exercise['exercises']}\n\n"
    #         message += "<b>Упражнения:</b>\n"
    #      #   message += "\n".join(f"• {ex}" for ex in exercise["exercises"])
    #     else:
    #         message = f"Упражнения для дня {day} ещё не добавлены"
    #     print("______message___________")
    #     print(message)
    # # Определяем, откуда пришел запрос - из callback или сообщения

    async def handle_libido_day_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Навигация по дням цикла"""
        query = update.callback_query
        await query.answer()
        
        current_day = int(query.data.split('_')[-1])
        action = query.data.split('_')[2]
        
        if action == "prev":
            new_day = current_day - 1
        else:
            new_day = current_day + 1
        
        await self.show_libido_day_exercises(update, context, new_day)
    
    async def handle_libido_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать список статей"""
        articles = self.db.get_libido_articles()
        print("xxxxxxxxxxx")
        print(articles)
        if not articles:
            await update.callback_query.edit_message_text(text="Статьи временно отсутствуют")
            return
        
        context.user_data["libido_articles"] = articles
        context.user_data["current_article_index"] = 0
        
        await self.show_libido_article(update, context)
    
    async def show_libido_article(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать конкретную статью"""
        articles = context.user_data.get("libido_articles", [])
        current_index = context.user_data.get("current_article_index", 0)
        
        if not articles or current_index >= len(articles):
            await update.callback_query.edit_message_text(text="Ошибка загрузки статей")
            return
        
        article = articles[current_index]
        
        keyboard = []
        nav_buttons = []
        
        if current_index > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data="libido_prev_article"))
        if current_index < len(articles) - 1:
            nav_buttons.append(InlineKeyboardButton("Далее ➡️", callback_data="libido_next_article"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton("В меню", callback_data="libido_back")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"📚 <b>{article.get('id')}</b>\n\n"
        message += article.get('text', 'Содержание отсутствует')
        
        await update.callback_query.edit_message_text(
            text=message,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    
    async def handle_libido_article_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Навигация по статьям"""
        query = update.callback_query
        await query.answer()
        
        current_index = context.user_data.get("current_article_index", 0)
        print("NEXT____________")
        if "next" in query.data:
            context.user_data["current_article_index"] = current_index + 1
            print("NEXT____________")
        else:
            context.user_data["current_article_index"] = current_index - 1
        
        await self.show_libido_article(update, context)
    
    async def show_libido_questionnaires(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать список опросников"""
        questionnaires = self.db.get_libido_questionnaires()
        
        if not questionnaires:
            await update.callback_query.edit_message_text(text="Опросники временно недоступны")
            return
        
        keyboard = [
            [InlineKeyboardButton(q["name"], callback_data=f"libido_q_{q['_id']}")] 
            for q in questionnaires
        ]
        keyboard.append([InlineKeyboardButton("Назад", callback_data="libido_back")])
        
        await update.callback_query.edit_message_text(
            text="Выберите опросник:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def handle_libido_questionnaire(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать опросник"""
        print("XXXXXXXXXXXXXXXXXPPPPPPPPPPPPPPPPPPPPPPPP")
        query = update.callback_query
        await query.answer()
        
        q_id = query.data.split('_')[2]
        questionnaire = self.db.get_libido_questionnaire(q_id)
        print(questionnaire)
        if not questionnaire:
            await query.edit_message_text(text="Ошибка: опросник не найден")
            return
        
        context.user_data["current_questionnaire"] = {
            "id": q_id,
            "name": questionnaire["name"],
            "questions": questionnaire["questions"],
            "answers": [],
            "current_question": 0
        }
        
        await self.show_next_question(update, context)
    
    async def show_next_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать следующий вопрос опросника"""
        q_data = context.user_data.get("current_questionnaire")
        
        if not q_data or q_data["current_question"] >= len(q_data["questions"]):
            await self.finish_questionnaire(update, context)
            return
        
        question = q_data["questions"][q_data["current_question"]]
        
        keyboard = [
            [InlineKeyboardButton(str(i), callback_data=f"ans_{i}") for i in range(1, 6)],
            [InlineKeyboardButton("Отменить", callback_data="cancel_questionnaire")]
        ]
        
        await update.callback_query.edit_message_text(
            text=f"{q_data['name']}\n\nВопрос {q_data['current_question']+1}/{len(q_data['questions'])}:\n\n{question}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def handle_questionnaire_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ответа на вопрос"""
        query = update.callback_query
        await query.answer()
        
        answer = int(query.data.split('_')[1])
        q_data = context.user_data.get("current_questionnaire")
        
        if not q_data:
            await query.edit_message_text(text="Ошибка: данные опросника не найдены")
            return
        
        q_data["answers"].append(answer)
        q_data["current_question"] += 1
        
        await self.show_next_question(update, context)
    
    async def finish_questionnaire(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Завершение опросника и вывод результатов"""
        q_data = context.user_data.get("current_questionnaire")
        
        if not q_data:
            await update.callback_query.edit_message_text(text="Ошибка завершения опросника")
            return
        
        total_score = sum(q_data["answers"])
        avg_score = total_score / len(q_data["answers"]) if q_data["answers"] else 0
        
        message = f"📊 Опросник '{q_data['name']}' завершен!\n\n"
        message += f"Ваш результат: {total_score} баллов (средний балл: {avg_score:.1f})\n\n"
        
        # Добавьте здесь интерпретацию результатов на основе вашей логики
        if avg_score < 2.5:
            message += "Результат ниже среднего. Рекомендуется обратить внимание на эту сферу."
        elif avg_score < 4:
            message += "Средний результат. Есть куда расти!"
        else:
            message += "Отличный результат! Продолжайте в том же духе."
        
        keyboard = [[InlineKeyboardButton("В меню", callback_data="libido_back")]]
        
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        context.user_data.pop("current_questionnaire", None)
    
    async def cancel_questionnaire(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена опросника"""
        context.user_data.pop("current_questionnaire", None)
        await self.show_libido_menu(update, context)
    
    # async def handle_libido_pre_intimacy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Упражнения перед близостью"""
    #     message = "💖 <b>Упражнения перед интимной близостью:</b>\n\n"
    #     message += "1. <b>Дыхательная синхронизация</b> (5 минут)\n"
    #     message += "Сядьте друг напротив друга, закройте глаза и синхронизируйте дыхание.\n\n"
    #     message += "2. <b>Нежный контакт</b> (10 минут)\n"
    #     message += "Медленно касайтесь друг друга, концентрируясь на ощущениях.\n\n"
    #     message += "3. <b>Эмоциональный обмен</b> (5 минут)\n"
    #     message += "Поделитесь тем, что вас волнует и что вы чувствуете в данный момент."
        
    #     keyboard = [[InlineKeyboardButton("Назад", callback_data="libido_back")]]
        
    #     await update.callback_query.edit_message_text(
    #         text=message,
    #         parse_mode="HTML",
    #         reply_markup=InlineKeyboardMarkup(keyboard)
    #     )
    # async def handle_libido_pre_intimacy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Упражнения перед близостью из базы данных"""
    #     try:
    #         # Получаем упражнения для интимной близости (например, день 5 - дыхание)
    #         breathing_exercise = self.db.get_exercise_by_day_and_category(5, "physical")
    #         mindfulness_exercise = self.db.get_exercise_by_day_and_category(6, "mindfulness")
    #         sensuality_exercise = self.db.get_exercise_by_day_and_category(9, "couple")
    #         print("внутри handle libid pre")
    #         message = "💖 <b>Упражнения перед интимной близостью:</b>\n\n"
            
    #         if breathing_exercise:
    #             message += f"1. <b>{breathing_exercise['title']}</b> ({breathing_exercise.get('duration_minutes', 10)} минут)\n"
    #             message += f"{breathing_exercise['goal']}\n\n"
            
    #         if mindfulness_exercise:
    #             message += f"2. <b>{mindfulness_exercise['title']}</b> ({mindfulness_exercise.get('duration_minutes', 15)} минут)\n"
    #             message += f"{mindfulness_exercise['goal']}\n\n"
            
    #         if sensuality_exercise:
    #             message += f"3. <b>{sensuality_exercise['title']}</b> ({sensuality_exercise.get('duration_minutes', 45)} минут)\n"
    #             message += f"{sensuality_exercise['goal']}\n\n"
            
    #         # Если нет упражнений в базе, показываем заглушку
    #         if message == "💖 <b>Упражнения перед интимной близостью:</b>\n\n":
    #             message += "❌ Упражнения временно недоступны. Попробуйте позже."
            
    #         keyboard = [
    #             [InlineKeyboardButton("🧘 Дыхательные практики", callback_data="l1ibido_breathing")],
    #             [InlineKeyboardButton("🎨 Упражнения на осознанность", callback_data="l1ibido_mindfulness")],
    #             [InlineKeyboardButton("👫 Парные практики", callback_data="l1ibido_couple")],
    #             [InlineKeyboardButton("Назад", callback_data="show_libido_menu")]
    #         ]
            
    #         await update.callback_query.edit_message_text(
    #             text=message,
    #             parse_mode="HTML",
    #             reply_markup=InlineKeyboardMarkup(keyboard)
    #         )
            
    #     except Exception as e:
    #         print(f"Ошибка при получении упражнений: {e}")
    #         await update.callback_query.edit_message_text(
    #             text="❌ Произошла ошибка при загрузке упражнений.",
    #             parse_mode="HTML"
    #         )
    async def handle_libido_pre_intimacy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Главное меню упражнений"""
        try:
            total_exercises = self.db.get_exercise_count()
            total_days = self.db.get_total_days()
            
            message = (
                "💖 <b>База упражнений для развития либидо</b>\n\n"
                f"📊 Статистика:\n"
                f"• Всего упражнений: {total_exercises}\n"
                f"• Дней с упражнениями: {total_days}\n\n"
                "<b>Выберите режим просмотра:</b>"
            )
            
            keyboard = [
                [InlineKeyboardButton("📅 Простой просмотр по дням", callback_data="l1ibido_simple_exercises")],
                [InlineKeyboardButton("📂 Просмотр по категориям", callback_data="l1ibido_categories")],
                [InlineKeyboardButton("🔙 Назад", callback_data="libido_back")]
            ]
            
            await update.callback_query.edit_message_text(
                text=message,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            print(f"Ошибка в handle_libido_pre_intimacy: {e}")
            await update.callback_query.edit_message_text(
                text="❌ Произошла ошибка при загрузке меню.",
                parse_mode="HTML"
            )
    async def show_breathing_exercises(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать дыхательные упражнения"""
        breathing_exercises = self.db.get_exercises_by_category("physical")
        
        message = "🌬️ <b>Дыхательные упражнения:</b>\n\n"
        
        for exercise in breathing_exercises:
            if 'дыхание' in exercise.get('tags', []):
                message += f"• <b>День {exercise['day']}: {exercise['title']}</b>\n"
                message += f"  {exercise['goal'][:100]}...\n\n"
        
        keyboard = [[InlineKeyboardButton("Назад", callback_data="l1ibido_pre_intimacy")]]
        await update.callback_query.edit_message_text(text=message, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

    # async def show_mindfulness_exercises(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Показать упражнения на осознанность"""
    #     mindfulness_exercises = self.db.get_exercises_by_category("mindfulness")[0]
        
    #     # message = "🎨 <b>Упражнения на осознанность:</b>\n\n"
    #     message=self.format_exercise_details(mindfulness_exercises)
    #     # for exercise in mindfulness_exercises:
    #     #     message += f"• <b>День {exercise['day']}: {exercise['title']}</b>\n"
    #     #     message += f"  {exercise['goal'][:100]}...\n\n"
        
    #     keyboard = [[InlineKeyboardButton("Назад", callback_data="l1ibido_pre_intimacy")]]
    #     await update.callback_query.edit_message_text(text=message, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

    async def show_couple_exercises(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать парные упражнения"""
        couple_exercises = self.db.get_exercises_by_category("couple")
        
        message = "👫 <b>Парные упражнения:</b>\n\n"
        
        for exercise in couple_exercises:
            message += f"• <b>День {exercise['day']}: {exercise['title']}</b>\n"
            message += f"  {exercise['goal'][:100]}...\n\n"
        
        keyboard = [[InlineKeyboardButton("Назад", callback_data="l1ibido_pre_intimacy")]]
        await update.callback_query.edit_message_text(text=message, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    async def show_exercises_by_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать упражнения по категории с возможностью детального просмотра"""
        try:
            query = update.callback_query
            category = query.data.replace('libido_category_', '')
            
            exercises = self.db.get_exercises_by_category(category)
            
            category_names = {
                "mental": "🧠 Ментальные упражнения",
                "physical": "💪 Физические практики",
                "couple": "👫 Парные упражнения", 
                "mindfulness": "🎨 Упражнения на осознанность"
            }
            
            message = f"<b>{category_names.get(category, category)}</b>\n\n"
            keyboard = []
            
            if exercises:
                for exercise in exercises:
                    day = exercise.get('day', '?')
                    title = exercise.get('title', 'Без названия')
                    duration = exercise.get('duration_minutes', '?')
                    difficulty = exercise.get('difficulty', 'Не указана')
                    
                    message += f"<b>День {day}: {title}</b>\n"
                    message += f"⏱ {duration} мин | 🎯 {difficulty}\n\n"
                    
                    # Добавляем кнопку для детального просмотра
                    keyboard.append([
                        InlineKeyboardButton(
                            f"📖 День {day}: {title[:20]}...", 
                            callback_data=f"l1ibido_exercise_{day}_{category}"
                        )
                    ])
            else:
                message += "❌ В этой категории пока нет упражнений."
            
            # Кнопки навигации
            keyboard.append([InlineKeyboardButton("🔙 Назад к разделам", callback_data="l1ibido_pre_intimacy")])
            keyboard.append([InlineKeyboardButton("🏠 В главное меню", callback_data="l1ibido_back")])
            
            await query.edit_message_text(
                text=message,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            print(f"Ошибка в show_exercises_by_category: {e}")
            await update.callback_query.edit_message_text(
                text="❌ Ошибка при загрузке упражнений категории.",
                parse_mode="HTML"
            )
    async def show_mindfulness_exercises(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать упражнения на осознанность"""
        try:
            mindfulness_exercises = self.db.get_exercises_by_category("mindfulness")
            
            if not mindfulness_exercises:
                message = "🎨 <b>Упражнения на осознанность:</b>\n\n❌ В этой категории пока нет упражнений."
                keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="l1ibido_pre_intimacy")]]
            else:
                message = "🎨 <b>Упражнения на осознанность:</b>\n\n"
                keyboard = []
                
                # Показываем краткий список всех упражнений
                for exercise in mindfulness_exercises:
                    day = exercise.get('day', '?')
                    title = exercise.get('title', 'Без названия')
                    duration = exercise.get('duration_minutes', '?')
                    
                    message += f"<b>День {day}: {title}</b>\n"
                    message += f"⏱ {duration} минут\n\n"
                
                message += "👇 <i>Выберите упражнение для детального просмотра:</i>"
                
                # Создаем кнопки для каждого упражнения
                for exercise in mindfulness_exercises:
                    day = exercise.get('day', '?')
                    title = exercise.get('title', 'Без названия')
                    short_title = title[:25] + "..." if len(title) > 25 else title
                    
                    keyboard.append([
                        InlineKeyboardButton(
                            f"🎨 День {day}: {short_title}", 
                            callback_data=f"l1ibido_exercise_{day}_mindfulness"
                        )
                    ])
                
                keyboard.append([InlineKeyboardButton("🔙 Назад к разделам", callback_data="l1ibido_pre_intimacy")])
            
            await update.callback_query.edit_message_text(
                text=message,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            print(f"Ошибка в show_mindfulness_exercises: {e}")
            await update.callback_query.edit_message_text(
                text="❌ Ошибка при загрузке упражнений на осознанность.",
                parse_mode="HTML"
            )
    def format_exercise_details(self, exercise):
        """Форматирование детальной информации об упражнении"""
        if not exercise:
            return "❌ Упражнение не найдено"
        
        message = f"<b>🎯 {exercise.get('title', 'Без названия')}</b>\n\n"
        
        # Основная информация
        message += f"<b>День:</b> {exercise.get('day', '?')}\n"
        message += f"<b>Категория:</b> {exercise.get('category', 'Не указана')}\n"
        message += f"<b>Сложность:</b> {exercise.get('difficulty', 'Не указана')}\n"
        message += f"<b>Длительность:</b> {exercise.get('duration_minutes', '?')} минут\n\n"
        
        # Цель и назначение
        if exercise.get('goal'):
            message += f"<b>Цель:</b>\n{exercise['goal']}\n\n"
        
        if exercise.get('purpose'):
            message += f"<b>Для чего это нужно:</b>\n{exercise['purpose']}\n\n"
        
        # Подготовка
        if exercise.get('preparation'):
            message += "<b>📋 Подготовка:</b>\n"
            for prep in exercise['preparation']:
                message += f"• {prep}\n"
            message += "\n"
        
        # Шаги выполнения
        if exercise.get('steps'):
            message += "<b>🔄 Шаги выполнения:</b>\n"
            for step in exercise['steps']:
                message += f"\n<b>{step.get('step_number', '?')}. {step.get('title', '')}</b>\n"
                message += f"{step.get('description', '')}\n"
                
                if step.get('substeps'):
                    for substep in step['substeps']:
                        message += f"   ◦ {substep}\n"
                
                # Параметры для физических упражнений
                if step.get('parameters'):
                    params = step['parameters']
                    message += f"   ⚙️ Параметры: {params.get('contraction_time', '?')}с сокращение, "
                    message += f"{params.get('relaxation_time', '?')}с расслабление, "
                    message += f"{params.get('repetitions', '?')} повторений\n"
        
        # График тренировок
        if exercise.get('training_schedule'):
            schedule = exercise['training_schedule']
            message += "\n<b>📅 График тренировок:</b>\n"
            message += f"• Частота: {schedule.get('frequency', 'Не указана')}\n"
            message += f"• Длительность сессии: {schedule.get('session_duration', 'Не указана')}\n"
            message += f"• Ежедневный объем: {schedule.get('daily_total', 'Не указана')}\n"
            message += f"• Прогрессия: {schedule.get('progression', 'Не указана')}\n"
        
        # Важные заметки
        if exercise.get('important_notes'):
            message += "\n<b>💡 Важные заметки:</b>\n"
            for note in exercise['important_notes']:
                message += f"• {note}\n"
        
        # Преимущества
        if exercise.get('benefits'):
            message += "\n<b>✅ Преимущества:</b>\n"
            for benefit in exercise['benefits']:
                message += f"• {benefit}\n"
        
        # Распространенные ошибки
        if exercise.get('common_mistakes'):
            message += "\n<b>⚠️ Распространенные ошибки:</b>\n"
            for mistake in exercise['common_mistakes']:
                message += f"• {mistake}\n"
        
        # Показатели прогресса
        if exercise.get('progress_indicators'):
            message += "\n<b>📈 Показатели прогресса:</b>\n"
            for indicator in exercise['progress_indicators']:
                message += f"• {indicator}\n"
        
        # Советы по интеграции
        if exercise.get('integration_tips'):
            message += "\n<b>💡 Советы по интеграции в жизнь:</b>\n"
            for tip in exercise['integration_tips']:
                message += f"• {tip}\n"
        
        # Противопоказания
        if exercise.get('contraindications'):
            message += "\n<b>🚫 Противопоказания:</b>\n"
            for contraindication in exercise['contraindications']:
                message += f"• {contraindication}\n"
        
        # Рекомендации
        if exercise.get('recommendations'):
            message += "\n<b>📝 Рекомендации:</b>\n"
            for recommendation in exercise['recommendations']:
                message += f"• {recommendation}\n"
        
        return message
    async def show_exercise_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать детальную информацию об упражнении"""
        try:
            query = update.callback_query
            data = query.data.replace('l1ibido_exercise_', '')
            day, category = data.split('_')
            
            exercise = self.db.get_exercise_details(int(day), category)
            
            if exercise:
                message = self.format_exercise_details(exercise)
            else:
                message = "❌ Упражнение не найдено"
            
            keyboard = [
                [InlineKeyboardButton("🔙 Назад к категории", callback_data=f"l1ibido_{category}")],
                [InlineKeyboardButton("🏠 В главное меню", callback_data="libido_back")]
            ]
            
            await query.edit_message_text(
                text=message,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            print(f"Ошибка в show_exercise_details: {e}")
            await update.callback_query.edit_message_text(
                text="❌ Ошибка при загрузке деталей упражнения.",
                parse_mode="HTML"
            )
    async def show_simple_exercises(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        try:
            # Получаем текущий день из контекста или начинаем с 1
            current_day = context.user_data.get('current_exercise_day', 1)
            exercise = self.db.get_exercise_by_day(current_day)
            
            if exercise:
                message = self.format_exercise_details(exercise)
            else:
                message = f"❌ Упражнение для дня {current_day} не найдено"
            
            # Создаем клавиатуру для навигации
            total_days = self.db.get_total_days()
            all_days = self.db.get_all_days()
            
            keyboard = []
            
            # Кнопки навигации
            nav_buttons = []
            if current_day > min(all_days) if all_days else False:
                nav_buttons.append(InlineKeyboardButton("⬅️ Предыдущий", callback_data="l1ibido_prev_day"))
            
            nav_buttons.append(InlineKeyboardButton(f"📅 День {current_day}/{total_days}", callback_data="l1ibido_current_day"))
            
            if current_day < max(all_days) if all_days else False:
                nav_buttons.append(InlineKeyboardButton("Следующий ➡️", callback_data="l1ibido_next_day"))
            
            if nav_buttons:
                keyboard.append(nav_buttons)
            
            # Кнопка выбора конкретного дня
            keyboard.append([InlineKeyboardButton("🎯 Выбрать конкретный день", callback_data="l1ibido_choose_day")])
            
            # Основные кнопки
            keyboard.append([InlineKeyboardButton("🔙 Назад к меню", callback_data="libido_back")])
            
            await update.callback_query.edit_message_text(
                text=message,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        except Exception as e:
            print(f"Ошибка в show_simple_exercises: {e}")
            await update.callback_query.edit_message_text(
                text="❌ Ошибка при загрузке упражнения.",
                parse_mode="HTML"
            )

    async def handle_day_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка навигации по дням"""
        try:
            query = update.callback_query
            action = query.data
            
            current_day = context.user_data.get('current_exercise_day', 1)
            all_days = self.db.get_all_days()
            
            if action == "l1ibido_next_day" and all_days:
                current_index = all_days.index(current_day)
                if current_index < len(all_days) - 1:
                    context.user_data['current_exercise_day'] = all_days[current_index + 1]
            
            elif action == "l1ibido_prev_day" and all_days:
                current_index = all_days.index(current_day)
                if current_index > 0:
                    context.user_data['current_exercise_day'] = all_days[current_index - 1]
            
            # Возвращаемся к показу упражнения
            await self.show_simple_exercises(update, context)
            
        except Exception as e:
            print(f"Ошибка в handle_day_navigation: {e}")
            await update.callback_query.edit_message_text(
                text="❌ Ошибка при навигации.",
                parse_mode="HTML"
            )

    async def choose_specific_day(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Выбор конкретного дня"""
        try:
            all_days = self.db.get_all_days()
            
            message = "🎯 <b>Выберите день:</b>\n\n"
            message += f"Доступные дни: {', '.join(map(str, all_days))}"
            
            keyboard = []
            
            # Создаем кнопки для дней (группируем по 5 в ряд)
            day_buttons = []
            for day in all_days:
                day_buttons.append(InlineKeyboardButton(f"День {day}", callback_data=f"l1ibido_day_{day}"))
                if len(day_buttons) == 5:
                    keyboard.append(day_buttons)
                    day_buttons = []
            
            if day_buttons:
                keyboard.append(day_buttons)
            
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="l1ibido_simple_exercises")])
            
            await update.callback_query.edit_message_text(
                text=message,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            print(f"Ошибка в choose_specific_day: {e}")
            await update.callback_query.edit_message_text(
                text="❌ Ошибка при выборе дня.",
                parse_mode="HTML"
            )

    async def handle_specific_day(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора конкретного дня"""
        try:
            query = update.callback_query
            day = int(query.data.replace('l1ibido_day_', ''))
            
            context.user_data['current_exercise_day'] = day
            await self.show_simple_exercises(update, context)
            
        except Exception as e:
            print(f"Ошибка в handle_specific_day: {e}")
            await update.callback_query.edit_message_text(
                text="❌ Ошибка при выборе дня.",
                parse_mode="HTML"
            )

LibidoHandlers=LibidoHandlers()