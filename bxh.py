import json # json
import os # os
from html import escape

bxh_file = "data.json" # file data

def lay_du_lieu_bxh(): # get_bxh_data
    if not os.path.exists(bxh_file): # check
        return [] # return empty
    try:
        with open(bxh_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # data có dạng { "user_id": { "name": "...", "balance": ..., "wins": ... } }
            danh_sach = []
            for uid, info in data.items():
                if not info.get("blocked", False): # Bỏ qua tài khoản bị khóa
                    danh_sach.append({
                        "id": uid,
                        "name": info.get("name", "Người chơi"),
                        "balance": info.get("balance", 0),
                        "wins": info.get("wins", 0)
                    })
            # Sắp xếp theo số dư giảm dần (Top đại gia)
            danh_sach.sort(key=lambda x: x["balance"], reverse=True)
            return danh_sach
    except:
        return []

def tao_noi_dung_bxh(): # format_bxh
    ds = lay_du_lieu_bxh()
    if not ds:
        return "🏆 <b>BẢNG XẾP HẠNG ĐẠI GIA</b>\n\n• Chưa có dữ liệu người chơi."
    
    text = "🏆 <b>TOP 10 ĐẠI GIA HÀNG ĐẦU</b> 🏆\n" + "—" * 20 + "\n"
    for idx, user in enumerate(ds[:10], 1):
        huy_chuong = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"<b>#{idx}</b>"
        text += f"{huy_chuong} <b>{escape(str(user['name']))}</b>\n"
        text += f"   • Số dư: <b>{user['balance']:,.0f} VNĐ</b> | Thắng: {user['wins']} trận\n"
    return text