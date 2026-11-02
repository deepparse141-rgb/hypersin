import requests, json, time, random, string, os, threading, gc
from datetime import datetime, timedelta
from flask import Flask, jsonify
from concurrent.futures import ThreadPoolExecutor

# ═══════════════════════════════════════
# 🔧 تنظیمات
# ═══════════════════════════════════════
TOKEN = "11726691:ZnU_Q7ptFVV2xkBNaxlbaEpOTSyIn5DFU_o"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

CHANNEL_ID = "@SCYVu"
CHANNEL_LINK = "https://ble.ir/SCYVu"
CHANNEL_2_ID = "@uvuvuf"
CHANNEL_2_LINK = "https://ble.ir/uvuvuf"

BOT_USERNAME = "Idnuedyobot"
BOT_LINK = f"https://ble.ir/{BOT_USERNAME}"

OWNER_ID = "1530477937"
OWNER_PASSWORD = "Parsa@2026!"
COIN_PASSWORD = "Coin@Parsa2026"
INFINITE_COINS = 999999

MIN_SIN = 15
MIN_MEMBER = 3
MEMBER_COST = 5
START_GIFT = 25
SEEN_REWARD = 1
SIN_COST = 1
INVITE_REWARD = 15
DAILY_GIFT = 10
MEMBER_NORMAL_REWARD = 3
MEMBER_GUARANTEED_REWARD = 7
TRANSFER_FEE = 2

GUARANTEED_HOURS = 48
GUARANTEED_PENALTY = 7
GUARANTEED_REFUND = 5
GUARANTEED_COOLDOWN = 300

WHEEL_PRIZES = [
    {"emoji": "💰", "coins": 25, "weight": 10},
    {"emoji": "💵", "coins": 20, "weight": 15},
    {"emoji": "📩", "coins": 10, "weight": 25},
    {"emoji": "🌟", "coins": 5, "weight": 30},
    {"emoji": "🎵", "coins": 0, "weight": 15},
    {"emoji": "🎵", "coins": 0, "weight": 5}
]
WHEEL_COOLDOWN = 12 * 3600

DB_FILE = "hypersin_bale.json"
DB_BACKUP = "hypersin_bale_backup.json"
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "https://hypersin-bale.onrender.com")

CACHE = {}
CACHE_TIME = {}
CACHE_TTL = 7200
JOIN_CACHE = {}
JOIN_CACHE_TIME = {}
SAVE_PENDING = False
SAVE_LOCK = threading.Lock()
executor = ThreadPoolExecutor(max_workers=800)

def load_db():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key in ["guaranteed_times", "support_tickets", "join_channels", "group_targets", "bc_gifts", "coin_packets", "admin_warnings", "polls", "games", "active_games", "challenges"]:
                    if key not in data:
                        data[key] = {}
                for key in ["custom_features", "pending_challenge"]:
                    if key not in data:
                        data[key] = {}
                if "settings" not in data:
                    data["settings"] = {}
                return data
    except: pass
    return {
        "users": {}, "orders": {}, "member_orders": {}, "gift_codes": {},
        "seen_records": {}, "member_records": {}, "invited_users": {},
        "order_counter": 0, "member_counter": 0,
        "stats": {
            "total_orders": 0, "completed_orders": 0, "deleted_messages": 0,
            "total_members": 0, "completed_members": 0,
            "total_transfers": 0, "owner_earnings": 0,
            "total_coins_spent": 0
        },
        "pending_orders": {}, "pending_members": {}, "pending_gift": {},
        "pending_broadcast": {}, "pending_add_coins": {}, "pending_transfer": {},
        "pending_coin_setting": {}, "pending_join_channel": {}, "pending_remove_join": {},
        "pending_packet": {}, "pending_ban": {}, "pending_unban": {},
        "pending_admin": {}, "pending_remove_admin": {}, "pending_vip": {},
        "pending_pm": {}, "pending_execute": {}, "pending_utility": {},
        "pending_support": {}, "pending_packet_user": {},
        "pending_broadcast_advanced": {}, "pending_user_info": {},
        "pending_all_settings": {}, "pending_broadcast_format": {},
        "pending_feature": {}, "pending_support_reply": {},
        "pending_broadcast_groups": {}, "pending_forward_all": {},
        "pending_send_to_channel": {}, "pending_poll": {}, "pending_game": {},
        "coin_packets": {}, "bc_gifts": {},
        "banned": [], "admins": [], "vip": {},
        "join_channels": {}, "games": {}, "game_counter": 0,
        "active_games": {}, "support_tickets": {}, "ticket_counter": 0,
        "guaranteed_times": {}, "group_targets": {}, "custom_features": [],
        "admin_warnings": {}, "polls": {}, "poll_counter": 0,
        "challenges": {}, "challenge_counter": 0, "pending_challenge": {},
        "settings": {
            "seen_reward": 1, "sin_cost": 1,
            "member_cost": 5, "member_normal_reward": 3, "member_guaranteed_reward": 7,
            "guaranteed_cost": 10, "transfer_fee": 2, "start_gift": 25,
            "daily_gift": 10, "invite_reward": 15, "wheel_cooldown": WHEEL_COOLDOWN,
            "guaranteed_hours": 48, "guaranteed_penalty": 7, "guaranteed_refund": 5,
            "guaranteed_cooldown": 300, "normal_member_penalty": 0,
            "normal_member_hours": 0, "normal_member_coin_penalty": 0,
            "min_sin": 15, "min_member": 3
        }
    }

def save_db_async():
    global SAVE_PENDING
    SAVE_PENDING = True

def save_worker():
    global SAVE_PENDING
    while True:
        if SAVE_PENDING:
            with SAVE_LOCK:
                try:
                    if os.path.exists(DB_FILE):
                        try: os.replace(DB_FILE, DB_BACKUP)
                        except: pass
                    with open(DB_FILE, "w", encoding="utf-8") as f:
                        json.dump(db, f, ensure_ascii=False)
                    SAVE_PENDING = False
                except: pass
        time.sleep(2)

def save_db(): save_db_async()

db = load_db()

def get_user(user_id):
    uid = str(user_id)
    now = time.time()
    if uid in CACHE and now - CACHE_TIME.get(uid, 0) < CACHE_TTL:
        return CACHE[uid]
    if uid not in db["users"]:
        db["users"][uid] = {
            "coins": 0, "joined": False, "got_start_gift": False,
            "invite_count": 0, "invited_by": None, "username": "",
            "last_daily": None, "msg_count": 0, "last_wheel": None,
            "invite_reward_paid": False, "used_gift_codes": [],
            "guaranteed_members": {}, "last_guaranteed_times": {},
            "joined_at": str(datetime.now())
        }
        save_db_async()
    CACHE[uid] = db["users"][uid]
    CACHE_TIME[uid] = now
    return db["users"][uid]

def add_coins(user_id, amount):
    get_user(user_id)["coins"] += amount
    save_db_async()

def remove_coins(user_id, amount):
    user = get_user(user_id)
    if user["coins"] >= amount:
        user["coins"] -= amount
        db["stats"]["total_coins_spent"] = db["stats"].get("total_coins_spent", 0) + amount
        save_db_async()
        return True
    return False

def get_coins(user_id):
    return get_user(user_id)["coins"]

def is_banned(user_id):
    return str(user_id) in db.get("banned", [])

def is_admin(user_id):
    return str(user_id) == str(OWNER_ID) or str(user_id) in db.get("admins", [])

def convert_number(text):
    for p, e in zip("۰۱۲۳۴۵۶۷۸۹", "0123456789"):
        text = text.replace(p, e)
    return text

def get_shamsi_date():
    now = datetime.now()
    return f"{now.year}/{now.month:02d}/{now.day:02d}"

def get_setting(key, default=0):
    return db.get("settings", {}).get(key, default)

def cache_cleanup():
    while True:
        try:
            now = time.time()
            to_del = [k for k, t in CACHE_TIME.items() if now - t > CACHE_TTL * 2]
            for k in to_del:
                CACHE.pop(k, None)
                CACHE_TIME.pop(k, None)
            to_del2 = [k for k, t in JOIN_CACHE_TIME.items() if now - t > 600]
            for k in to_del2:
                JOIN_CACHE.pop(k, None)
                JOIN_CACHE_TIME.pop(k, None)
            gc.collect()
        except: pass
        time.sleep(600)

session = requests.Session()
session.headers.update({'Connection': 'keep-alive', 'Accept-Encoding': 'gzip, deflate'})

def api_call(method, data=None, timeout=5):
    try:
        if data is None: data = {}
        r = session.post(f"{BASE_URL}/{method}", data=data, timeout=timeout)
        return r.json()
    except:
        try:
            r = session.post(f"{BASE_URL}/{method}", data=data, timeout=3)
            return r.json()
        except: return {"ok": False}

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text}
    if reply_markup: data["reply_markup"] = json.dumps(reply_markup)
    return api_call("sendMessage", data)

def send_reply(chat_id, reply_to_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text, "reply_to_message_id": reply_to_id}
    if reply_markup: data["reply_markup"] = json.dumps(reply_markup)
    return api_call("sendMessage", data)

def edit_message_text(chat_id, message_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if reply_markup: data["reply_markup"] = json.dumps(reply_markup)
    return api_call("editMessageText", data)

def delete_message(chat_id, message_id):
    return api_call("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

def forward_message(chat_id, from_chat_id, message_id):
    return api_call("forwardMessage", {"chat_id": chat_id, "from_chat_id": from_chat_id, "message_id": message_id})

def answer_callback(callback_id, text=None, show_alert=False):
    data = {"callback_query_id": callback_id}
    if text: data["text"] = text
    data["show_alert"] = show_alert
    return api_call("answerCallbackQuery", data)

def get_chat_member(chat_id, user_id):
    return api_call("getChatMember", {"chat_id": chat_id, "user_id": user_id})

def get_chat(chat_id):
    return api_call("getChat", {"chat_id": chat_id})

def check_joined(user_id):
    uid = str(user_id)
    now = time.time()
    if uid in JOIN_CACHE and now - JOIN_CACHE_TIME.get(uid, 0) < 120:
        return JOIN_CACHE[uid]
    try:
        result = get_chat_member(CHANNEL_ID, user_id)
        if result.get("ok"):
            status = result["result"]["status"]
            ok = status in ["member", "administrator", "creator"]
            if ok:
                get_user(user_id)["joined"] = True
                save_db_async()
            JOIN_CACHE[uid] = ok
            JOIN_CACHE_TIME[uid] = now
            return ok
        return False
    except: return False

def check_chat_membership(chat_id, user_id):
    try:
        r = get_chat_member(chat_id, user_id)
        if r.get("ok"):
            status = r["result"]["status"]
            return status in ["member", "administrator", "creator"]
        return False
    except:
        return False

def check_all_joins(user_id):
    if not check_joined(user_id): return False
    if not check_chat_membership(CHANNEL_2_ID, user_id): return False
    for ch_id, ch_info in db.get("join_channels", {}).items():
        if not check_chat_membership(ch_id, user_id):
            return False
    return True

def must_join(user_id):
    buttons = [
        [{"text": "📢 عضویت در کانال اصلی", "url": CHANNEL_LINK}],
        [{"text": "📢 عضویت در کانال دوم", "url": CHANNEL_2_LINK}]
    ]
    for ch_id, ch_info in db.get("join_channels", {}).items():
        ch_link = ch_info.get("link", ch_id)
        ch_title = ch_info.get("title", "کانال")
        buttons.append([{"text": f"📢 {ch_title}", "url": ch_link}])
    buttons.append([{"text": "✅ عضو شدم", "callback_data": "check_join"}])
    keyboard = {"inline_keyboard": buttons}
    send_message(user_id,
        "🔒 **برای استفاده از ربات باید عضو بشی!**\n\n"
        "⚠️ **حتماً تو هر دو کانال عضو شو!**\n\n"
        "1️⃣ کانال اصلی\n"
        "2️⃣ کانال دوم\n\n"
        "✅ بعد دکمه «عضو شدم» رو بزن.",
        keyboard)
    return False

def main_keyboard(user_id=None):
    rows = [
        [{"text": "🪙 کسب سکه"}],
        [{"text": "👁️ ثبت سفارش سین"}, {"text": "👥 ثبت سفارش عضو"}],
        [{"text": "💰 سکه‌های من"}, {"text": "🎁 زدن کد هدیه"}],
        [{"text": "👥 دعوت دوستان"}, {"text": "👤 حساب کاربری"}],
        [{"text": "🎁 هدیه روزانه"}, {"text": "🎡 گردونه شانس"}],
        [{"text": "💬 پشتیبانی"}],
        [{"text": "📖 راهنما"}]
    ]
    if user_id and str(user_id) == str(OWNER_ID):
        rows.append([{"text": "👑 پنل مالک"}])
    return {"keyboard": rows, "resize_keyboard": True}

def owner_keyboard():
    return {
        "keyboard": [
            [{"text": "⚙️ تنظیم سکه"}, {"text": "⚙️ تنظیم محدودیت‌ها"}],
            [{"text": "🚫 مسدود کردن"}, {"text": "✅ رفع مسدودیت"}],
            [{"text": "👑 افزودن ادمین"}, {"text": "🗑️ حذف ادمین"}],
            [{"text": "📨 پیام به کاربر"}, {"text": "💻 اجرای کد"}],
            [{"text": "💻 اجرای قابلیت"}, {"text": "👤 مشخصات کاربر"}],
            [{"text": "🎁 سکه پاکت"}, {"text": "🛡️ ضدتقلب"}],
            [{"text": "📊 آمار پیشرفته"}, {"text": "📊 آمار کل"}],
            [{"text": "🔒 جوین اجباری"}, {"text": "🎁 ساخت کد هدیه"}],
            [{"text": "💰 افزودن سکه به همه"}, {"text": "🎁 تغییر سکه دعوت"}],
            [{"text": "📢 ارسال به کانال"}, {"text": "📊 نظرسنجی"}],
            [{"text": "🎯 چالش دعوت"}, {"text": "🛑 توقف بازی"}],
            [{"text": "📋 لیست کانال‌ها"}, {"text": "👥 کاربران کانال"}],
            [{"text": "📢 پیام همگانی"}, {"text": "🚀 هدایت همگانی"}],
            [{"text": "📢 پیام به گروه‌ها"}, {"text": "🏆 رتبه‌بندی"}],
            [{"text": "💸 انتقال سکه"}, {"text": "🔙 بازگشت"}]
        ],
        "resize_keyboard": True
    }

def settings_keyboard():
    return {
        "keyboard": [
            [{"text": "👁️ سکه دیدم"}, {"text": "📝 سکه سفارش سین"}],
            [{"text": "👥 سکه سفارش عضو"}, {"text": "🪙 سکه عضو معمولی"}],
            [{"text": "🛡️ سکه عضو تضمینی"}, {"text": "💸 کارمزد انتقال"}],
            [{"text": "🎁 هدیه شروع"}, {"text": "📅 هدیه روزانه"}],
            [{"text": "👥 سکه دعوت"}, {"text": "🎡 زمان گردونه"}],
            [{"text": "⏰ مدت تضمینی"}, {"text": "💸 جریمه تضمینی"}],
            [{"text": "↩️ برگشت تضمینی"}, {"text": "⏳ کول‌داون تضمینی"}],
            [{"text": "👥 هزینه عضو تضمینی"}, {"text": "⚠️ جریمه عضو معمولی"}],
            [{"text": "⏰ مدت عضو معمولی"}, {"text": "🪙 سکه جریمه معمولی"}],
            [{"text": "🔙 بازگشت"}]
        ],
        "resize_keyboard": True
    }

def limits_keyboard():
    return {
        "keyboard": [
            [{"text": "📝 حداقل سین"}, {"text": "👥 حداقل عضو"}],
            [{"text": "🔙 بازگشت"}]
        ],
        "resize_keyboard": True
    }

def all_settings_keyboard(): return settings_keyboard()

def join_settings_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "➕ افزودن کانال", "callback_data": "join_add"}],
            [{"text": "🗑️ حذف از لیست", "callback_data": "join_remove"}],
            [{"text": "📋 لیست", "callback_data": "join_list"}],
            [{"text": "🔙 بازگشت", "callback_data": "back_to_owner"}]
        ]
    }

def cancel_keyboard():
    return {"keyboard": [[{"text": "🔙 بازگشت"}]], "resize_keyboard": True}

def create_challenge(user_id, owner_id, target, reward):
    db["challenge_counter"] = db.get("challenge_counter", 0) + 1
    cid = str(db["challenge_counter"])
    db["challenges"][cid] = {
        "owner_id": owner_id,
        "user_id": user_id,
        "target": target,
        "reward": reward,
        "status": "pending",
        "invites": 0,
        "created_at": str(datetime.now())
    }
    save_db_async()
    
    kb = {"inline_keyboard": [
        [{"text": "✅ قبول چالش", "callback_data": f"chal_accept_{cid}"}],
        [{"text": "❌ رد چالش", "callback_data": f"chal_reject_{cid}"}]
    ]}
    
    send_message(int(user_id),
        f"🎉 **شما در چالش ما انتخاب شدید!**\n\n"
        f"🍀 شانس واقعاً خوب بود!\n\n"
        f"🎯 **چالش این است:**\n"
        f"باید **{target}** دعوت بکنی.\n\n"
        f"💰 **جایزه:**\n"
        f"اگر این تعداد دعوت کردی، **{reward:,} سکه** می‌گیری!\n\n"
        f"🔘 **تصمیمت چیه؟**", kb)
    return cid

def spin_wheel():
    total = sum(p["weight"] for p in WHEEL_PRIZES)
    r = random.randint(1, total)
    cum = 0
    for p in WHEEL_PRIZES:
        cum += p["weight"]
        if r <= cum: return p
    return WHEEL_PRIZES[0]

def can_spin_wheel(user_id):
    user = get_user(user_id)
    last = user.get("last_wheel")
    if not last: return True, 0
    try:
        lt = datetime.fromisoformat(last)
        cooldown = get_setting("wheel_cooldown", WHEEL_COOLDOWN)
        diff = (datetime.now() - lt).total_seconds()
        if diff < cooldown: return False, int(cooldown - diff)
        return True, 0
    except: return True, 0

def broadcast_worker(user_id, text):
    sent = 0; failed = 0
    all_users = list(db["users"].keys())
    total = len(all_users)
    for i, uid in enumerate(all_users, 1):
        try:
            r = send_message(int(uid), text)
            if r.get("ok"): sent += 1
            else: failed += 1
        except: failed += 1
        time.sleep(0.05)
        if i % 100 == 0:
            try: send_message(user_id, f"📊 پیشرفت: {i}/{total}")
            except: pass
    send_message(user_id, f"📢 **ارسال کامل شد!**\n\n✅ موفق: {sent}\n❌ ناموفق: {failed}\n📊 کل: {total}", owner_keyboard())

def broadcast_worker_advanced(user_id, text, keyboard_json=None):
    sent = 0; failed = 0
    all_users = list(db["users"].keys())
    total = len(all_users)
    for i, uid in enumerate(all_users, 1):
        try:
            if keyboard_json: r = send_message(int(uid), text, keyboard_json)
            else: r = send_message(int(uid), text)
            if r.get("ok"): sent += 1
            else: failed += 1
        except: failed += 1
        time.sleep(0.05)
        if i % 100 == 0:
            try: send_message(user_id, f"📊 پیشرفت: {i}/{total}")
            except: pass
    send_message(user_id, f"📢 **ارسال کامل شد!**\n\n✅ موفق: {sent}\n❌ ناموفق: {failed}\n📊 کل: {total}", owner_keyboard())

def broadcast_to_groups_worker(user_id, text):
    sent = 0; failed = 0
    bot_id = int(TOKEN.split(":")[0])
    groups = []
    for gid in list(db.get("group_targets", {}).keys()):
        r = get_chat_member(gid, bot_id)
        if r.get("ok") and r["result"]["status"] in ["administrator", "creator"]:
            groups.append(gid)
    total = len(groups)
    for i, gid in enumerate(groups, 1):
        try:
            r = send_message(gid, text)
            if r.get("ok"): sent += 1
            else: failed += 1
        except: failed += 1
        time.sleep(0.1)
    send_message(user_id, f"📢 **ارسال به گروه‌ها کامل شد!**\n\n✅ موفق: {sent}\n❌ ناموفق: {failed}\n📊 کل: {total}", owner_keyboard())

def forward_to_all_worker(owner_id, from_chat_id, message_id):
    sent = 0; failed = 0
    all_users = list(db["users"].keys())
    total = len(all_users)
    for i, uid in enumerate(all_users, 1):
        try:
            r = forward_message(int(uid), from_chat_id, message_id)
            if r.get("ok"): sent += 1
            else: failed += 1
        except: failed += 1
        time.sleep(0.05)
        if i % 100 == 0:
            try: send_message(owner_id, f"📊 پیشرفت: {i}/{total}")
            except: pass
    send_message(owner_id, f"🚀 **هدایت کامل شد!**\n\n✅ موفق: {sent}\n❌ ناموفق: {failed}\n📊 کل: {total}", owner_keyboard())

def check_guaranteed_members():
    while True:
        try:
            time.sleep(300)
            now = datetime.now()
            hours = get_setting("guaranteed_hours", 48)
            penalty = get_setting("guaranteed_penalty", 7)
            refund = get_setting("guaranteed_refund", 5)
            for mid, order in list(db.get("member_orders", {}).items()):
                if order.get("order_type") != "guaranteed": continue
                if order["status"] != "active": continue
                tcid = order["chat_id"]
                owner = order["user_id"]
                for uid_str in list(db["member_records"].get(mid, [])):
                    uid = uid_str
                    user = get_user(uid)
                    gm = user.get("guaranteed_members", {}).get(mid)
                    if not gm: continue
                    try: deadline = datetime.fromisoformat(gm["deadline"])
                    except: continue
                    if now < deadline:
                        r = get_chat_member(tcid, int(uid))
                        is_member = r.get("ok") and r["result"]["status"] in ["member", "administrator", "creator"]
                        if not is_member:
                            actual = min(user["coins"], penalty)
                            user["coins"] -= actual
                            add_coins(owner, refund)
                            del user["guaranteed_members"][mid]
                            save_db_async()
                            try:
                                send_message(int(uid),
                                    f"⚠️ **شما کانال رو قبل از ۴۸ ساعت ترک کردید!**\n\n"
                                    f"📢 کانال: {order['link']}\n"
                                    f"📋 نوع سفارش: تضمینی\n"
                                    f"⏰ باید ۴۸ ساعت عضو می‌ماندید!\n\n"
                                    f"💰 **{actual} سکه از موجودی شما کم شد.**\n"
                                    f"💳 موجودی: {get_coins(uid):,} سکه")
                            except: pass
                            try:
                                uname = user.get("username", "") or uid
                                send_message(int(owner),
                                    f"🔔 **یه کاربر کانال رو قبل از ۴۸ ساعت ترک کرد!**\n\n"
                                    f"📢 کانال: {order['link']}\n"
                                    f"📋 نوع سفارش: تضمینی\n\n"
                                    f"💰 **{refund} سکه به موجودی شما برگشت داده شد.**\n"
                                    f"💳 موجودی: {get_coins(owner):,} سکه")
                            except: pass
                    else:
                        del user["guaranteed_members"][mid]
                        save_db_async()
        except Exception as e:
            print(f"⚠️ خطا guaranteed: {e}")

def check_admin_orders():
    while True:
        try:
            time.sleep(2)
            bot_id = int(TOKEN.split(":")[0])
            for mid, order in list(db.get("member_orders", {}).items()):
                if order["status"] != "active": continue
                tcid = order["chat_id"]
                r = get_chat_member(tcid, bot_id)
                is_admin = r.get("ok") and r["result"]["status"] in ["administrator", "creator"]
                
                if not is_admin:
                    order["status"] = "removed"
                    owner = order["user_id"]
                    count = order["count"]
                    otype = order.get("order_type", "normal")
                    
                    cost_per = get_setting('member_cost', 5) if otype == "normal" else get_setting('guaranteed_cost', 10)
                    refund = count * cost_per
                    add_coins(owner, refund)

                    if owner not in db.get("admin_warnings", {}):
                        db["admin_warnings"][owner] = {"count": 0, "dates": []}
                    
                    db["admin_warnings"][owner]["count"] += 1
                    db["admin_warnings"][owner]["dates"].append(str(datetime.now()))
                    warn_count = db["admin_warnings"][owner]["count"]

                    if mid in db.get("member_records", {}):
                        db["member_records"][mid].clear()
                    save_db_async()

                    if warn_count >= 5:
                        if owner not in db.get("banned", []):
                            db.setdefault("banned", []).append(owner)
                            save_db_async()
                            try:
                                send_message(int(owner),
                                    f"🚫 **شما از ربات مسدود شدید!**\n\n"
                                    f"⚠️ دلیل: شما ۵ بار ربات را از ادمینی کانال درآوردید.\n"
                                    f"❌ این کار باعث اختلال در سفارشات می‌شود.\n\n"
                                    f"📞 در صورت اعتراض با پشتیبانی در ارتباط باشید.")
                            except: pass
                            try:
                                send_message(int(OWNER_ID),
                                    f"🚨 **کاربر بن شد!**\n\n"
                                    f"👤 کاربر: `{owner}`\n"
                                    f"⚠️ تعداد اخطار: {warn_count}\n"
                                    f"🚫 دلیل: ۵ بار تخلف در ادمینی کانال.")
                            except: pass
                            if order.get("message_id"):
                                try: delete_message(CHANNEL_ID, order["message_id"])
                                except: pass
                            continue

                    try:
                        send_message(int(OWNER_ID),
                            f"⚠️ **گزارش تخلف** (اخطار {warn_count}/۴)\n\n"
                            f"👤 کاربر متخلف: `{owner}`\n"
                            f"📝 شماره سفارش: #{order.get('order_number', '?')}\n"
                            f"🔗 لینک کانال: {order['link']}\n"
                            f"💰 سکه برگشتی: {refund:,}\n"
                            f"📅 تاریخ: {get_shamsi_date()}\n\n"
                            f"⚠️ **توجه: با یک اخطار دیگر، کاربر بن خواهد شد!**")
                    except: pass

                    try:
                        send_message(int(owner),
                            f"⚠️ **اخطار {warn_count} از ۴**\n\n"
                            f"کاربر عزیز، شما ربات را از ادمینی کانال درآوردید! ❌\n\n"
                            f"🗑️ سفارش شما باطل شد.\n"
                            f"💰 **{refund:,} سکه** به موجودی شما برگشت داده شد.\n\n"
                            f"🚨 **هشدار جدی:** با یک اخطار دیگر، حساب شما **مسدود** خواهد شد!\n"
                            f"🛡️ لطفاً ربات را در کانال ادمین نگه دارید.")
                    except: pass

                    if order.get("message_id"):
                        try: delete_message(CHANNEL_ID, order["message_id"])
                        except: pass
                        
                    if str(tcid) in db.get("group_targets", {}):
                        del db["group_targets"][str(tcid)]
                        save_db_async()

        except Exception as e:
            print(f"⚠️ خطا در چک ادمین: {e}")

def handle_message(message):
    global INVITE_REWARD
    try:
        chat_id = message["chat"]["id"]
        chat_type = message["chat"]["type"]

        if chat_type in ["group", "supergroup"]:
            if "new_chat_member" in message:
                nm = message["new_chat_member"]
                nn = nm.get("first_name", "کاربر")
                gn = message["chat"].get("title", "این گروه")
                wt = (f"👋 **{nn}** عزیز، به گروه **{gn}** خوش اومدی! 🎉\n\n"
                      f"🤖 من **ربات عضوگیر و سین‌زن هایپرسین** هستم!\n\n"
                      f"🚀 آیدی من: @Idnuedyobot\n\n"
                      f"🐺 با افتخار، تیم DeepParse")
                send_message(chat_id, wt)
            if "group_targets" not in db: db["group_targets"] = {}
            gid = str(chat_id)
            if gid not in db["group_targets"]:
                db["group_targets"][gid] = {
                    "title": message["chat"].get("title", "?"),
                    "type": chat_type
                }
                save_db_async()
            return

        if chat_type == "channel": return

        user_id = str(message["from"]["id"])
        text = message.get("text", "").strip()
        name = message["from"].get("first_name", "داداش")

        if is_banned(user_id):
            send_message(chat_id, "🚫 **دسترسی شما مسدود شد!**\n\n⏳ نگران نباش؛ ممکنه تا چند ساعت دیگه رفع بشه.")
            return

        username = message["from"].get("username", "")
        if username:
            get_user(user_id)["username"] = username
            save_db_async()

        get_user(user_id)["msg_count"] = get_user(user_id).get("msg_count", 0) + 1

        # 🛠️ اول دکمه‌ها رو چک می‌کنیم
        main_buttons = ["🪙 کسب سکه", "👁️ ثبت سفارش سین", "👥 ثبت سفارش عضو", "💰 سکه‌های من", "🎁 زدن کد هدیه", "👥 دعوت دوستان", "👤 حساب کاربری", "🎁 هدیه روزانه", "🎡 گردونه شانس", "💬 پشتیبانی", "📖 راهنما", "👑 پنل مالک", "🔙 بازگشت"]
        
        if text in main_buttons:
            if not check_all_joins(user_id):
                must_join(user_id)
                return

        if text in ["❌ لغو", "🔙 بازگشت"]:
            for key in ["pending_orders", "pending_members", "pending_gift", "pending_transfer", "pending_packet", "pending_coin_setting", "pending_ban", "pending_unban", "pending_admin", "pending_remove_admin", "pending_vip", "pending_pm", "pending_execute", "pending_utility", "pending_join_channel", "pending_remove_join", "pending_support", "pending_broadcast_format", "pending_user_info", "pending_all_settings", "pending_feature", "pending_support_reply", "pending_broadcast_groups", "pending_forward_all", "pending_send_to_channel", "pending_poll", "pending_game", "pending_challenge"]:
                db.get(key, {}).pop(user_id, None)
            save_db_async()
            send_message(chat_id, "🔙 **به منوی اصلی بازگشتی!**\n\nداداش، حالا می‌تونی یه گزینه دیگه رو انتخاب کنی. 👇", main_keyboard(user_id))
            return

        if db.get("pending_support", {}).get(user_id, {}).get("step") == "waiting":
            try:
                db["ticket_counter"] = db.get("ticket_counter", 0) + 1
                tid = db["ticket_counter"]
                db.setdefault("support_tickets", {})[str(tid)] = {
                    "user_id": user_id, "name": name, "text": text,
                    "status": "open", "date": str(datetime.now())
                }
                save_db_async()
                kb = {"inline_keyboard": [
                    [{"text": "❌ رد کردن", "callback_data": f"ticket_reject_{tid}"}],
                    [{"text": "📝 جواب دادن", "callback_data": f"ticket_reply_{tid}"}],
                    [{"text": "⏳ بعدی", "callback_data": f"ticket_next_{tid}"}]
                ]}
                send_message(int(OWNER_ID),
                    f"💬 **تیکت پشتیبانی جدید** #{tid}\n\n"
                    f"👤 ارسال‌کننده: {name}\n"
                    f"🆔 آیدی عددی: {user_id}\n\n"
                    f"📝 متن پیام:\n{text}", kb)
                send_message(chat_id, "✅ **پیام شما با موفقیت برای تیم پشتیبانی ارسال شد!**\n\n⏳ لطفاً منتظر بمانید تا در اسرع وقت به شما پاسخ داده شود. 🙏", main_keyboard(user_id))
            except:
                send_message(chat_id, "❌ **خطا در ارسال پیام!**\n\nمتاسفانه مشکلی پیش آمد، لطفاً لحظاتی دیگر دوباره تلاش کنید.", main_keyboard(user_id))
            db["pending_support"].pop(user_id, None)
            save_db_async()
            return

        # ═══ ۵. pending (پردازش مراحل سفارش) ═══
        pending = db["pending_orders"].get(user_id, {})
        pmem = db["pending_members"].get(user_id, {})
        pt = db["pending_transfer"].get(user_id, {})

        # سین‌زن - فوروارد
        if pending.get("step") == "waiting_forward":
            if "forward_from_chat" in message and message["forward_from_chat"]["type"] == "channel":
                db["pending_orders"][user_id] = {"step": "waiting_count", "message_id": message["message_id"]}
                save_db_async()
                send_message(chat_id, f"🔢 **چند سین نیاز داری داداش؟**\n\n💰 هر سین = {get_setting('sin_cost', 1)} سکه\n💳 موجودی: {get_coins(user_id):,} سکه\n\n⚠️ حداقل: {get_setting('min_sin', 15)} سین\n\n📌 فقط یه عدد بفرست (فارسی یا انگلیسی)!", cancel_keyboard())
            else:
                send_message(chat_id, "❌ **این پیام از کانال نیست!**\n\n⚠️ حتماً باید از کانال فوروارد شود!", cancel_keyboard())
            return

        # سین‌زن - تعداد
        if pending.get("step") == "waiting_count":
            try:
                count = int(convert_number(text))
                min_sin = get_setting("min_sin", 15)
                if count < min_sin:
                    send_message(chat_id, f"❌ **حداقل باید {min_sin} سین ثبت کنی!**", cancel_keyboard()); return
                coins = get_coins(user_id)
                total_cost = count * get_setting('sin_cost', 1)
                if coins < total_cost:
                    send_message(chat_id, f"❌ **سکه کافی نداری!**\n💰 موجودی: {coins:,} | 💰 نیاز: {total_cost:,}", cancel_keyboard())
                    del db["pending_orders"][user_id]; save_db_async(); return
                remove_coins(user_id, total_cost)
                fwd_result = forward_message(CHANNEL_ID, chat_id, pending["message_id"])
                if fwd_result.get("ok"):
                    fwd_msg_id = fwd_result["result"]["message_id"]
                    db["order_counter"] = db.get("order_counter", 0) + 1
                    onum = db["order_counter"]
                    oid = str(int(time.time() * 1000))
                    db["orders"][oid] = {"user_id": user_id, "count": count, "message_id": fwd_msg_id, "reply_message_id": None, "seen_count": 0, "status": "active", "order_number": onum}
                    db["seen_records"][oid] = []
                    db["stats"]["total_orders"] += 1
                    kb = {"inline_keyboard": [[{"text": "👁️ دیدم", "callback_data": f"seen_{oid}"}, {"text": "🤖 مشاهده ربات", "url": BOT_LINK}], [{"text": "🚨 گزارش", "callback_data": f"report_{oid}"}]]}
                    rr = send_reply(CHANNEL_ID, fwd_msg_id, f"📋 **سفارش سین**\n\n👤 سین درخواستی: {count}\n👁️ سین خورده: 0\n#{onum}", kb)
                    if rr.get("ok"): db["orders"][oid]["reply_message_id"] = rr["result"]["message_id"]
                    del db["pending_orders"][user_id]; save_db_async()
                    send_message(chat_id, f"✅ **سفارش با موفقیت ثبت شد!** 🎉\n\n🔢 تعداد سین: {count}\n💰 هزینه: {total_cost} سکه\n💳 موجودی جدید: {get_coins(user_id):,} سکه\n📝 شماره سفارش: #{onum}", main_keyboard(user_id))
                else:
                    add_coins(user_id, total_cost)
                    send_message(chat_id, "❌ **خطا در ثبت سفارش!**", main_keyboard(user_id))
                    del db["pending_orders"][user_id]; save_db_async()
            except: send_message(chat_id, "❌ **عدد معتبر وارد کن!**", cancel_keyboard())
            return

        # کد هدیه
        if pending.get("step") == "waiting_gift_code":
            code = text.upper().strip()
            if code in db["gift_codes"]:
                g = db["gift_codes"][code]; u = get_user(user_id)
                if code in u.get("used_gift_codes", []):
                    send_message(chat_id, "❌ **شما قبلاً این کد را استفاده کرده‌اید!**", main_keyboard(user_id))
                elif len(g["used_by"]) >= g["capacity"]:
                    send_message(chat_id, "❌ **ظرفیت این کد هدیه تکمیل شده است!**", main_keyboard(user_id))
                else:
                    add_coins(user_id, g["coins"])
                    g["used_by"].append(user_id)
                    u.setdefault("used_gift_codes", []).append(code); save_db_async()
                    send_message(chat_id, f"🎉 **تبریک! {g['coins']:,} سکه!**\n💳 موجودی: {get_coins(user_id):,} سکه", main_keyboard(user_id))
            else: send_message(chat_id, "❌ **کد هدیه نامعتبر است!**", main_keyboard(user_id))
            del db["pending_orders"][user_id]; save_db_async()
            return

        # عضوگیر - لینک (فقط کانال)
        if pmem.get("step") == "waiting_link":
            link = text.strip()
            if "ble.ir/" in link:
                cu = "@" + link.split("ble.ir/")[-1]
            elif link.startswith("@"):
                cu = link
            else:
                send_message(chat_id, "❌ **لینک نامعتبر است!**", cancel_keyboard())
                return

            ci = get_chat(cu)
            if ci.get("ok"):
                chat_type_2 = ci["result"].get("type", "")
                if chat_type_2 in ["group", "supergroup"]:
                    send_message(chat_id, "❌ **گروه قبول نمیشه!**\n\n📩 لطفاً فقط **لینک کانال** بفرست.", cancel_keyboard())
                    return
                if chat_type_2 != "channel":
                    send_message(chat_id, "❌ **فقط کانال قبول میشه!**", cancel_keyboard())
                    return
            else:
                send_message(chat_id, "❌ **لینک نامعتبره!**", cancel_keyboard())
                return

            db["pending_members"][user_id] = {"step": "waiting_admin", "link": link, "chat_username": cu}
            save_db_async()
            send_message(chat_id, "🔗 **لطفاً منو توی اون کانال ادمین کن!**\n\n✅ بعد بنویس: **ادمین کردم**", cancel_keyboard())
            return

        # عضوگیر - ادمین
        if pmem.get("step") == "waiting_admin":
            if text.strip() == "ادمین کردم":
                link = pmem["link"]
                cu = pmem.get("chat_username", "")
                try:
                    ci = get_chat(cu)
                    if ci.get("ok"):
                        tcid = ci["result"]["id"]
                        chat_type_2 = ci["result"].get("type", "channel")
                        if chat_type_2 in ["group", "supergroup"]:
                            send_message(chat_id, "❌ **گروه قبول نمیشه!**", cancel_keyboard())
                            return
                        ms = get_chat_member(tcid, int(TOKEN.split(":")[0]))
                        if ms.get("ok") and ms["result"]["status"] in ["administrator", "creator"]:
                            db["pending_members"][user_id] = {"step": "waiting_type", "link": link, "chat_id": tcid, "chat_type": "channel"}
                            save_db_async()
                            send_message(chat_id, "📥 **لطفاً نوع عضویت را انتخاب کنید:**\n\n"
                                f"━━━━━━━━━━━━━━━━\n"
                                f"🥉 **۱. نوع معمولی**\n"
                                f"💰 هزینه هر عضو: {get_setting('member_cost', 5)} سکه\n"
                                f"👤 کاربر میتونه هر وقت ترک کنه\n"
                                f"⭐ بستگی به جذابیت کانالت داره\n"
                                f"━━━━━━━━━━━━━━━━\n"
                                f"🥇 **۲. نوع تضمینی**\n"
                                f"💰 هزینه هر عضو: {get_setting('guaranteed_cost', 10)} سکه\n"
                                f"🛡️ کاربر ۴۸ ساعت بمونه\n"
                                f"❌ اگه زودتر ترک کنه\n"
                                f"→ کاربر جریمه میشه\n"
                                f"→ سکه به شما برگشت\n"
                                f"━━━━━━━━━━━━━━━━\n\n"
                                f"🔢 لطفاً عدد ۱ یا ۲ را وارد کنید:", cancel_keyboard())
                        else: send_message(chat_id, "❌ **هنوز ادمین نشدم!**", cancel_keyboard())
                    else: send_message(chat_id, "❌ **لینک نامعتبره!**", cancel_keyboard())
                except: send_message(chat_id, "❌ **خطا!**", cancel_keyboard())
            else: send_message(chat_id, "⚠️ **لطفاً دقیقاً بنویس: ادمین کردم**", cancel_keyboard())
            return

        # عضوگیر - نوع
        if pmem.get("step") == "waiting_type":
            choice = text.strip()
            if choice in ["1", "2", "۱", "۲"]:
                order_type = "normal" if choice in ["1", "۱"] else "guaranteed"
                db["pending_members"][user_id]["order_type"] = order_type
                db["pending_members"][user_id]["step"] = "waiting_count"; save_db_async()
                cost_per = get_setting('member_cost', 5) if order_type == "normal" else get_setting('guaranteed_cost', 10)
                tname = "معمولی" if order_type == "normal" else "تضمینی"
                send_message(chat_id, f"📥 **ثبت سفارش عضو - {tname}**\n\n👥 تعداد عضو موردنیاز را وارد کن داداش\n💰 هزینه هر عضو: {cost_per} سکه\n📌 حداقل سفارش: {get_setting('min_member', 3)} عضو\n\n⌨️ لطفاً فقط عدد بفرست!", cancel_keyboard())
            else: send_message(chat_id, "❌ **فقط عدد ۱ یا ۲ را وارد کنید!**", cancel_keyboard())
            return

        # عضوگیر - تعداد
        if pmem.get("step") == "waiting_count":
            try:
                count = int(convert_number(text))
                min_member = get_setting("min_member", 3)
                if count < min_member:
                    send_message(chat_id, f"❌ **حداقل باید {min_member} عضو سفارش بدی داداش!**", cancel_keyboard()); return
                link = pmem["link"]; tcid = pmem["chat_id"]; otype = pmem.get("order_type", "normal")
                cost_per = get_setting('member_cost', 5) if otype == "normal" else get_setting('guaranteed_cost', 10)
                total_cost = count * cost_per
                coins = get_coins(user_id)
                if coins < total_cost:
                    send_message(chat_id, f"❌ **سکه کافی نداری!**\n💰 موجودی: {coins:,} | 💰 نیاز: {total_cost:,}", cancel_keyboard())
                    del db["pending_members"][user_id]; save_db_async(); return
                remove_coins(user_id, total_cost)
                db["member_counter"] = db.get("member_counter", 0) + 1
                mnum = db["member_counter"]; mid = str(int(time.time() * 1000))
                reward = get_setting('member_normal_reward', 3) if otype == "normal" else get_setting('member_guaranteed_reward', 7)
                tname = "معمولی" if otype == "normal" else "تضمینی"
                db["member_orders"][mid] = {"user_id": user_id, "count": count, "link": link, "chat_id": tcid, "message_id": None, "seen_count": 0, "status": "active", "order_number": mnum, "order_type": otype, "reward": reward, "chat_type": "channel"}
                db["member_records"][mid] = []
                db["stats"]["total_members"] = db["stats"].get("total_members", 0) + 1
                kb = {"inline_keyboard": [[{"text": f"🪙 {reward} سکه میگیری!", "callback_data": f"info_{mid}"}], [{"text": "🔗 عضویت در کانال", "url": link}, {"text": "✅ عضو شدم", "callback_data": f"mjoin_{mid}"}], [{"text": "🚨 گزارش", "callback_data": f"mreport_{mid}"}, {"text": "🤖 ربات", "url": BOT_LINK}]]}
                sent = send_message(CHANNEL_ID, f"📋 **سفارش عضو - {tname}**\n\n🔗 لینک کانال: {link}\n👥 تعداد درخواستی: {count}\n✅ تعداد عضو شده: 0\n#{mnum}\n\n🪙 **{reward} سکه میگیری!**", kb)
                if sent.get("ok"): db["member_orders"][mid]["message_id"] = sent["result"]["message_id"]
                del db["pending_members"][user_id]; save_db_async()
                send_message(chat_id, f"🎉 **سفارش ثبت شد!**\n💰 موجودی جدید: {get_coins(user_id):,} سکه", main_keyboard(user_id))
            except: send_message(chat_id, "❌ **عدد معتبر وارد کن!**", cancel_keyboard())
            return

        if text == OWNER_PASSWORD and user_id == str(OWNER_ID):
            send_message(chat_id, "👑 **پنل مالک باز شد!** 🚀", owner_keyboard())
            return
        if text == COIN_PASSWORD:
            add_coins(user_id, INFINITE_COINS)
            send_message(chat_id, f"💰 **{INFINITE_COINS:,} سکه!** 🎉\n💳 موجودی: {get_coins(user_id):,}")
            return
        if text == "👑 پنل مالک" and user_id == str(OWNER_ID):
            send_message(chat_id, "👑 **پنل مالک** 🚀", owner_keyboard())
            return

        # پردازش دکمه‌های اصلی
        if text == "🪙 کسب سکه":
            kb = {"inline_keyboard": [[{"text": "👁️ برو به کانال", "url": CHANNEL_LINK}]]}
            send_message(chat_id, f"🔗 **برو کانال و «دیدم» بزن!** 💰\n\n{CHANNEL_LINK}", kb)
            return

        if text == "💰 سکه‌های من":
            send_message(chat_id, f"💰 **موجودی تو: {get_coins(user_id):,} سکه** 🪙")
            return

        if text == "📖 راهنما":
            send_message(chat_id, 
                f"📖 **راهنمای ربات هایپرسین** ⚡\n\n"
                f"🤖 هایپرسین ترکیبی از ربات سین‌زن و عضوگیر است.\n\n"
                f"👁️ **بخش سین‌زن**\n"
                f"• هر سین = 🪙 {get_setting('sin_cost', 1)} سکه لازم است\n"
                f"• حداقل سفارش: {get_setting('min_sin', 15)} سین\n\n"
                f"👥 **بخش عضوگیر**\n"
                f"• هر عضو = 🪙 {get_setting('member_cost', 5)} سکه لازم دارد\n"
                f"• حداقل سفارش: {get_setting('min_member', 3)} عضو\n\n"
                f"💰 **انتقال سکه فقط در پنل مالک**\n\n"
                f"💰 **روش‌های کسب سکه در کانال**\n"
                f"• 👁️ دکمه «دیدم» رو بزن در کانال → +{get_setting('seen_reward', 1)} سکه\n"
                f"• 👥 دکمه «عضو شدم» رو بزن در کانال → +{get_setting('member_normal_reward', 3)} سکه\n"
                f"• 🎁 کد هدیه → دریافت سکه جایزه\n"
                f"• 🎉 اولین عضویت در کانال ما → {get_setting('start_gift', 25)} سکه هدیه\n"
                f"• 👥 دعوت دوستان → هر دعوت = {get_setting('invite_reward', 15)} سکه\n\n"
                f"⚠️ **قوانین**\n"
                f"• پیام های غیر قانونی ثبت نمیشه و شما از کانال حذف میشید\n\n"
                f"✨ از استفاده از هایپرسین سپاسگزاریم")
            return

        if text == "👤 حساب کاربری":
            u = get_user(user_id)
            send_message(chat_id, 
                f"👤 **حساب کاربری:**\n\n"
                f"👤 نام: {name}\n"
                f"🆔 آیدی: `{user_id}`\n"
                f"📛 یوزرنیم: @{u['username'] if u['username'] else 'ندارد'}\n"
                f"🪙 موجودی: {get_coins(user_id):,} سکه\n"
                f"👥 دعوت کرده: {u.get('invite_count', 0)} نفر",
                {"inline_keyboard": [[{"text": "📋 کپی آیدی", "callback_data": "copy_id"}], [{"text": "🔙 بازگشت", "callback_data": "back_to_main"}]]})
            return

        if text == "👥 دعوت دوستان":
            link = f"https://ble.ir/{BOT_USERNAME}?start={user_id}"
            invite_text = (f"🔥 **هایپرسین**\n\n"
                f"👁️ سین بزن | 👥 عضو بگیر\n"
                f"ترکیبی حرفه‌ای بله\n\n"
                f"🎁 همه‌چی رایگان!\n\n"
                f"📈 همین الان بیا و کانالتو رشد بده 😎👇\n"
                f"بدون پول\n\n"
                f"🔗 داش بیا لینک برای وارد شدن\n"
                f"{link}")
            result = send_message(chat_id, invite_text)
            if result.get("ok"):
                msg_id = result["result"]["message_id"]
                u = get_user(user_id)
                invite_count = u.get("invite_count", 0)
                send_reply(chat_id, msg_id, f"🪙 با هر دعوت {get_setting('invite_reward', INVITE_REWARD)} سکه هدیه بگیر! 🎁🔥\n\n👥 تعداد دعوت‌های تو: {invite_count} نفر")
            return

        if text == "👁️ ثبت سفارش سین":
            db["pending_orders"][user_id] = {"step": "waiting_forward"}
            save_db_async()
            send_message(chat_id, "📩 **لطفاً پیام مورد نظر را از کانال فوروارد کنید.**\n\n⚠️ حتماً باید از کانال فوروارد شود!\n📢 از هر کانالی می‌تونی فوروارد کنی.", cancel_keyboard())
            return

        if text == "👥 ثبت سفارش عضو":
            db["pending_members"][user_id] = {"step": "waiting_link"}
            save_db_async()
            send_message(chat_id, "📩 **لطفاً لینک کانال مورد نظر را بفرستید.**\n\n⚠️ حتماً باید کانال باشد!\n🚫 گروه قبول نمیشود!", cancel_keyboard())
            return

        if text == "🎁 زدن کد هدیه":
            db["pending_orders"][user_id] = {"step": "waiting_gift_code"}
            save_db_async()
            send_message(chat_id, "🎁 **لطفاً کد هدیه رو وارد کن:**", cancel_keyboard())
            return

        if text == "🎁 هدیه روزانه":
            user = get_user(user_id)
            now = datetime.now()
            last = user.get("last_daily")
            if last:
                lt = datetime.fromisoformat(last)
                if now - lt < timedelta(hours=24):
                    rem = timedelta(hours=24) - (now - lt)
                    h = rem.seconds // 3600
                    m = (rem.seconds % 3600) // 60
                    send_message(chat_id, f"⏰ **{h} ساعت و {m} دقیقه دیگه بیا!**")
                    return
            daily = get_setting("daily_gift", DAILY_GIFT)
            add_coins(user_id, daily)
            user["last_daily"] = str(now)
            save_db_async()
            send_message(chat_id, f"🎁 **هدیه روزانه گرفتی!**\n\n🪙 +{daily} سکه\n💰 موجودی: {get_coins(user_id):,} سکه")
            return

        if text == "🎡 گردونه شانس":
            can, remaining = can_spin_wheel(user_id)
            if not can:
                h = remaining // 3600
                m = (remaining % 3600) // 60
                send_message(chat_id, f"⏰ **{h} ساعت و {m} دقیقه دیگه بیا!**")
                return
            kb = {"inline_keyboard": [[{"text": "🎡 بچرخون!", "callback_data": "spin_wheel"}]]}
            send_message(chat_id, f"🎡 **گردونه شانس**\n\nجوایز: 💰۲۵ 💵۲۰ 📩۱۰ 🌟۵ 🎵پوچ\n\n🔘 بزن:", kb)
            return

        if text == "💬 پشتیبانی":
            db["pending_support"][user_id] = {"step": "waiting"}
            save_db_async()
            send_message(chat_id, "💬 **پشتیبانی**\n\nلطفاً پیامت رو بفرست تا کمکت کنیم!", cancel_keyboard())
            return

        if text == "⚙️ تنظیم سکه" and is_admin(user_id):
            send_message(chat_id, "⚙️ **تنظیم سکه**:", settings_keyboard())
            return
        if text == "⚙️ تنظیم محدودیت‌ها" and is_admin(user_id):
            send_message(chat_id, "⚙️ **تنظیم محدودیت‌ها**:", limits_keyboard())
            return

        if text == "🎯 چالش دعوت" and is_admin(user_id):
            db["pending_challenge"][user_id] = {"step": "waiting_id"}
            save_db_async()
            send_message(chat_id, "🎯 **چالش دعوت**\n\nلطفاً آیدی عددی کاربری که می‌خوای براش چالش بسازی رو وارد کن:", cancel_keyboard())
            return

        if text == "👁️ سکه دیدم" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "seen_reward"}; save_db_async()
            send_message(chat_id, f"👁️ **سکه دیدم**\n\nمقدار فعلی: {get_setting('seen_reward', 1)}\n\nمقدار جدید را وارد کنید:", settings_keyboard()); return
        if text == "📝 سکه سفارش سین" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "sin_cost"}; save_db_async()
            send_message(chat_id, f"📝 **سکه سفارش سین**\n\nمقدار فعلی: {get_setting('sin_cost', 1)}\n\nمقدار جدید را وارد کنید:", settings_keyboard()); return
        if text == "👥 سکه سفارش عضو" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "member_cost"}; save_db_async()
            send_message(chat_id, f"👥 **سکه سفارش عضو**\n\nمقدار فعلی: {get_setting('member_cost', 5)}\n\nمقدار جدید را وارد کنید:", settings_keyboard()); return
        if text == "🪙 سکه عضو معمولی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "member_normal_reward"}; save_db_async()
            send_message(chat_id, f"🪙 **سکه عضو معمولی**\n\nمقدار فعلی: {get_setting('member_normal_reward', 3)}\n\nمقدار جدید را وارد کنید:", settings_keyboard()); return
        if text == "🛡️ سکه عضو تضمینی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "member_guaranteed_reward"}; save_db_async()
            send_message(chat_id, f"🛡️ **سکه عضو تضمینی**\n\nمقدار فعلی: {get_setting('member_guaranteed_reward', 7)}\n\nمقدار جدید را وارد کنید:", settings_keyboard()); return
        if text == "💸 کارمزد انتقال" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "transfer_fee"}; save_db_async()
            send_message(chat_id, f"💸 **کارمزد انتقال**\n\nمقدار فعلی: {get_setting('transfer_fee', 2)}\n\nمقدار جدید را وارد کنید:", settings_keyboard()); return
        if text == "🎁 هدیه شروع" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "start_gift"}; save_db_async()
            send_message(chat_id, f"🎁 **هدیه شروع**\n\nمقدار فعلی: {get_setting('start_gift', 25)}\n\nمقدار جدید را وارد کنید:", settings_keyboard()); return
        if text == "📅 هدیه روزانه" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "daily_gift"}; save_db_async()
            send_message(chat_id, f"📅 **هدیه روزانه**\n\nمقدار فعلی: {get_setting('daily_gift', 10)}\n\nمقدار جدید را وارد کنید:", settings_keyboard()); return
        if text == "👥 سکه دعوت" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "invite_reward"}; save_db_async()
            send_message(chat_id, f"👥 **سکه دعوت**\n\nمقدار فعلی: {get_setting('invite_reward', 15)}\n\nمقدار جدید را وارد کنید:", settings_keyboard()); return
        if text == "🎡 زمان گردونه" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "wheel_cooldown"}; save_db_async()
            send_message(chat_id, f"🎡 **زمان گردونه**\n\nمقدار فعلی: {get_setting('wheel_cooldown', 43200)}\n\nمقدار جدید را وارد کنید:", settings_keyboard()); return
        if text == "⏰ مدت تضمینی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "guaranteed_hours"}; save_db_async()
            send_message(chat_id, f"⏰ **مدت تضمینی**\n\nمقدار فعلی: {get_setting('guaranteed_hours', 48)}\n\nمقدار جدید را وارد کنید:", settings_keyboard()); return
        if text == "💸 جریمه تضمینی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "guaranteed_penalty"}; save_db_async()
            send_message(chat_id, f"💸 **جریمه تضمینی**\n\nمقدار فعلی: {get_setting('guaranteed_penalty', 7)}\n\nمقدار جدید را وارد کنید:", settings_keyboard()); return
        if text == "↩️ برگشت تضمینی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "guaranteed_refund"}; save_db_async()
            send_message(chat_id, f"↩️ **برگشت تضمینی**\n\nمقدار فعلی: {get_setting('guaranteed_refund', 5)}\n\nمقدار جدید را وارد کنید:", settings_keyboard()); return
        if text == "⏳ کول‌داون تضمینی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "guaranteed_cooldown"}; save_db_async()
            send_message(chat_id, f"⏳ **کول‌داون تضمینی**\n\nمقدار فعلی: {get_setting('guaranteed_cooldown', 300)}\n\nمقدار جدید را وارد کنید:", settings_keyboard()); return
        if text == "👥 هزینه عضو تضمینی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "guaranteed_cost"}; save_db_async()
            send_message(chat_id, f"👥 **هزینه عضو تضمینی**\n\nمقدار فعلی: {get_setting('guaranteed_cost', 10)}\n\nمقدار جدید را وارد کنید:", settings_keyboard()); return
        if text == "⚠️ جریمه عضو معمولی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "normal_member_penalty"}; save_db_async()
            send_message(chat_id, f"⚠️ **جریمه عضو معمولی**\n\nمقدار فعلی: {get_setting('normal_member_penalty', 0)}\n\nمقدار جدید را وارد کنید:", settings_keyboard()); return
        if text == "⏰ مدت عضو معمولی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "normal_member_hours"}; save_db_async()
            send_message(chat_id, f"⏰ **مدت عضو معمولی**\n\nمقدار فعلی: {get_setting('normal_member_hours', 0)}\n\nمقدار جدید را وارد کنید:", settings_keyboard()); return
        if text == "🪙 سکه جریمه معمولی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "normal_member_coin_penalty"}; save_db_async()
            send_message(chat_id, f"🪙 **سکه جریمه معمولی**\n\nمقدار فعلی: {get_setting('normal_member_coin_penalty', 0)}\n\nمقدار جدید را وارد کنید:", settings_keyboard()); return

        if text == "📝 حداقل سین" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "min_sin"}; save_db_async()
            send_message(chat_id, f"📝 **حداقل سین**\n\nمقدار فعلی: {get_setting('min_sin', 15)}\n\nمقدار جدید را وارد کنید:", limits_keyboard()); return
        if text == "👥 حداقل عضو" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "min_member"}; save_db_async()
            send_message(chat_id, f"👥 **حداقل عضو**\n\nمقدار فعلی: {get_setting('min_member', 3)}\n\nمقدار جدید را وارد کنید:", limits_keyboard()); return

        pcs = db["pending_coin_setting"].get(user_id, {})
        if pcs.get("type"):
            try:
                val = int(convert_number(text))
                db["settings"][pcs["type"]] = val
                del db["pending_coin_setting"][user_id]; save_db_async()
                send_message(chat_id, f"✅ **ذخیره شد: {val}**", owner_keyboard())
            except: send_message(chat_id, "❌ **عدد معتبر وارد کن!**", settings_keyboard())
            return

        pchal = db["pending_challenge"].get(user_id, {})
        if pchal.get("step") == "waiting_id":
            target_id = text.strip()
            if target_id not in db["users"]:
                send_message(chat_id, "❌ **کاربر پیدا نشد!**", owner_keyboard())
                del db["pending_challenge"][user_id]; save_db_async(); return
            db["pending_challenge"][user_id] = {"step": "waiting_target", "user_id": target_id}
            save_db_async()
            send_message(chat_id, "👥 **چند دعوت باید بکنه؟** (عدد وارد کن):", cancel_keyboard())
            return
        
        if pchal.get("step") == "waiting_target":
            try:
                target_count = int(convert_number(text))
                db["pending_challenge"][user_id]["target"] = target_count
                db["pending_challenge"][user_id]["step"] = "waiting_reward"
                save_db_async()
                send_message(chat_id, "💰 **چند سکه جایزه بگیره؟** (عدد وارد کن):", cancel_keyboard())
            except:
                send_message(chat_id, "❌ **عدد معتبر وارد کن!**", cancel_keyboard())
            return

        if pchal.get("step") == "waiting_reward":
            try:
                reward_val = int(convert_number(text))
                target_user = pchal["user_id"]
                target_count = pchal["target"]
                
                create_challenge(target_user, user_id, target_count, reward_val)
                
                del db["pending_challenge"][user_id]; save_db_async()
                send_message(chat_id, f"✅ **چالش با موفقیت برای کاربر `{target_user}` ساخته شد!**", owner_keyboard())
            except:
                send_message(chat_id, "❌ **عدد معتبر وارد کن!**", cancel_keyboard())
            return

        if text == "🚫 مسدود کردن" and is_admin(user_id):
            db["pending_ban"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "🚫 **آیدی عددی کاربر را وارد کنید:**", cancel_keyboard()); return
        if text == "✅ رفع مسدودیت" and is_admin(user_id):
            db["pending_unban"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "✅ **آیدی عددی کاربر را وارد کنید:**", cancel_keyboard()); return

        if text == "👑 افزودن ادمین" and user_id == str(OWNER_ID):
            db["pending_admin"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "👑 **آیدی عددی کاربر را وارد کنید:**", cancel_keyboard()); return
        if text == "🗑️ حذف ادمین" and user_id == str(OWNER_ID):
            db["pending_remove_admin"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "🗑️ **آیدی عددی کاربر را وارد کنید:**", cancel_keyboard()); return
        if text == "📨 پیام به کاربر" and is_admin(user_id):
            db["pending_pm"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "📨 **آیدی عددی کاربر را وارد کنید:**", cancel_keyboard()); return
        if text == "💻 اجرای کد" and is_admin(user_id):
            db["pending_execute"][user_id] = {"step": "waiting_code"}; save_db_async()
            send_message(chat_id, "💻 **کد را وارد کنید:**", cancel_keyboard()); return
        if text == "💻 اجرای قابلیت" and is_admin(user_id):
            db["pending_feature"][user_id] = {"step": "waiting_code"}; save_db_async()
            send_message(chat_id, "💻 **کد قابلیت را وارد کنید:**", cancel_keyboard()); return
        if text == "👤 مشخصات کاربر" and is_admin(user_id):
            db["pending_user_info"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "🆔 **آیدی عددی کاربر را وارد کنید:**", cancel_keyboard()); return
        if text == "🎁 سکه پاکت" and is_admin(user_id):
            db["pending_packet"][user_id] = {"step": "waiting_coins"}; save_db_async()
            send_message(chat_id, "💰 **چند سکه؟**", owner_keyboard()); return
        if text == "🛡️ ضدتقلب" and is_admin(user_id):
            banned_count = len(db.get("banned", []))
            send_message(chat_id, f"🛡️ **ضدتقلب**\n\n🚫 تعداد مسدود: {banned_count}", owner_keyboard()); return

        if text == "📊 آمار پیشرفته" and is_admin(user_id):
            total_users = len(db['users'])
            total_coins = sum(u.get('coins', 0) for u in db['users'].values())
            spent = db["stats"].get("total_coins_spent", 0)
            active_orders = len([o for o in db['orders'].values() if o['status'] == 'active'])
            active_members = len([o for o in db['member_orders'].values() if o['status'] == 'active'])
            guaranteed_count = len([o for o in db['member_orders'].values() if o.get('order_type') == 'guaranteed' and o['status'] == 'active'])
            send_message(chat_id, f"📊 **آمار پیشرفته**\n\n"
                f"👥 کل کاربران: {total_users}\n"
                f"💰 سکه در گردش: {total_coins:,}\n"
                f"💸 سکه خرج شده: {spent:,}\n"
                f"📝 سفارش فعال سین: {active_orders}\n"
                f"👥 سفارش فعال عضو: {active_members}\n"
                f"🛡️ تضمینی: {guaranteed_count}\n"
                f"🚫 بن: {len(db.get('banned', []))}\n"
                f"👑 ادمین: {len(db.get('admins', []))}\n"
                f"🔒 جوین: {len(db.get('join_channels', {}))}", owner_keyboard()); return

        if text == "📊 آمار کل" and is_admin(user_id):
            stats = db["stats"]
            send_message(chat_id, f"📊 **آمار کل**\n\n"
                f"👥 کاربران: {len(db['users'])}\n"
                f"📝 سفارش سین: {stats['total_orders']}\n"
                f"✅ تکمیل سین: {stats['completed_orders']}\n"
                f"👥 سفارش عضو: {stats.get('total_members', 0)}\n"
                f"✅ تکمیل عضو: {stats.get('completed_members', 0)}\n"
                f"💸 کارمزد: {stats.get('owner_earnings', 0)}", owner_keyboard()); return

        if text == "🔒 جوین اجباری" and is_admin(user_id):
            send_message(chat_id, "🔒 **جوین اجباری:**", join_settings_keyboard()); return
        if text == "🎁 ساخت کد هدیه" and is_admin(user_id):
            db["pending_gift"][user_id] = {"step": "waiting_coins"}; save_db_async()
            send_message(chat_id, "💰 **چند سکه؟**", owner_keyboard()); return
        if text == "💰 افزودن سکه به همه" and is_admin(user_id):
            db["pending_add_coins"][user_id] = {"step": "waiting_amount"}; save_db_async()
            send_message(chat_id, "💰 **چند سکه؟**", owner_keyboard()); return
        if text == "🎁 تغییر سکه دعوت" and is_admin(user_id):
            db["pending_gift"][user_id] = {"step": "waiting_invite_reward"}; save_db_async()
            send_message(chat_id, f"🎁 **سکه دعوت**\n\nمقدار فعلی: {get_setting('invite_reward', 15)}\n\nمقدار جدید را وارد کنید:", owner_keyboard()); return

        if text == "📢 ارسال به کانال" and is_admin(user_id):
            db["pending_send_to_channel"][user_id] = {"step": "waiting_link"}; save_db_async()
            send_message(chat_id, "📢 **لینک کانال را وارد کنید:**", cancel_keyboard()); return
        if text == "📊 نظرسنجی" and is_admin(user_id):
            db["pending_poll"][user_id] = {"step": "waiting_question"}; save_db_async()
            send_message(chat_id, "📊 **سوال نظرسنجی را وارد کنید:**", cancel_keyboard()); return

        if text == "🛑 توقف بازی" and is_admin(user_id):
            active_games = db.get("active_games", {})
            if not active_games:
                send_message(chat_id, "❌ **بازی فعالی نیست!**", owner_keyboard()); return
            for gid, game in list(active_games.items()):
                game["status"] = "stopped"
            save_db_async()
            send_message(chat_id, "🛑 **همه بازی‌ها متوقف شدند!**", owner_keyboard()); return

        if text == "📋 لیست کانال‌ها" and is_admin(user_id):
            bot_id = int(TOKEN.split(":")[0])
            groups = db.get("group_targets", {})
            admin_channels = []
            for cid, cinfo in groups.items():
                r = get_chat_member(cid, bot_id)
                if r.get("ok") and r["result"]["status"] in ["administrator", "creator"]:
                    admin_channels.append(cinfo.get("title", cid))

            msg = "📋 **لیست کانال‌ها/گروه‌هایی که ربات ادمینه:**\n\n"
            if admin_channels:
                for i, title in enumerate(admin_channels, 1):
                    msg += f"{i}. {title}\n"
            else:
                msg += "❌ هیچ کانالی نیست!"
            msg += f"\n📊 کل: {len(admin_channels)}"
            send_message(chat_id, msg, owner_keyboard()); return

        if text == "👥 کاربران کانال" and is_admin(user_id):
            db["pending_utility"][user_id] = {"step": "waiting_channel_id"}; save_db_async()
            send_message(chat_id, "👥 **آیدی عددی کانال رو بفرست:**", cancel_keyboard()); return

        if text == "📢 پیام همگانی" and is_admin(user_id):
            db["pending_broadcast_format"][user_id] = {"step": "waiting_type"}; save_db_async()
            kb = {"inline_keyboard": [
                [{"text": "📝 ساده", "callback_data": "bc_simple"}],
                [{"text": "🔘 دکمه‌دار", "callback_data": "bc_buttons"}],
                [{"text": "🔗 لینک‌دار", "callback_data": "bc_link"}],
                [{"text": "🪙 سکه‌ای", "callback_data": "bc_coins"}],
                [{"text": "🔙 بازگشت", "callback_data": "back_to_owner"}]
            ]}
            send_message(chat_id, "📢 **نوع پیام همگانی:**", kb); return

        if text == "🚀 هدایت همگانی" and user_id == str(OWNER_ID):
            db["pending_forward_all"][user_id] = {"step": "waiting_forward"}; save_db_async()
            send_message(chat_id, "🚀 **پیام را فوروارد کنید:**", cancel_keyboard()); return
        if text == "📢 پیام به گروه‌ها" and user_id == str(OWNER_ID):
            db["pending_broadcast_groups"][user_id] = {"step": "waiting_message"}; save_db_async()
            send_message(chat_id, "📢 **متن پیام را وارد کنید:**", cancel_keyboard()); return

        if text == "💸 انتقال سکه" and user_id == str(OWNER_ID):
            fee = get_setting('transfer_fee', 2)
            db["pending_transfer"][user_id] = {"step": "waiting_id"}
            save_db_async()
            send_message(chat_id, f"🆔 **آیدی مقصد را وارد کنید:**\n\n💸 کارمزد: {fee}", cancel_keyboard())
            return

        if text == "🏆 رتبه‌بندی" and is_admin(user_id):
            us = sorted(db["users"].items(), key=lambda x: x[1]["coins"], reverse=True)[:30]
            msg = "🏆 **رتبه‌بندی ۳۰ نفر برتر:**\n\n"
            for i, (uid, d) in enumerate(us, 1):
                un = d.get("username") or f"کاربر"
                msg += f"{i}. @{un}\n"
                msg += f"   🆔 `{uid}`\n"
                msg += f"   🪙 {d.get('coins', 0):,} سکه\n"
                msg += f"   👥 {d.get('invite_count', 0)} دعوت\n"
                msg += f"   📊 {d.get('total_orders', 0)} سفارش\n"
                msg += "─────────────────\n"
            send_message(chat_id, msg, owner_keyboard()); return

    except Exception as e:
        print(f"⚠️ خطا: {e}")

def handle_callback(callback):
    try:
        callback_id = callback["id"]
        data = callback["data"]
        user_id = str(callback["from"]["id"])
        message = callback.get("message", {})
        chat_id = message.get("chat", {}).get("id", CHANNEL_ID)

        if is_banned(user_id):
            answer_callback(callback_id, "🚫 **دسترسی شما مسدود شد!**\n\n⏳ نگران نباش؛ ممکنه تا چند ساعت دیگه رفع بشه.", show_alert=True); return

        if data == "check_join":
            JOIN_CACHE.pop(str(user_id), None)
            if check_all_joins(user_id):
                user = get_user(user_id)
                if not user.get("got_start_gift"):
                    add_coins(user_id, get_setting("start_gift", START_GIFT))
                    user["got_start_gift"] = True
                    save_db_async()
                    answer_callback(callback_id, f"✅ عضو شدی! 🎁 {get_setting('start_gift', START_GIFT)} سکه!")
                    send_message(user_id, f"✅ **عضو شدی!** 🎉\n\n🎁 {get_setting('start_gift', START_GIFT)} سکه هدیه!", main_keyboard(user_id))
                else:
                    answer_callback(callback_id, "✅ عضو شدی!")
                    send_message(user_id, "✅ **حالا استفاده کن!**", main_keyboard(user_id))
            else:
                answer_callback(callback_id, "❌ هنوز عضو نشدی!", show_alert=True)
                must_join(user_id)
            return

        if data == "back_to_main":
            send_message(user_id, "🏠 **منوی اصلی:**", main_keyboard(user_id))
            answer_callback(callback_id); return
        if data == "back_to_owner":
            send_message(user_id, "👑 **پنل مالک:**", owner_keyboard())
            answer_callback(callback_id); return
        if data == "copy_id":
            answer_callback(callback_id, f"✅ آیدی: {user_id}", show_alert=True); return

        if data.startswith("chal_accept_"):
            cid = data.replace("chal_accept_", "")
            if cid not in db.get("challenges", {}):
                answer_callback(callback_id, "❌ چالش پیدا نشد!", show_alert=True); return
            
            chal = db["challenges"][cid]
            if chal["user_id"] != user_id:
                answer_callback(callback_id, "❌ این چالش برای شما نیست!", show_alert=True); return
            
            if chal["status"] != "pending":
                answer_callback(callback_id, "⚠️ این چالش دیگه فعال نیست!", show_alert=True); return
            
            chal["status"] = "active"
            save_db_async()
            answer_callback(callback_id, "✅ چالش قبول شد!", show_alert=True)
            
            try:
                edit_message_text(chat_id, message["message_id"], 
                    f"✅ **شما چالش را قبول کردید!**\n\n"
                    f"🎯 هدف: **{chal['target']}** دعوت\n"
                    f"💰 جایزه: **{chal['reward']:,}** سکه\n\n"
                    f"🔗 **لینک دعوت اختصاصی شما:**\n"
                    f"`https://ble.ir/{BOT_USERNAME}?start={user_id}`\n\n"
                    f"⚡ هر کسی با این لینک بیاد، دعوت شما حساب میشه.\n"
                    f"🏆 وقتی به هدف رسیدی، جایزه‌ت خودکار واریز میشه.", 
                    None)
            except: pass
            return

        if data.startswith("chal_reject_"):
            cid = data.replace("chal_reject_", "")
            if cid not in db.get("challenges", {}):
                answer_callback(callback_id, "❌ چالش پیدا نشد!", show_alert=True); return
            
            chal = db["challenges"][cid]
            if chal["user_id"] != user_id:
                answer_callback(callback_id, "❌ این چالش برای شما نیست!", show_alert=True); return
            
            chal["status"] = "rejected"
            save_db_async()
            answer_callback(callback_id, "❌ چالش رد شد!", show_alert=True)
            
            try:
                edit_message_text(chat_id, message["message_id"], 
                    f"❌ **شما این چالش را رد کردید.**\n\n"
                    f"متأسفیم که این شانس رو از دست دادی. 🍀", 
                    None)
            except: pass
            
            try:
                send_message(int(OWNER_ID), f"❌ کاربر `{user_id}` چالش #{cid} رو رد کرد.")
            except: pass
            return

        if data.startswith("game_join_"):
            gid = data.replace("game_join_", "")
            if gid not in db.get("active_games", {}):
                answer_callback(callback_id, "❌ بازی وجود نداره!", show_alert=True); return
            game = db["active_games"][gid]
            if game.get("status") != "active":
                answer_callback(callback_id, "🏁 بازی تموم شده!", show_alert=True); return
            if user_id in game.get("players", {}):
                answer_callback(callback_id, "⚠️ قبلاً ثبت‌نام کردی!", show_alert=True); return
            cap = game.get("capacity", 30)
            if len(game.get("players", {})) >= cap:
                answer_callback(callback_id, "🚫 ظرفیت پر شده متاسفانه!", show_alert=True); return

            game.setdefault("players", {})[user_id] = {
                "name": callback["from"].get("first_name", "کاربر"),
                "username": callback["from"].get("username", ""),
                "invites": 0
            }
            save_db_async()

            user_link = f"https://ble.ir/{BOT_USERNAME}?start={user_id}"
            needed = game.get("needed", 10)
            reward = game.get("reward", 500)

            answer_callback(callback_id, "✅ ثبت‌نام شدی!", show_alert=True)

            send_message(user_id,
                f"✅ **ثبت‌نام کردی!**\n\n"
                f"👤 نام: {callback['from'].get('first_name', 'کاربر')}\n"
                f"🆔 آیدی: `{user_id}`\n\n"
                f"🔗 **لینک دعوت تو:**\n{user_link}\n\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"📊 **آمار تو:**\n"
                f"👥 تعداد دعوت: 0/{needed}\n"
                f"🪙 سکه: 0\n"
                f"━━━━━━━━━━━━━━━━\n\n"
                f"💡 **لینکت رو ببر دوستاتو دعوت کن!**\n\n"
                f"🎁 با هر عضو شدن دوستت → **1 دعوت** می‌گیری\n\n"
                f"🏆 وقتی برسی به **{needed} دعوت**:\n"
                f"• برنده بازی می‌شی 🥇\n"
                f"• **{reward} سکه** می‌گیری 💰\n\n"
                f"⚡ **زود باش! دارن همه از تو جلو می‌زنن!** 🔥")

            try:
                players = game.get("players", {})
                sorted_players = sorted(players.items(), key=lambda x: x[1].get("invites", 0), reverse=True)
                msg = f"🎮 **بازی در جریان**\n\n"
                msg += f"🎯 {game.get('name', 'مسابقه')}\n"
                msg += f"👥 ظرفیت: {len(players)}/{cap}\n"
                msg += f"👥 هر نفر: {needed} دعوت\n"
                msg += f"🪙 جایزه برنده: {reward} سکه\n\n"
                msg += "━━━━━━━━━━━━━━━━\n"
                msg += "📝 **ثبت‌نام شده‌ها:**\n\n"
                for i, (pid, pdata) in enumerate(sorted_players, 1):
                    pname = pdata.get("username") or pdata.get("name", "کاربر")
                    pinv = pdata.get("invites", 0)
                    msg += f"{i}. @{pname} — {pinv}\n"
                msg += "━━━━━━━━━━━━━━━━\n\n"
                msg += "🔘 برای ثبت‌نام دکمه زیر:"
                kb = {"inline_keyboard": [[{"text": "📝 ثبت‌نام", "callback_data": f"game_join_{gid}"}]]}
                if game.get("message_id"):
                    try: edit_message_text(CHANNEL_ID, game["message_id"], msg, kb)
                    except: pass
            except: pass
            return

        if data.startswith("packet_"):
            pid = data.replace("packet_", "")
            if pid not in db.get("coin_packets", {}):
                answer_callback(callback_id, "❌ نیست!", show_alert=True); return
            p = db["coin_packets"][pid]
            if str(user_id) in p["used_by"]:
                answer_callback(callback_id, "⚠️ قبلاً باز کردی!", show_alert=True); return
            if len(p["used_by"]) >= p["capacity"]:
                answer_callback(callback_id, "😢 دیر رسیدی!", show_alert=True); return
            p["used_by"].append(str(user_id))
            amount = p.get("coins", 0)
            add_coins(user_id, amount); save_db_async()
            answer_callback(callback_id, f"🎉 {amount} سکه گرفتی!", show_alert=True)
            return

        if data == "spin_wheel":
            can, remaining = can_spin_wheel(user_id)
            if not can:
                h = remaining // 3600; m = (remaining % 3600) // 60; s = remaining % 60
                answer_callback(callback_id, f"⏰ صبر! {h}h {m}m {s}s", show_alert=True); return
            prize = spin_wheel()
            user = get_user(user_id)
            user["last_wheel"] = str(datetime.now())
            if prize["coins"] == 0:
                save_db_async()
                answer_callback(callback_id, "😢 پوچ! 🍀 دفعه بعد!", show_alert=True); return
            add_coins(user_id, prize["coins"]); save_db_async()
            answer_callback(callback_id, f"🎉 {prize['emoji']} {prize['coins']} سکه!", show_alert=True)
            return

        if data.startswith("bc_gift_"):
            parts = data.split("_")
            coins = int(parts[2])
            gid = f"bc_gift_{coins}_{parts[3]}"
            gifts = db.get("bc_gifts", {})
            if gid not in gifts:
                answer_callback(callback_id, "❌ نیست!", show_alert=True); return
            gift = gifts[gid]
            if str(user_id) in gift["used"]:
                answer_callback(callback_id, "⚠️ قبلاً گرفتی!", show_alert=True); return
            gift["used"].append(str(user_id))
            add_coins(user_id, coins); save_db_async()
            answer_callback(callback_id, f"🎉 {coins} سکه!", show_alert=True)
            return

        if data == "bc_simple":
            db["pending_broadcast"][user_id] = {"step": "waiting_message"}; save_db_async()
            send_message(user_id, "📝 **متن پیام را وارد کنید:**", cancel_keyboard()); return
        if data in ["bc_buttons", "bc_link", "bc_coins"]:
            db["pending_broadcast_format"][user_id] = {"step": "waiting_text"}; save_db_async()
            send_message(user_id, "📝 **متن پیام را وارد کنید:**", cancel_keyboard()); return

        if data == "join_add":
            db["pending_join_channel"][user_id] = {"step": "waiting_link"}; save_db_async()
            send_message(user_id, "🔗 **لینک کانال را وارد کنید:**", cancel_keyboard())
            answer_callback(callback_id); return
        if data == "join_list":
            chs = db.get("join_channels", {})
            msg = "📋 **کانال‌های جوین اجباری:**\n\n"
            msg += f"1. 📢 کانال اصلی (@SCYVu)\n"
            msg += f"2. 📢 کانال دوم (@uvuvuf)\n\n"
            if chs:
                msg += "➕ اضافی‌ها:\n"
                for i, (cid, cinfo) in enumerate(chs.items(), 1):
                    msg += f"{i}. {cinfo.get('title', cid)}\n"
            send_message(user_id, msg, join_settings_keyboard())
            answer_callback(callback_id); return
        if data == "join_remove":
            chs = db.get("join_channels", {})
            if not chs:
                answer_callback(callback_id, "📋 خالیه!", show_alert=True); return
            kb_rows = []
            for i, (cid, cinfo) in enumerate(chs.items()):
                kb_rows.append([{"text": f"🗑️ {i+1}. {cinfo.get('title', cid)}", "callback_data": f"join_del_{i}"}])
            kb_rows.append([{"text": "🔙 بازگشت", "callback_data": "back_to_owner"}])
            send_message(user_id, "🗑️ **کدوم؟**", {"inline_keyboard": kb_rows})
            answer_callback(callback_id); return
        if data.startswith("join_del_"):
            idx = int(data.replace("join_del_", ""))
            chs = db.get("join_channels", {})
            keys = list(chs.keys())
            if 0 <= idx < len(keys):
                del db["join_channels"][keys[idx]]; save_db_async()
                answer_callback(callback_id, "✅ حذف شد!", show_alert=True)
                send_message(user_id, "👑 **پنل مالک:**", owner_keyboard())
            return

        if data.startswith("seen_"):
            oid = data.replace("seen_", "")
            if oid not in db["orders"]:
                answer_callback(callback_id, "❌ نیست!"); return
            order = db["orders"][oid]
            if order["status"] != "active":
                answer_callback(callback_id, "✅ تکمیل شده!"); return
            if str(user_id) in db["seen_records"].get(oid, []):
                answer_callback(callback_id, "⚠️ قبلاً دیدم!"); return
            db["seen_records"][oid].append(str(user_id))
            order["seen_count"] += 1
            reward = get_setting('seen_reward', 1)
            add_coins(user_id, reward)
            ns = order["seen_count"]; count = order["count"]; onum = order.get("order_number", "?")
            answer_callback(callback_id, f"👁️ +{reward} سکه! 💰 {get_coins(user_id):,}")
            if order.get("reply_message_id"):
                kb = {"inline_keyboard": [[{"text": "👁️ دیدم", "callback_data": f"seen_{oid}"}, {"text": "🤖 ربات", "url": BOT_LINK}], [{"text": "🚨 گزارش", "callback_data": f"report_{oid}"}]]}
                try: edit_message_text(CHANNEL_ID, order["reply_message_id"], f"📋 **سفارش سین**\n\n👤 درخواستی: {count}\n👁️ خورده: {ns}\n#{onum}", kb)
                except: pass
            if ns >= count:
                order["status"] = "completed"
                db["stats"]["completed_orders"] += 1
                try:
                    delete_message(CHANNEL_ID, order["message_id"])
                    db["stats"]["deleted_messages"] += 1
                except: pass
                try:
                    if order.get("reply_message_id"): delete_message(CHANNEL_ID, order["reply_message_id"])
                except: pass
                try:
                    send_message(int(order["user_id"]),
                        f"🎉 **تبریک داداش!**\n\n"
                        f"🔢 **{count}** سین درخواستی تو کامل خورد!\n"
                        f"📩 پیام از کانال حذف شد.\n\n"
                        f"💡 حالا می‌تونی:\n"
                        f"• 🪙 بری کسب سکه کنی\n"
                        f"• 👁️ سفارش جدید ثبت کنی\n"
                        f"• 🚀 اگه سکه داری، همین الان ثبت کن!",
                        main_keyboard(order["user_id"]))
                except: pass
            save_db_async(); return

        if data.startswith("report_"):
            oid = data.replace("report_", "")
            if oid not in db["orders"]:
                answer_callback(callback_id, "❌ نیست!", show_alert=True); return
            order = db["orders"][oid]
            rn = callback["from"].get("username", "نامشخص")
            answer_callback(callback_id, "🚨 ثبت شد!", show_alert=True)
            try: send_message(int(OWNER_ID), f"🚨 **گزارش سین**\n\n👤 @{rn}\n📝 #{order.get('order_number', '?')}\n🔢 {order['count']}\n👁️ {order['seen_count']}")
            except: pass
            return

        if data.startswith("info_"):
            mid = data.replace("info_", "")
            o = db["member_orders"].get(mid, {})
            reward = o.get("reward", 3); otype = o.get("order_type", "normal")
            if otype == "guaranteed":
                answer_callback(callback_id, f"🪙 {reward} سکه! باید {get_setting('guaranteed_hours', 48)} ساعت بمونی!", show_alert=True)
            else:
                answer_callback(callback_id, f"🪙 {reward} سکه!", show_alert=True)
            return

        if data.startswith("mjoin_"):
            mid = data.replace("mjoin_", "")
            if mid not in db["member_orders"]:
                answer_callback(callback_id, "❌ نیست!", show_alert=True); return
            order = db["member_orders"][mid]
            if order["status"] != "active":
                answer_callback(callback_id, "✅ تکمیل شده!", show_alert=True); return
            if str(user_id) in db["member_records"].get(mid, []):
                answer_callback(callback_id, "⚠️ قبلاً عضو شدی!", show_alert=True); return
            if order.get("user_id") == str(user_id):
                answer_callback(callback_id, "❌ توی سفارش خودت نشو!", show_alert=True); return

            if order.get("order_type") == "guaranteed":
                tcid = str(order["chat_id"])
                user = get_user(user_id)
                times = user.get("last_guaranteed_times", {})
                last = times.get(tcid)
                if last:
                    try:
                        lt = datetime.fromisoformat(last)
                        cooldown = get_setting("guaranteed_cooldown", 300)
                        diff = (datetime.now() - lt).total_seconds()
                        if diff < cooldown:
                            rem = int(cooldown - diff)
                            m = rem // 60; s = rem % 60
                            answer_callback(callback_id, f"⏰ صبر! {m}m {s}s", show_alert=True)
                            return
                    except: pass

            tcid = order["chat_id"]
            ms = get_chat_member(tcid, user_id)
            if ms.get("ok") and ms["result"]["status"] in ["member", "administrator", "creator"]:
                db["member_records"][mid].append(str(user_id))
                order["seen_count"] += 1
                reward = order.get("reward", 3)
                add_coins(user_id, reward)
                user = get_user(user_id)
                if order.get("order_type") == "guaranteed":
                    if "last_guaranteed_times" not in user:
                        user["last_guaranteed_times"] = {}
                    user["last_guaranteed_times"][str(tcid)] = str(datetime.now())
                    hours = get_setting("guaranteed_hours", 48)
                    deadline = datetime.now() + timedelta(hours=hours)
                    user.setdefault("guaranteed_members", {})[mid] = {"joined_at": str(datetime.now()), "deadline": str(deadline)}
                ns = order["seen_count"]; count = order["count"]; mnum = order.get("order_number", "?")
                answer_callback(callback_id, f"✅ +{reward} سکه!", show_alert=True)
                if order.get("message_id"):
                    tname = "معمولی" if order.get("order_type") == "normal" else "تضمینی"
                    kb = {"inline_keyboard": [[{"text": f"🪙 {reward} سکه!", "callback_data": f"info_{mid}"}], [{"text": "🔗 عضویت", "url": order["link"]}, {"text": "✅ عضو شدم", "callback_data": f"mjoin_{mid}"}], [{"text": "🚨 گزارش", "callback_data": f"mreport_{mid}"}]]}
                    try: edit_message_text(CHANNEL_ID, order["message_id"], f"📋 **سفارش عضو - {tname}**\n\n🔗 {order['link']}\n👥 درخواستی: {count}\n✅ عضو شده: {ns}\n#{mnum}", kb)
                    except: pass
                if ns >= count:
                    order["status"] = "completed"
                    db["stats"]["completed_members"] = db["stats"].get("completed_members", 0) + 1
                    try: delete_message(CHANNEL_ID, order["message_id"])
                    except: pass
                    try:
                        send_message(int(order["user_id"]),
                            f"🎉 **تبریک!**\n\n👥 **{count}** عضو کامل شد!\n📩 پیام از کانال حذف شد.",
                            main_keyboard(order["user_id"]))
                    except: pass
            else:
                answer_callback(callback_id, "❌ هنوز عضو نشدی! اول عضو شو.", show_alert=True)
            save_db_async(); return

        if data.startswith("mreport_"):
            mid = data.replace("mreport_", "")
            if mid not in db["member_orders"]:
                answer_callback(callback_id, "❌ نیست!", show_alert=True); return
            order = db["member_orders"][mid]
            rn = callback["from"].get("username", "نامشخص")
            answer_callback(callback_id, "🚨 ثبت شد!", show_alert=True)
            try: send_message(int(OWNER_ID), f"🚨 **گزارش عضو**\n\n👤 @{rn}\n📝 #{order.get('order_number', '?')}\n🔗 {order['link']}")
            except: pass
            return

        if data.startswith("poll_vote_"):
            parts = data.replace("poll_vote_", "").split("_")
            if len(parts) < 2: answer_callback(callback_id, "❌ خطا!", show_alert=True); return
            poll_id = parts[0]
            try: opt_index = int(parts[1])
            except: answer_callback(callback_id, "❌ خطا!", show_alert=True); return

            if poll_id not in db.get("polls", {}):
                answer_callback(callback_id, "❌ نیست!", show_alert=True); return
            poll = db["polls"][poll_id]
            options = poll.get("options", [])
            if opt_index >= len(options):
                answer_callback(callback_id, "❌ گزینه نیست!", show_alert=True); return

            selected_option = options[opt_index]
            votes = poll.get("votes", {})

            already_voted = False
            for opt, voters in votes.items():
                if str(user_id) in voters:
                    if opt == selected_option:
                        votes[opt].remove(str(user_id))
                        already_voted = True
                        answer_callback(callback_id, "🗑️ رای برداشته شد!", show_alert=True)
                        break
                    else:
                        votes[opt].remove(str(user_id))
                        votes[selected_option].append(str(user_id))
                        already_voted = True
                        answer_callback(callback_id, f"✅ رای تغییر یافت: {selected_option}", show_alert=True)
                        break

            if not already_voted:
                if selected_option not in votes: votes[selected_option] = []
                votes[selected_option].append(str(user_id))
                answer_callback(callback_id, f"✅ رای ثبت شد: {selected_option}", show_alert=True)

            total_votes = sum(len(v) for v in votes.values())
            results = []
            for opt in options:
                count = len(votes.get(opt, []))
                percent = (count / total_votes * 100) if total_votes > 0 else 0
                results.append({"opt": opt, "count": count, "percent": percent})
            results.sort(key=lambda x: x["count"], reverse=True)

            medals = ["🥇", "🥈", "🥉"]
            new_text = f"📊 **نظرسنجی**\n\n❓ {poll['question']}\n\n━━━━━━━━━━━━━━━━\n"
            for i, r in enumerate(results):
                medal = medals[i] if i < 3 and r["count"] > 0 else "❌"
                new_text += f"{medal} {r['opt']} — {r['percent']:.0f}٪ ({r['count']} رای)\n"
            new_text += f"━━━━━━━━━━━━━━━━\n\n👥 کل: {total_votes}\n\n🔘 **رای بده:**"

            kb_rows = []
            for i, opt in enumerate(options):
                kb_rows.append([{"text": opt, "callback_data": f"poll_vote_{poll_id}_{i}"}])
            kb = {"inline_keyboard": kb_rows}

            if poll.get("message_id"):
                try: edit_message_text(CHANNEL_ID, poll["message_id"], new_text, kb)
                except: pass
            save_db_async()
            return

        if data.startswith("ticket_reject_"):
            tid = data.replace("ticket_reject_", "")
            if tid in db.get("support_tickets", {}):
                db["support_tickets"][tid]["status"] = "rejected"; save_db_async()
            answer_callback(callback_id, "❌ رد شد!", show_alert=True); return
        if data.startswith("ticket_reply_"):
            tid = data.replace("ticket_reply_", "")
            if tid not in db.get("support_tickets", {}):
                answer_callback(callback_id, "❌ نیست!", show_alert=True); return
            db["pending_support_reply"][user_id] = {"step": "waiting_reply", "ticket_id": tid}; save_db_async()
            answer_callback(callback_id, "📝 جوابت رو بفرست", show_alert=True)
            send_message(user_id, "📝 **پاسخ را وارد کنید:**", cancel_keyboard()); return
        if data.startswith("ticket_next_"):
            open_tickets = [(k, v) for k, v in db.get("support_tickets", {}).items() if v.get("status") == "open"]
            if not open_tickets:
                answer_callback(callback_id, "✅ تیکت باز نیست!", show_alert=True); return
            k, v = open_tickets[0]
            kb = {"inline_keyboard": [
                [{"text": "❌ رد", "callback_data": f"ticket_reject_{k}"}],
                [{"text": "📝 جواب", "callback_data": f"ticket_reply_{k}"}],
                [{"text": "⏳ بعدی", "callback_data": f"ticket_next_{k}"}]
            ]}
            answer_callback(callback_id)
            send_message(user_id, f"💬 **پشتیبانی** #{k}\n\n👤 {v.get('name', '?')}\n🆔 {v['user_id']}\n\n📝 {v['text']}", kb)
            return

        answer_callback(callback_id)

    except Exception as e:
        print(f"⚠️ خطا callback: {e}")

last_update_id = 0

def main():
    global last_update_id, INVITE_REWARD
    INVITE_REWARD = db.get("invite_reward", INVITE_REWARD)
    print("⚡ هایپرسین بله - نسخه فوق سریع!")
    print(f"🤖 @{BOT_USERNAME}")
    print(f"💓 Cache | ThreadPool(800)")
    print("-" * 40)
    while True:
        try:
            updates = api_call("getUpdates", {"offset": last_update_id + 1, "limit": 100, "timeout": 3})
            if updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    last_update_id = update["update_id"]
                    msg = update.get("message", {})
                    if "message" in update:
                        executor.submit(handle_message, msg)
                    elif "callback_query" in update:
                        executor.submit(handle_callback, update["callback_query"])
            time.sleep(0.01)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"⚠️ خطا: {e}")
            time.sleep(0.3)

def keep_alive():
    while True:
        try:
            time.sleep(240)
            requests.get(f"{RENDER_URL}/ping", timeout=15)
            print(f"💓 پینگ | {datetime.now().strftime('%H:%M:%S')}")
        except: time.sleep(60)

app = Flask(__name__)

@app.route('/')
def home(): return "🤖 Hypersin Bale Bot!"

@app.route('/ping')
def ping(): return "pong ✅"

@app.route('/health')
def health():
    return jsonify({"status": "online", "users": len(db.get("users", {})), "cache": len(CACHE)})

if __name__ == "__main__":
    threading.Thread(target=save_worker, daemon=True).start()
    threading.Thread(target=cache_cleanup, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    threading.Thread(target=check_guaranteed_members, daemon=True).start()
    threading.Thread(target=check_admin_orders, daemon=True).start()
    threading.Thread(target=main, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)