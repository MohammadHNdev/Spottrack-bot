import sys
import os
import asyncio
import logging # ایمپورت ماژول لاگ‌گیری

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode # ایمپورت ParseMode
# ایمپورت کلاس DefaultBotProperties برای تنظیمات پیش‌فرض ربات در نسخه‌های جدید aiogram
from aiogram.client.default import DefaultBotProperties

# ایمپورت ماژول‌های داخلی
from config import settings
from handlers import user
from db import mongo # ایمپورت ماژول دیتابیس

# --- تنظیمات لاگ‌گیری ---
# تنظیمات لاگ‌گیری را در نقطه ورود اصلی برنامه متمرکز می‌کنیم
logging.basicConfig(
    level=logging.INFO, # سطح لاگ‌گیری را از DEBUG به INFO تغییر دادیم
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', # فرمت نمایش لاگ
    stream=sys.stdout # ارسال لاگ به خروجی استاندارد (کنسول)
)
logger = logging.getLogger(__name__) # ایجاد یک لاگر برای این ماژول
# --- پایان تنظیمات لاگ‌گیری ---


# --- توابع Startup و Shutdown ---
async def on_startup(dispatcher: Dispatcher):
    """تابعی که هنگام شروع ربات اجرا می‌شود."""
    logger.info("Bot is starting up...")

    # مقداردهی اولیه و اتصال به دیتابیس MongoDB
    # این تابع ناهمگام است و باید با await فراخوانی شود.
    await mongo.init_db()
    logger.info("Database connection initialized and tested.")

    # می‌توانید تابع cleanup_old_temp_dirs را در اینجا فراخوانی کنید (اختیاری)
    # اگر این تابع همگام است، باید آن را در یک ترد جداگانه اجرا کنید
    # از آنجایی که پوشه موقت در settings تعریف شده، بهتر است تابع cleanup در downloader.py باشد.
    # from services import downloader
    # await asyncio.to_thread(downloader.cleanup_old_temp_dirs, settings.TEMP_DIR) # فرض بر وجود تابع cleanup در downloader.py

    logger.info("Bot is ready to receive messages.")

async def on_shutdown(dispatcher: Dispatcher):
    """تابعی که هنگام خاموش شدن ربات اجرا می‌شود."""
    logger.info("Bot is shutting down...")
    # بستن اتصال دیتابیس
    # تابع close_db در mongo.py ناهمگام است و باید با await فراخوانی شود.
    await mongo.close_db()
    logger.info("Database connection closed.")
    logger.info("Bot shutdown complete.")
# --- پایان توابع Startup و Shutdown ---


async def main():
    # اضافه کردن مسیر پروژه به sys.path برای دسترسی به ماژول‌های داخلی
    # این خط برای اجرای کد در محیط‌های خاص ممکن است لازم باشد.
    # فرض می‌کنیم main.py در ریشه پروژه (spotify_telegram_bot) قرار دارد.
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
         sys.path.append(project_root)
         logger.debug(f"Added {project_root} to sys.path")

    # ایجاد شیء Bot با استفاده از BOT_TOKEN از settings
    # تنظیم ParseMode پیش‌فرض با استفاده از DefaultBotProperties برای سازگاری با aiogram >= 3.7.0
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # ثبت توابع startup و shutdown در دیسپچر
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # اضافه کردن روترهای هندلرها
    dp.include_router(user.router)

    # شروع فرآیند دریافت به‌روزرسانی‌ها (polling)
    # aiogram به صورت خودکار خاموش شدن با وقار را در زمان دریافت سیگنال‌های SIGINT/SIGTERM مدیریت می‌کند
    logger.info("Starting bot polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        # اجرای تابع اصلی ناهمگام
        asyncio.run(main())
    except KeyboardInterrupt:
        # مدیریت خاموش شدن دستی با Ctrl+C
        logger.info("Bot stopped manually by KeyboardInterrupt.")
    except Exception as e:
        # لاگ کردن هر خطای غیرمنتظره دیگر
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)