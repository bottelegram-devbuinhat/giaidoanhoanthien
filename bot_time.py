"""Vietnam-local clock helpers used by game rounds and scheduled messages."""
from datetime import datetime
from zoneinfo import ZoneInfo

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def g_d(now=None):
    """Return a consistent Vietnam-local timestamp for display and logs."""
    current = now.astimezone(VN_TZ) if now is not None else datetime.now(VN_TZ)
    return {
        "now": current,
        "log_str": current.strftime("%Y-%m-%d %H:%M:%S"),
        "date": current.strftime("%Y-%m-%d"),
        "time": current.strftime("%H:%M:%S"),
    }
