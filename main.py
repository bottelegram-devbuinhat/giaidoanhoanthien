import logging # l
import os # o
import asyncio # a
import traceback # tb
from html import escape
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton # t
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters # e

import bxh # bxh
from config import c, u, g, f_w, p, q, t_f # cfg
from game import chay_vong_quay_game # g
from notif import cmd_tat_tb, cmd_bat_tb, ds_tat_tb # nf
from wallet import cmd_nap, cmd_cong, cmd_tru, cmd_rut, cmd_duyet, cmd_tuchoi
from giftcode import cmd_crcode, cmd_duyetcode, xu_ly_nhap_code, check_code # gc
from admin import cmd_addadmin, cmd_kickadmin, ghi_log_tat_bot # ad
from utils import gui_huong_dan # ut
from history import xem_lich_su_user, xem_lich_su_admin # hs
import wallet # w
from firebase_logger import ghi_log_loi, ghi_log_admin, ghi_log_wallet, ghi_log_game # fgl
from datetime import datetime
from zoneinfo import ZoneInfo

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO) # log

def g_u(i, n=""): # gu
    s = str(i) # s
    if s not in u: u[s] = {}
    dv = { # dv
        "name": n,
        "balance": c.get("default_balance", 1000),
        "wins": 0,
        "bets_count": 0,
        "refs": 0,
        "referrals": [],
        "referred_by": None,
        "ref_earnings": 0,
        "blocked": False,
        "current_bet": None,
        "history": [],
        "nhan_thong_bao": False
    }
    x = False # x
    for k in dv:
        if k not in u[s]:
            u[s][k] = dv[k]
            x = True
    if x: f_w(p, u)
    return u[s]

async def c_s(u_obj: Update, x_obj: ContextTypes.DEFAULT_TYPE): # cs
    i = u_obj.effective_user.id # i
    name = u_obj.effective_user.first_name # name
    w = g_u(i, name) # w
    try:
        parts = (u_obj.message.text or "").split(maxsplit=1)
        referrer = parts[1].strip() if len(parts) > 1 else ""
        my_id = str(i)
        if referrer.isdigit() and referrer != my_id and referrer in u and not w.get("referred_by"):
            referral_list = u[referrer].setdefault("referrals", [])
            if my_id not in referral_list:
                w["referred_by"] = referrer
                referral_list.append(my_id)
                u[referrer]["refs"] = len(referral_list)
                f_w(p, u)
                ghi_log_wallet(referrer, "REFERRAL_REGISTERED", f"New referral {my_id}", referred_user=my_id)
                ghi_log_wallet(my_id, "REFERRED_BY", f"Referred by {referrer}", referrer_id=referrer)
    except Exception as exc:
        ghi_log_loi(f"Referral attribution failed: {type(exc).__name__}: {exc}", user_id=str(i))
    ghi_log_wallet(i, "START", "User opened bot", is_admin=(i in c.get("admin_ids", [])))
    if w["blocked"]:
        await u_obj.message.reply_text("<b>Tài khoản bị khóa!</b>", parse_mode="HTML")
        return
    
    ss = f"#{c.get('session_id', 1):04d}" # ss
    if i in c["admin_ids"]:
        welcome_admin = ( # wa
            f"✨━━━━━━━━━━━━━━━━━━✨\n"
            f"👑 <b>TRUNG TÂM QUẢN TRỊ</b> 👑\n"
            f"✨━━━━━━━━━━━━━━━━━━✨\n"
            f"• Xin chào Admin: <b>{escape(str(name))}</b>\n"
            f"• ID Telegram: <code>{i}</code>\n"
            f"• Trạng thái phiên hiện tại: <b>{ss}</b>\n\n"
            f"💡 <i>Sử dụng các công cụ quản trị game để vận hành.</i>"
        )
        k = ReplyKeyboardMarkup([ # k
            [KeyboardButton("👥 Quản lý người chơi"), KeyboardButton("👑 Quản lý Admin")],
            [KeyboardButton("🎟️ Tạo code"), KeyboardButton("📜 Lịch sử Server & Code")],
            [KeyboardButton("💰 Cộng/Trừ tiền"), KeyboardButton("📊 Thống kê hệ thống")],
            [KeyboardButton("🧾 Hủy phiên & hoàn cược")],
            [KeyboardButton("📖 Hướng dẫn Admin"), KeyboardButton("🛑 Tắt bot")]
        ], resize_keyboard=True)
        await u_obj.message.reply_text(welcome_admin, reply_markup=k, parse_mode="HTML")
    else:
        st = "🟢 Đang mở" if c["bet_active"] else "🔴 Đang khóa" # st
        welcome_user = ( # wu
            f"🎲━━━━━━━━━━━━━━━━━━🎲\n"
            f"🌟 <b>CHÀO MỪNG BẠN ĐẾN SẢNH GAME</b> 🌟\n"
            f"🎲━━━━━━━━━━━━━━━━━━🎲\n"
            f"• Chào mừng: <b>{escape(str(name))}</b>\n"
            f"• Số dư khả dụng: <b>{w['balance']:,.0f} VNĐ</b>\n"
            f"• Phiên hiện tại: <b>{ss}</b> ({st})\n\n"
            f"💡 <i>Nhắn nhanh <code>T[số_tiền]</code> (Tài) hoặc <code>X[số_tiền]</code> (Xỉu) để tham gia đặt cược ngay!</i>"
        )
        k = ReplyKeyboardMarkup([ # k
            [KeyboardButton("🎲 Sảnh game"), KeyboardButton("💰 Thông tin tài khoản")],
            [KeyboardButton("💳 Nạp tiền"), KeyboardButton("💸 Rút tiền")],
            [KeyboardButton("🔗 Mời bạn"), KeyboardButton("🏆 Bảng xếp hạng")],
            [KeyboardButton("📜 Lịch sử cược cá nhân"), KeyboardButton("🔕 Tắt/Bật thông báo")],
            [KeyboardButton("🎟️ Nhập code"), KeyboardButton("📖 Hướng dẫn")]
        ], resize_keyboard=True)
        await u_obj.message.reply_text(welcome_user, reply_markup=k, parse_mode="HTML")

async def h_m(u_obj: Update, x_obj: ContextTypes.DEFAULT_TYPE): # hm
    m = u_obj.message.text.strip() # m
    i = u_obj.effective_user.id # i
    w = g_u(i, u_obj.effective_user.first_name) # w
    if w["blocked"]: return

    if i in c["admin_ids"]:
        if m == "👥 Quản lý người chơi":
            kl = [[InlineKeyboardButton(f"{str(vv.get('name', 'User'))[:24]} ({kk})", callback_data=f"us_view_{kk}")] for kk, vv in list(u.items())[:80]]
            # Tích hợp thêm 2 nút Duyệt nạp tiền và Duyệt rút tiền cho Admin theo yêu cầu trên ảnh
            kl.insert(0, [
                InlineKeyboardButton("💳 Duyệt nạp tiền", callback_data="admin_deposit_queue"),
                InlineKeyboardButton("💸 Duyệt rút tiền", callback_data="admin_withdraw_queue")
            ])
            await u_obj.message.reply_text(f"👥 <b>QUẢN LÝ USER & GIAO DỊCH</b> (hiển thị tối đa 80 tài khoản đầu tiên)", reply_markup=InlineKeyboardMarkup(kl), parse_mode="HTML")
            return
        elif m == "👑 Quản lý Admin":
            await u_obj.message.reply_text(f"👑 <b>ADMINS</b>: <code>{c['admin_ids']}</code>\n• Thêm: <code>/addadmin [id]</code>\n• Kick: <code>/kickadmin [id]</code>", parse_mode="HTML")
            return
        elif m == "🎟️ Tạo code":
            await u_obj.message.reply_text("🎟️ Lệnh tạo code: <code>/crcode [mã] [số_người] [tiền]</code>", parse_mode="HTML")
            return
        elif m == "📜 Lịch sử Server & Code":
            await xem_lich_su_admin(u_obj)
            return
        elif m == "💰 Cộng/Trừ tiền":
            await u_obj.message.reply_text("💰 Lệnh:\n• <code>/cong [id] [tiền]</code>\n• <code>/tru [id] [tiền]</code>\n• Duyệt rút: <code>/duyet [id] [tiền]</code>\n• Từ chối rút: <code>/tuchoi [id] [tiền]</code>\n• Hủy phiên và hoàn cược: nút <b>Hủy phiên & hoàn cược</b> (không ép kết quả).", parse_mode="HTML")
            return
        elif m == "🧾 Hủy phiên & hoàn cược":
            if not c.get("bet_active", False):
                await u_obj.message.reply_text("⚠️ Hiện không có phiên đang mở cược để hủy.", parse_mode="HTML")
                return
            c["cancel_round_requested"] = True
            f_w("config.json", c)
            ghi_log_admin(i, "ROUND_VOID_REQUESTED", f"Admin requested cancellation of session {c.get('session_id', 1)}")
            await u_obj.message.reply_text("🧾 Đã yêu cầu hủy phiên đang mở. Bot sẽ hoàn cược và ghi log khi xử lý phiên.", parse_mode="HTML")
            return
        elif m == "📊 Thống kê hệ thống":
            tb = sum(acc.get("balance", 0) for acc in u.values()) # tb
            await u_obj.message.reply_text(f"📊 <b>THỐNG KÊ</b>\n• Tổng user: {len(u)}\n• Tổng tiền: <b>{tb:,.0f} VNĐ</b>", parse_mode="HTML")
            return
        elif m == "📖 Hướng dẫn Admin":
            await gui_huong_dan(u_obj)
            return
        elif m == "🛑 Tắt bot":
            ghi_log_tat_bot(i)
            await u_obj.message.reply_text("🛑 Đang tắt hệ thống...", parse_mode="HTML")
            os._exit(0)

    if m == "🎲 Sảnh game":
        ss = f"#{c.get('session_id', 1):04d}" # ss
        st = "🟢 Mở" if c["bet_active"] else "🔴 Khóa" # st
        await u_obj.message.reply_text(f"🎲 <b>SẢNH - {ss}</b> ({st})\n• Nhắn <code>T[tiền]</code> hoặc <code>X[tiền]</code> (1k - 100k).", parse_mode="HTML")
    elif m == "💰 Thông tin tài khoản":
        cb = w["current_bet"] # cb
        bs = f"{cb['type']} - {cb['amount']:,.0f}đ" if cb else "Chưa đặt" # bs
        it = ( # it
            f"👤 <b>THÔNG TIN TÀI KHOẢN</b>\n"
            f"• Tên: {escape(str(w['name']))}\n"
            f"• ID Telegram: <code>{i}</code>\n"
            f"• Số dư: <b>{w['balance']:,.0f} VNĐ</b>\n"
            f"• Người được giới thiệu: {w['refs']}\n"
            f"• Thưởng giới thiệu đã nhận: {int(w.get('ref_earnings', 0)):,.0f} VNĐ\n"
            f"• Danh sách ref gần đây: {', '.join(str(x) for x in w.get('referrals', [])[-10:]) or 'Chưa có'}\n"
            f"• Số trận thắng: {w['wins']}\n"
            f"• Cược phiên hiện tại: {bs}"
        )
        await u_obj.message.reply_text(it, parse_mode="HTML")
    elif m == "💳 Nạp tiền":
        kr_nap = InlineKeyboardMarkup([
            [InlineKeyboardButton("10 (10.000đ)", callback_data="nap_10"), InlineKeyboardButton("50 (50.000đ)", callback_data="nap_50"), InlineKeyboardButton("100 (100.000đ)", callback_data="nap_100")],
            [InlineKeyboardButton("200 (200.000đ)", callback_data="nap_200"), InlineKeyboardButton("500 (500.000đ)", callback_data="nap_500"), InlineKeyboardButton("1,000 (1.000.000đ)", callback_data="nap_1000")]
        ])
        await u_obj.message.reply_text("💳 <b>CHỌN MỆNH GIÁ NẠP TIỀN</b>\n• Vui lòng chọn mệnh giá bên dưới để tạo mã QR:", reply_markup=kr_nap, parse_mode="HTML")
    elif m == "💸 Rút tiền":
        await u_obj.message.reply_text("💸 Cú pháp rút tiền:\n<code>/rut [ngân_hàng] [stk] [tên_tk] [số_tiền]</code>", parse_mode="HTML")
    elif m == "🔗 Mời bạn":
        await u_obj.message.reply_text(
            f"🔗 <b>CHƯƠNG TRÌNH GIỚI THIỆU</b>\n"
            f"Mời bạn bằng liên kết bên dưới. Bạn nhận <b>1% tiền cược hợp lệ</b> của người được giới thiệu sau khi phiên chốt.\n"
            f"Link của bạn: <code>https://t.me/madeinnhatdz_bot?start={i}</code>\n"
            f"👥 Đã giới thiệu: <b>{int(w.get('refs', 0))}</b> người\n"
            f"💰 Tổng thưởng: <b>{int(w.get('ref_earnings', 0)):,.0f}đ</b>", parse_mode="HTML")
    elif m == "🏆 Bảng xếp hạng":
        await u_obj.message.reply_text(bxh.tao_noi_dung_bxh(), parse_mode="HTML")
    elif m == "📜 Lịch sử cược cá nhân":
        await xem_lich_su_user(u_obj, w, str(i))
        return
    elif m == "🔕 Tắt/Bật thông báo":
        str_i = str(i) # si
        if str_i in ds_tat_tb:
            ds_tat_tb.remove(str_i)
            f_w(t_f, ds_tat_tb)
            ghi_log_wallet(i, "NOTIFICATIONS_ENABLED", "User enabled round notifications")
            await u_obj.message.reply_text("🔔 Đã <b>BẬT</b> thông báo phiên!", parse_mode="HTML")
        else:
            ds_tat_tb.append(str_i)
            f_w(t_f, ds_tat_tb)
            ghi_log_wallet(i, "NOTIFICATIONS_DISABLED", "User disabled round notifications")
            await u_obj.message.reply_text("🔕 Đã <b>TẮT</b> thông báo phiên!", parse_mode="HTML")
    elif m == "🎟️ Nhập code":
        await u_obj.message.reply_text("🎟️ Nhắn mã dạng <code>BNDZ_XXXXXXXX</code> để nhận thưởng.", parse_mode="HTML")
    elif m == "📖 Hướng dẫn":
        await gui_huong_dan(u_obj)
    else:
        tu = m.upper() # tu
        if tu.startswith("/CODE ") or check_code(tu):
            ck = tu.replace("/CODE ", "").strip() # ck
            if not check_code(ck):
                await u_obj.message.reply_text("❌ Sai định dạng mã!", parse_mode="HTML")
                return
            await xu_ly_nhap_code(u_obj, ck)
        elif tu.startswith("T") or tu.startswith("X"):
            if not c["bet_active"]:
                await u_obj.message.reply_text("🔴 Đã hết giờ cược phiên này!", parse_mode="HTML")
                return
             
            if w.get("current_bet") is not None:
                await u_obj.message.reply_text("⚠️ Bạn đã đặt cược trong phiên này rồi!", parse_mode="HTML")
                return

            try:
                bt = "TAI" if tu.startswith("T") else "XIU" # bt
                amt = int(tu[1:]) # amt
                if amt < 1000 or amt > 100000:
                    await u_obj.message.reply_text("⚠️ Mức cược từ 1.000đ đến 100.000đ!", parse_mode="HTML")
                    return
                if w["balance"] < amt:
                    await u_obj.message.reply_text("❌ Số dư không đủ để đặt cược!", parse_mode="HTML")
                    return
                 
                w["balance"] -= amt
                w["bets_count"] += 1
                w["current_bet"] = {"type": bt, "amount": amt}
                w["nhan_thong_bao"] = True
                 
                str_i = str(i) # si
                if str_i in ds_tat_tb:
                    ds_tat_tb.remove(str_i)
                    f_w(t_f, ds_tat_tb)

                f_w(p, u)
                ghi_log_wallet(i, "PLACE_BET", f"Placed {amt} VND on {bt}", amount=amt, bet_type=bt, session_id=c.get("session_id", 1))
                ghi_log_game(c.get("session_id", 1), i, bt, amt, "BET_PLACED", balance_after=w["balance"])
                nt = "TÀI 🎲" if bt == "TAI" else "XỈU 🎲" # nt
                await u_obj.message.reply_text(f"✅ Đặt cược thành công <b>{amt:,.0f}đ</b> vào cửa <b>{nt}</b>!", parse_mode="HTML")
            except Exception as exc:
                ghi_log_loi(f"Bet input failed: {type(exc).__name__}: {exc}", user_id=str(i), message=m)
                await u_obj.message.reply_text("❌ Không đọc được mức cược. Ví dụ: T10000 hoặc X50000.")

async def f_c(u_obj: Update, x_obj: ContextTypes.DEFAULT_TYPE):
    query = u_obj.callback_query
    data = query.data or ""
    actor = query.from_user.id
    is_admin = actor in c.get("admin_ids", [])
    
    # Thêm nhánh xử lý 2 callback_data đúng như yêu cầu trên ảnh số 3
    if data == "admin_deposit_queue":
        if actor not in c.get("admin_ids", []):
            await query.answer(
                "Bạn không có quyền thực hiện thao tác này.",
                show_alert=True
            )
            return
        await query.answer()
        await query.message.reply_text(
            "💳 <b>QUẢN LÝ NẠP TIỀN</b>\n\n"
            "Bot hiện chỉ tạo QR và ghi lịch sử yêu cầu; chưa có webhook/API ngân hàng "
            "để xác minh tiền vào tự động. Không cộng số dư chỉ dựa trên ảnh QR. "
            "Đối chiếu giao dịch thực nhận trước khi dùng /cong.",
            parse_mode="HTML",
        )
        return

    elif data == "admin_withdraw_queue":
        if actor not in c.get("admin_ids", []):
            await query.answer("Bạn không có quyền thực hiện thao tác này.", show_alert=True)
            return
        await query.answer()
        pending_rows = []
        for uid, account in list(u.items()):
            pending = account.get("pending_withdrawal")
            if not pending:
                continue
            amount = int(pending.get("amount", 0))
            bank = escape(str(pending.get("bank", "Không rõ")))
            acc_no = escape(str(pending.get("account_number", "")))
            acc_name = escape(str(pending.get("account_name", "")))
            pending_rows.append(
                f"• <code>{escape(str(uid))}</code> — <b>{amount:,}đ</b>\n"
                f"  {bank} | {acc_no} | {acc_name}\n"
                f"  Duyệt: <code>/duyet {escape(str(uid))} {amount}</code> | "
                f"Từ chối: <code>/tuchoi {escape(str(uid))} {amount}</code>"
            )
        body = "\n\n".join(pending_rows) if pending_rows else "Không có yêu cầu rút đang chờ."
        await query.message.reply_text(
            "💸 <b>YÊU CẦU RÚT TIỀN CHỜ DUYỆT</b>\n\n" + body,
            parse_mode="HTML",
        )
        return

    if data.startswith("nap_"):
        await query.answer()
        try:
            value = int(data.split("_", 1)[1])
            class FakeArgs: args = [str(value * 1000)]
            class FakeUpdate:
                effective_user = query.from_user
                reply_text = query.message.reply_text
                reply_photo = query.message.reply_photo
            await cmd_nap(FakeUpdate(), FakeArgs())
        except Exception as exc:
            ghi_log_loi(f"Deposit callback failed: {type(exc).__name__}: {exc}", user_id=str(actor))
            await query.message.reply_text("❌ Không tạo được QR. Lỗi đã được ghi log.")
        return
    if not is_admin:
        await query.answer("Bạn không có quyền thực hiện thao tác này.", show_alert=True)
        return
    if data.startswith("us_view_"):
        uid = data[len("us_view_"):]
        if uid not in u:
            await query.answer("Không tìm thấy người chơi.", show_alert=True); return
        user = u[uid]
        blocked = bool(user.get("blocked", False))
        action = "us_unblock_" if blocked else "us_block_"
        label = "🔓 Mở chặn người chơi" if blocked else "🚫 Chặn người chơi"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=f"{action}{uid}")]])
        text = (f"👤 <b>Người chơi {escape(uid)}</b>\nTên: {escape(str(user.get('name','(không tên)')))}\n"
                f"Số dư: {int(user.get('balance',0)):,}đ\nThắng: {int(user.get('wins',0))}\n"
                f"Trạng thái: {'BỊ CHẶN' if blocked else 'Đang hoạt động'}")
        await query.answer()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")
        return
    if data.startswith("us_block_") or data.startswith("us_unblock_"):
        block = data.startswith("us_block_")
        uid = data[len("us_block_"):] if block else data[len("us_unblock_"):]
        if uid not in u:
            await query.answer("Không tìm thấy người chơi.", show_alert=True); return
        u[uid]["blocked"] = block
        f_w(p, u)
        action = "BLOCK_USER" if block else "UNBLOCK_USER"
        ghi_log_admin(actor, action, f"{'Blocked' if block else 'Unblocked'} user {uid}", target_user=uid)
        ghi_log_wallet(uid, action, f"Admin {actor} {'blocked' if block else 'unblocked'} this user", admin_id=str(actor))
        await query.answer("Đã chặn người chơi." if block else "Đã mở chặn người chơi.", show_alert=True)
        label = "🔓 Mở chặn người chơi" if block else "🚫 Chặn người chơi"
        next_action = "us_unblock_" if block else "us_block_"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=f"{next_action}{uid}")]])
        await query.edit_message_reply_markup(reply_markup=keyboard)
        return
    await query.answer("Thao tác không hợp lệ.", show_alert=True)

async def e_h(u_obj, c_obj):
    error = c_obj.error
    trace = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    try:
        with open("system_error.txt", "a", encoding="utf-8") as f:
            f.write(f"--- SYSTEM ERROR ---\n{trace}\n")
    except OSError:
        logging.exception("Could not write system_error.txt")
    ghi_log_loi(f"{type(error).__name__}: {error}", traceback=trace[-3500:])
    logging.error("Unhandled Telegram handler exception", exc_info=(type(error), error, error.__traceback__))

async def greeting_scheduler(app_obj):
    """Send daily greetings at 06:00 and 08:00 Vietnam time."""
    tz = ZoneInfo("Asia/Ho_Chi_Minh")
    targets = ((6, 0), (8, 0))
    while True:
        now = datetime.now(tz)
        candidates = []
        for hour, minute in targets:
            candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if candidate <= now:
                from datetime import timedelta
                candidate += timedelta(days=1)
            candidates.append(candidate)
        next_run = min(candidates)
        await asyncio.sleep(max(1, (next_run - now).total_seconds()))

        sent_key = next_run.strftime("%Y-%m-%d:%H:%M")
        sent = c.setdefault("morning_greetings_sent", [])
        if sent_key in sent:
            continue
        for uid, account in list(u.items()):
            if account.get("blocked", False):
                continue
            try:
                name = escape(str(account.get("name") or "bạn"))
                balance = int(account.get("balance", 0))
                greeting = (
                    f"☀️ Chào buổi sáng, <b>{name}</b>!\n"
                    f"Chúc bạn một ngày tốt lành.\n"
                    f"💰 Số dư hiện tại: <b>{balance:,} VNĐ</b>"
                )
                await app_obj.bot.send_message(
                    chat_id=int(uid), text=greeting, parse_mode="HTML"
                )
            except Exception as exc:
                ghi_log_loi(
                    f"Morning greeting failed: {type(exc).__name__}: {exc}",
                    user_id=str(uid), scheduled_at=sent_key,
                )
        sent.append(sent_key)
        c["morning_greetings_sent"] = sent[-60:]
        f_w("config.json", c)


async def _post_init(app_obj):
    """Start background jobs only after the Telegram application is initialized."""
    app_obj.create_task(chay_vong_quay_game(app_obj), name="game-round-loop")
    app_obj.create_task(greeting_scheduler(app_obj), name="morning-greeting-loop")


def main():
    try:
        from keep_alive import k as start_health_server
        start_health_server()
    except OSError as exc:
        logging.warning("Health endpoint not started: %s", exc)

    tk = c.get("token", "").strip()
    if not tk:
        raise RuntimeError(
            "Thiếu TELEGRAM_BOT_TOKEN. Hãy đặt biến môi trường TELEGRAM_BOT_TOKEN "
            "bằng token bot mới từ BotFather trước khi chạy."
        )

    app = Application.builder().token(tk).post_init(_post_init).build()
    app.add_handler(CommandHandler("start", c_s))
    app.add_handler(CommandHandler("nap", cmd_nap))
    app.add_handler(CommandHandler("cong", cmd_cong))
    app.add_handler(CommandHandler("tru", cmd_tru))
    app.add_handler(CommandHandler("rut", cmd_rut))
    app.add_handler(CommandHandler("duyet", cmd_duyet))
    app.add_handler(CommandHandler("tuchoi", cmd_tuchoi))
    app.add_handler(CommandHandler("crcode", cmd_crcode))
    app.add_handler(CommandHandler("duyetcode", cmd_duyetcode))
    app.add_handler(CommandHandler("addadmin", cmd_addadmin))
    app.add_handler(CommandHandler("kickadmin", cmd_kickadmin))
    app.add_handler(CommandHandler("tatthongbao", cmd_tat_tb))
    app.add_handler(CommandHandler("batthongbao", cmd_bat_tb))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, h_m))
    app.add_handler(CallbackQueryHandler(f_c))
    app.add_error_handler(e_h)

    logging.info("Starting Telegram bot polling")
    app.run_polling(drop_pending_updates=False)


if __name__ == "__main__":
    main()
