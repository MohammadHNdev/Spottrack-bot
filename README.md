# SpotTrack Bot - ربات تلگرام دانلود موزیک از اسپاتیفای

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Telegram Bot](https://img.shields.io/badge/Telegram%20Bot-API-blue?style=for-the-badge&logo=telegram)
![Spotify API](https://img.shields.io/badge/Spotify%20API-Spotipy-green?style=for-the-badge&logo=spotify)

---

## 🚀 معرفی پروژه

**SpotTrack Bot** یک ربات تلگرام است که به شما امکان می‌دهد به سادگی موزیک‌های اسپاتیفای را دانلود کنید. کافی است لینک آهنگ اسپاتیفای را ارسال کنید و فایل MP3 با کیفیت بالا را دریافت نمایید.

این ربات با استفاده از API اسپاتیفای، سیستم پروکسی چرخشی برای دور زدن محدودیت‌ها، و yt-dlp برای دانلود و تبدیل موزیک‌ها ساخته شده است.

**توسعه‌دهنده:** محمدحسین نوروزی

---

## ⚙️ قابلیت‌ها

- دریافت اطلاعات کامل آهنگ (نام، خواننده، آلبوم، کاور) فقط با ارسال لینک اسپاتیفای  
- دانلود و تبدیل آهنگ‌ها به فرمت MP3 با کیفیت ۱۹۲kbps  
- استفاده از سیستم پروکسی چرخشی برای افزایش پایداری و جلوگیری از بلاک شدن توسط اسپاتیفای  
- آرشیو کردن آهنگ‌های دانلود شده در کانال تلگرام برای دسترسی سریع‌تر  
- مدیریت محدودیت دانلود روزانه برای کاربران عادی و پشتیبانی از کاربران VIP  
- رابط کاربری ساده و تعاملی در تلگرام با پشتیبانی از چند زبان  
- نمایش انیمیشن پیشرفت دانلود در پیام‌ها  

---

## 🛠️ معماری و ساختار پروژه

### ۱. نقطه ورود: `main.py`

- راه‌اندازی ربات و دیسپچر aiogram  
- تنظیم لاگ‌گیری و مدیریت اتصال به دیتابیس MongoDB  
- ثبت هندلرهای پیام و کال‌بک‌ها  
- مدیریت رویدادهای startup و shutdown  

### ۲. هندلرهای کاربر: `handlers/user.py`

- مدیریت دستورات `/start` و `/help`  
- دریافت و پردازش لینک‌های اسپاتیفای (ترک، آلبوم، پلی‌لیست)  
- مدیریت وضعیت کاربر با FSM (انتظار برای لینک)  
- هندلرهای کال‌بک برای دانلود، لغو، تغییر زبان، ارتقا به VIP و بازگشت  
- انیمیشن پیشرفت دانلود  
- ارسال فایل صوتی و کاور به کاربر و آرشیو  

### ۳. ارتباط با Spotify API: `services/spotify.py`

- استفاده از کتابخانه `spotipy` برای دریافت اطلاعات ترک  
- استفاده از پروکسی‌های HTTP/HTTPS به صورت چرخشی برای جلوگیری از بلاک شدن  
- استخراج اطلاعات مهم ترک شامل نام، خواننده، آلبوم، کاور و مدت زمان  

### ۴. دانلود و تبدیل موزیک: `services/downloader.py`

- استفاده از `yt_dlp` برای جستجو و دانلود موزیک از یوتیوب  
- تبدیل فایل صوتی به MP3 با کیفیت ۱۹۲kbps  
- دانلود کاور و ذخیره آن در کنار فایل صوتی  
- ساخت پوشه موقت منحصربه‌فرد برای هر دانلود  
- بازگرداندن مسیر فایل صوتی، پوشه موقت و فایل کاور  

### ۵. مدیریت دیتابیس MongoDB: `db/mongo.py`

- اتصال async به MongoDB با `motor`  
- ذخیره و بازیابی اطلاعات کاربران، وضعیت VIP، تعداد دانلودها  
- ذخیره و بازیابی آرشیو آهنگ‌ها با `file_id` فایل‌های آپلود شده در تلگرام  
- مدیریت محدودیت دانلود روزانه و بررسی وضعیت VIP  
- ایندکس‌گذاری بهینه روی فیلدهای کلیدی  

### ۶. رابط کاربری و متن‌ها: `utils/ui.py` (خارج از این مستند)

- تولید متن‌های چندزبانه  
- ساخت کیبوردهای Reply و Inline برای تعامل با کاربر  

---

## 🔧 پیش‌نیازها و نصب

### پیش‌نیازها

- Python 3.10+  
- ffmpeg (برای پردازش صوت)  
- MongoDB (دیتابیس)  
- توکن ربات تلگرام از [@BotFather](https://t.me/BotFather)  
- حساب Spotify Developer برای دریافت Client ID و Client Secret  
- لیست پروکسی‌های HTTP/HTTPS با احراز هویت (ترجیحاً اختصاصی یا مسکونی)  

### نصب و راه‌اندازی

```bash
git clone https://github.com/YOUR_USERNAME/spotify_telegram_bot.git
cd spotify_telegram_bot

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

sudo apt update
sudo apt install ffmpeg
تنظیمات
یک فایل config.py بسازید و مقادیر زیر را وارد کنید (یا متغیرهای محیطی تنظیم کنید):

python
Copy Code
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID", "YOUR_SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET", "YOUR_SPOTIPY_CLIENT_SECRET")
ARCHIVE_CHANNEL_ID = os.getenv("ARCHIVE_CHANNEL_ID", None)  # آیدی کانال تلگرام برای آرشیو
PROXIES = [
    "http://user:pass@ip:port",
    # پروکسی‌های دیگر
]
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "temp_downloads")
DEFAULT_LANGUAGE = "fa"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "spottrack_db")
BOT_TOKEN = TELEGRAM_BOT_TOKEN
STORAGE_CHANNEL_ID = ARCHIVE_CHANNEL_ID
DOWNLOAD_LIMIT_PER_USER = 5  # محدودیت دانلود روزانه برای کاربران عادی
📚 وابستگی‌ها (requirements.txt)
aiogram
spotipy
pymongo
python-dotenv
loguru
yt-dlp
mutagen
aiofiles
requests
📝 نکات مهم
پروکسی‌ها برای جلوگیری از بلاک شدن توسط اسپاتیفای حیاتی هستند. حتماً پروکسی‌های با کیفیت و احراز هویت شده استفاده کنید.
محدودیت دانلود روزانه برای کاربران عادی اعمال شده است و کاربران VIP محدودیت ندارند.
آرشیو آهنگ‌ها در کانال تلگرام ذخیره می‌شود تا در دفعات بعد سریع‌تر ارسال شوند.
انیمیشن پیشرفت دانلود در پیام‌ها تجربه کاربری بهتری ایجاد می‌کند.
مدیریت زبان و رابط کاربری چندزبانه برای راحتی کاربران فراهم شده است.
🙏 قدردانی
این ربات نتیجه تلاش و تجربه فراوان در کار با APIهای مختلف، مدیریت پروکسی‌ها و طراحی رابط کاربری در تلگرام است. امیدوارم برای شما مفید و لذت‌بخش باشد.

توسعه‌دهنده: محمدحسین نوروزی
تاریخ: ۱۴۰۲

🆘 پشتیبانی و ارتباط
برای سوالات و مشکلات، لطفاً از طریق ایمیل یا گیت‌هاب با من در ارتباط باشید.

## 📄 لایسنس و حق نشر

تمامی حقوق این پروژه متعلق به **محمدحسین نوروزی** است.  
استفاده، کپی، تغییر و انتشار این کد تنها با ذکر نام توسعه‌دهنده و کسب اجازه کتبی مجاز است.