from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import config
from database import db
from payment import payment_system

# Словарь для отслеживания ожидающих платежей
pending_payments = {}

async def handle_buy_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка покупки подписки"""
    if not update.callback_query:
        return
        
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Проверяем, прошел ли пользователь опросник
    if not db.has_completed_survey(user_id):
        await query.answer("❌ Сначала пройдите опросник", show_alert=True)
        return
    
    # Проверяем, нет ли уже активной подписки
    if db.is_subscription_active(user_id):
        await query.answer("✅ У вас уже есть активная подписка!", show_alert=True)
        return
    
    # Создаем платеж
    payment = payment_system.create_payment(
        user_id=user_id,
        amount=config.SUBSCRIPTION_PRICE,
        description="Подписка на персонализированные рекомендации по отношениям"
    )
    
    if not payment:
        await query.edit_message_text("❌ Ошибка создания платежа. Попробуйте позже.")
        return
    
    # Сохраняем информацию о платеже
    pending_payments[payment.id] = {
        'user_id': user_id,
        'message_id': query.message.message_id
    }
    
    payment_url = payment.confirmation.confirmation_url
    
    # Создаем клавиатуру с кнопками
    keyboard = [
        [InlineKeyboardButton("🔗 Перейти к оплате", url=payment_url)],
        [InlineKeyboardButton("🔄 Проверить оплату", callback_data=f"check_payment_{payment.id}")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем сообщение с информацией о платеже
    await query.edit_message_text(
        f"💳 *Оплата подписки*\n\n"
        f"💰 Сумма: {config.SUBSCRIPTION_PRICE} руб.\n"
        f"📅 Срок: {config.SUBSCRIPTION_DURATION} дней\n"
        f"🎯 Доступ: персонализированные рекомендации\n\n"
        f"🔗 [Ссылка для оплаты]({payment_url})\n\n"
        f"*Инструкция:*\n"
        f"1. Нажмите 'Перейти к оплате'\n"
        f"2. Оплатите подписку\n"
        f"3. Вернитесь в бот и нажмите 'Проверить оплату'",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса оплаты"""
    if not update.callback_query:
        return
        
    query = update.callback_query
    await query.answer()
    
    payment_id = query.data.replace("check_payment_", "")
    
    if payment_id not in pending_payments:
        await query.answer("❌ Платеж не найден", show_alert=True)
        return
    
    # Проверяем статус платежа
    status = payment_system.check_payment_status(payment_id)
    
    if status == "succeeded":
        await _handle_successful_payment(update, context, payment_id)
    elif status == "pending":
        await _handle_pending_payment(update, context, payment_id)
    elif status == "canceled":
        await _handle_canceled_payment(update, context, payment_id)
    else:
        await _handle_failed_payment(update, context, payment_id)

async def _handle_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, payment_id: str):
    """Обработка успешного платежа"""
    payment_data = pending_payments[payment_id]
    user_id = payment_data['user_id']
    
    # Активируем подписку
    db.update_subscription(user_id, config.SUBSCRIPTION_DURATION)
    
    # Удаляем из ожидающих платежей
    del pending_payments[payment_id]
    
    # Получаем информацию о пользователе для персонализации
    user = db.get_user(user_id)
    username = user.get('username', 'пользователь')
    
    # Создаем клавиатуру для следующего шага
    keyboard = [
        [InlineKeyboardButton("💫 Смотреть рекомендации", callback_data="show_recommendations")],
        [InlineKeyboardButton("👤 Мой профиль", callback_data="my_profile")],
        [InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_main")]
    ]
    if db.is_female(user_id):
            keyboard = [
                [InlineKeyboardButton("💫 Смотреть рекомендации", callback_data="show_recommendations")],
                 [InlineKeyboardButton("👤 Мой профиль", callback_data="my_profile")],
                 [InlineKeyboardButton("🔥 Либидо", callback_data="show_libido_menu")],
                 [InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_main")]


            ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем сообщение об успехе
    await update.callback_query.edit_message_text(
        f"🎉 *Поздравляем!*\n\n"
        f"✅ *Оплата прошла успешно!*\n\n"
        f"✨ Теперь вам доступны:\n"
        f"• Персонализированные рекомендации\n"
        f"• Материалы по улучшению отношений\n"
        f"• Экспертные советы и методики\n\n"
        f"⏰ Рекомендации будут приходить по одной каждые 10 секунд "
        f"для лучшего усвоения материала.\n\n"
        f"💡 *Совет:* Начните с раздела рекомендаций, чтобы увидеть "
        f"персональную программу для ваших отношений!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def _handle_pending_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, payment_id: str):
    """Обработка ожидающего платежа"""
    payment_data = pending_payments[payment_id]
    
    keyboard = [
        [InlineKeyboardButton("🔄 Проверить еще раз", callback_data=f"check_payment_{payment_id}")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "⏳ *Платеж обрабатывается*\n\n"
        "Банк обрабатывает вашу операцию. Это может занять несколько минут.\n\n"
        "Пожалуйста, подождите и проверьте статус через пару минут.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def _handle_canceled_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, payment_id: str):
    """Обработка отмененного платежа"""
    del pending_payments[payment_id]
    
    keyboard = [
        [InlineKeyboardButton("💳 Попробовать снова", callback_data="buy_subscription")],
        [InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "❌ *Платеж отменен*\n\n"
        "Вы отменили платеж или время для оплаты истекло.\n\n"
        "Вы можете попробовать оплатить подписку снова.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def _handle_failed_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, payment_id: str):
    """Обработка неудачного платежа"""
    if payment_id in pending_payments:
        del pending_payments[payment_id]
    
    keyboard = [
        [InlineKeyboardButton("💳 Попробовать снова", callback_data="buy_subscription")],
        [InlineKeyboardButton("🆘 Помощь", callback_data="help_payment")],
        [InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "❌ *Платеж не прошел*\n\n"
        "Возможные причины:\n"
        "• Недостаточно средств на карте\n"
        "• Карта не поддерживает онлайн-платежи\n"
        "• Превышен лимит операций\n"
        "• Техническая ошибка банка\n\n"
        "Попробуйте использовать другую карту или обратитесь в ваш банк.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_help_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь по оплате"""
    if not update.callback_query:
        return
        
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("💳 Попробовать снова", callback_data="buy_subscription")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🆘 *Помощь по оплате*\n\n"
        "Если у вас возникают проблемы с оплатой:\n\n"
        "1. *Проверьте карту:*\n"
        "   - Достаточно ли средств\n"
        "   - Поддерживает ли онлайн-платежи\n"
        "   - Не заблокирована ли для интернет-платежей\n\n"
        "2. *Попробуйте другую карту*\n"
        "   - Кредитную или дебетовую другого банка\n\n"
        "3. *Обратитесь в банк:*\n"
        "   - Уточните лимиты на онлайн-платежи\n"
        "   - Проверьте, не блокирует ли банк операцию\n\n"
        "4. *Технические проблемы:*\n"
        "   - Попробуйте позже\n"
        "   - Перезагрузите приложение\n\n"
        "Если проблемы сохраняются, напишите в поддержку.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def cleanup_expired_payments():
    """Очистка просроченных платежей (можно запускать по расписанию)"""
    expired_payments = []
    # Здесь можно добавить логику очистки старых платежей
    for payment_id, payment_data in pending_payments.items():
        # Логика определения просроченных платежей
        pass
    
    for payment_id in expired_payments:
        del pending_payments[payment_id]
    
    return len(expired_payments)

def get_pending_payments_count():
    """Возвращает количество ожидающих платежей"""
    return len(pending_payments)