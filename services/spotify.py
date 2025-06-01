from config import settings
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import sys
import os
import logging
import itertools  # برای چرخش پروکسی‌ها
import requests  # برای استفاده از پروکسی با requests.Session

# تنظیم لاگ‌گیری برای این ماژول
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# لیست پروکسی‌های شما
# فرمت: "http://user:pass@ip:port"
# توجه: برای استفاده از پروکسی‌های HTTP/HTTPS، باید پروتکل را نیز مشخص کنید.
# اگر پروکسی‌ها SOCKS5 هستند، باید 'socks5://' را اضافه کنید.
PROXIES = [
    "http://nxeoktwx:a30uy1jr8c43@198.23.239.134:6540",
    "http://nxeoktwx:a30uy1jr8c43@207.244.217.165:6712",
    "http://nxeoktwx:a30uy1jr8c43@107.172.163.27:6543",
    "http://nxeoktwx:a30uy1jr8c43@23.94.138.75:6349",
    "http://nxeoktwx:a30uy1jr8c43@216.10.27.159:6837",
    "http://nxeoktwx:a30uy1jr8c43@136.0.207.84:6661",
    "http://nxeoktwx:a30uy1jr8c43@64.64.118.149:6732",
    "http://nxeoktwx:a30uy1jr8c43@142.147.128.93:6593",
    "http://nxeoktwx:a30uy1jr8c43@104.239.105.125:6655",
    "http://nxeoktwx:a30uy1jr8c43@166.88.58.10:5735"
]

# ایجاد یک iterator چرخشی برای پروکسی‌ها
proxy_cycle = itertools.cycle(PROXIES)


def get_track_info(spotify_url: str) -> dict | None:
    """
    Fetches track information from Spotify using spotipy with rotating proxies.
    Note: spotipy is a synchronous library. This function should be run in a separate thread
    (e.g., using asyncio.to_thread) in an async environment.

    Args:
        spotify_url: The Spotify track URL.

    Returns:
        A dictionary containing track information if successful, None otherwise.
    """
    logger.debug(f"Attempting to get track info for URL: {spotify_url}")
    try:
        # انتخاب پروکسی بعدی از لیست چرخشی
        current_proxy = next(proxy_cycle)
        logger.debug(f"Using proxy: {current_proxy}")

        # ایجاد یک requests.Session و تنظیم پروکسی
        session = requests.Session()
        session.proxies = {
            "http": current_proxy,
            "https": current_proxy,
        }

        auth_manager = SpotifyClientCredentials(
            client_id=settings.SPOTIPY_CLIENT_ID,
            client_secret=settings.SPOTIPY_CLIENT_SECRET
        )
        # پاس دادن session به spotipy و افزایش تایم‌اوت
        sp = spotipy.Spotify(auth_manager=auth_manager, requests_session=session,
                             requests_timeout=15)  # تایم‌اوت را اینجا تنظیم کنید

        # Extract track ID from URL
        track_id = spotify_url.split("/")[-1].split("?")[0]
        logger.debug(f"Extracted track ID: {track_id}")

        # Fetch track info from Spotify API (synchronous call)
        track = sp.track(track_id)
        logger.debug(f"Successfully fetched track data for ID: {track_id}")

        # Construct info dictionary with safe access using .get()
        info = {
            "id": track_id,
            "name": track.get('name', 'Unknown Title'),
            "artist": track['artists'][0].get('name', 'Unknown Artist') if track.get('artists') and track['artists'] else 'Unknown Artist',
            "duration_ms": track.get('duration_ms', 0),
            "cover_url": track['album']['images'][0].get('url') if track.get('album') and track['album'].get('images') and track['album']['images'] else None,
            "album": track['album'].get('name', 'Unknown Album') if track.get('album') else 'Unknown Album'
        }
        logger.info(f"Successfully processed track info for ID: {track_id}")
        return info
    except Exception as e:
        logger.error(
            f"ERROR in get_track_info for URL {spotify_url} with proxy {current_proxy}: {e}", exc_info=True)
        return None
