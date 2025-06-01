import logging
import asyncio
from datetime import datetime, timedelta, timezone

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import OperationFailure # اضافه کردن این ایمپورت برای مدیریت خطای OperationFailure

from config import settings

logger = logging.getLogger(__name__)

# متغیر سراسری برای نگهداری کلاینت و دیتابیس موتور
client: AsyncIOMotorClient = None
db = None

async def init_db():
    """
    مقداردهی اولیه اتصال به دیتابیس MongoDB با استفاده از موتور.
    """
    global client, db
    try:
        # استفاده از URL اتصال از تنظیمات
        client = AsyncIOMotorClient(settings.MONGO_URI)
        # انتخاب دیتابیس بر اساس نام دیتابیس از تنظیمات
        db = client[settings.MONGO_DB_NAME]

        # تست اتصال با اجرای یک دستور ساده
        await db.command('ping')
        logger.info("MongoDB connection successful.")

        # اطمینان از وجود ایندکس‌ها (اختیاری اما توصیه می‌شود)
        # مثال: ایندکس روی user_id در کالکشن users
        # فرض می‌کنیم user_id در کالکشن users به صورت عدد صحیح است
        await db.users.create_index("user_id", unique=True, background=True)
        # مثال: ایندکس روی track_id در کالکشن archived_tracks
        await db.archived_tracks.create_index("track_id", unique=True, background=True)
        # اضافه کردن ایندکس برای user_id در vip_users
        # بر اساس تصویر دیتابیس شما، user_id در vip_users به صورت رشته است، پس ایندکس هم باید روی رشته باشد
        await db.vip_users.create_index("user_id", unique=True, background=True)
        logger.info("MongoDB indexes ensured.")

    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}", exc_info=True)
        # در صورت عدم اتصال، برنامه باید متوقف شود یا با حالت محدود ادامه یابد
        # در اینجا، استثنا را دوباره پرتاب می‌کنیم تا مشکل مشخص شود
        raise

async def close_db():
    """
    بستن اتصال به دیتابیس MongoDB.
    """
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed.")

# --- توابع مربوط به کاربران ---

async def get_user(user_id: int):
    """
    کاربر را بر اساس user_id از دیتابیس دریافت می‌کند.
    اگر کاربر وجود نداشته باشد، None برمی‌گرداند.
    """
    if db is None:
        logger.error("Database not initialized in get_user.")
        return None
    try:
        # فرض می‌کنیم user_id در کالکشن users به صورت عدد صحیح است
        user = await db.users.find_one({"user_id": user_id})
        logger.debug(f"Fetched user {user_id} from 'users' collection: {user}")
        return user
    except Exception as e:
        logger.error(f"Error fetching user {user_id} from 'users': {e}", exc_info=True)
        return None


async def add_user(user_id: int):
    """
    کاربر جدیدی را به دیتابیس اضافه می‌کند.
    """
    if db is None:
        logger.error("Database not initialized in add_user.")
        return
    try:
        # بررسی وجود کاربر قبل از اضافه کردن
        # فرض می‌کنیم user_id در کالکشن users به صورت عدد صحیح است
        existing_user = await db.users.find_one({"user_id": user_id})
        if existing_user:
            logger.debug(f"User {user_id} already exists in 'users' collection.")
            return # کاربر از قبل وجود دارد، نیازی به اضافه کردن نیست

        user_data = {
            "user_id": user_id,
            "language": settings.DEFAULT_LANGUAGE,
            "is_vip": False, # پیش‌فرض False است، مگر اینکه در vip_users باشد یا دستی تنظیم شود
            "daily_downloads": [],
            "total_downloads": 0,
            "joined_at": datetime.now(timezone.utc) # ذخیره زمان پیوستن با منطقه زمانی UTC
        }
        await db.users.insert_one(user_data)
        logger.info(f"User {user_id} added to 'users' collection.")
    except Exception as e:
        logger.error(f"Error adding user {user_id} to 'users': {e}", exc_info=True)


async def update_user_language(user_id: int, language: str):
    """
    زبان کاربر را در دیتابیس به‌روزرسانی می‌کند.
    """
    if db is None:
        logger.error("Database not initialized in update_user_language.")
        return
    try:
        # فرض می‌کنیم user_id در کالکشن users به صورت عدد صحیح است
        result = await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"language": language}}
        )
        if result.matched_count > 0:
            logger.debug(f"User {user_id} language updated to {language}.")
        else:
            logger.warning(f"Could not find user {user_id} to update language.")
    except Exception as e:
        logger.error(f"Error updating language for user {user_id}: {e}", exc_info=True)


async def is_vip(user_id: int) -> bool:
    """
    وضعیت VIP کاربر را بررسی می‌کند.
    ابتدا فیلد 'is_vip' در کالکشن 'users' را بررسی می‌کند،
    سپس وجود کاربر در کالکشن 'vip_users' و تاریخ انقضای آن را چک می‌کند.
    """
    logger.debug(f"Checking VIP status for user_id: {user_id}") # لاگ شروع تابع

    if db is None:
        logger.error("Database not initialized in is_vip.")
        return False

    # 1. بررسی فیلد 'is_vip' در کالکشن 'users' (برای سازگاری با روش‌های قبلی یا دستی)
    # این بخش را نگه می‌داریم مگر اینکه بخواهید داشبورد تنها منبع تعیین VIP باشد.
    # فرض می‌کنیم user_id در کالکشن users به صورت عدد صحیح است
    try:
        user_doc = await db.users.find_one({"user_id": user_id})
        if user_doc and user_doc.get("is_vip", False) is True:
            logger.debug(f"User {user_id} is VIP based on 'users' collection flag.")
            return True
    except Exception as e:
        logger.error(f"Error checking 'users' collection for user {user_id}: {e}", exc_info=True)
        # در صورت خطا در این مرحله، ادامه می‌دهیم تا کالکشن vip_users را چک کنیم

    # 2. بررسی وجود کاربر در کالکشن 'vip_users' و چک کردن تاریخ انقضا
    try:
        # نکته مهم: user_id در MongoDB در کالکشن vip_users به صورت رشته ذخیره شده است
        # در حالی که user_id از تلگرام عدد صحیح است.
        # مطمئن شوید که نوع داده user_id در کوئری با نوع داده آن در دیتابیس مطابقت دارد.
        # بر اساس تصویر دیتابیس شما، user_id در vip_users به صورت رشته است، پس آن را به رشته تبدیل می‌کنیم:
        vip_entry = await db.vip_users.find_one({"user_id": str(user_id)}) # <--- اصلاح شده به str(user_id)

        logger.debug(f"MongoDB query for vip_users with user_id {user_id} (as string) returned: {vip_entry}") # لاگ نتیجه کوئری

        if vip_entry:
            end_date_str = vip_entry.get("end_date")
            logger.debug(f"Found VIP entry for user {user_id}. end_date_str: {end_date_str}") # لاگ تاریخ انقضا

            if end_date_str:
                try:
                    # فرض می‌کنیم end_date_str به فرمت 'YYYY-MM-DD' میلادی ذخیره شده است
                    # تبدیل رشته تاریخ به شیء date میلادی
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                    logger.debug(f"Parsed end_date: {end_date}") # لاگ تاریخ انقضای پارس شده

                    # دریافت تاریخ امروز (فقط تاریخ، بدون زمان)
                    now_date = datetime.now().date()
                    logger.debug(f"Current date: {now_date}") # لاگ تاریخ امروز

                    # مقایسه تاریخ انقضا با تاریخ امروز
                    if end_date >= now_date:
                        logger.debug(f"User {user_id} is VIP. End date ({end_date}) is >= current date ({now_date}).")
                        return True
                    else:
                        logger.debug(f"User {user_id} VIP expired. End date ({end_date}) is < current date ({now_date}).")
                        return False
                except (ValueError, TypeError) as e:
                    logger.error(f"Error parsing VIP end_date '{end_date_str}' for user {user_id}: {e}", exc_info=True)
                    # در صورت خطا در بررسی تاریخ، فرض می‌کنیم VIP معتبر نیست
                    return False
            else:
                # اگر فیلد end_date وجود ندارد اما سند وجود دارد (وضعیت نامشخص)
                logger.warning(f"VIP entry found for user {user_id} but 'end_date' is missing.")
                return False # یا True بسته به منطق کسب و کار شما برای این حالت

    except OperationFailure as e:
        logger.error(f"MongoDB Operation Error in is_vip for user {user_id}: {e}", exc_info=True)
        return False # در صورت خطای دیتابیس، فرض می‌کنیم VIP نیست
    except Exception as e:
        logger.error(f"An unexpected error occurred in is_vip for user {user_id}: {e}", exc_info=True)
        return False # در صورت خطای غیرمنتظره، فرض می‌کنیم VIP نیست


async def increment_download_count(user_id: int):
    """
    تعداد دانلودهای کاربر را افزایش داده و زمان دانلود را ثبت می‌کند.
    """
    if db is None:
        logger.error("Database not initialized in increment_download_count.")
        return
    try:
        # از $push برای اضافه کردن زمان دانلود جدید و از $slice برای نگه داشتن فقط N مورد آخر استفاده می‌کنیم
        # این کار باعث می‌شود آرایه daily_downloads بیش از حد بزرگ نشود.
        # فرض می‌کنیم می‌خواهیم فقط دانلودهای 24 ساعت گذشته را نگه داریم، اما برای اطمینان بیشتر
        # می‌توانیم تعداد بیشتری را نگه داریم و سپس در get_today_downloads فیلتر کنیم.
        # یا می‌توانیم فقط دانلودهای 24 ساعت گذشته را با $pull پاک کنیم (همانطور که قبلاً اشاره شد).
        # روش فعلی (فقط اضافه کردن و فیلتر در get_today_downloads) ساده‌تر است.
        # اگر می‌خواهید لیست را محدود کنید، می‌توانید از $push با $slice استفاده کنید:
        # await db.users.update_one(
        #     {"user_id": user_id},
        #     {
        #         "$inc": {"total_downloads": 1},
        #         "$push": {
        #             "daily_downloads": {
        #                 "$each": [datetime.now(timezone.utc)],
        #                 "$slice": -100 # مثال: فقط 100 دانلود آخر را نگه دار
        #             }
        #         }
        #     }
        # )
        # یا فقط اضافه کردن:
        # فرض می‌کنیم user_id در کالکشن users به صورت عدد صحیح است
        result = await db.users.update_one(
            {"user_id": user_id},
            {
                "$inc": {"total_downloads": 1},
                "$push": {"daily_downloads": datetime.now(timezone.utc)} # ذخیره زمان دانلود با منطقه زمانی UTC
            }
        )
        if result.matched_count > 0:
            logger.debug(f"Download count incremented and timestamp added for user {user_id}.")
        else:
            logger.warning(f"Could not find user {user_id} to increment download count.")
    except Exception as e:
        logger.error(f"Error incrementing download count for user {user_id}: {e}", exc_info=True)


async def get_today_downloads(user_id: int) -> int:
    """
    تعداد دانلودهای کاربر در ۲۴ ساعت گذشته را برمی‌گرداند.
    """
    if db is None:
        logger.error("Database not initialized in get_today_downloads.")
        return 0

    try:
        # فرض می‌کنیم user_id در کالکشن users به صورت عدد صحیح است
        user = await get_user(user_id)
        if not user or "daily_downloads" not in user:
            logger.debug(f"User {user_id} not found or has no daily_downloads.")
            return 0

        # محاسبه زمان ۲۴ ساعت پیش نسبت به زمان فعلی UTC
        twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
        logger.debug(f"Calculating downloads since: {twenty_four_hours_ago}")

        recent_downloads_count = 0
        # اطمینان از اینکه daily_downloads یک لیست است
        daily_downloads = user.get("daily_downloads", [])
        if not isinstance(daily_downloads, list):
            logger.error(f"daily_downloads field for user {user_id} is not a list: {daily_downloads}")
            return 0

        for d in daily_downloads:
            if isinstance(d, datetime):
                # اگر تاریخ naive بود، آن را به عنوان UTC در نظر بگیر
                if d.tzinfo is None:
                    d_aware = d.replace(tzinfo=timezone.utc)
                    # logger.debug(f"Converted naive datetime {d} to aware {d_aware}") # این لاگ ممکن است خیلی زیاد باشد
                else:
                    d_aware = d # تاریخ از قبل aware است

                # مقایسه تاریخ آگاه از منطقه زمانی
                if d_aware > twenty_four_hours_ago:
                    recent_downloads_count += 1
            else:
                logger.warning(f"Found non-datetime entry in daily_downloads for user {user_id}: {d}")


        logger.debug(f"Found {recent_downloads_count} recent downloads for user {user_id}")

        # (اختیاری) پاکسازی ورودی‌های قدیمی‌تر از ۲۴ ساعت از لیست daily_downloads
        # این کار باعث می‌شود لیست بیش از حد بزرگ نشود.
        # این عملیات را می‌توان به صورت ناهمگام در پس‌زمینه انجام داد یا در زمان‌های مشخص اجرا کرد.
        # برای سادگی در این مثال، فقط تعداد را محاسبه می‌کنیم.
        # اگر نیاز به پاکسازی دارید، می‌توانید از $pull در update_one استفاده کنید.
        # مثال:
        # await db.users.update_one(
        #     {"user_id": user_id},
        #     {"$pull": {"daily_downloads": {"$lt": twenty_four_hours_ago}}}
        # )
        # logger.debug(f"Cleaned up old download timestamps for user {user_id}")


        return recent_downloads_count
    except Exception as e:
        logger.error(f"Error getting today's downloads for user {user_id}: {e}", exc_info=True)
        return 0


# --- توابع مربوط به آرشیو آهنگ‌ها ---

async def archive_track(track_id: str, file_id: str):
    """
    اطلاعات آهنگ دانلود شده را در کالکشن آرشیو ذخیره می‌کند.
    اگر آهنگ از قبل وجود داشته باشد، file_id آن را به‌روزرسانی می‌کند.
    """
    if db is None:
        logger.error("Database not initialized in archive_track.")
        return
    try:
        result = await db.archived_tracks.update_one(
            {"track_id": track_id},
            {"$set": {"file_id": file_id, "archived_at": datetime.now(timezone.utc)}}, # ذخیره زمان آرشیو با منطقه زمانی UTC
            upsert=True
        )
        if result.upserted_id:
            logger.info(f"Track {track_id} archived with file_id {file_id}.")
        elif result.matched_count > 0:
             logger.info(f"Track {track_id} updated with new file_id {file_id}.")
        else:
             logger.warning(f"Archive track operation for {track_id} did not match or upsert.")
    except Exception as e:
        logger.error(f"Error archiving track {track_id}: {e}", exc_info=True)


async def get_archived_track(track_id: str):
    """
    اطلاعات آهنگ آرشیو شده را بر اساس track_id دریافت می‌کند.
    اگر آهنگ در آرشیو نباشد، None برمی‌گرداند.
    """
    if db is None:
        logger.error("Database not initialized in get_archived_track.")
        return None
    try:
        archived_track = await db.archived_tracks.find_one({"track_id": track_id})
        logger.debug(f"Fetched archived track {track_id} from 'archived_tracks' collection: {archived_track}")
        return archived_track
    except Exception as e:
        logger.error(f"Error fetching archived track {track_id}: {e}", exc_info=True)
        return None

# TODO: توابع مربوط به مدیریت کاربران VIP در کالکشن vip_users را اضافه کنید
# مثال: تابع برای اضافه کردن کاربر به vip_users، تابع برای حذف کاربر از vip_users
# این توابع برای مدیریت VIP از طریق پنل ادمین یا روش‌های دیگر لازم هستند.
# توجه: این توابع در حال حاضر توسط داشبورد Flask مدیریت می‌شوند و نیازی نیست در اینجا تکرار شوند
# مگر اینکه بخواهید ربات هم قابلیت مدیریت مستقیم VIP را داشته باشد.