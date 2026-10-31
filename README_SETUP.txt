HUONG DAN CAI DAT BAN DA SUA
===========================

1. Cai Python 3.10 tro len.
2. Cai thu vien Python:
   pip install -r requirements.txt
3. Neu CairoSVG khong cai duoc tren Linux/Termux, can cai them thu vien he thong Cairo theo huong dan cua he dieu hanh.
4. Token thu nghiem da duoc khoi phuc trong config.json. Neu muon ghi de, dat bien moi truong TELEGRAM_BOT_TOKEN.
   - Linux/Termux: export TELEGRAM_BOT_TOKEN="TOKEN_MOI"
   - Windows CMD: set TELEGRAM_BOT_TOKEN=TOKEN_MOI
   Khong ghi token vao config.json.
5. Chay bot:
   python main.py
6. Kiem tra log neu co loi:
   - system_error.txt
   - game_error.log
   - audit_fallback.log (neu Firebase khong nhan log)
   - Firebase RTDB: system_errors, wallet_logs, admin_logs, game_logs

Luu y:
- Token thu nghiem duoc giu lai trong config.json theo yeu cau.
- QR chi tao thong tin chuyen khoan; chua co webhook/nguon du lieu ngan hang de tu dong xac minh giao dich. Admin can chuyen khoan rut tien thu cong truoc khi dung /duyet.
- Kiem tra Firebase Realtime Database Rules truoc khi chay tren du lieu that.
- Da kiem thu offline cac luong logic va cu phap; chua the xac minh ket noi Telegram/Firebase/ngan hang that trong moi truong nay.


CHUC NANG MOI (ban cap nhat)
- Loi chao buoi sang duoc gui luc 06:00 va 08:00 theo gio Viet Nam cho cac tai khoan da tung mo bot va khong bi chan.
- Profile hien thi so nguoi gioi thieu, danh sach 10 ref gan nhat va tong thuong ref.
- Thuong ref mac dinh 1% tien cuoc cua nguoi duoc gioi thieu, chi tinh sau khi phien duoc chot; co the chinh referral_rate trong config.json. Muc 2% co the an het phan lon bien loi nhuan ly thuyet khi ti le tra 1.95x, nen mac dinh 1%.
- Admin co nut "Huy phien & hoan cuoc" chi khi phien dang mo; thao tac hoan cuoc duoc ghi log. Khong co chuc nang ep ket qua am tham.
- Ma phien duoc tang va luu truoc khi mo cuoc, tranh dung lai ma phien neu bot restart.
- Telegram khong cho doi icon nut tuy y ngoai emoji Unicode; giao dien dung emoji va bo cuc text.
