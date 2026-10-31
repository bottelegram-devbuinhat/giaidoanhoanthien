import os
from html import escape
from config import c

async def gui_huong_dan(update):
    user_id = update.effective_user.id
    filename = "huong_dan_admin.txt" if user_id in c["admin_ids"] else "huong_dan_nguoi_choi.txt"
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f: text = f.read()
    else:
        text = "Không tìm thấy file hướng dẫn trên hệ thống."
    await update.message.reply_text(text, parse_mode="HTML")
