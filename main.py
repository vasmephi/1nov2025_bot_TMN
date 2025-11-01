from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import config
from database import db
import survey_handlers
import recommendation_handlers as rec_handlers
import libido_handlers
import payment_handlers
from scheduler import scheduler
from scheduler import ExtendedScheduler as extended_scheduler
from couple_survey import couple_survey
from couple_manager import couple_manager
from libido_handlers import LibidoHandlers

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает команду /start с параметрами"""
    if context.args and context.args[0].startswith('invite_'):
        token = context.args[0].replace('invite_', '')
        await couple_manager.handle_invite_start(update, context, token)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    
    # ДОБАВЬ ЭТУ ПРОВЕРКУ В САМОЕ НАЧАЛО твоей функции start:
    print(f"🔍 Кто-то запустил бота. Args: {context.args}")
    
    # ЕСЛИ ЕСТЬ ПРИГЛАШЕНИЕ - обрабатываем его
    if context.args and context.args[0].startswith('invite_'):
        token = context.args[0].replace('invite_', '')
        print(f"🔍 Обнаружено приглашение! Токен: {token}")
        await couple_manager.handle_invite_start(update, context, token)
        return  # ВАЖНО: выходим после обработки приглашения
 
    await rec_handlers.back_to_main(update, context)

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текстовый ввод для кастомного расписания"""
    await rec_handlers.handle_custom_schedule_input(update, context)

def main():
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Основные команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test_priority", survey_handlers.test_priority_calculation))
    application.add_handler(CommandHandler("quick_test", survey_handlers.quick_test_priority))

    # Обработчики выбора пола
    application.add_handler(CallbackQueryHandler(rec_handlers.handle_gender_selection, pattern="^gender_"))
    application.add_handler(CallbackQueryHandler(rec_handlers.handle_gender_selection1, pattern="^g1ender_"))
    

    application.add_handler(CallbackQueryHandler(couple_manager.show_couple_menu, pattern="^start_couple_menu$"))
    application.add_handler(CallbackQueryHandler(couple_manager.show_couple_menu, pattern="^couple_profile$"))
    application.add_handler(CallbackQueryHandler(couple_manager.create_invite_link, pattern="^create_invite_link$"))
    application.add_handler(CallbackQueryHandler(couple_manager.accept_invite, pattern="^accept_invite_"))

        # Обработчики опросника
    application.add_handler(CallbackQueryHandler(couple_survey.start_couple_survey, pattern="^start_couple_survey$"))
    #application.add_handler(CallbackQueryHandler(couple_survey.handle_answer, pattern="^ans1wer_"))
    #application.add_handler(CallbackQueryHandler(couple_survey.start_section, pattern="^start_section_"))

    application.add_handler(CallbackQueryHandler(survey_handlers.survey_manager.start_survey, pattern="^start_survey$"))
    application.add_handler(CallbackQueryHandler(survey_handlers.survey_manager.handle_answer, pattern="^answer_"))
    application.add_handler(CallbackQueryHandler(survey_handlers.survey_manager.restart_survey, pattern="^restart_survey$"))
    application.add_handler(CallbackQueryHandler(survey_handlers.survey_manager.start_section, pattern="^start_section_"))
    application.add_handler(CallbackQueryHandler(survey_handlers.survey_manager.skip_section, pattern="^skip_section_"))
    application.add_handler(CallbackQueryHandler(survey_handlers.survey_manager.complete_all_sections, pattern="^complete_all_sections$"))
    application.add_handler(CallbackQueryHandler(survey_handlers.survey_manager.show_section_intro, pattern="^back_to_sections$"))

    application.add_handler(CallbackQueryHandler(LibidoHandlers.request_day_input, pattern='libido_enter_day$'))
    application.add_handler(CallbackQueryHandler(LibidoHandlers.handle_libido_questionnaire, pattern='^libido_q_'))
    application.add_handler(CallbackQueryHandler(LibidoHandlers.handle_libido_day_navigation, pattern='^libido_(prev|next)_day$'))
    application.add_handler(CallbackQueryHandler(LibidoHandlers.handle_libido_article_navigation, pattern='^libido_(prev|next)_article$'))
    application.add_handler(CallbackQueryHandler(LibidoHandlers.handle_libido_selection, pattern='^libido_'))
            
    application.add_handler(CallbackQueryHandler(LibidoHandlers.handle_questionnaire_answer, pattern='^ans_'))
    application.add_handler(CallbackQueryHandler(LibidoHandlers.cancel_questionnaire, pattern='^cancel_questionnaire$'))
    application.add_handler(CallbackQueryHandler(LibidoHandlers.handle_libido_pre_intimacy, pattern='^l1ibido_pre_intimacy$'))
    application.add_handler(CallbackQueryHandler(LibidoHandlers.show_breathing_exercises, pattern='^l1ibido_breathing$'))
    application.add_handler(CallbackQueryHandler(LibidoHandlers.show_mindfulness_exercises, pattern='^l1ibido_mindfulness$'))
    application.add_handler(CallbackQueryHandler(LibidoHandlers.show_couple_exercises, pattern='^l1ibido_couple$'))
    application.add_handler(CallbackQueryHandler(LibidoHandlers.show_exercise_details, pattern='^libido_exercise_'))


    application.add_handler(CallbackQueryHandler(LibidoHandlers.show_simple_exercises, pattern='^l1ibido_simple_exercises$'))
    application.add_handler(CallbackQueryHandler(LibidoHandlers.handle_day_navigation, pattern='^l1ibido_(prev|next)_day$'))
    application.add_handler(CallbackQueryHandler(LibidoHandlers.choose_specific_day, pattern='^l1ibido_choose_day$'))
    application.add_handler(CallbackQueryHandler(LibidoHandlers.handle_specific_day, pattern='^l1ibido_day_'))






    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'^\d+$'), LibidoHandlers.process_day_input))

    # Обработчики платежей
    application.add_handler(CallbackQueryHandler(payment_handlers.handle_buy_subscription, pattern="^buy_subscription$"))
    application.add_handler(CallbackQueryHandler(payment_handlers.handle_check_payment, pattern="^check_payment_"))
    application.add_handler(CallbackQueryHandler(payment_handlers.handle_help_payment, pattern="^help_payment$"))
    
    # Обработчики рекомендаций и расписания
    application.add_handler(CallbackQueryHandler(rec_handlers.show_recommendations_menu, pattern="^(show_recommendations|get_recommendations)$"))
    application.add_handler(CallbackQueryHandler(rec_handlers.start_reading_recommendations, pattern="^start_reading_recommendations$"))
    application.add_handler(CallbackQueryHandler(rec_handlers.stop_recommendations, pattern="^stop_recommendations$"))
    application.add_handler(CallbackQueryHandler(rec_handlers.show_schedule_settings, pattern="^schedule_settings$"))
    application.add_handler(CallbackQueryHandler(rec_handlers.handle_schedule_selection, pattern="^schedule_"))
    application.add_handler(CallbackQueryHandler(rec_handlers.request_movie_recommendation, pattern="^request_movie$"))
    application.add_handler(CallbackQueryHandler(rec_handlers.request_book_recommendation, pattern="^request_book$"))
    
    # Обработчик текстового ввода для кастомного расписания
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
    
    # Обработчики раздела либидо
    application.add_handler(CallbackQueryHandler(LibidoHandlers.show_libido_menu, pattern="^show_libido_menu$"))

    application.add_handler(CallbackQueryHandler(libido_handlers.start_reading_libido, pattern="^start_reading_libido$"))
    application.add_handler(CallbackQueryHandler(libido_handlers.stop_libido, pattern="^stop_libido$"))
    application.add_handler(CallbackQueryHandler(libido_handlers.restart_libido, pattern="^restart_libido$"))
    
    # Обработчики навигации
    application.add_handler(CallbackQueryHandler(rec_handlers.back_to_main, pattern="^back_to_main$"))
    application.add_handler(CallbackQueryHandler(rec_handlers.show_my_profile, pattern="^my_profile$"))
        
    print("💑 Бот по семейным отношениям запущен!")
    print("⏰ Система расписания рекомендаций активирована")
    application.run_polling()

if __name__ == "__main__":
    main()