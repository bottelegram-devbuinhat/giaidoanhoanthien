"""Centralized, non-blocking audit logging for bot activity."""
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import requests

logger = logging.getLogger(__name__)
FB_ERROR_URL = "https://bot-log-telegram-5baeb-default-rtdb.asia-southeast1.firebasedatabase.app/system_errors.json"
FB_TRANS_URL = "https://bot-log-telegram-5baeb-default-rtdb.asia-southeast1.firebasedatabase.app/wallet_logs.json"
FB_ADMIN_URL = "https://bot-log-telegram-5baeb-default-rtdb.asia-southeast1.firebasedatabase.app/admin_logs.json"
FB_GAME_URL = "https://bot-log-telegram-5baeb-default-rtdb.asia-southeast1.firebasedatabase.app/game_logs.json"
_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="audit-log")


def _time():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _fallback(payload, error):
    try:
        with open("audit_fallback.log", "a", encoding="utf-8") as stream:
            stream.write(f"{payload!r} | logging_error={error!r}\n")
    except OSError:
        logger.exception("Unable to write local audit fallback")


def _post(url, payload):
    response = requests.post(url, json=payload, timeout=4)
    response.raise_for_status()


def _completed(future, payload):
    try:
        future.result()
    except Exception as exc:
        logger.warning("Firebase audit log failed: %s", exc)
        _fallback(payload, exc)


def _gui(url, data):
    """Queue log writes off the Telegram event loop; failures go to a local fallback."""
    payload = {"time": _time(), **data}
    try:
        future = _EXECUTOR.submit(_post, url, payload)
        future.add_done_callback(lambda result: _completed(result, payload))
    except Exception as exc:
        logger.warning("Could not queue Firebase audit log: %s", exc)
        _fallback(payload, exc)


def ghi_log_loi(error, **context):
    _gui(FB_ERROR_URL, {"error": str(error)[:4000], "context": context})


def ghi_log_wallet(uid, action_type, detail, **extra):
    _gui(FB_TRANS_URL, {"user_id": str(uid), "action": str(action_type), "detail": str(detail)[:2000], **extra})


def ghi_log_admin(admin_id, action_type, detail, **extra):
    _gui(FB_ADMIN_URL, {"admin_id": str(admin_id), "action": str(action_type), "detail": str(detail)[:2000], **extra})


def ghi_log_game(session_id, uid, bet_type, amount, result_status, **extra):
    _gui(FB_GAME_URL, {"session_id": session_id, "user_id": str(uid), "bet_type": bet_type,
                       "amount": amount, "status": result_status, **extra})
