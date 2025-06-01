import requests
from requests.auth import HTTPBasicAuth

# مشخصات کلاینت اسپاتیفای
CLIENT_ID = ''
CLIENT_SECRET = ''

# پراکسی (می‌تونی اینجا هر پراکسی که تست کردی بذاری)
proxy = "http://nxeoktwx:a30uy1jr8c43@198.23.239.134:6540"

proxies = {
    "http": proxy,
    "https": proxy,
}

# آدرس گرفتن توکن
url = "https://accounts.spotify.com/api/token"

# داده‌های درخواست
data = {
    "grant_type": "client_credentials"
}

try:
    response = requests.post(
        url,
        data=data,
        auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
        proxies=proxies,
        timeout=10,
    )
    response.raise_for_status()
    token_data = response.json()
    print("Access token:", token_data.get("access_token"))
except requests.exceptions.RequestException as e:
    print("Error:", e)
