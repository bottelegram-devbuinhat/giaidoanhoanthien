from datetime import datetime # dt
from config import c, r, f_w # cfg
from firebase_logger import ghi_log_admin # gla

async def cmd_addadmin(u_obj, x_obj): # ca
    cur = u_obj.effective_user.id
    if cur not in c["admin_ids"]: return
    args = x_obj.args
    if not args:
        await u_obj.message.reply_text("Cú pháp: /addadmin [user_id]"); return
    try:
        na = int(args[0])
        if na not in c["admin_ids"]:
            c["admin_ids"].append(na)
            f_w(r, c)
            ghi_log_admin(cur, "ADD_ADMIN", f"Thêm admin mới ID: {na}")
            await u_obj.message.reply_text(f"👑 Đã thêm Admin: <code>{na}</code>", parse_mode="HTML")
    except Exception as exc:
        from firebase_logger import ghi_log_loi
        ghi_log_loi(f"addadmin failed: {type(exc).__name__}: {exc}", admin_id=str(cur))

async def cmd_kickadmin(u_obj, x_obj): # cka
    cur = u_obj.effective_user.id
    if cur != c.get("admin_ids", [8792000582])[0]:
        await u_obj.message.reply_text("❌ Chỉ Admin tối cao mới có quyền này!", parse_mode="HTML")
        return
    args = x_obj.args
    if not args:
        await u_obj.message.reply_text("Cú pháp: /kickadmin [user_id]"); return
    try:
        tar = int(args[0])
        if tar == c.get("admin_ids", [8792000582])[0]: return
        if tar in c["admin_ids"]:
            c["admin_ids"].remove(tar)
            f_w(r, c)
            ghi_log_admin(cur, "KICK_ADMIN", f"Xóa quyền admin ID: {tar}")
            await u_obj.message.reply_text(f"✅ Đã xóa quyền Admin của: <code>{tar}</code>", parse_mode="HTML")
    except Exception as exc:
        from firebase_logger import ghi_log_loi
        ghi_log_loi(f"kickadmin failed: {type(exc).__name__}: {exc}", admin_id=str(cur))

def ghi_log_tat_bot(admin_id): # gltb
    """Lưu sự kiện TẮT BOT trước khi tắt hoàn toàn kèm ID người tắt"""
    msg = f"Hệ thống bot đã bị tắt lệnh thủ công bởi Admin ID: {admin_id}"
    ghi_log_admin(admin_id, "SHUTDOWN_BOT", msg)
    with open("system_error.txt", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] SHUTDOWN BY ADMIN {admin_id}\n")