from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# --- دیکشنری برای متن‌های چندزبانه ---
TEXTS = {
    "welcome": {
        "fa": "سلام! لینک آهنگ  اسپاتیفای رو برام بفرست تا دانلودش کنم.",
        "en": "Hello! Send me a Spotify track  to download it."
    },
    "help": {
        "fa": "برای دانلود آهنگ، لینک اسپاتیفای اون رو برام بفرست. آلبوم‌ها و پلی‌لیست‌ها(ققط VIP) هنوز پشتیبانی نمی‌شن.",
        "en": "To download a track, send me its Spotify link. Albums and playlists are not supported yet."
    },
    "please_send_link": {
        "fa": "لطفاً لینک آهنگ  اسپاتیفای رو برام بفرستید.",
        "en": "Please send me a Spotify track  link."
    },
    "unsupported_link_type": {
        "fa": "متاسفم، این نوع لینک اسپاتیفای هنوز پشتیبانی نمی‌شه.",
        "en": "Sorry, this type of Spotify link is not supported yet."
    },
     "album_not_supported": {
        "fa": "متاسفم، دانلود آلبوم‌ها هنوز پشتیبانی نمی‌شه.",
        "en": "Sorry, downloading albums is not supported yet."
    },
     "playlist_not_supported": {
        "fa": "متاسفم، دانلود پلی‌لیست‌ها هنوز پشتیبانی نمی‌شه.",
        "en": "Sorry, downloading playlists is not supported yet."
    },
    "fetching_info": {
        "fa": "در حال دریافت اطلاعات آهنگ...",
        "en": "Fetching track information..."
    },
    "error_fetching_track_info": {
        "fa": "خطا در دریافت اطلاعات آهنگ. لطفاً دوباره تلاش کنید یا از لینک دیگری استفاده کنید.",
        "en": "Error fetching track information. Please try again or use a different link."
    },
    "download_started_ack": {
        "fa": "دانلود آغاز شد...",
        "en": "Download started..."
    },
    "downloading": {
        "fa": "در حال دانلود آهنگ...",
        "en": "Downloading track..."
    },
    "download_failed": {
        "fa": "خطا در دانلود آهنگ. لطفاً دوباره تلاش کنید.",
        "en": "Error downloading track. Please try again."
    },
    "download_success": {
        "fa": "دانلود با موفقیت انجام شد!",
        "en": "Download successful!"
    },
    "download_limit_reached": {
        "fa": "شما به محدودیت دانلود روزانه رسیده‌اید. برای دانلود نامحدود، اشتراک VIP تهیه کنید.",
        "en": "You have reached your daily download limit. Get a VIP subscription for unlimited downloads."
    },
    "error_sending_file": {
        "fa": "خطا در ارسال فایل. لطفاً دوباره تلاش کنید.",
        "en": "Error sending file. Please try again."
    },
    "error_track_info_missing": {
        "fa": "اطلاعات آهنگ یافت نشد. لطفاً دوباره لینک را ارسال کنید.",
        "en": "Track information missing. Please send the link again."
    },
    "unknown_command": {
        "fa": "دستور نامفهوم. لطفاً لینک اسپاتیفای را ارسال کنید یا از دستور /help استفاده کنید.",
        "en": "Unknown command. Please send a Spotify link or use the /help command."
    },
    "language_changed": {
        "fa": "زبان به فارسی تغییر یافت.",
        "en": "Language changed to English."
    },
    "language_changed_ack": {
        "fa": "زبان تغییر کرد.",
        "en": "Language changed."
    },
    "error_changing_language": {
        "fa": "خطا در تغییر زبان.",
        "en": "Error changing language."
    },
    "error_changing_language_ack": {
        "fa": "خطا در تغییر زبان.",
        "en": "Error changing language."
    },
     "back_ack": {
        "fa": "بازگشت.",
        "en": "Back."
    },
    # متن‌های مربوط به VIP
    "vip_info": {
        "fa": "✨ **اشتراک VIP** ✨\n\nبا تهیه اشتراک VIP از مزایای زیر بهره‌مند شوید:\n\n- دانلود نامحدود آهنگ در روز\n- سرعت بالاتر در دانلود \n- دانلود پلی لیست\n\nبرای اطلاعات بیشتر و خرید، با پشتیبانی تماس بگیرید یا از طریق دکمه زیر اقدام کنید.",
        "en": "✨ **VIP Subscription** ✨\n\nGet the following benefits by purchasing a VIP subscription:\n\n- Unlimited daily downloads\n- \n- downlod playlist\n\nFor more information and purchase, contact support or use the button below."
    },
    "contact_support": {
        "fa": "📞 تماس با پشتیبانی",
        "en": "📞 Contact Support"
    },
    "buy_vip": {
        "fa": "💳 خرید اشتراک VIP",
        "en": "💳 Buy VIP Subscription"
    },
    # متن‌های جدید برای دکمه‌ها
    "select_language": { # متن جدید برای درخواست انتخاب زبان
        "fa": "لطفاً زبان مورد نظر خود را انتخاب کنید:",
        "en": "Please select your language:"
    },
    "cancel_ack": { # متن جدید برای تأیید لغو عملیات
        "fa": "عملیات لغو شد.",
        "en": "Operation cancelled."
    }
}

# --- تابع دریافت متن بر اساس کلید و زبان ---
def get_text(key: str, lang: str = "fa") -> str:
    """متن مربوط به یک کلید و زبان مشخص را برمی‌گرداند."""
    return TEXTS.get(key, {}).get(lang, f"Error: Text key '{key}' not found for language '{lang}'")

# --- تابع فرمت کردن مدت زمان ---
def format_duration(ms: int) -> str:
    """مدت زمان را از میلی‌ثانیه به فرمت دقیقه:ثانیه تبدیل می‌کند."""
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    return f"{minutes}:{str(seconds).zfill(2)}"

# --- تابع تولید کپشن آهنگ ---
def generate_track_caption(info: dict, lang: str = "fa", for_download: bool = False) -> str:
    """کپشن اطلاعات آهنگ را تولید می‌کند."""
    track_name = info.get('name', 'N/A')
    artist_name = info.get('artist', 'N/A')
    album_name = info.get('album', 'N/A')
    duration_ms = info.get('duration_ms', 0)
    duration_formatted = format_duration(duration_ms)

    if lang == "fa":
        caption = (
            f"🎵 <b>نام آهنگ:</b> {track_name}\n"
            f"🎤 <b>آرتیست:</b> {artist_name}\n"
            f"💽 <b>آلبوم:</b> {album_name}\n"
            f"⏱ <b>مدت:</b> {duration_formatted} دقیقه"
        )
        if not for_download:
            caption += "\n\nآیا مایل به دانلود این آهنگ هستید؟"
        return caption
    else: # Default to English
        caption = (
            f"🎵 <b>Track:</b> {track_name}\n"
            f"🎤 <b>Artist:</b> {artist_name}\n"
            f"💽 <b>Album:</b> {album_name}\n"
            f"⏱ <b>Duration:</b> {duration_formatted}"
        )
        if not for_download:
            caption += "\n\nWould you like to download this track?"
        return caption

# --- تابع تولید کیبورد اینلاین دانلود آهنگ ---
def generate_track_inline_keyboard(track_id: str, lang: str = "fa") -> InlineKeyboardMarkup:
    """کیبورد اینلاین شامل دکمه دانلود برای یک آهنگ خاص را تولید می‌کند."""
    if lang == "fa":
        buttons = [
            [InlineKeyboardButton(text="⬇️ دانلود", callback_data=f"download_{track_id}")],
            [InlineKeyboardButton(text="❌ لغو", callback_data="cancel"),
             InlineKeyboardButton(text="🌐 تغییر زبان", callback_data="change_lang")] # callback_data="change_lang"
        ]
    else: # Default to English
        buttons = [
            [InlineKeyboardButton(text="⬇️ Download", callback_data=f"download_{track_id}")],
            [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel"),
             InlineKeyboardButton(text="🌐 Change Language", callback_data="change_lang")] # callback_data="change_lang"
        ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- تابع تولید کیبورد اصلی (Reply Keyboard) ---
def get_main_keyboard(lang: str = "fa") -> ReplyKeyboardMarkup:
    """کیبورد اصلی ربات را تولید می‌کند."""
    if lang == "fa":
        buttons = [
            [KeyboardButton(text="🌐 تغییر زبان")]
        ]
    else: # Default to English
        buttons = [
            [KeyboardButton(text="🌐 Change Language")]
        ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=False, is_persistent=True)

# --- تابع تولید کیبورد ارتقا به VIP ---
def get_vip_upgrade_keyboard(lang: str = "fa") -> InlineKeyboardMarkup:
    """کیبورد اینلاین برای پیشنهاد ارتقا به VIP را تولید می‌کند."""
    if lang == "fa":
        buttons = [
            [InlineKeyboardButton(text="✨ ارتقا به VIP ✨", callback_data="upgrade_vip")],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back")]
        ]
    else: # Default to English
        buttons = [
            [InlineKeyboardButton(text="✨ Upgrade to VIP ✨", callback_data="upgrade_vip")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="back")]
        ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- تابع دریافت اطلاعات و کیبورد VIP ---
def get_vip_info(lang: str = "fa") -> tuple[str, InlineKeyboardMarkup]:
    """متن و کیبورد مربوط به اطلاعات VIP را برمی‌گرداند."""
    text = get_text("vip_info", lang)

    if lang == "fa":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text("contact_support", lang), url="https://t.me/DiamondcodeSupport")], # لینک پشتیبانی خود را جایگزین کنید
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back")]
        ])
    else: # Default to English
         keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text("contact_support", lang), url="https://t.me/DiamondcodeSupport")], # Replace with your support link
            [InlineKeyboardButton(text="🔙 Back", callback_data="back")]
        ])

    return text, keyboard

# --- تابع تولید کیبورد تغییر زبان ---
def get_language_keyboard() -> InlineKeyboardMarkup:
    """کیبورد اینلاین برای انتخاب زبان را تولید می‌کند."""
    buttons = [
        [InlineKeyboardButton(text="فارسی 🇮🇷", callback_data="lang_fa")],
        [InlineKeyboardButton(text="English 🇺🇸", callback_data="lang_en")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)