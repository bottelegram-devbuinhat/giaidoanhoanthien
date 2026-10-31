import json
import os
from datetime import datetime
from pathlib import Path

p = "data.json"
q = "giftcodes.json"
r = "config.json"
l_f = "lich_su_chung.txt"
t_f = "danh_sach_tat_tb.json"
lich_su_nap_rut = "lich_su_nap_rut.txt"


def f_r(filename, default):
    path = Path(filename)
    if not path.exists():
        f_w(filename, default)
        return default
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
        return value
    except Exception as exc:
        message = f"[{datetime.now().astimezone().isoformat()}] JSON read failed for {filename}: {type(exc).__name__}: {exc}\n"
        try:
            with open("system_error.txt", "a", encoding="utf-8") as log:
                log.write(message)
        except OSError:
            pass
        return default


def f_w(filename, value):
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    with temp.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=4)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


u = f_r(p, {})
g = f_r(q, {})
ds_tat_tb = f_r(t_f, [])
c = f_r(r, {
    "token": "8978297117:AAG9-QJwd2s3YJ-5QhHiVE-pUovhan99qtM",
    "admin_ids": [8792000582],
    "default_balance": 10000,
    "tai_ratio": 1.95,
    "xiu_ratio": 1.95,
    "bet_active": True,
    "session_id": 1,
    "session_date": datetime.now().strftime("%Y-%m-%d"),
    "referral_rate": 0.01,
    "morning_greetings_sent": []
})

# Keep the configured test token by default; an environment variable may override it.
env_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
if env_token:
    c["token"] = env_token

# Safe defaults for new features when upgrading an existing config.json.
c.setdefault("referral_rate", 0.01)
c.setdefault("morning_greetings_sent", [])
c.setdefault("cancel_round_requested", False)
