import asyncio
from qr_generator import tai_va_luu_qr_code

if __name__ == "__main__":
    path = asyncio.run(tai_va_luu_qr_code("test_user", 50000))
    if path:
        print(f"QR PNG hợp lệ: {path}")
    else:
        raise SystemExit("Không tạo được QR. Xem audit_fallback.log / Firebase.")
