"""Fair dice rounds with fixed published payout ratios and complete per-round audit logs."""
import asyncio
import secrets
from datetime import datetime
from config import c, u, f_w, p, l_f
from bot_time import g_d
from firebase_logger import ghi_log_game, ghi_log_loi, ghi_log_wallet
from html import escape

async def chay_vong_quay_game(app_obj):
    # Any bet still present at process startup belongs to an interrupted round.
    # Refund it instead of accidentally settling it in a different session.
    stale_refunds = 0
    for uid, account in list(u.items()):
        bet = account.get("current_bet")
        if not bet:
            continue
        amount = max(0, int(bet.get("amount", 0)))
        before = int(account.get("balance", 0))
        account["balance"] = before + amount
        account["current_bet"] = None
        account.setdefault("history", []).append(
            f"Khởi động lại: hoàn cược phiên bị gián đoạn {amount:,}đ"
        )
        account["history"] = account["history"][-20:]
        stale_refunds += amount
        ghi_log_game(
            c.get("session_id", 1), uid, bet.get("type", "UNKNOWN"),
            amount, "STARTUP_RECOVERY_REFUND",
            balance_before=before, balance_after=account["balance"],
        )
        ghi_log_wallet(
            uid, "STARTUP_RECOVERY_REFUND",
            f"Refunded unsettled bet {amount} VND after restart",
            amount=amount,
        )
        try:
            await app_obj.bot.send_message(
                chat_id=int(uid),
                text=f"⚠️ Phiên trước bị gián đoạn do bot khởi động lại. "
                     f"Đã hoàn {amount:,}đ vào số dư của bạn.",
            )
        except Exception as exc:
            ghi_log_loi(
                f"Cannot notify startup refund: {type(exc).__name__}: {exc}",
                user_id=uid,
            )
    if stale_refunds:
        f_w(p, u)
        ghi_log_game(
            c.get("session_id", 1), "SYSTEM", "STARTUP_RECOVERY",
            stale_refunds, "REFUNDED",
        )

    while True:
        try:
            c["bet_active"] = True
            f_w("config.json", c)
            sid = int(c.get("session_id", 1))
            # Reserve the session number before opening it, so a restart never reuses an ID.
            c["session_id"] = sid + 1
            c["session_date"] = g_d()["log_str"][:10]
            f_w("config.json", c)
            time_info = g_d()
            from notif import ds_tat_tb
            open_msg = (f"🟢 MỞ CƯỢC #{sid:04d}\nThời gian: {time_info['log_str']}\n"
                        f"Nhắn T[số_tiền] (Tài) hoặc X[số_tiền] (Xỉu). Mức cược 1.000–100.000đ.\nTỉ lệ trả thưởng hiện tại: Tài {float(c.get('tai_ratio',1.95)):.2f}x, Xỉu {float(c.get('xiu_ratio',1.95)):.2f}x.")
            for uid in list(u.keys()):
                if uid in ds_tat_tb or u.get(uid, {}).get("blocked", False): continue
                try: await app_obj.bot.send_message(chat_id=int(uid), text=open_msg)
                except Exception as exc: ghi_log_loi(f"Cannot send round-open message: {exc}", user_id=uid, session_id=sid)
            await asyncio.sleep(45)
            c["bet_active"] = False
            f_w("config.json", c)
            if c.pop("cancel_round_requested", False):
                refunds = 0
                for uid, acc in list(u.items()):
                    bet = acc.get("current_bet")
                    if not bet:
                        continue
                    amount = max(0, int(bet.get("amount", 0)))
                    before = int(acc.get("balance", 0))
                    acc["balance"] = before + amount
                    acc["current_bet"] = None
                    acc.setdefault("history", []).append(f"Phiên #{sid}: Đã hủy, hoàn cược {amount:,}đ")
                    acc["history"] = acc["history"][-20:]
                    refunds += amount
                    ghi_log_game(sid, uid, bet.get("type", "UNKNOWN"), amount, "ROUND_VOID_REFUND", balance_before=before, balance_after=acc["balance"])
                    try:
                        await app_obj.bot.send_message(chat_id=int(uid), text=f"🧾 Phiên #{sid:04d} đã được hủy bởi quản trị viên. Bạn được hoàn {amount:,}đ. Số dư: {acc['balance']:,}đ.")
                    except Exception as exc:
                        ghi_log_loi(f"Cannot notify round refund: {exc}", user_id=uid, session_id=sid)
                f_w(p, u)
                f_w("config.json", c)
                ghi_log_game(sid, "SYSTEM", "ROUND_VOIDED", refunds, "REFUNDED", reason="admin_request")
                ghi_log_loi("Round cancelled by admin; all unsettled bets refunded", session_id=sid, refunded_total=refunds)
                await asyncio.sleep(3)
                continue
            dice = [(secrets.randbelow(6) + 1) for _ in range(3)]
            total = sum(dice)
            result = "TAI" if total >= 11 else "XIU"
            bet_details = []
            user_outcomes = {}
            total_stake = 0
            for uid, acc in list(u.items()):
                bet = acc.get("current_bet")
                if not bet: continue
                side, amount = bet.get("type"), int(bet.get("amount", 0))
                total_stake += amount
                if side == result:
                    ratio = float(c.get("tai_ratio", 1.95) if result == "TAI" else c.get("xiu_ratio", 1.95))
                    payout = int(amount * ratio)
                    acc["balance"] = int(acc.get("balance", 0)) + payout
                    acc["wins"] = int(acc.get("wins", 0)) + 1
                    status, net = "WIN", payout - amount
                    acc.setdefault("history", []).append(f"Phiên #{sid}: Đặt {amount}đ {side} -> Thắng (+{net}đ)")
                else:
                    status, net = "LOSE", -amount
                    acc.setdefault("history", []).append(f"Phiên #{sid}: Đặt {amount}đ {side} -> Thua (-{amount}đ)")
                acc["current_bet"] = None
                acc["history"] = acc.get("history", [])[-20:]
                # Referral reward: 1% of settled stake, paid to the original referrer.
                referrer_id = str(acc.get("referred_by") or "")
                reward_rate = float(c.get("referral_rate", 0.01))
                if referrer_id and referrer_id != str(uid) and referrer_id in u and 0 < reward_rate <= 0.02:
                    reward = int(amount * reward_rate)
                    if reward > 0:
                        referrer = u[referrer_id]
                        referrer["balance"] = int(referrer.get("balance", 0)) + reward
                        referrer["ref_earnings"] = int(referrer.get("ref_earnings", 0)) + reward
                        ghi_log_wallet(referrer_id, "REFERRAL_BET_REWARD", f"Referral {uid} wagered {amount}; reward {reward}", referred_user=str(uid), session_id=sid, stake=amount, rate=reward_rate, reward=reward)
                        ghi_log_game(sid, referrer_id, "REFERRAL", reward, "REFERRAL_REWARD", referred_user=str(uid), stake=amount, rate=reward_rate)
                user_outcomes[uid] = (status, net, side, amount)
                bet_details.append(f"{escape(str(acc.get('name', uid)))}: {'Thắng' if status == 'WIN' else 'Thua'} ({net:+,}đ)")
                ghi_log_game(sid, uid, side, amount, status, dice=dice, total=total, result=result, net_change=net, payout_ratio=(c.get('tai_ratio',1.95) if result=='TAI' else c.get('xiu_ratio',1.95)))
            f_w(p, u)
            with open(l_f, "a", encoding="utf-8") as log:
                log.write(f"Phiên #{sid} | {time_info['log_str']} | Dice: {dice} total={total} -> {result} | stake={total_stake}\n")
            ghi_log_game(sid, "SYSTEM", "ROUND_RESULT", total_stake, result, dice=dice, total=total, bets=len(bet_details))
            # Individual results are private; do not expose other players' balances/outcomes.
            for uid, acc in list(u.items()):
                if uid in ds_tat_tb: continue
                try:
                    personal = user_outcomes.get(uid)
                    outcome_text = (f"\nCược của bạn: {personal[2]} {personal[3]:,}đ — {'THẮNG' if personal[0] == 'WIN' else 'THUA'} ({personal[1]:+,}đ)") if personal else "\nBạn không đặt cược ở phiên này."
                    await app_obj.bot.send_message(chat_id=int(uid), text=(f"🎲 KẾT QUẢ PHIÊN #{sid:04d}\nXúc xắc: {dice[0]}-{dice[1]}-{dice[2]} (tổng {total})\n"
                        f"Kết quả: {'TÀI' if result == 'TAI' else 'XỈU'}{outcome_text}\nSố dư hiện tại: {int(acc.get('balance',0)):,}đ"))
                except Exception as exc: ghi_log_loi(f"Cannot send round-result message: {exc}", user_id=uid, session_id=sid)
            f_w(p, u)
            await asyncio.sleep(15)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            ghi_log_loi(f"Game round crashed: {type(exc).__name__}: {exc}")
            try:
                with open("game_error.log", "a", encoding="utf-8") as log:
                    log.write(f"[{datetime.now().astimezone().isoformat()}] {type(exc).__name__}: {exc}\n")
            except OSError: pass
            await asyncio.sleep(5)
