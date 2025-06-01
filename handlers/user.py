import logging
import asyncio
import os
import shutil
from datetime import datetime, timedelta, timezone

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile, BufferedInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from aiogram.exceptions import TelegramBadRequest, TelegramAPIError

import aiohttp

from config import settings
from services import spotify, downloader
from db import mongo
from utils import ui

logger = logging.getLogger(__name__)

router = Router()

class UserState(StatesGroup):
    waiting_for_link = State()
    # می‌توانید حالت‌های دیگری در آینده اضافه کنید

# --- هندلر دستور /start ---
@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    await ensure_user_exists(user_id)
    lang = await get_user_language(user_id)

    welcome_text = ui.get_text("welcome", lang)
    # استفاده از ReplyKeyboardMarkup برای کیبورد اصلی
    await message.answer(welcome_text, reply_markup=ui.get_main_keyboard(lang))
    await state.set_state(UserState.waiting_for_link)
    logger.info(f"User {user_id} started bot. State set to waiting_for_link.")

# --- هندلر دستور /help ---
@router.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    help_text = ui.get_text("help", lang)
    await message.answer(help_text)
    logger.info(f"User {user_id} requested help.")

# --- هندلر درخواست تغییر زبان (از دکمه اینلاین) ---
@router.callback_query(F.data == "change_lang")
async def callback_change_language_request(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await get_user_language(user_id) # دریافت زبان فعلی برای پیام پاسخ

    logger.info(f"Change language request callback received from user {user_id}.")

    # ارسال کیبورد انتخاب زبان
    await callback.message.answer(ui.get_text("select_language", lang), reply_markup=ui.get_language_keyboard())

    # پاسخ به کال‌بک
    try:
        await callback.answer()
        logger.debug(f"Answered change_lang callback for user {user_id}")
    except Exception:
        pass # نادیده گرفتن اگر قبلاً پاسخ داده شده است

# --- هندلر انتخاب زبان (از کیبورد انتخاب زبان) ---
@router.callback_query(F.data.startswith("lang_"))
async def callback_change_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    new_lang = callback.data.split("_")[1]
    logger.info(f"Change language callback received from user {user_id}. New lang: {new_lang}")

    try:
        await mongo.update_user_language(user_id, new_lang)
        logger.info(f"Language changed to {new_lang} for user {user_id}")

        confirmation_text = ui.get_text("language_changed", new_lang)

        # ویرایش پیام اصلی (پیام "Please select your language:")
        try:
            await callback.message.edit_text(confirmation_text) # حذف کیبورد اینلاین انتخاب زبان
            # می‌توانید کیبورد اصلی Reply را دوباره ارسال کنید اگر لازم است
            # await callback.message.answer(ui.get_text("welcome", new_lang), reply_markup=ui.get_main_keyboard(new_lang))
        except Exception as e:
            logger.warning(f"Could not edit language selection message for user {user_id}: {e}")
            # اگر ویرایش پیام ممکن نبود، پیام جدید ارسال کنید
            await callback.message.answer(confirmation_text)

        await callback.answer(ui.get_text("language_changed_ack", new_lang))

    except Exception as e:
        logger.error(f"Error changing language for user {user_id} to {new_lang}: {e}", exc_info=True)
        lang = await get_user_language(user_id)
        await callback.message.answer(ui.get_text("error_changing_language", lang))
        await callback.answer(ui.get_text("error_changing_language_ack", lang))

# --- هندلر دریافت لینک اسپاتیفای ---
@router.message(F.text.regexp(r'https?://open\.spotify\.com/(track|album|playlist)/[a-zA-Z0-9]+'))
async def handle_spotify_link(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await ensure_user_exists(user_id)
    lang = await get_user_language(user_id)

    link = message.text.strip()
    logger.info(f"User {user_id} sent message: {link}")

    # پاکسازی state قبلی قبل از پردازش لینک جدید
    await state.clear()
    logger.debug(f"State cleared for user {user_id} before processing new link.")

    if '/track/' in link:
        try:
            track_id = link.split('/track/')[1].split('?')[0].split('/')[0]
            if not track_id:
                 raise ValueError("Could not extract track ID")
            logger.info(f"Detected track link with ID: {track_id}")
            await process_track_link(message, state, track_id, lang)
        except Exception as e:
            logger.error(f"Error extracting track ID from link {link}: {e}", exc_info=True)
            await message.answer(ui.get_text("invalid_link_format", lang))

    elif '/album/' in link:
        album_id = link.split('/album/')[1].split('?')[0].split('/')[0]
        logger.info(f"Detected album link with ID: {album_id}")
        await message.answer(ui.get_text("album_not_supported", lang))
    elif '/playlist/' in link:
        playlist_id = link.split('/playlist/')[1].split('?')[0].split('/')[0]
        logger.info(f"Detected playlist link with ID: {playlist_id}")
        await message.answer(ui.get_text("playlist_not_supported", lang))
    else:
        logger.warning(f"Received unhandled Spotify link type from user {user_id}: {link}")
        await message.answer(ui.get_text("unsupported_link_type", lang))

# --- تابع پردازش لینک ترک ---
async def process_track_link(message: Message, state: FSMContext, track_id: str, lang: str):
    user_id = message.from_user.id
    bot = message.bot

    try:
        processing_msg = await message.answer(ui.get_text("fetching_info", lang))
        logger.info(f"Sent 'fetching info' message for user {user_id}, track {track_id}")

        logger.info(f"Fetching track info for track ID: {track_id} using asyncio.to_thread")
        track_info = await asyncio.to_thread(spotify.get_track_info, track_id)

        try:
            await processing_msg.delete()
            logger.debug(f"'Fetching info' message deleted for user {user_id}")
        except Exception:
            pass

        if not track_info:
            logger.error(f"Could not fetch info for track {track_id} for user {user_id}")
            await message.answer(ui.get_text("error_fetching_track_info", lang))
            return

        logger.info(f"Successfully fetched info for track {track_id} for user {user_id}")

        await state.update_data(track_info=track_info)
        logger.debug(f"Track info for {track_id} stored in state for user {user_id}")

        caption = ui.generate_track_caption(track_info, lang)
        # استفاده از تابع جدید generate_track_inline_keyboard که track_id را می‌گیرد
        reply_markup = ui.generate_track_inline_keyboard(track_id, lang)

        cover_url = track_info.get('cover_url')
        if cover_url:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(cover_url) as resp:
                        if resp.status == 200:
                            photo_bytes = await resp.read()
                            photo_file = BufferedInputFile(photo_bytes, filename="cover.jpg")
                            await message.answer_photo(
                                photo=photo_file,
                                caption=caption,
                                reply_markup=reply_markup,
                                parse_mode="HTML"
                            )
                            logger.info(f"Sent cover photo for track {track_id} to user {user_id}")
                        else:
                            logger.warning(f"Failed to fetch cover photo for track {track_id}. Status: {resp.status}")
                            await message.answer(
                                caption,
                                reply_markup=reply_markup,
                                parse_mode="HTML"
                            )
                            logger.info(f"Sent text caption for track {track_id} to user {user_id} (photo download failed)")
            except Exception as e:
                logger.warning(f"Error sending cover photo for track {track_id} to user {user_id}: {e}")
                await message.answer(
                    caption,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
                logger.info(f"Sent text caption for track {track_id} to user {user_id} (photo failed)")
        else:
            await message.answer(
                caption,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            logger.info(f"No cover URL found for track {track_id}. Sent text caption to user {user_id}")

    except Exception as e:
        logger.error(f"An error occurred while processing track link {track_id} for user {user_id}: {e}", exc_info=True)
        await message.answer(ui.get_text("error_processing_link", lang))
        await state.clear()

# --- هندلر کال‌بک دانلود ---
@router.callback_query(F.data.startswith("download_"))
async def callback_download_track(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    track_id_from_callback = callback.data.split("_")[1]

    logger.info(f"Download callback received from user {user_id} for track ID from callback: {track_id_from_callback}")

    await callback.answer(ui.get_text("download_started_ack", lang))

    user_data = await state.get_data()
    track_info = user_data.get('track_info')

    if not track_info or track_info.get('id') != track_id_from_callback:
        logger.error(f"Track info not found in state or mismatch for user {user_id}. State info: {track_info}, Callback ID: {track_id_from_callback}")
        await callback.message.answer(ui.get_text("error_track_info_missing", lang))
        await state.clear()
        return

    spotify_id = track_info.get('id')

    # بررسی محدودیت دانلود کاربر و وضعیت VIP
    is_user_vip = await mongo.is_vip(user_id)
    logger.debug(f"User {user_id} VIP status: {is_user_vip}")

    if not is_user_vip:
        today_downloads = await mongo.get_today_downloads(user_id)
        logger.debug(f"User {user_id} today downloads: {today_downloads}")
        if today_downloads >= settings.DOWNLOAD_LIMIT_PER_USER:
            logger.warning(f"User {user_id} reached download limit.")
            await callback.message.answer(
                ui.get_text("download_limit_reached", lang),
                reply_markup=ui.get_vip_upgrade_keyboard(lang)
            )
            await state.clear()
            return

    # بررسی وجود آهنگ در آرشیو (دیتابیس)
    archived_track = await mongo.get_archived_track(spotify_id)
    if archived_track:
        logger.info(f"Track {spotify_id} found in archive. Sending archived file to user {user_id}")
        try:
            # هنگام ارسال از آرشیو، اگر thumbnail_file_id در آرشیو ذخیره شده باشد، می‌توان از آن استفاده کرد.
            # در حال حاضر فقط file_id آهنگ ذخیره می‌شود.
            # برای نمایش کاور در thumbnail، باید thumbnail را هم در آرشیو ذخیره کنیم
            # یا هر بار کاور را از URL اصلی دانلود کرده و ارسال کنیم (که کارآمد نیست)
            # یا از file_id کاوری که قبلا به تلگرام آپلود شده استفاده کنیم (بهترین روش)

            # فعلا فرض می‌کنیم thumbnail_file_id در آرشیو ذخیره نشده است.
            # اگر می‌خواهید کاور نمایش داده شود، باید آن را هنگام ارسال از آرشیو هم فراهم کنید.
            # یک راه این است که URL کاور را از track_info بگیرید و آن را دانلود کرده و به عنوان thumbnail ارسال کنید.
            # اما این کار باعث می‌شود هر بار که آهنگ از آرشیو ارسال می‌شود، کاور دوباره دانلود شود.
            # راه بهتر این است که file_id کاور را هم هنگام آرشیو کردن ذخیره کنیم.
            # برای سادگی در این مرحله، فقط فایل صوتی را از آرشیو ارسال می‌کنیم.
            # اگر نیاز به نمایش کاور هنگام ارسال از آرشیو دارید، باید تابع archive_track و get_archived_track را تغییر دهید.

            await callback.bot.send_audio(
                chat_id=user_id,
                audio=archived_track['file_id'],
                caption=ui.generate_track_caption(track_info, lang, for_download=True),
                title=track_info.get('name'),
                performer=track_info.get('artist'),
                # thumbnail=... # اینجا باید thumbnail را فراهم کنید اگر می‌خواهید نمایش داده شود
            )
            logger.info(f"Sent archived track {spotify_id} to user {user_id}")
            # به‌روزرسانی تعداد دانلود کاربر (فقط برای کاربران عادی)
            if not is_user_vip:
                 await mongo.increment_download_count(user_id)
                 logger.debug(f"Download count incremented for user {user_id} (from archive)")

        except Exception as e:
            logger.error(f"Error sending archived track {spotify_id} to user {user_id}: {e}", exc_info=True)
            await callback.message.answer(ui.get_text("error_sending_file", lang))

        await state.clear()
        return
    else:
        logger.info(f"Track {spotify_id} not in archive. Starting download process for user {user_id}")
        await _download_and_process_track(callback, state, track_info, user_id, lang, is_user_vip)

# --- هندلر کال‌بک لغو ---
@router.callback_query(F.data == "cancel")
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)

    logger.info(f"Cancel callback received from user {user_id}")

    # پاکسازی state
    await state.clear()
    logger.debug(f"State cleared for user {user_id} on cancel.")

    # ویرایش پیام اصلی برای حذف دکمه‌ها و نمایش پیام لغو
    try:
        # اطمینان از وجود متن "cancel_ack" در ui.py
        await callback.message.edit_text(ui.get_text("cancel_ack", lang))
        logger.debug(f"Edited message on cancel for user {user_id}")
    except Exception as e:
        logger.warning(f"Could not edit message on cancel for user {user_id}: {e}")
        # اگر ویرایش نشد، پیام جدید ارسال کنید
        await callback.message.answer(ui.get_text("cancel_ack", lang))


    # پاسخ به کال‌بک
    try:
        await callback.answer(ui.get_text("cancel_ack", lang))
        logger.debug(f"Answered cancel callback for user {user_id}")
    except Exception:
        pass # نادیده گرفتن اگر قبلاً پاسخ داده شده است


# --- تابع کمکی برای دانلود و پردازش ترک ---
# تغییر در امضای تابع: دریافت thumbnail_filename
async def _download_and_process_track(callback: CallbackQuery, state: FSMContext, info: dict, user_id: int, lang: str, is_user_vip: bool):
    """مدیریت فرآیند دانلود، انیمیشن، ارسال به آرشیو و ارسال به کاربر."""
    loading_text = ui.get_text("downloading", lang)
    loading_msg = None
    anim_task = None
    filename = None
    temp_dir = None
    thumbnail_filename = None # متغیر جدید برای مسیر فایل کاور
    spotify_id = info.get("id")

    try:
        loading_msg = await callback.message.answer(f"⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛\n{loading_text}")
        logger.info(f"Sent initial loading message for user {user_id}, track {spotify_id}")

        anim_task = asyncio.create_task(_animate_download(loading_msg, loading_text))
        logger.debug(f"Animation task started for user {user_id}")

        logger.info(f"Starting download for track {spotify_id} for user {user_id} using asyncio.to_thread")
        # دریافت مسیر فایل کاور از تابع download_track
        filename, temp_dir, thumbnail_filename = await asyncio.to_thread(downloader.download_track, info)

        logger.info(f"Download finished for track {spotify_id}. Filename: {filename}, Temp Dir: {temp_dir}, Thumbnail: {thumbnail_filename}")

        if anim_task and not anim_task.done():
            anim_task.cancel()
            try:
                await anim_task
            except asyncio.CancelledError:
                logger.debug(f"Animation task cancelled for user {user_id}")
                pass

        if loading_msg:
            try:
                await loading_msg.delete()
                loading_msg = None
                logger.debug(f"Loading message deleted for user {user_id}")
            except Exception as e:
                 logger.warning(f"Could not delete loading message after download for user {user_id}: {e}")
                 pass

        if not filename or not os.path.exists(filename):
             logger.error(f"Downloaded file not found or invalid for track {spotify_id}, user {user_id}. Filename: {filename}")
             await callback.message.answer(ui.get_text("download_failed", lang))
             return

        audio_file = FSInputFile(filename)
        thumbnail_file = None
        if thumbnail_filename and os.path.exists(thumbnail_filename):
             thumbnail_file = FSInputFile(thumbnail_filename)
             logger.debug(f"Created FSInputFile for thumbnail: {thumbnail_filename}")
        else:
             logger.warning(f"Thumbnail file not available or not found for track {spotify_id}, user {user_id}.")


        try:
            logger.info(f"Sending track {spotify_id} to archive channel {settings.STORAGE_CHANNEL_ID}")
            # هنگام ارسال به کانال آرشیو، فقط فایل و کپشن کافی است.
            # اگر می‌خواهید thumbnail را هم در آرشیو ذخیره کنید، باید اینجا هم آن را ارسال کنید
            # و file_id thumbnail را هم در دیتابیس ذخیره کنید.
            sent_msg = await callback.bot.send_audio(
                chat_id=settings.STORAGE_CHANNEL_ID,
                audio=audio_file,
                caption=ui.generate_track_caption(info, lang, for_download=True),
                parse_mode="HTML",
                title=info.get('name'), # اضافه کردن title و performer برای آرشیو
                performer=info.get('artist'),
                # thumbnail=thumbnail_file # اگر می‌خواهید thumbnail را هم در آرشیو ذخیره کنید
            )
            file_id = sent_msg.audio.file_id
            # اگر thumbnail را هم ارسال کردید، file_id آن را هم بگیرید: sent_msg.audio.thumbnail.file_id
            logger.info(f"Track {spotify_id} sent to archive. File ID: {file_id}")

            await mongo.archive_track(
                track_id=spotify_id,
                file_id=file_id,
                # thumbnail_file_id=... # اگر thumbnail را هم ذخیره می‌کنید
            )
            logger.debug(f"File ID {file_id} archived for spotify_id {spotify_id}")

        except Exception as e:
            logger.error(f"ERROR in sending track {spotify_id} to archive channel {settings.STORAGE_CHANNEL_ID}: {e}", exc_info=True)
            # اگر ارسال به آرشیو ناموفق بود، همچنان سعی می‌کنیم فایل را به کاربر ارسال کنیم
            # اما بدون ذخیره در آرشیو
            file_id = None # file_id آرشیو در دسترس نیست

        if not is_user_vip:
            await mongo.increment_download_count(user_id)
            logger.debug(f"Download count incremented for user {user_id}")

        logger.info(f"Sending track {spotify_id} to user {user_id}")
        # هنگام ارسال به کاربر، از file_id آرشیو (اگر موجود باشد) یا FSInputFile اصلی استفاده می‌کنیم
        # و thumbnail را نیز ارسال می‌کنیم.
        try:
            await callback.message.answer_audio(
                audio=file_id if file_id else audio_file, # استفاده از file_id اگر موجود باشد، در غیر این صورت فایل اصلی
                caption=ui.generate_track_caption(info, lang, for_download=True),
                parse_mode="HTML",
                title=info.get('name'),
                performer=info.get('artist'),
                thumbnail=thumbnail_file if thumbnail_file else None # ارسال thumbnail اگر موجود باشد
            )
            logger.info(f"Track {spotify_id} successfully sent to user {user_id}")
        except Exception as e:
             logger.error(f"ERROR sending track {spotify_id} to user {user_id}: {e}", exc_info=True)
             await callback.message.answer(ui.get_text("error_sending_file", lang))


    except asyncio.CancelledError:
        logger.warning(f"Download task cancelled for user {user_id}, track {spotify_id}")
        if loading_msg:
            try:
                await loading_msg.delete()
                loading_msg = None
            except Exception: pass
        # پاکسازی پوشه موقت در finally انجام می‌شود

    except Exception as e:
        logger.error(f"ERROR during download or sending for user {user_id}, track {spotify_id}: {e}", exc_info=True)
        if anim_task and not anim_task.done():
             anim_task.cancel()
             try:
                 await anim_task
             except asyncio.CancelledError:
                 pass

        error_message_text = ui.get_text("download_failed", lang)

        if loading_msg:
            try:
                await loading_msg.edit_text(error_message_text)
                loading_msg = None
            except Exception as edit_e:
                logger.warning(f"Could not edit loading message to show error for user {user_id}: {edit_e}")
                await callback.message.answer(error_message_text)
        else:
            await callback.message.answer(error_message_text)

    finally:
        if anim_task and not anim_task.done():
             anim_task.cancel()
             try:
                 await anim_task
             except asyncio.CancelledError:
                 pass

        # پاکسازی پوشه موقت و محتویات آن (فایل صوتی و کاور)
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Could not remove temporary directory {temp_dir}: {e}")

        try:
            await state.clear()
            logger.debug(f"State cleared for user {user_id} after download process.")
        except Exception as e:
            logger.warning(f"Could not clear state for user {user_id} after download process: {e}")


# --- تابع کمکی برای دریافت زبان کاربر ---
async def get_user_language(user_id: int) -> str:
    user_data = await mongo.get_user(user_id)
    if user_data and 'language' in user_data:
        return user_data['language']
    return settings.DEFAULT_LANGUAGE

# --- تابع کمکی برای اطمینان از وجود کاربر در دیتابیس ---
async def ensure_user_exists(user_id: int):
    user_data = await mongo.get_user(user_id)
    if not user_data:
        await mongo.add_user(user_id)
        logger.info(f"Added new user {user_id} to database.")

# --- تابع کمکی برای انیمیشن دانلود ---
async def _animate_download(loading_msg: Message, loading_text: str):
    bar_frames = [
        "⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛", "🟩⬛⬛⬛⬛⬛⬛⬛⬛⬛", "🟩🟩⬛⬛⬛⬛⬛⬛⬛⬛",
        "🟩🟩🟩⬛⬛⬛⬛⬛⬛⬛", "🟩🟩🟩🟩⬛⬛⬛⬛⬛⬛", "🟩🟩🟩🟩🟩⬛⬛⬛⬛⬛",
        "🟩🟩🟩🟩🟩🟩⬛⬛⬛⬛", "🟩🟩🟩🟩🟩🟩🟩⬛⬛⬛", "🟩🟩🟩🟩🟩🟩🟩🟩⬛⬛",
        "🟩🟩🟩🟩🟩🟩🟩🟩🟩⬛", "🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩",
    ]
    i = 0
    while True:
        try:
            new_text = f"{bar_frames[i % len(bar_frames)]}\n{loading_text}"
            await loading_msg.edit_text(new_text, reply_markup=None)
            logger.debug(f"Animation frame {i} sent.")

        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                pass
            else:
                logger.error(f"Animation edit failed (Bad Request): {e}")
                break
        except TelegramAPIError as e:
             logger.error(f"Animation edit failed (Telegram API Error): {e}")
             break
        except asyncio.CancelledError:
             logger.debug("Animation task received cancel signal.")
             raise
        except Exception as e:
            logger.error(f"Animation edit failed (Other Error): {e}", exc_info=True)
            break

        i = (i + 1) % len(bar_frames)
        await asyncio.sleep(1.0)

# --- هندلر پیام‌های غیر از لینک اسپاتیفای ---
@router.message()
async def handle_other_messages(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await ensure_user_exists(user_id)
    lang = await get_user_language(user_id)

    current_state = await state.get_state()
    if current_state == UserState.waiting_for_link:
        await message.answer(ui.get_text("please_send_link", lang))
    else:
        await message.answer(ui.get_text("unknown_command", lang))

# --- هندلر کال‌بک ارتقا به VIP ---
@router.callback_query(F.data == "upgrade_vip")
async def handle_upgrade_vip(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)

    logger.info(f"Upgrade VIP callback received from user {user_id}")

    vip_text, vip_keyboard = ui.get_vip_info(lang)

    await callback.message.answer(
        vip_text,
        reply_markup=vip_keyboard,
        parse_mode="Markdown"
    )
    logger.info(f"Sent VIP upgrade info to user {user_id}")

    try:
        await callback.answer()
        logger.debug(f"Answered VIP callback for user {user_id}")
    except Exception:
        pass

# --- هندلر کال‌بک بازگشت ---
@router.callback_query(F.data == "back")
async def handle_back_callback(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)

    logger.info(f"Back callback received from user {user_id}")

    # پاکسازی state
    await state.clear()
    logger.debug(f"State cleared for user {user_id} on back callback.")

    # ویرایش پیام اصلی برای حذف کیبورد اینلاین
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        logger.debug(f"Removed inline markup on back for user {user_id}")
    except Exception:
        pass

    await callback.answer(ui.get_text("back_ack", lang))
    # می‌توانید پیام خوش‌آمدگویی و کیبورد اصلی را دوباره ارسال کنید
    # welcome_text = ui.get_text("welcome", lang)
    # await callback.message.answer(welcome_text, reply_markup=ui.get_main_keyboard(lang))