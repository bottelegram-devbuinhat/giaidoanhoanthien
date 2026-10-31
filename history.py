import os
from html import escape

from config import g, l_f, lich_su_nap_rut


async def xem_lich_su_user(u_obj, user_data, uid):
    history = user_data.get("history", [])
    text = "📜 <b>LỊCH SỬ CƯỢC CÁ NHÂN</b>\n" + "—" * 15 + "\n"
    if not history:
        text += "• Chưa có lịch sử cược.\n"
    else:
        text += "\n".join(f"• {escape(str(item))}" for item in history) + "\n"

    text += "\n💳 <b>LỊCH SỬ NẠP/RÚT GIAO DỊCH:</b>\n" + "—" * 15 + "\n"
    found = False
    if os.path.exists(lich_su_nap_rut):
        with open(lich_su_nap_rut, "r", encoding="utf-8") as stream:
            for line in stream:
                # Match the complete user-id field, not a prefix of another ID.
                if line.startswith(f"USER:{uid} |"):
                    found = True
                    parts = line.split("|", 1)
                    if len(parts) > 1:
                        text += f"• {escape(parts[1].strip())}\n"
    if not found:
        text += "• Chưa có giao dịch nạp rút nào."

    await u_obj.message.reply_text(text, parse_mode="HTML")


async def xem_lich_su_admin(u_obj):
    text = ""
    if os.path.exists(l_f):
        with open(l_f, "r", encoding="utf-8") as stream:
            lines = stream.readlines()
        text += (
            "📜 <b>LỊCH SỬ PHIÊN SERVER (10 phiên gần nhất)</b>\n"
            + "".join(escape(line) for line in lines[-10:])
            + "\n"
        )
    else:
        text += "📜 Chưa có lịch sử phiên server.\n"

    text += "\n💸 <b>YÊU CẦU NẠP / RÚT GIAO DỊCH GẦN ĐÂY:</b>\n"
    if os.path.exists(lich_su_nap_rut):
        with open(lich_su_nap_rut, "r", encoding="utf-8") as stream:
            nr_lines = stream.readlines()
        text += "".join(
            f"• {escape(line.strip())}\n" for line in nr_lines[-10:]
        ) + "\n"
        text += (
            "💡 <i>Duyệt: <code>/duyet [id] [số_tiền]</code> | "
            "Từ chối: <code>/tuchoi [id] [số_tiền]</code></i>\n\n"
        )
    else:
        text += "• Chưa có lịch sử giao dịch.\n\n"

    text += "🎟️ <b>THỐNG KÊ GIFTCODE:</b>\n"
    for code, details in g.items():
        used = details.get("used", [])
        used_list = ", ".join(escape(str(user_id)) for user_id in used) if used else "Chưa có"
        safe_code = escape(str(code))
        amount = int(details.get("amount", 0))
        text += (
            f"• Mã <code>{safe_code}</code> ({amount:,}đ) - "
            f"Dùng: {len(used)}/{details.get('max_uses', 1)} | [ID: {used_list}]\n"
        )

    await u_obj.message.reply_text(text, parse_mode="HTML")
