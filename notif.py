from config import f_r, f_w, t_f
from firebase_logger import ghi_log_wallet

ds_tat_tb = f_r(t_f, []) # dsttb

async def cmd_tat_tb(u_obj, x_obj): # cttb
    i = str(u_obj.effective_user.id)
    if i not in ds_tat_tb:
        ds_tat_tb.append(i)
        f_w(t_f, ds_tat_tb)
    ghi_log_wallet(i, "NOTIFICATIONS_DISABLED", "User disabled round notifications via command")
    await u_obj.message.reply_text("🔕 Đã tắt thông báo phiên thành công!", parse_mode="HTML")

async def cmd_bat_tb(u_obj, x_obj): # cbtt
    i = str(u_obj.effective_user.id)
    if i in ds_tat_tb:
        ds_tat_tb.remove(i)
        f_w(t_f, ds_tat_tb)
    ghi_log_wallet(i, "NOTIFICATIONS_ENABLED", "User enabled round notifications via command")
    await u_obj.message.reply_text("🔔 Đã bật lại thông báo thành công!", parse_mode="HTML")