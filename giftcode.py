import json # j
import os
import re
from datetime import datetime # dt
from config import g, q, f_w, p, u, c # cfg
from firebase_logger import ghi_log_admin, ghi_log_wallet # gl

# Pending code approvals persist across restarts.
PENDING_CODES_FILE = "pending_codes.json"
try:
    with open(PENDING_CODES_FILE, "r", encoding="utf-8") as stream:
        pending_codes = json.load(stream)
except (OSError, json.JSONDecodeError):
    pending_codes = {}


def save_pending_codes():
    temp = PENDING_CODES_FILE + ".tmp"
    with open(temp, "w", encoding="utf-8") as stream:
        json.dump(pending_codes, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, PENDING_CODES_FILE)

def check_code(k): # cc
    """Kiểm tra định dạng mã code hợp lệ (BNDZ_xxx)"""
    return bool(re.fullmatch(r"BNDZ_[A-Z0-9_-]{1,40}", str(k)))

async def cmd_crcode(u_obj, x_obj): # crc
    """Lệnh tạo code dành cho Admin: /crcode [mã] [số_lượng] [số_tiền]"""
    aid = u_obj.effective_user.id # aid
    if aid not in c["admin_ids"]: 
        return
        
    args = x_obj.args # a
    if len(args) < 3:
        await u_obj.message.reply_text(
            "⚠️ <b>Cú pháp tạo mã:</b> <code>/crcode [mã] [số_lượng] [số_tiền]</code>\n"
            "<i>(Ví dụ: /crcode BNDZ_VIP100K 10 100000)</i>", 
            parse_mode="HTML"
        )
        return

    code_str = args[0].upper() # cs
    try:
        mu = int(args[1]) # max_uses (số lượt dùng)
        amt = int(args[2]) # amount (số tiền cộng/trừ)
    except ValueError:
        await u_obj.message.reply_text("❌ Số lượng người dùng và số tiền phải là số nguyên!", parse_mode="HTML")
        return

    if mu <= 0 or mu > 1000 or amt <= 0 or amt > 200000:
        await u_obj.message.reply_text("❌ Số lượt phải từ 1–1.000 và giá trị code từ 1–200.000đ.")
        ghi_log_admin(aid, "CREATE_CODE_REJECTED", f"Invalid limits for {code_str}: uses={mu}, amount={amt}")
        return

    if not check_code(code_str):
        await u_obj.message.reply_text("❌ Mã code phải có định dạng <code>BNDZ_XXXXXXXX</code>!", parse_mode="HTML")
        return

    if code_str in g or code_str in pending_codes:
        await u_obj.message.reply_text("❌ Mã code này đã tồn tại hoặc đang chờ duyệt!", parse_mode="HTML")
        return

    # Ngưỡng kiểm duyệt an toàn cho Admin thường
    nguong_tien = 200000 # nt (Tối đa 200k/mã)
    nguong_luot = 50 # nl (Tối đa 50 lượt)

    # Nếu Admin thường tạo mã vượt hạn mức -> Đưa vào hàng chờ duyệt
    if aid != 8792000582 and (abs(amt) > nguong_tien or mu > nguong_luot):
        pending_codes[code_str] = {"creator": aid, "max_uses": mu, "amount": amt}
        save_pending_codes()
        ghi_log_admin(aid, "REQUEST_CREATE_CODE", f"Xin tạo mã khủng {code_str} (SL: {mu}, Tiền: {amt:,.0f}đ) - Chờ duyệt")
        
        await u_obj.message.reply_text(
            f"⏳ <b>Mã code vượt hạn mức an toàn!</b>\n"
            f"Mã <code>{code_str}</code> (Trị giá: {amt:,.0f}đ | Số lượng: {mu}) đã được gửi vào danh sách chờ.\n"
            f"👑 Yêu cầu cần <b>Admin tối cao (8792000582)</b> duyệt lệnh: <code>/duyetcode {code_str}</code>",
            parse_mode="HTML"
        )
        return

    # Nếu là Admin tối cao hoặc tạo mã trong hạn mức cho phép
    g[code_str] = {"amount": amt, "max_uses": mu, "used": []}
    f_w(q, g)
    ghi_log_admin(aid, "CREATE_CODE", f"Tạo thành công mã {code_str} | SL: {mu} | Tiền: {amt:,.0f}đ")
    await u_obj.message.reply_text(f"✅ Đã tạo thành công mã Giftcode: <code>{code_str}</code>", parse_mode="HTML")

async def cmd_duyetcode(u_obj, x_obj): # cdc
    """Lệnh dành riêng cho Admin tối cao để duyệt mã code khủng"""
    aid = u_obj.effective_user.id # aid
    if aid != 8792000582:
        await u_obj.message.reply_text("❌ Chỉ có Admin tối cao (<code>8792000582</code>) mới có quyền duyệt!", parse_mode="HTML")
        return

    args = x_obj.args # a
    if not args:
        await u_obj.message.reply_text("⚠️ Nhập mã cần duyệt: <code>/duyetcode [mã]</code>", parse_mode="HTML")
        return
        
    code_str = args[0].upper() # cs

    if code_str in pending_codes:
        data = pending_codes[code_str] # d
        g[code_str] = {"amount": data["amount"], "max_uses": data["max_uses"], "used": []}
        f_w(q, g)
        
        creator = data["creator"] # cr
        del pending_codes[code_str]
        save_pending_codes()
        
        ghi_log_admin(aid, "APPROVE_CODE", f"Đã duyệt mã khủng {code_str} do Admin {creator} yêu cầu")
        await u_obj.message.reply_text(f"🎉 <b>Đã duyệt thành công mã khủng:</b> <code>{code_str}</code>!", parse_mode="HTML")
    else:
        await u_obj.message.reply_text("❌ Không tìm thấy mã này trong danh sách chờ duyệt!", parse_mode="HTML")

async def xu_ly_nhap_code(u_obj, ck): # xnc
    """Xử lý logic khi người dùng nhập mã quà tặng"""
    uid = str(u_obj.effective_user.id) # uid
    
    if ck not in g:
        ghi_log_wallet(uid, "REDEEM_CODE_FAILED", f"Unknown code: {ck[:80]}")
        await u_obj.message.reply_text("❌ Mã quà tặng không tồn tại!", parse_mode="HTML")
        return

    gd = g[ck] # gd
    if gd.get("disabled", False):
        ghi_log_wallet(uid, "REDEEM_CODE_REJECTED", f"Attempt to redeem disabled code {ck}")
        await u_obj.message.reply_text("❌ Mã quà tặng này đã bị vô hiệu hóa, vui lòng liên hệ quản trị viên.")
        return
    if "used" not in gd: gd["used"] = []

    # Kiểm tra giới hạn số lượt sử dụng
    if len(gd["used"]) >= gd.get("max_uses", 1):
        ghi_log_wallet(uid, "REDEEM_CODE_FAILED", f"Code exhausted: {ck}")
        await u_obj.message.reply_text("❌ Mã quà tặng này đã hết lượt sử dụng!", parse_mode="HTML")
        return

    # Kiểm tra xem user đã nhập mã này chưa
    if uid in gd["used"]:
        ghi_log_wallet(uid, "REDEEM_CODE_FAILED", f"Duplicate redemption attempt: {ck}")
        await u_obj.message.reply_text("❌ Bạn đã sử dụng mã này rồi!", parse_mode="HTML")
        return

    # Thực hiện cộng / trừ tiền ví dựa trên giá trị amount của code
    amt = int(gd["amount"]) # amt
    if amt <= 0:
        ghi_log_wallet(uid, "REDEEM_CODE_REJECTED", f"Invalid non-positive code value for {ck}")
        await u_obj.message.reply_text("❌ Mã quà tặng không hợp lệ.")
        return
    if uid not in u:
        await u_obj.message.reply_text("❌ Hãy nhấn /start trước khi nhập code.")
        return
    gd["used"].append(uid)
    u[uid]["balance"] = int(u[uid].get("balance", 0)) + amt
    
    f_w(q, g)
    f_w(p, u)

    # Ghi log người dùng nhập code thành công lên Firebase
    ghi_log_wallet(uid, "REDEEM_CODE", f"Nhập mã {ck} thành công | Biến động: {amt:+,.0f}đ", amount=amt)
    ghi_log_admin("SYSTEM", "CODE_REDEEMED", f"User {uid} redeemed code {ck} for {amt} VND")
    
    so_tien_str = f"+{amt:,.0f}" if amt > 0 else f"{amt:,.0f}"
    await u_obj.message.reply_text(
        f"🎉 <b>Nhập mã quà tặng thành công!</b>\n"
        f"• Mã: <code>{ck}</code>\n"
        f"• Biến động số dư: <b>{so_tien_str} VNĐ</b>\n"
        f"• Số dư mới: <b>{u[uid]['balance']:,.0f} VNĐ</b>", 
        parse_mode="HTML"
    )