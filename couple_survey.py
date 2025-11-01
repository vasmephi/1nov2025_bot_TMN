
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database_couples import DatabaseCouples
from recommendation_handlers import show_recommendations_menu
import config
class CoupleSurvey:
    def __init__(self):
        self.db = DatabaseCouples()
        self.user_sessions = {}
        self.sections_order = self._get_sections_order()

    def _get_sections_order(self):
        """Возвращает порядок разделов по приоритету из config"""
        return sorted(config.SECTIONS_CONFIG.keys(), 
                     key=lambda x: config.SECTIONS_CONFIG[x]['priority'])
    
    async def show_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показывает текущий вопрос с вариантами ответов из базы"""
        session = self.user_sessions.get(user_id)
        if not session:
            await self.restart_survey(update, context)
            return
        
        current_index = session['current_question']
        questions = session['current_questions']
        section_id = session['current_section']
        section_config = config.SECTIONS_CONFIG[section_id]
        
        if current_index >= len(questions):
            await self.complete_section(update, context, user_id)
            return
        
        # 🔥 БЕРЕМ ВОПРОС ИЗ БАЗЫ ДАННЫХ С ВАРИАНТАМИ ОТВЕТОВ
        question = questions[current_index]
        
        # 🔥 СОЗДАЕМ КЛАВИАТУРУ ИЗ ВАРИАНТОВ ОТВЕТОВ ИЗ БАЗЫ
        keyboard = []
        for option in question.get('options', []):
            keyboard.append([InlineKeyboardButton(
                option['text'], 
                callback_data=f"answer_{section_id}_{question['question_id']}_{option['value']}"
            )])
        
        keyboard.append([InlineKeyboardButton("⬅️ Назад к разделам", callback_data="back_to_sections")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        progress = f"{current_index + 1}/{len(questions)}"
        text = f"📝 *{section_config['name']}* | Вопрос {progress}\n\n"
        text += f"{question['question']}"
        
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает ответ на вопрос"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        callback_data = query.data.replace("answer_", "")
        
        # Парсим данные ответа: section_questionId_answerValue
        parts = callback_data.split("_")
        if len(parts) < 3:
            await query.edit_message_text("❌ Ошибка обработки ответа")
            return
        
        section_id = parts[0]
        question_id = parts[1]
        answer_value = float(parts[2:][1])  # ⬅️ Используем значение из базы
        
        # Сохраняем ответ
        session = self.user_sessions.get(user_id)
        if session and session['current_section'] == section_id:
            session['answers'][question_id] = answer_value
            session['current_question'] += 1
            
            # Удаляем старое сообщение с вопросом
            try:
                await query.delete_message()
            except:
                pass
            
            # Показываем следующий вопрос
            await self.show_question(update, context, user_id)
    
    async def complete_section(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Завершает раздел и переходит к следующему"""
        session = self.user_sessions.get(user_id)
        if not session:
            await self.restart_survey(update, context)
            return
        
        section_id = session['current_section']
        
        # Сохраняем ответы раздела
        session['section_answers'][section_id] = session['answers'].copy()
        session['completed_sections'].append(section_id)
        
        # Переходим к следующему разделу
        session['current_section_index'] += 1
        print(session['current_section_index'])
        print("session['current_section_index'])")
        print("len(session['sections_order'])")
        if session['current_section_index'] < len(session['sections_order']):
            await self.show_section_intro(update, context, user_id)
        else:
            await self.complete_survey(update, context, user_id)

    
    async def start_couple_survey(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начинает парный опросник"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # Проверяем, есть ли пара
        partner_id = self.db.get_partner_id(user_id)
        print(partner_id,"partner_id")
        print("partner_id")
        if not partner_id:
            await query.edit_message_text("❌ У вас нет пары. Сначала добавьте партнера.")
            return
        
       # Проверяем, проходил ли уже пользователь опрос
        if self.db.has_completed_survey(user_id):
            await self.show_survey_completed(update, context, user_id, partner_id)
            return
        
        # Удаляем старое меню
        try:
            await query.delete_message()
        except:
            pass
        
        # Создаем сессию опроса
        self.user_sessions[user_id] = {
            'current_section_index': 0,
            'current_question': 0,
            'section_answers': {},
            'completed_sections': [],
            'sections_order': self.sections_order.copy(),
            'started_at': query.message.date
        }
        
        # Показываем первый раздел
      #  from survey_handlers import survey_manager
      #  await survey_manager.show_section_intro(update, context, user_id)
        await self.show_section_intro(update, context, user_id)




    async def show_section_intro(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int=None):
        """Показывает введение в раздел"""
        if user_id is None:
            if update.callback_query:
                user_id = update.callback_query.from_user.id
        else:
            user_id = update.effective_user.id
    
        print(f"🔍 show_section_intro: user_id={user_id}")
    
        session = self.user_sessions.get(user_id)
        if not session:
            await self.start_couple_survey(update, context)
            return
        session = self.user_sessions.get(user_id)
        print("внутри show section")
        if not session:
            await self.start_couple_survey(update, context)
            return
        
        section_index = session['current_section_index']
        if section_index >= len(session['sections_order']):
            await self.complete_survey(update, context, user_id)
            return
        
        section_id = session['sections_order'][section_index]
        section_config = config.SECTIONS_CONFIG[section_id]
        
        # 🔥 ЗАГРУЖАЕМ ВОПРОСЫ ИЗ БАЗЫ ДАННЫХ (как в индивидуальных опросах)
        questions = self.db.get_section_questions(section_id)
        if not questions:
            await self._handle_section_error(update, section_config['name'])
            return
        
        # Обновляем сессию
        session['current_section'] = section_id
        session['current_questions'] = questions
        session['current_question'] = 0
        session['answers'] = {}
        
        # Показываем введение в раздел
        completed_count = len(session['completed_sections'])
        total_sections = len(self.sections_order)
        text= f"Для получения рекомендаций Вам и Вашему партнеру необходимо пройти несколько опросников, состоящие из 7 секций"
        # text = f"📊 *Раздел {section_index + 1}/{total_sections}*\n\n"
        # text += f"**{section_config['name']}**\n"
        # text += f"{section_config['description']}\n\n"
        # text += f"📝 Вопросов в разделе: {len(questions)}\n"
        # text += f"⏱️ Примерное время: {len(questions) * 2} минут\n\n"
        # text += f"🎯 Прогресс: {completed_count}/{total_sections} разделов"
        
        keyboard = [
            [InlineKeyboardButton("📋 Начать опрос", callback_data=f"start_section_{section_id}")],
            [InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
   
    # async def handle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     """Обрабатывает ответ"""
    #     query = update.callback_query
    #     await query.answer()
        
    #     user_id = query.from_user.id
    #     data = query.data.replace('ans1wer_', '')
    #     section, score = data.split('_')
        
    #     # Сохраняем ответ
    #     if user_id in self.user_sessions:
    #         if section not in self.user_sessions[user_id]['answers']:
    #             self.user_sessions[user_id]['answers'][section] = []
    #         self.user_sessions[user_id]['answers'][section].append(int(score))
        
    #     # Показываем следующий вопрос
    #     await self.show_question(update, context, user_id)
    
    async def complete_section(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Завершает раздел"""
        session = self.user_sessions.get(user_id)
        if not session:
            return
        
        # Простая логика перехода между разделами
        sections = ['communication', 'intimacy', 'conflicts', 'goals']
        current_index = sections.index(session['current_section'])
        
        if current_index + 1 < len(sections):
            # Переходим к следующему разделу
            session['current_section'] = sections[current_index + 1]
            await self.show_question(update, context, user_id)
        else:
            # Завершаем опрос
            await self.complete_survey(update, context, user_id)
    
   
    # async def show_couple_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user1_id: int, user2_id: int):
    #     """Показывает результаты пары"""
    #     # Получаем результаты обоих
    #     user1_answers = self.db.get_user_results(user1_id)
    #     user2_answers = self.db.get_user_results(user2_id)
        
    #     # Простой анализ (замени на свою логику)
    #     weak_sections = self._analyze_weak_sections(user1_answers, user2_answers)
        
    #     text = "👫 *Результаты парной диагностики*\n\n"
    #     text += "📊 *Ваши слабые стороны:*\n"
        
    #     for section, score in weak_sections[:3]:
    #         text += f"• {section}: {score}%\n"
        
    #     text += "\n💡 *Рекомендации:*\n"
    #     text += "1. Больше общайтесь о чувствах\n"
    #     text += "2. Уделяйте время совместным занятиям\n"
    #     text += "3. Практикуйте активное слушание\n\n"
    #     text += "💞 Работайте над отношениями вместе!"
        
    #     keyboard = [
    #         [InlineKeyboardButton("📋 Детальные рекомендации", callback_data="detailed_recommendations")],
    #         [InlineKeyboardButton("👫 Профиль пары", callback_data="couple_profile")],
    #         [InlineKeyboardButton("⬅️ В меню", callback_data="couple_menu")]
    #     ]
    #     reply_markup = InlineKeyboardMarkup(keyboard)
        
    #     # Отправляем обоим пользователям
    #     for user_id in [user1_id, user2_id]:
    #         try:
    #             await context.bot.send_message(
    #                 chat_id=user_id,
    #                 text=text,
    #                 reply_markup=reply_markup,
    #                 parse_mode='Markdown'
    #             )
    #         except Exception as e:
    #             print(f"❌ Не удалось отправить результаты {user_id}: {e}")
    
    # def _analyze_weak_sections(self, user1_answers: dict, user2_answers: dict) -> list:
    #     """Простой анализ слабых сторон"""
    #     # Заглушка - замени на реальную логику
    #     return [
    #         ("Коммуникация", 65),
    #         ("Близость", 72), 
    #         ("Решение конфликтов", 58)
    #     ]
    
    async def show_survey_completed(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, partner_id: int):
        """Показывает что опрос уже пройден"""
        partner_completed = self.db.has_completed_survey(partner_id)
        
        if partner_completed:
            text = "✅ *Оба партнера завершили опрос!*\n\n"
            text += "Перейдите в профиль пары чтобы посмотреть результаты."
            keyboard = [[InlineKeyboardButton("👫 Профиль пары", callback_data="couple_profile")]]
        else:
            text = "✅ *Вы уже прошли опрос!*\n\n"
            text += "⏳ Ожидаем, когда ваш партнер завершит диагностику."
            keyboard = [[InlineKeyboardButton("👫 Профиль пары", callback_data="couple_profile")]]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_couple_menu_for_user(self, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показывает меню пары для конкретного пользователя"""
        try:
            from recommendation_handlers import back_to_main
            
            # Создаем простое сообщение с кнопкой рекомендаций
            text = "💑 *Вы в паре!*\n\n" + \
                "Теперь доступны парные рекомендации для совместной работы над отношениями."
            
            keyboard = [
                [InlineKeyboardButton("💫 Мои рекомендации", callback_data="show_recommendations")],
                [InlineKeyboardButton("👫 Профиль пары", callback_data="couple_profile")],
                [InlineKeyboardButton("⬅️ Главное меню", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            print(f"❌ Ошибка показа меню для {user_id}: {e}")

# Глобальный экземпляр
    async def start_section(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начинает конкретный раздел"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        section_id = query.data.replace("start_section_", "")
        
        session = self.user_sessions.get(user_id)
        if not session:
            await self.restart_survey(update, context)
            return
        
        # Обновляем сессию
        session['current_section'] = section_id
        session['current_question'] = 0
        session['answers'] = {}
        
        # Загружаем вопросы для этого раздела ИЗ БАЗЫ
        questions = self.db.get_section_questions(section_id)
        if not questions:
            await self._handle_section_error(update, config.SECTIONS_CONFIG.get(section_id, {}).get('name', section_id))
            return
        
        session['current_questions'] = questions
        await self.show_question(update, context, user_id)
    
    async def show_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Показывает текущий вопрос из базы данных"""
        session = self.user_sessions.get(user_id)
        if not session:
            await self.restart_survey(update, context)
            return
        
        current_index = session['current_question']
        questions = session['current_questions']
        section_id = session['current_section']
        section_config = config.SECTIONS_CONFIG[section_id]
        
        if current_index >= len(questions):
            await self.complete_section(update, context, user_id)
            return
        
        # 🔥 БЕРЕМ ВОПРОС ИЗ БАЗЫ ДАННЫХ
        question = questions[current_index]
        
        # Создаем клавиатуру с вариантами ответов (шкала 1-5)
        keyboard = []
        for i in range(1, 6):
            emoji = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"][i-1]
            keyboard.append([InlineKeyboardButton(
                f"{emoji} {i}", 
                callback_data=f"answer_{section_id}_{question['question_id']}_{i}"
            )])
        
        keyboard.append([InlineKeyboardButton("⬅️ Назад к разделам", callback_data="back_to_sections")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        progress = f"{current_index + 1}/{len(questions)}"
        text = f"📝 *{section_config['name']}* | Вопрос {progress}\n\n"
        text += f"{question['question']}"
        
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает ответ на вопрос"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        callback_data = query.data.replace("answer_", "")
        
        # Парсим данные ответа: section_questionId_answerValue
        parts = callback_data.split("_")
        if len(parts) < 3:
            await query.edit_message_text("❌ Ошибка обработки ответа")
            return
        
        section_id = parts[0]
        question_id = parts[1]
        answer_value = parts[2]
        
        # Сохраняем ответ
        session = self.user_sessions.get(user_id)
        if session and session['current_section'] == section_id:
            session['answers'][question_id] = answer_value
            session['current_question'] += 1
            
            # Удаляем старое сообщение с вопросом
            try:
                await query.delete_message()
            except:
                pass
            
            # Показываем следующий вопрос
            await self.show_question(update, context, user_id)

    # couple_survey.py
    async def complete_survey(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Завершает опрос и проверяет готовность пары"""
        session = self.user_sessions.get(user_id)
        if not session:
            return
        print("внутри complete survey!!!!!!!!!!")
        partner_id = self.db.get_partner_id(user_id)
        
        # Сохраняем индивидуальные результаты
        success = self.db.save_individual_results(user_id, session['section_answers'])
        print("sucersssss")
        if not success:
            print(f"❌ Не удалось сохранить результаты для {user_id}")
        
        # 🔥 ПРОВЕРЯЕМ ПО НОВОМУ МЕТОДУ - surveys_completed В ПАРЕ
        both_completed = self.db.has_both_partners_completed_survey(user_id)
        print(both_completed,"both_completed")
        if both_completed:
            # 🔥 ОБА УЖЕ ЗАВЕРШИЛИ - показываем результаты
            await self.show_couple_results(update, context, user_id, partner_id)
        else:
            # 🔥 ПЕРВЫЙ ИЗ ПАРЫ ЗАВЕРШАЕТ - проверяем стал ли второй
            partner_completed = self.db.has_completed_survey(partner_id) if partner_id else False
            print(partner_completed,"partner_completed")
            if partner_completed:
                # 🔥 ВТОРОЙ ТОЖЕ ЗАВЕРШИЛ - ОТМЕЧАЕМ ПАРУ КАК ЗАВЕРШИВШУЮ
                self.db.mark_couple_survey_completed(user_id, partner_id)
                await self.show_couple_results(update, context, user_id, partner_id)
            else:
                # 🔥 ЖДЕМ ПАРТНЕРА
                text = "✅ *Вы завершили опрос!*\n\n"
                text += "⏳ Ожидаем, когда ваш партнер также завершит диагностику.\n"
                text += "Вы получите уведомление, когда оба будут готовы."
                
                keyboard = [[InlineKeyboardButton("⬅️ В меню", callback_data="couple_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Очищаем сессию
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]


    async def _handle_section_error(self, update: Update, section_name: str):
        """Обрабатывает ошибку загрузки раздела"""
        text = f"❌ *Ошибка загрузки раздела*\n\n"
        text += f"Раздел '{section_name}' временно недоступен.\n"
        text += "Пожалуйста, попробуйте позже."
        
        keyboard = [
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data="start_couple_survey")],
            [InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            

couple_survey = CoupleSurvey()



# Не забудь зарегистрировать хэндлер в __init__:
# application.add_handler(CommandHandler("test_priority", survey_handlers.test_priority_calculation))






    
    