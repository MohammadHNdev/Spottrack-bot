import yt_dlp
import os
import logging
import shutil
import glob # اضافه کردن ایمپورت glob

from config import settings

logger = logging.getLogger(__name__)

YDL_OPTS = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }, {
        'key': 'EmbedThumbnail', # This postprocessor embeds the thumbnail into the audio file
    }],
    'outtmpl': '%(title)s.%(ext)s',
    'quiet': True,
    'no_warnings': True,
    'geo_bypass': True,
    'nocheckcertificate': True,
    'logtostderr': False,
    'logger': logger,
    'writethumbnail': True, # This option downloads the thumbnail file
}

# تغییر در مقدار بازگشتی: اکنون مسیر فایل کاور را نیز برمی‌گرداند
def download_track(track_info: dict) -> tuple[str | None, str | None, str | None]:
    """
    آهنگ را از یوتیوب دانلود و به MP3 تبدیل می‌کند و کاور را نیز دانلود می‌کند.
    مسیر فایل MP3، مسیر پوشه موقت و مسیر فایل کاور را برمی‌گرداند.
    """
    if not track_info:
        logger.error("No track info provided for download.")
        return None, None, None

    query = f"{track_info.get('name', '')} - {track_info.get('artist', '')}"
    if not query or query == " - ":
        logger.error(f"Invalid query generated from track info: {track_info}")
        return None, None, None

    logger.info(f"Attempting to download track: {query}")

    temp_dir = os.path.join(settings.TEMP_DIR, str(os.getpid()), str(os.getppid()), str(os.getuid()), str(os.getgid()), str(os.urandom(8).hex()))
    os.makedirs(temp_dir, exist_ok=True)
    logger.debug(f"Created temporary directory for download: {temp_dir}")

    ydl_opts = YDL_OPTS.copy()
    ydl_opts['outtmpl'] = os.path.join(temp_dir, '%(title)s.%(ext)s')
    ydl_opts['paths'] = {'temp': temp_dir, 'home': temp_dir}

    filename = None
    thumbnail_filename = None # متغیر جدید برای مسیر فایل کاور

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(f"ytsearch1:{query}", download=True)

            if info_dict:
                entry = info_dict.get('entries', [None])[0]
                if entry:
                    # Find the downloaded MP3 file in the temp directory
                    mp3_files = glob.glob(os.path.join(temp_dir, '*.mp3'))
                    if mp3_files:
                        filename = mp3_files[0]
                        logger.info(f"Successfully downloaded and converted to MP3: {filename}")

                        # Find the downloaded thumbnail file in the temp directory
                        # yt-dlp معمولا کاور را با پسوندهای webp, jpg, png دانلود می‌کند
                        thumbnail_files = glob.glob(os.path.join(temp_dir, '*.webp')) + \
                                          glob.glob(os.path.join(temp_dir, '*.jpg')) + \
                                          glob.glob(os.path.join(temp_dir, '*.png'))

                        if thumbnail_files:
                            # معمولا اولین فایل پیدا شده کاور اصلی است
                            thumbnail_filename = thumbnail_files[0]
                            logger.info(f"Found thumbnail file: {thumbnail_filename}")
                        else:
                            logger.warning(f"Thumbnail file not found in temporary directory {temp_dir} after download.")

                    else:
                        logger.error(f"MP3 file not found in temporary directory {temp_dir} after download.")
                        filename = None
                else:
                    logger.error(f"No entries found in info_dict for query: {query}")
                    filename = None
            else:
                logger.error(f"yt-dlp extract_info returned None for query: {query}")
                filename = None

    except yt_dlp.DownloadError as e:
        logger.error(f"Download error for query '{query}': {e}", exc_info=True)
        filename = None
        thumbnail_filename = None
    except Exception as e:
        logger.error(f"An unexpected error occurred during download for query '{query}': {e}", exc_info=True)
        filename = None
        thumbnail_filename = None

    return filename, temp_dir, thumbnail_filename # برگرداندن مسیر فایل کاور


# تابع کمکی برای پاکسازی پوشه موقت (اختیاری، چون در finally هندلر اصلی هم انجام می‌شود)
# def cleanup_temp_dir(temp_dir: str | None):
#     if temp_dir and os.path.exists(temp_dir):
#         try:
#             shutil.rmtree(temp_dir)
#             logger.debug(f"Cleaned up temporary directory: {temp_dir}")
#         except Exception as e:
#             logger.warning(f"Could not remove temporary directory {temp_dir}: {e}")