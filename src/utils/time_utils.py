import pytz
from datetime import datetime, timezone

SERVER_TZ = timezone.utc
KYIV_TZ = pytz.timezone("Europe/Kyiv")
today = datetime.now(KYIV_TZ).strftime("%Y-%m-%d")
today_date = datetime.strptime(today, "%Y-%m-%d").date()

def get_kyiv_date(created_at_str: str) -> str:
    try:
        dt_utc = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        dt_kyiv = dt_utc.astimezone(KYIV_TZ)
        return dt_kyiv.strftime("%Y-%m-%d")
    except Exception:
        return ""