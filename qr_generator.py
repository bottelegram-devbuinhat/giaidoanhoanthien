"""Download VietQR content and ensure it is a real PNG before Telegram upload."""
import asyncio
import base64
import os
import urllib.parse
import urllib.request
from pathlib import Path
import cairosvg
from firebase_logger import ghi_log_wallet

QR_DIR = Path("QRCODE")
QR_DIR.mkdir(parents=True, exist_ok=True)
ACCOUNT_NUMBER = "860671050278271"
BANK_ID = "970422"
ACCOUNT_NAME = "BUI NGUYEN XUAN NHAT"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _valid_png(path):
    try:
        with open(path, "rb") as f:
            head = f.read(24)
        if len(head) < 24 or not head.startswith(PNG_SIGNATURE):
            return False
        width = int.from_bytes(head[16:20], "big")
        height = int.from_bytes(head[20:24], "big")
        return width >= 200 and height >= 200 and os.path.getsize(path) > 500
    except OSError:
        return False


def _download_and_convert(url, filepath):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "image/png,image/svg+xml"})
    with urllib.request.urlopen(req, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(f"VietQR returned HTTP {response.status}")
        data = response.read()
        content_type = response.headers.get("Content-Type", "").lower()
    if data.startswith(PNG_SIGNATURE):
        png_data = data
    elif data.lstrip().startswith(b"<svg") or "svg" in content_type or b"<svg" in data[:500].lower():
        png_data = cairosvg.svg2png(bytestring=data, output_width=1080, output_height=1080)
    else:
        raise ValueError(f"VietQR returned unsupported image data (Content-Type={content_type!r}, bytes={len(data)})")
    tmp = str(filepath) + ".tmp"
    with open(tmp, "wb") as f:
        f.write(png_data)
    os.replace(tmp, filepath)
    if not _valid_png(filepath):
        try: os.remove(filepath)
        except OSError: pass
        raise ValueError("Downloaded QR failed PNG signature/dimension validation")
    return str(filepath)


async def tai_va_luu_qr_code(user_id, amount):
    user_id = str(user_id)
    try:
        amount = int(amount)
        if amount < 10000:
            raise ValueError("Minimum deposit is 10000 VND")
        filepath = QR_DIR / f"{user_id}_{amount}.png"
        if _valid_png(filepath):
            return str(filepath)
        if filepath.exists():
            filepath.unlink()
        params = urllib.parse.urlencode({"amount": amount, "addInfo": f"NAPTIEN_{user_id}", "accountName": ACCOUNT_NAME})
        url = f"https://img.vietqr.io/image/{BANK_ID}-{ACCOUNT_NUMBER}-compact2.svg?{params}"
        result = await asyncio.to_thread(_download_and_convert, url, filepath)
        ghi_log_wallet(user_id, "CREATE_QR", f"Created validated QR for {amount} VND")
        return result
    except Exception as exc:
        ghi_log_wallet(user_id, "ERROR_QR", f"QR generation failed: {type(exc).__name__}: {exc}")
        return None
