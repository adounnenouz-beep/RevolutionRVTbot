import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import config
import handlers
from handlers import start, start_tap, tap_click, tap_end_early, daily, wheel, wheel_result, stats, referral, ad_confirm, roadmap

def main():
    # إنشاء تطبيق البوت
    app = Application.builder().token(config.BOT_TOKEN).build()

    # الأوامر الأساسية
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("roadmap", roadmap))
    
    # أزرار الضغط (CallbackQuery)
    app.add_handler(CallbackQueryHandler(start_tap, pattern="^start_tap$"))
    app.add_handler(CallbackQueryHandler(tap_click, pattern="^tap_click_"))
    app.add_handler(CallbackQueryHandler(tap_end_early, pattern="^tap_end$"))
    app.add_handler(CallbackQueryHandler(daily, pattern="^daily$"))
    app.add_handler(CallbackQueryHandler(wheel, pattern="^wheel$"))
    app.add_handler(CallbackQueryHandler(stats, pattern="^stats$"))
    app.add_handler(CallbackQueryHandler(referral, pattern="^referral$"))
    app.add_handler(CallbackQueryHandler(ad_confirm, pattern="^ad_confirm_"))
    
    # استقبال بيانات العجلة القادمة من WebApp (Netlify)
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, wheel_result))

    print("🚀 البوت يعمل الآن...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
