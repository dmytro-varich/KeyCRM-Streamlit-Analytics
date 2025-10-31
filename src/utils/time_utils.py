import pytz
from datetime import datetime, timezone

SERVER_TZ = timezone.utc
KYIV_TZ = pytz.timezone("Europe/Kyiv")

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

def get_now_kyiv_iso() -> str:
    return datetime.now(KYIV_TZ).isoformat()

def get_today_date_kyiv():
    return datetime.now(KYIV_TZ).date()

def get_kyiv_date(created_at_str: str) -> str:
    try:
        dt_utc = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=SERVER_TZ)
        dt_kyiv = dt_utc.astimezone(KYIV_TZ)
        return dt_kyiv.strftime("%Y-%m-%d")
    except Exception:
        return ""