from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

class LibidoHandlers:
    def __init__(self, bot):
        self.client = MongoClient(config.MONGO_URI)
        self.db = self.client.family_bot
    
    def register_handlers(self):
        """Регистрация всех обработчиков модуля либидо"""
        handlers = [
            CommandHandler("libido", self.show_libido_menu),
            CallbackQueryHandler(self.request_day_input, pattern='libido_enter_day$'),
            CallbackQueryHandler(self.handle_libido_questionnaire, pattern='^libido_q_'),
            CallbackQueryHandler(self.handle_libido_day_navigation, pattern='^libido_(prev|next)_day$'),
            CallbackQueryHandler(self.handle_libido_article_navigation, pattern='^libido_(prev|next)_article$'),
            CallbackQueryHandler(self.handle_libido_selection, pattern='^libido_'),
            
            CallbackQueryHandler(self.handle_questionnaire_answer, pattern='^ans_'),
            CallbackQueryHandler(self.cancel_questionnaire, pattern='^cancel_questionnaire$'),
            
            MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'^\d+$'), self.process_day_input)

            
    # Обработчик для кнопки "Ввести день вручную" и самого ввода дня
        #    CallbackQueryHandler(self.handle_day_input, pattern='^libido_enter_day$'))
        ]
        for handler in handlers:
            self.bot.application.add_handler(handler)
    
    async def show_libido_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Главное меню модуля либидо"""
        keyboard = [
            [InlineKeyboardButton("Упражнения по дням фазы", callback_data="libido_exercises")],
            [InlineKeyboardButton("Полезные статьи", callback_data="libido_content")],
            [InlineKeyboardButton("Опросники", callback_data="libido_questionnaires")],
            [InlineKeyboardButton("Упражнения перед близостью", callback_data="libido_pre_intimacy")],
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
            await self.bot.common_handlers.show_main_menu(update, context)
    
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


    async def show_libido_day_exercises(self, update: Update, context: ContextTypes.DEFAULT_TYPE, day: int):
        """Показать упражнения для конкретного дня"""
        exercise = self.db.get_libido_exercise(day)[0]
        print("exercise")
        print(exercise)
        print("exercise")
        print(exercise['exercises'])
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
            message = f"📅 <b>День {day}:</b>\n{exercise['exercises']}\n\n"
            message += "<b>Упражнения:</b>\n"
         #   message += "\n".join(f"• {ex}" for ex in exercise["exercises"])
        else:
            message = f"Упражнения для дня {day} ещё не добавлены"
        print("______message___________")
        print(message)
    # Определяем, откуда пришел запрос - из callback или сообщения
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
    
    async def handle_libido_pre_intimacy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Упражнения перед близостью"""
        message = "💖 <b>Упражнения перед интимной близостью:</b>\n\n"
        message += "1. <b>Дыхательная синхронизация</b> (5 минут)\n"
        message += "Сядьте друг напротив друга, закройте глаза и синхронизируйте дыхание.\n\n"
        message += "2. <b>Нежный контакт</b> (10 минут)\n"
        message += "Медленно касайтесь друг друга, концентрируясь на ощущениях.\n\n"
        message += "3. <b>Эмоциональный обмен</b> (5 минут)\n"
        message += "Поделитесь тем, что вас волнует и что вы чувствуете в данный момент."
        
        keyboard = [[InlineKeyboardButton("Назад", callback_data="libido_back")]]
        
        await update.callback_query.edit_message_text(
            text=message,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )