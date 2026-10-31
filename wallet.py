import os
from datetime import datetime
from config import u, f_w, p, lich_su_nap_rut, c
from ngan_hang_checker import chuan_hoa_va_check_ngan_hang
from firebase_logger import ghi_log_wallet, ghi_log_admin, ghi_log_loi
from qr_generator import tai_va_luu_qr_code


def ghi_ls_nap_rut(i, detail):
    with open(lich_su_nap_rut, "a", encoding="utf-8") as f:
        # Sử dụng thời gian hiện tại có múi giờ chuẩn theo yêu cầu
        f.write(f"USER:{i} | [{datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %z')}] {detail}\n")


async def cmd_nap(u_obj, x_obj):
    message = getattr(u_obj, "message", u_obj)
    effective_user = getattr(u_obj, "effective_user", None)
    i = str(effective_user.id if effective_user else message.chat.id)
    args = getattr(x_obj, "args", []) or []
    if not args:
        ghi_log_wallet(i, "DEPOSIT_REQUEST_FAILED", "Missing amount")
        await message.reply_text("⚠️ Cú pháp: /nap [số_tiền] (tối thiểu 10.000đ)")
        return
    try: amount = int(args[0])
    except (ValueError, TypeError):
        await message.reply_text("❌ Số tiền không hợp lệ!")
        ghi_log_wallet(i, "DEPOSIT_REQUEST_FAILED", f"Invalid amount: {args[0]!r}")
        return
    if amount < 10000 or amount > 100000000:
        await message.reply_text("❌ Số tiền nạp phải từ 10.000đ đến 100.000.000đ.")
        ghi_log_wallet(i, "DEPOSIT_REQUEST_FAILED", f"Out-of-range amount: {amount}")
        return
    content = f"NAPTIEN_{i}"
    ghi_ls_nap_rut(i, f"YÊU CẦU QR NẠP: {amount:,.0f}đ | Nội dung: {content}")
    ghi_log_wallet(i, "REQUEST_DEPOSIT_QR", f"Requested QR for {amount} VND", amount=amount)
    qr_path = await tai_va_luu_qr_code(i, amount)
    if not qr_path:
        await message.reply_text("❌ Chưa tạo được mã QR hợp lệ. Hãy thử lại sau hoặc liên hệ quản trị viên.")
        return
    caption = ("<b>HƯỚNG DẪN CHUYỂN KHOẢN</b>\n\n"
        "Ngân hàng: <b>MB BANK</b>\n"
        "Số tài khoản: <code>860671050278271</code>\n"
        "Chủ tài khoản: <b>BUI NGUYEN XUAN NHAT</b>\n"
        f"Số tiền: <b>{amount:,.0f} VNĐ</b>\nNội dung: <code>{content}</code>\n\n"
        "⚠️ QR chỉ tạo yêu cầu chuyển khoản; bot hiện chưa xác minh giao dịch ngân hàng tự động. Không coi ảnh QR là xác nhận đã nạp tiền.")
    try:
        with open(qr_path, "rb") as qr_file:
            await message.reply_photo(photo=qr_file, caption=caption, parse_mode="HTML")
    except Exception as exc:
        ghi_log_loi(f"QR upload failed: {type(exc).__name__}: {exc}", user_id=i, amount=amount)
        await message.reply_text("❌ Telegram không nhận được ảnh QR hợp lệ. Lỗi đã được ghi log.")


async def cmd_cong(u_obj, x_obj):
    admin = u_obj.effective_user.id
    if admin not in c["admin_ids"]: return
    args = x_obj.args or []
    if len(args) != 2:
        await u_obj.message.reply_text("Cú pháp: /cong [user_id] [số_tiền_dương]")
        return
    try: uid, amount = str(int(args[0])), int(args[1])
    except ValueError:
        await u_obj.message.reply_text("ID và số tiền phải là số nguyên."); return
    if amount <= 0 or uid not in u:
        await u_obj.message.reply_text("Số tiền phải dương và user phải tồn tại."); return
    before = int(u[uid].get("balance", 0)); u[uid]["balance"] = before + amount; f_w(p, u)
    detail = f"Admin {admin} credited {amount} VND; balance {before} -> {u[uid]['balance']}"
    ghi_log_admin(admin, "BALANCE_CREDIT", detail, target_user=uid, amount=amount)
    ghi_log_wallet(uid, "ADMIN_CREDIT", detail, admin_id=str(admin), amount=amount)
    ghi_ls_nap_rut(uid, f"ADMIN {admin} CỘNG TIỀN: +{amount:,.0f}đ")
    await u_obj.message.reply_text(f"✅ Đã cộng {amount:,.0f}đ cho <code>{uid}</code>.", parse_mode="HTML")


async def cmd_tru(u_obj, x_obj):
    admin = u_obj.effective_user.id
    if admin not in c["admin_ids"]: return
    args = x_obj.args or []
    if len(args) != 2:
        await u_obj.message.reply_text("Cú pháp: /tru [user_id] [số_tiền_dương]"); return
    try: uid, amount = str(int(args[0])), int(args[1])
    except ValueError:
        await u_obj.message.reply_text("ID và số tiền phải là số nguyên."); return
    if amount <= 0 or uid not in u:
        await u_obj.message.reply_text("Số tiền phải dương và user phải tồn tại."); return
    before = int(u[uid].get("balance", 0))
    if before < amount:
        await u_obj.message.reply_text("Không thể trừ vượt số dư hiện có."); return
    u[uid]["balance"] = before - amount; f_w(p, u)
    detail = f"Admin {admin} debited {amount} VND; balance {before} -> {u[uid]['balance']}"
    ghi_log_admin(admin, "BALANCE_DEBIT", detail, target_user=uid, amount=amount)
    ghi_log_wallet(uid, "ADMIN_DEBIT", detail, admin_id=str(admin), amount=amount)
    ghi_ls_nap_rut(uid, f"ADMIN {admin} TRỪ TIỀN: -{amount:,.0f}đ")
    await u_obj.message.reply_text(f"✅ Đã trừ {amount:,.0f}đ của <code>{uid}</code>.", parse_mode="HTML")


async def cmd_rut(u_obj, x_obj):
    uid = str(u_obj.effective_user.id)
    args = x_obj.args or []
    if len(args) < 4:
        ghi_log_wallet(uid, "WITHDRAW_FAILED", "Invalid syntax")
        await u_obj.message.reply_text("Cú pháp: /rut [ngân_hàng] [stk] [tên_tài_khoản_nhiều_từ] [số_tiền]")
        return
    try: amount = int(args[-1])
    except ValueError:
        await u_obj.message.reply_text("Số tiền rút không hợp lệ."); return
    bank_text, account_number = args[0], args[1]
    account_name = " ".join(args[2:-1]).strip()
    valid_bank, bank_name = chuan_hoa_va_check_ngan_hang(bank_text)
    if not valid_bank or not account_number.isdigit() or len(account_name) < 2 or not (100000 <= amount <= 1000000):
        ghi_log_wallet(uid, "WITHDRAW_FAILED", "Invalid bank/account/amount")
        await u_obj.message.reply_text("Thông tin không hợp lệ. Số tiền rút từ 100.000đ đến 1.000.000đ."); return
    if uid not in u: return
    if u[uid].get("pending_withdrawal"):
        await u_obj.message.reply_text("Bạn đang có yêu cầu rút tiền chờ xử lý."); return
    if int(u[uid].get("balance", 0)) < amount:
        ghi_log_wallet(uid, "WITHDRAW_FAILED", f"Insufficient balance for {amount} VND")
        await u_obj.message.reply_text("Số dư không đủ."); return
    before = int(u[uid]["balance"])
    u[uid]["balance"] = before - amount
    u[uid]["pending_withdrawal"] = {
        "amount": amount, 
        "bank": bank_name, 
        "account_number": account_number,
        "account_name": account_name, 
        "requested_at": datetime.now().astimezone().isoformat(timespec="seconds")
    }
    f_w(p, u)
    ghi_ls_nap_rut(uid, f"YÊU CẦU RÚT: {amount:,.0f}đ | {bank_name} | STK: {account_number} | TÊN: {account_name}")
    ghi_log_wallet(uid, "REQUEST_WITHDRAWAL", f"Requested {amount} VND to {bank_name}; balance {before}->{u[uid]['balance']}", amount=amount)
    await u_obj.message.reply_text("⏳ Đã gửi yêu cầu rút tiền, số dư đã được giữ lại. Chờ admin duyệt.")


async def cmd_duyet(u_obj, x_obj):
    admin = u_obj.effective_user.id
    if admin not in c["admin_ids"]: return
    args = x_obj.args or []
    if len(args) != 2:
        await u_obj.message.reply_text("Cú pháp: /duyet [user_id] [số_tiền]"); return
    try: uid, amount = str(int(args[0])), int(args[1])
    except ValueError:
        await u_obj.message.reply_text("ID và số tiền phải là số nguyên."); return
    if amount <= 0 or uid not in u:
        await u_obj.message.reply_text("Dữ liệu không hợp lệ."); return
    pending = u[uid].get("pending_withdrawal")
    if not pending or int(pending.get("amount", 0)) != amount:
        await u_obj.message.reply_text("Không có yêu cầu rút đang chờ đúng số tiền này."); return
    del u[uid]["pending_withdrawal"]; f_w(p, u)
    detail = f"Admin {admin} approved withdrawal {amount} VND"
    ghi_log_admin(admin, "APPROVE_WITHDRAWAL", detail, target_user=uid, amount=amount)
    ghi_log_wallet(uid, "WITHDRAWAL_APPROVED", detail, admin_id=str(admin), amount=amount)
    ghi_ls_nap_rut(uid, f"ADMIN {admin} ĐÃ DUYỆT RÚT: {amount:,.0f}đ")
    try: await x_obj.bot.send_message(chat_id=int(uid), text=f"Yêu cầu rút {amount:,.0f}đ đã được duyệt.")
    except Exception as exc: ghi_log_loi(f"Cannot notify withdrawal approval: {exc}", user_id=uid)
    await u_obj.message.reply_text(f"Đã duyệt yêu cầu rút của <code>{uid}</code>.", parse_mode="HTML")


async def cmd_tuchoi(u_obj, x_obj):
    admin = u_obj.effective_user.id
    if admin not in c["admin_ids"]: return
    args = x_obj.args or []
    if len(args) != 2:
        await u_obj.message.reply_text("Cú pháp: /tuchoi [user_id] [số_tiền]"); return
    try: uid, amount = str(int(args[0])), int(args[1])
    except ValueError:
        await u_obj.message.reply_text("ID và số tiền phải là số nguyên."); return
    if amount <= 0 or uid not in u:
        await u_obj.message.reply_text("Dữ liệu không hợp lệ."); return
    pending = u[uid].get("pending_withdrawal")
    if not pending or int(pending.get("amount", 0)) != amount:
        await u_obj.message.reply_text("Không có yêu cầu rút đang chờ đúng số tiền này."); return
    before = int(u[uid].get("balance", 0)); u[uid]["balance"] = before + amount
    del u[uid]["pending_withdrawal"]; f_w(p, u)
    detail = f"Admin {admin} rejected withdrawal {amount} VND; refund balance {before}->{u[uid]['balance']}"
    ghi_log_admin(admin, "REJECT_WITHDRAWAL_REFUND", detail, target_user=uid, amount=amount)
    ghi_log_wallet(uid, "WITHDRAWAL_REJECTED_REFUND", detail, admin_id=str(admin), amount=amount)
    ghi_ls_nap_rut(uid, f"ADMIN {admin} TỪ CHỐI RÚT: {amount:,.0f}đ | Hoàn tiền")
    try: await x_obj.bot.send_message(chat_id=int(uid), text=f"Yêu cầu rút {amount:,.0f}đ bị từ chối; đã hoàn tiền.")
    except Exception as exc: ghi_log_loi(f"Cannot notify withdrawal rejection: {exc}", user_id=uid)
    await u_obj.message.reply_text(f"Đã từ chối và hoàn tiền cho <code>{uid}</code>.", parse_mode="HTML")
