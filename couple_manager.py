# couple_manager.py
import secrets
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database_couples import DatabaseCouples  # твой отдельный модуль
import config
import recommendation_handlers as rec_handlers

class CoupleManager:
    def __init__(self):
        self.db = DatabaseCouples()
    
    def generate_invite_link(self, user_id: int) -> str:
        """Генерирует уникальную ссылку-приглашение"""
        token = secrets.token_urlsafe(16)
        
        # Сохраняем приглашение в БД
        self.db.create_invite(user_id, token)
        
        # Формируем ссылку для Telegram
        bot_username = config.BOT_USERNAME
        invite_link = f"https://t.me/{bot_username}?start=invite_{token}"
        
        return invite_link
    async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает команду /start с параметрами"""
        if context.args and context.args[0].startswith('invite_'):
            token = context.args[0].replace('invite_', '')
            
            await self.handle_invite_start(update, context, token)
        else:
            await show_main_menu(update, context)
        
    async def handle_invite_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE, token: str):
        """Обрабатывает переход по ссылке-приглашению"""
        user_id = update.effective_user.id
        await rec_handlers.show_gender_selection1(update, context)
        print("внутри handle invite start")
        # Проверяем валидность токена
        invite_data = self.db.get_invite_by_token(token)
        if not invite_data:
            await update.message.reply_text("❌ Ссылка недействительна или устарела.")
            return
        
        inviter_id = invite_data['user_id']
        
        # Проверяем, не пытается ли пользователь добавить сам себя
        if user_id == inviter_id:
            await update.message.reply_text("❌ Нельзя добавить самого себя в качестве партнера.")
            return
        
        # Проверяем, нет ли уже пары у пользователей
        if self.db.has_partner(user_id) or self.db.has_partner(inviter_id):
            await update.message.reply_text("❌ У одного из пользователей уже есть партнер.")
            return
        
        # Показываем подтверждение
        inviter_info = self.db.get_user_info(inviter_id)
        inviter_name = inviter_info.get('first_name', 'Пользователь') if inviter_info else 'Пользователь'
        
        text = f"👫 *Приглашение в пару*\n\n"
        text += f"Пользователь *{inviter_name}* приглашает вас стать партнерами в боте.\n\n"
        text += "После подтверждения вы сможете:\n"
        text += "• Проходить совместные диагностики\n"
        text += "• Получать общие рекомендации\n"
        text += "• Сравнивать результаты\n"
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Принять приглашение", callback_data=f"accept_invite_{token}"),
                InlineKeyboardButton("❌ Отклонить", callback_data="decline_invite")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def accept_invite(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает принятие приглашения"""
        query = update.callback_query
        await query.answer()
        
        # ИЗВЛЕКАЕМ ТОКЕН ИЗ callback_data
        # callback_data выглядит как: "accept_invite_AbC123def456"
        token = query.data.replace("accept_invite_", "")
        print(f"🔍 Пользователь принимает приглашение с токеном: {token}")
        
        user_id = query.from_user.id
        
        # Теперь можем найти приглашение в БД по токену
        invite_data = self.db.get_invite_by_token(token)
        if not invite_data:
            await query.edit_message_text("❌ Приглашение недействительно или устарело.")
            return
        
        inviter_id = invite_data['user_id']
        
        # Создаем пару
        success = self.db.create_couple(inviter_id, user_id)
        if success:
            await self._notify_couple_created(context, inviter_id, user_id)
            await query.edit_message_text("✅ Вы успешно стали партнерами!")
        else:
            await query.edit_message_text("❌ Произошла ошибка при создании пары.")
    async def _notify_couple_created(self, context: ContextTypes.DEFAULT_TYPE, user1_id: int, user2_id: int):
        """Уведомляет обоих пользователей о создании пары"""
        user1_info = self.db.get_user_info(user1_id)
        user2_info = self.db.get_user_info(user2_id)
        
        user1_name = user1_info.get('first_name', 'Партнер') if user1_info else 'Партнер'
        user2_name = user2_info.get('first_name', 'Партнер') if user2_info else 'Партнер'
        
        # Уведомление первому пользователю
        text1 = f"✅ *Пара создана!*\n\nВы теперь в паре с *{user2_name}*.\n\n"
        text1 += "Теперь вы можете пройти совместную диагностику отношений."
        
        keyboard = [
            [InlineKeyboardButton("📊 Пройти диагностику", callback_data="start_couple_survey")],
            [InlineKeyboardButton("👫 Профиль пары", callback_data="couple_profile")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await context.bot.send_message(
                chat_id=user1_id,
                text=text1,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"❌ Не удалось уведомить пользователя {user1_id}: {e}")
        
        # Уведомление второму пользователю
        text2 = f"✅ *Пара создана!*\n\nВы теперь в паре с *{user1_name}*.\n\n"
        text2 += "Теперь вы можете пройти совместную диагностику отношений."
        
        try:
            await context.bot.send_message(
                chat_id=user2_id,
                text=text2,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"❌ Не удалось уведомить пользователя {user2_id}: {e}")
    
    async def show_couple_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает меню работы с парой СО СТАТУСОМ ОПРОСА"""
        user_id = update.effective_user.id
        
        if self.db.has_partner(user_id):
            partner_id = self.db.get_partner_id(user_id)
            partner_completed = self.db.has_completed_survey(partner_id)
            user_completed = self.db.has_completed_survey(user_id)
            
            partner_info = self.db.get_user_info(partner_id)
            partner_name = partner_info.get('first_name', 'Партнер') if partner_info else 'Партнер'
            
            text = f"👫 *Профиль пары*\n\n"
            text += f"💑 *Вы + {partner_name}*\n\n"
            text += f"📊 *Статус опросников:*\n"
            text += f"• Вы: {'✅ Завершено' if user_completed else '❌ Не завершено'}\n"
            text += f"• {partner_name}: {'✅ Завершено' if partner_completed else '❌ Не завершено'}\n\n"
            
            if user_completed and partner_completed:
                text += "🎉 Оба партнера завершили опрос! Доступны парные рекомендации."
                keyboard = [
                    [InlineKeyboardButton("💫 Получить рекомендации", callback_data="show_recommendations")],
                    [InlineKeyboardButton("👫 Обновить статус", callback_data="start_couple_menu")],
                    [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
                ]
            else:
                text += "⏳ Для парных рекомендаций необходимо, чтобы оба партнера прошли опросник."
                keyboard = [
                    [InlineKeyboardButton("📊 Пройти опросник", callback_data="start_couple_survey")],
                    [InlineKeyboardButton("👫 Обновить статус", callback_data="start_couple_menu")],
                    [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
                ]
        else:
            text = "👫 *Управление парой*\n\n"
            text += "Добавьте партнера для совместной работы над отношениями."
            keyboard = [
                [InlineKeyboardButton("🔗 Создать приглашение", callback_data="create_invite_link")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    def _get_couple_profile_text(self, user_id: int) -> str:
        """Генерирует текст профиля пары"""
        partner_id = self.db.get_partner_id(user_id)
        if not partner_id:
            return "👫 У вас пока нет пары."
        
        user_info = self.db.get_user_info(user_id)
        partner_info = self.db.get_user_info(partner_id)
        
        user_name = user_info.get('first_name', 'Вы') if user_info else 'Вы'
        partner_name = partner_info.get('first_name', 'Партнер') if partner_info else 'Партнер'
        
        text = f"👫 *Профиль пары*\n\n"
        text += f"💑 *{user_name}* + *{partner_name}*\n\n"
        text += "✅ Вы в паре! Теперь можете пройти совместную диагностику."
        
        return text
    
    async def create_invite_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Создает ссылку-приглашение"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # Проверяем, нет ли уже партнера
        if self.db.has_partner(user_id):
            await query.edit_message_text("❌ У вас уже есть партнер.")
            return
        
        # Генерируем ссылку
        invite_link = self.generate_invite_link(user_id)
        
        text = "👫 *Приглашение партнера*\n\n"
        text += "Отправьте эту ссылку вашему партнеру:\n\n"
        text += f"`{invite_link}`\n\n"
        text += "📋 *Инструкция:*\n"
        text += "1. Отправьте ссылку партнеру\n"
        text += "2. Партнер должен открыть бот, выбрать пол и затем перейти по ссылке\n"
        text += "3. Он подтвердит приглашение в боте\n"
        text += "4. Вы получите уведомление о создании пары\n\n"
        text += "⏳ Ссылка действительна 24 часа"
        
        keyboard = [
            [InlineKeyboardButton("⬅️ Назад", callback_data="couple_menu")],
            [InlineKeyboardButton("📤 Поделиться ссылкой", 
                               url=f"https://t.me/share/url?url={invite_link}&text=Присоединяйся%20ко%20мне%20в%20боте%20для%20работы%20над%20отношениями!")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# Глобальный экземпляр менеджера пар
couple_manager = CoupleManager()