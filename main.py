import requests, json, time, random, string, os, threading, gc
from datetime import datetime, timedelta
from flask import Flask, jsonify
from concurrent.futures import ThreadPoolExecutor

# ═══════════════════════════════════════
# 🔧 تنظیمات
# ═══════════════════════════════════════
TOKEN = "1224499710:Whyt_329-tLCDsbZMEq82FGdVMVsVcmK0rM"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

# 📢 کانال اصلی (سفارشات)
CHANNEL_ID = "@SCYVu"
CHANNEL_LINK = "https://ble.ir/SCYVu"

# 📢 کانال دوم (فقط جوین اجباری)
CHANNEL_2_ID = "@uvuvuf"
CHANNEL_2_LINK = "https://ble.ir/uvuvuf"

BOT_USERNAME = "Idnuedobot"
BOT_LINK = f"https://ble.ir/{BOT_USERNAME}"

OWNER_ID = "1530477937"
OWNER_PASSWORD = "Parsa@2026!"
COIN_PASSWORD = "Coin@Parsa2026"
INFINITE_COINS = 999999
MIN_SIN = 15
MIN_MEMBER = 1
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
RENDER_URL = "https://hypersin-bale.onrender.com"

# ⚡ کش فوق سریع
CACHE = {}
CACHE_TIME = {}
CACHE_TTL = 7200
JOIN_CACHE = {}
JOIN_CACHE_TIME = {}
SAVE_PENDING = False
SAVE_LOCK = threading.Lock()
executor = ThreadPoolExecutor(max_workers=2000)

def load_db():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key in ["guaranteed_times", "support_tickets", "join_channels", "group_targets", "bc_gifts", "coin_packets", "admin_warnings", "polls", "games", "active_games"]:
                    if key not in data:
                        data[key] = {}
                for key in ["custom_features"]:
                    if key not in data:
                        data[key] = []
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
        "pending_send_to_channel": {},
        "pending_poll": {},
        "pending_game": {},
        "coin_packets": {}, "bc_gifts": {},
        "banned": [], "admins": [], "vip": {},
        "join_channels": {},
        "games": {}, "game_counter": 0,
        "active_games": {},
        "support_tickets": {}, "ticket_counter": 0,
        "guaranteed_times": {},
        "group_targets": {},
        "custom_features": [],
        "admin_warnings": {},
        "polls": {},
        "poll_counter": 0,
        "settings": {
            "seen_reward": 1, "sin_cost": 1,
            "member_cost": 5,
            "member_normal_reward": 3,
            "member_guaranteed_reward": 7,
            "guaranteed_cost": 10,
            "transfer_fee": 2,
            "start_gift": 25,
            "daily_gift": 10,
            "invite_reward": 15,
            "wheel_cooldown": WHEEL_COOLDOWN,
            "guaranteed_hours": 48,
            "guaranteed_penalty": 7,
            "guaranteed_refund": 5,
            "guaranteed_cooldown": 300,
            "normal_member_penalty": 0,
            "normal_member_hours": 0,
            "normal_member_coin_penalty": 0
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

# ─── پایان بخش ۱ ───
# ═══════════════════════════════════════
# 💰 توابع با Cache فوق سریع
# ═══════════════════════════════════════
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

# ═══════════════════════════════════════
# 📡 API فوق سریع
# ═══════════════════════════════════════
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

# ═══════════════════════════════════════
# ✅ چک عضویت (دو کانال)
# ═══════════════════════════════════════
def check_joined(user_id):
    """چک عضویت در کانال اصلی"""
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
    """چک عضویت در هر چت"""
    try:
        r = get_chat_member(chat_id, user_id)
        if r.get("ok"):
            status = r["result"]["status"]
            return status in ["member", "administrator", "creator"]
        return False
    except:
        return False

def check_all_joins(user_id):
    """چک عضویت در کانال اصلی + کانال دوم + جوین‌های اضافی"""
    if not check_joined(user_id): return False
    if not check_chat_membership(CHANNEL_2_ID, user_id): return False
    for ch_id, ch_info in db.get("join_channels", {}).items():
        if not check_chat_membership(ch_id, user_id):
            return False
    return True

def must_join(user_id):
    """پیام جوین اجباری دو کانال"""
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

# ─── پایان بخش ۲ ───
# ═══════════════════════════════════════
# 🎮 کیبوردها
# ═══════════════════════════════════════
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
            [{"text": "⚙️ تنظیم سکه"}, {"text": "⚙️ تنظیم همه چیز"}],
            [{"text": "🚫 مسدود کردن"}, {"text": "✅ رفع مسدودیت"}],
            [{"text": "👑 افزودن ادمین"}, {"text": "🗑️ حذف ادمین"}],
            [{"text": "📨 پیام به کاربر"}, {"text": "💻 اجرای کد"}],
            [{"text": "💻 اجرای قابلیت"}, {"text": "👤 مشخصات کاربر"}],
            [{"text": "🎁 سکه پاکت"}, {"text": "🛡️ ضدتقلب"}],
            [{"text": "📊 آمار پیشرفته"}, {"text": "📊 آمار کل"}],
            [{"text": "🔒 جوین اجباری"}, {"text": "🎁 ساخت کد هدیه"}],
            [{"text": "💰 افزودن سکه به همه"}, {"text": "🎁 تغییر سکه دعوت"}],
            [{"text": "📢 ارسال به کانال"}, {"text": "📊 نظرسنجی"}],
            [{"text": "🎮 شروع بازی"}, {"text": "🛑 توقف بازی"}],
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

def all_settings_keyboard():
    return settings_keyboard()

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

# ═══════════════════════════════════════
# 🎡 گردونه شانس
# ═══════════════════════════════════════
def spin_wheel():
    total = sum(p["weight"] for p in WHEEL_PRIZES)
    r = random.randint(1, total)
    cum = 0
    for p in WHEEL_PRIZES:
        cum += p["weight"]
        if r <= cum:
            return p
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

# ─── پایان بخش ۳ ───
# ═══════════════════════════════════════
# 📢 پیام همگانی
# ═══════════════════════════════════════
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
            if keyboard_json:
                r = send_message(int(uid), text, keyboard_json)
            else:
                r = send_message(int(uid), text)
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

# ═══════════════════════════════════════
# 🛡️ چک تضمینی
# ═══════════════════════════════════════
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
                                    f"⚠️ **داداش جان، تو کانال رو ترک کردی!**\n\n"
                                    f"🔗 کانال: {order['link']}\n"
                                    f"🛡️ نوع عضویت: **تضمینی**\n"
                                    f"⏰ مدت لازم: **{hours} ساعت** موندن\n\n"
                                    f"❌ چون قبل از {hours} ساعت رفتی:\n"
                                    f"💸 **{actual} سکه** ازت کم شد\n"
                                    f"💰 موجودی جدیدت: **{get_coins(uid):,}** سکه")
                            except: pass
                            try:
                                uname = user.get("username", "") or uid
                                send_message(int(owner),
                                    f"🔔 **داداش جان، یه کاربر کانالت رو ترک کرد!**\n\n"
                                    f"👤 کاربر: {uname}\n"
                                    f"🔗 کانال: {order['link']}\n\n"
                                    f"🎁 **{refund} سکه** بهت برگشت داده شد!\n"
                                    f"💰 موجودی جدید: **{get_coins(owner):,}** سکه")
                            except: pass
                    else:
                        del user["guaranteed_members"][mid]
                        save_db_async()
        except Exception as e:
            print(f"⚠️ خطا guaranteed: {e}")

# ═══════════════════════════════════════
# 🛡️ چک ادمین سفارش‌ها (هر ۲ ثانیه - فقط اخطار، بدون بن!)
# ═══════════════════════════════════════
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
                    
                    # 📊 افزایش اخطار
                    if owner not in db.get("admin_warnings", {}):
                        db["admin_warnings"][owner] = {"count": 0, "dates": []}
                    db["admin_warnings"][owner]["count"] += 1
                    db["admin_warnings"][owner]["dates"].append(str(datetime.now()))
                    warn_count = db["admin_warnings"][owner]["count"]
                    
                    if mid in db.get("member_records", {}):
                        db["member_records"][mid].clear()
                    save_db_async()
                    
                    # 📩 گزارش به مالک
                    try:
                        send_message(int(OWNER_ID),
                            f"⚠️ **گزارش تخلف**\n\n"
                            f"👤 کاربر: `{owner}`\n"
                            f"📝 سفارش: #{order.get('order_number', '?')}\n"
                            f"🔗 کانال: {order['link']}\n"
                            f"💰 سکه برگشتی: {refund:,}\n"
                            f"⚠️ اخطار: {warn_count}\n"
                            f"📅 تاریخ: {get_shamsi_date()}")
                    except: pass
                    
                    # ⚠️ پیام به کاربر (فقط اخطار، بدون بن!)
                    try:
                        send_message(int(owner),
                            f"⚠️ **اخطار {warn_count}**\n\n"
                            f"کاربر عزیز، شما ربات رو از ادمینی درآوردید! ❌\n\n"
                            f"🗑️ سفارشتون باطل شد\n"
                            f"💰 **{refund:,} سکه** بهتون برگشت داده شد\n\n"
                            f"⚠️ **اخطار: {warn_count}**\n"
                            f"🛡️ لطفاً دفعه بعد ربات رو ادمین نگه دارید.")
                    except: pass
                    
                    if order.get("message_id"):
                        try: delete_message(CHANNEL_ID, order["message_id"])
                        except: pass
        except Exception as e:
            print(f"⚠️ خطا check_admin: {e}")

# ─── پایان بخش ۴ ───
# ═══════════════════════════════════════
# 🎯 پردازش پیام
# ═══════════════════════════════════════
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
                wt = (f"👋 **{nn}** به **{gn}** خوش اومدی! 🎉\n\n"
                      f"🤖 من **ربات عضوگیر و سین‌زن** هستم!\n\n"
                      f"🚀 @Idnuedobot\n\n"
                      f"🐺 تیم DeepParse")
                send_message(chat_id, wt)
            if "group_targets" not in db:
                db["group_targets"] = {}
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
            send_message(chat_id, "🚫 **شما مسدود شدید!**\n\n❌ دسترسی شما به ربات قطع شده است.")
            return
        
        username = message["from"].get("username", "")
        if username:
            get_user(user_id)["username"] = username
            save_db_async()
        
        get_user(user_id)["msg_count"] = get_user(user_id).get("msg_count", 0) + 1
        
        # ═══ ۱. بازگشت ═══
        if text in ["❌ لغو", "🔙 بازگشت"]:
            for key in ["pending_orders", "pending_members", "pending_gift", "pending_transfer", "pending_packet", "pending_coin_setting", "pending_ban", "pending_unban", "pending_admin", "pending_remove_admin", "pending_vip", "pending_pm", "pending_execute", "pending_utility", "pending_join_channel", "pending_remove_join", "pending_support", "pending_broadcast_format", "pending_user_info", "pending_all_settings", "pending_feature", "pending_support_reply", "pending_broadcast_groups", "pending_forward_all", "pending_send_to_channel", "pending_poll", "pending_game"]:
                db.get(key, {}).pop(user_id, None)
            save_db_async()
            send_message(chat_id, "🔙 **برگشتی به منوی اصلی!**", main_keyboard(user_id))
            return
        
        # ═══ ۲. پشتیبانی ═══
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
                    f"💬 **پیام پشتیبانی** #{tid}\n\n"
                    f"👤 از: {name}\n"
                    f"🆔 آیدی: {user_id}\n\n"
                    f"📝 پیام:\n{text}", kb)
                send_message(chat_id, "✅ پیامت برای پشتیبانی ارسال شد!", main_keyboard(user_id))
            except:
                send_message(chat_id, "❌ خطا در ارسال!", main_keyboard(user_id))
            db["pending_support"].pop(user_id, None)
            save_db_async()
            return
        
        # ═══ ۳. /start ═══
        if text.startswith("/start"):
            parts = text.split(" ")
            if len(parts) > 1:
                inviter_id = parts[1]
                if inviter_id != user_id:
                    u = get_user(user_id)
                    if not u.get("invited_by"):
                        u["invited_by"] = inviter_id
                        save_db_async()
                        
                        # 🎮 چک کن آیا بازی فعاله و دعوت‌کننده تو بازیه
                        for gid, game in db.get("active_games", {}).items():
                            if game.get("status") == "active":
                                if inviter_id in game.get("players", {}):
                                    # افزایش تعداد دعوت
                                    game["players"][inviter_id]["invites"] = game["players"][inviter_id].get("invites", 0) + 1
                                    invites_count = game["players"][inviter_id]["invites"]
                                    needed = game.get("needed", 10)
                                    reward = game.get("reward", 500)
                                    
                                    # پیام به دعوت‌کننده
                                    try:
                                        send_message(int(inviter_id),
                                            f"🎉 **یه دعوت جدید!**\n\n"
                                            f"👥 تعداد دعوت: {invites_count}/{needed}\n\n"
                                            f"🏆 {needed - invites_count} دعوت دیگه مونده تا برنده شی!")
                                    except: pass
                                    
                                    # 🏆 چک برنده شدن
                                    if invites_count >= needed:
                                        # اولین نفر برنده
                                        game["status"] = "finished"
                                        game["winner"] = inviter_id
                                        add_coins(inviter_id, reward)
                                        save_db_async()
                                        
                                        # پیام به کانال
                                        try:
                                            send_message(CHANNEL_ID,
                                                f"🏆🏆🏆 **برنده اعلام شد!** 🏆🏆🏆\n\n"
                                                f"🥇 **@{u.get('username') or inviter_id}** با {invites_count} دعوت برنده شد!\n\n"
                                                f"💰 جایزه: **{reward} سکه**\n"
                                                f"✅ به حسابش واریز شد\n\n"
                                                f"━━━━━━━━━━━━━━━━\n"
                                                f"🎮 بازی تموم شد!")
                                        except: pass
                                        
                                        # پیام به برنده
                                        try:
                                            send_message(int(inviter_id),
                                                f"🎉🎉🎉 **تبریک!** 🎉🎉🎉\n\n"
                                                f"🥇 **تو برنده شدی!**\n\n"
                                                f"👥 کل دعوت: {invites_count}\n"
                                                f"💰 جایزه: **{reward} سکه**\n\n"
                                                f"💰 سکه به حسابت واریز شد!")
                                        except: pass
                                    
                                    # آپدیت پیام کانال
                                    try:
                                        players = game.get("players", {})
                                        sorted_players = sorted(players.items(), key=lambda x: x[1].get("invites", 0), reverse=True)
                                        msg = f"🎮 **بازی در جریان**\n\n"
                                        msg += f"🎯 {game.get('name', 'مسابقه')}\n"
                                        msg += f"👥 ظرفیت: {len(players)}/{game.get('capacity', 30)}\n"
                                        msg += f"👥 هر نفر: {needed} دعوت\n"
                                        msg += f"🪙 جایزه: {reward} سکه\n\n"
                                        msg += "━━━━━━━━━━━━━━━━\n"
                                        msg += "📝 **ثبت‌نام شده‌ها:**\n\n"
                                        for i, (pid, pdata) in enumerate(sorted_players, 1):
                                            pname = pdata.get("username") or pdata.get("name", "کاربر")
                                            pinv = pdata.get("invites", 0)
                                            msg += f"{i}. @{pname} — {pinv}\n"
                                        msg += "━━━━━━━━━━━━━━━━"
                                        if game.get("message_id"):
                                            try:
                                                edit_message_text(CHANNEL_ID, game["message_id"], msg)
                                            except: pass
                                    except: pass
                                
                                elif inviter_id not in game.get("players", {}):
                                    # کاربر تو بازی نیست
                                    pass
                                break
                        
                        try:
                            send_message(int(inviter_id),
                                f"🔔 **یه کاربر با لینک دعوت تو اومد!**\n\n"
                                f"👤 کاربر: {name}\n"
                                f"⏰ منتظر عضویت در کانال‌ها...")
                        except: pass
            
            if not check_all_joins(user_id):
                must_join(user_id)
                return
            
            user = get_user(user_id)
            if not user.get("got_start_gift"):
                add_coins(user_id, get_setting("start_gift", START_GIFT))
                user["got_start_gift"] = True
                save_db_async()
                send_message(chat_id, f"👋 **سلام {name} جان!** 😎\n\n⚡ به هایپرسین خوش اومدی!\n🎁 **{get_setting('start_gift', START_GIFT)} سکه هدیه** بهت اضافه شد!\n💰 موجودی: {get_coins(user_id):,} سکه", main_keyboard(user_id))
            else:
                send_message(chat_id, f"👋 **سلام {name} جان!** 😎", main_keyboard(user_id))
            return
        
        # ═══ ۴. چک عضویت ═══
        main_buttons = ["🪙 کسب سکه", "👁️ ثبت سفارش سین", "👥 ثبت سفارش عضو", "💰 سکه‌های من", "🎁 زدن کد هدیه", "👥 دعوت دوستان", "👤 حساب کاربری", "🎁 هدیه روزانه", "🎡 گردونه شانس", "💬 پشتیبانی", "📖 راهنما"]
        if text in main_buttons:
            if not check_all_joins(user_id):
                must_join(user_id)
                return
        
        # ═══ ۵. pending ═══
        pending = db["pending_orders"].get(user_id, {})
        pmem = db["pending_members"].get(user_id, {})
        pt = db["pending_transfer"].get(user_id, {})
        
        # سین‌زن - فوروارد
        if pending.get("step") == "waiting_forward":
            if "forward_from_chat" in message and message["forward_from_chat"]["type"] == "channel":
                db["pending_orders"][user_id] = {"step": "waiting_count", "message_id": message["message_id"]}
                save_db_async()
                send_message(chat_id, f"🔢 **چند سین نیاز داری داداش؟**\n\n💰 هر سین = {get_setting('sin_cost', 1)} سکه\n💳 موجودی: {get_coins(user_id):,} سکه\n\n⚠️ حداقل: {MIN_SIN} سین", cancel_keyboard())
            else:
                send_message(chat_id, "❌ **این پیام از کانال نیست!**", cancel_keyboard())
            return
        
        # سین‌زن - تعداد
        if pending.get("step") == "waiting_count":
            try:
                count = int(convert_number(text))
                if count < MIN_SIN:
                    send_message(chat_id, f"❌ حداقل باید {MIN_SIN} سین ثبت کنی!", cancel_keyboard()); return
                coins = get_coins(user_id)
                total_cost = count * get_setting('sin_cost', 1)
                if coins < total_cost:
                    send_message(chat_id, f"❌ سکه کافی نداری!\n💰 موجودی: {coins:,} | 💰 نیاز: {total_cost:,}", cancel_keyboard())
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
                    send_message(chat_id, f"✅ **سفارش ثبت شد!** 🎉\n\n🔢 تعداد: {count}\n💰 هزینه: {total_cost} سکه\n💳 موجودی جدید: {get_coins(user_id):,} سکه\n📝 #{onum}", main_keyboard(user_id))
                else:
                    add_coins(user_id, total_cost)
                    send_message(chat_id, "❌ **خطا!**", main_keyboard(user_id))
                    del db["pending_orders"][user_id]; save_db_async()
            except: send_message(chat_id, "❌ **عدد معتبر وارد کن!**", cancel_keyboard())
            return
        
        # کد هدیه
        if pending.get("step") == "waiting_gift_code":
            code = text.upper().strip()
            if code in db["gift_codes"]:
                g = db["gift_codes"][code]; u = get_user(user_id)
                if code in u.get("used_gift_codes", []):
                    send_message(chat_id, "❌ قبلاً زدی!", main_keyboard(user_id))
                elif len(g["used_by"]) >= g["capacity"]:
                    send_message(chat_id, "❌ تموم شده!", main_keyboard(user_id))
                else:
                    add_coins(user_id, g["coins"])
                    g["used_by"].append(user_id)
                    u.setdefault("used_gift_codes", []).append(code); save_db_async()
                    send_message(chat_id, f"🎉 **{g['coins']:,} سکه!**\n💳 موجودی: {get_coins(user_id):,}", main_keyboard(user_id))
            else: send_message(chat_id, "❌ کد نامعتبر!", main_keyboard(user_id))
            del db["pending_orders"][user_id]; save_db_async()
            return
        
        # انتقال سکه (فقط مالک)
        if pt.get("step") == "waiting_id" and user_id == str(OWNER_ID):
            target = text.strip()
            if target in db["users"] and target != user_id:
                fee = get_setting('transfer_fee', 2)
                db["pending_transfer"][user_id] = {"step": "waiting_amount", "target": target}
                save_db_async()
                send_message(chat_id, f"💰 **چند سکه به {target}؟**\n\n💳 موجودی تو: {get_coins(user_id):,}\n💸 کارمزد: {fee}", cancel_keyboard())
            else:
                send_message(chat_id, "❌ کاربر پیدا نشد!", main_keyboard(user_id))
                db["pending_transfer"].pop(user_id, None); save_db_async()
            return
        if pt.get("step") == "waiting_amount" and user_id == str(OWNER_ID):
            try:
                amount = int(convert_number(text))
                target = pt["target"]
                fee = get_setting('transfer_fee', 2)
                total = amount + fee
                if amount <= 0:
                    send_message(chat_id, "❌ عدد بزرگتر از صفر!", main_keyboard(user_id))
                elif remove_coins(user_id, total):
                    add_coins(target, amount)
                    add_coins(OWNER_ID, fee)
                    save_db_async()
                    send_message(chat_id, f"✅ **{amount} سکه به {target} انتقال دادی!**\n💸 کارمزد: {fee}", main_keyboard(user_id))
                    try:
                        send_message(int(target), f"🎉 **تبریک!**\n\n👤 {name} برات {amount} سکه انتقال داد!\n💰 موجودی: {get_coins(target):,}")
                    except: pass
                else:
                    send_message(chat_id, f"❌ سکه کافی نداری!", main_keyboard(user_id))
            except:
                send_message(chat_id, "❌ عدد معتبر!", main_keyboard(user_id))
            db["pending_transfer"].pop(user_id, None); save_db_async()
            return
        
        # عضوگیر - لینک (فقط کانال)
        if pmem.get("step") == "waiting_link":
            link = text.strip()
            if "ble.ir/" in link:
                cu = "@" + link.split("ble.ir/")[-1]
            elif link.startswith("@"):
                cu = link
            else:
                send_message(chat_id, "❌ **لینک نامعتبر!**", cancel_keyboard())
                return
            
            ci = get_chat(cu)
            if ci.get("ok"):
                chat_type_2 = ci["result"].get("type", "")
                if chat_type_2 in ["group", "supergroup"]:
                    send_message(chat_id, "❌ **گروه قبول نمیشه!**\n\n📩 لطفاً **لینک کانال** بفرست.", cancel_keyboard())
                    return
                if chat_type_2 != "channel":
                    send_message(chat_id, "❌ **فقط کانال!**", cancel_keyboard())
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
                            send_message(chat_id, "📥 **نوع عضویت:**\n\n"
                                f"━━━━━━━━━━━━━━━━\n"
                                f"🥉 **۱. معمولی** — {get_setting('member_cost', 5)} سکه\n"
                                f"━━━━━━━━━━━━━━━━\n"
                                f"🥇 **۲. تضمینی** — {get_setting('guaranteed_cost', 10)} سکه\n"
                                f"🛡️ کاربر {get_setting('guaranteed_hours', 48)} ساعت بمونه\n"
                                f"━━━━━━━━━━━━━━━━\n\n"
                                f"🔢 عدد ۱ یا ۲:", cancel_keyboard())
                        else: send_message(chat_id, "❌ **هنوز ادمین نشدم!**", cancel_keyboard())
                    else: send_message(chat_id, "❌ **لینک نامعتبره!**", cancel_keyboard())
                except: send_message(chat_id, "❌ **خطا!**", cancel_keyboard())
            else: send_message(chat_id, "⚠️ بنویس: **ادمین کردم**", cancel_keyboard())
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
                send_message(chat_id, f"📥 **ثبت سفارش عضو - {tname}**\n\n👥 تعداد:\n💰 هر عضو: {cost_per} سکه\n📌 حداقل: {MIN_MEMBER}\n\n⌨️ فقط عدد:", cancel_keyboard())
            else: send_message(chat_id, "❌ فقط ۱ یا ۲!", cancel_keyboard())
            return
        
        # عضوگیر - تعداد
        if pmem.get("step") == "waiting_count":
            try:
                count = int(convert_number(text))
                if count < MIN_MEMBER:
                    send_message(chat_id, f"❌ حداقل {MIN_MEMBER} عضو!", cancel_keyboard()); return
                link = pmem["link"]; tcid = pmem["chat_id"]; otype = pmem.get("order_type", "normal")
                cost_per = get_setting('member_cost', 5) if otype == "normal" else get_setting('guaranteed_cost', 10)
                total_cost = count * cost_per
                coins = get_coins(user_id)
                if coins < total_cost:
                    send_message(chat_id, f"❌ سکه کافی نداری!\n💰 موجودی: {coins:,} | 💰 نیاز: {total_cost:,}", cancel_keyboard())
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
                sent = send_message(CHANNEL_ID, f"📋 **سفارش عضو - {tname}**\n\n🔗 {link}\n👥 درخواستی: {count}\n✅ عضو شده: 0\n#{mnum}\n\n🪙 **{reward} سکه میگیری!**", kb)
                if sent.get("ok"): db["member_orders"][mid]["message_id"] = sent["result"]["message_id"]
                del db["pending_members"][user_id]; save_db_async()
                send_message(chat_id, f"🎉 **سفارش ثبت شد!**\n💰 موجودی جدید: {get_coins(user_id):,} سکه", main_keyboard(user_id))
            except: send_message(chat_id, "❌ عدد معتبر!", cancel_keyboard())
            return
        
        # ═══ ۶. پنل مالک ═══
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
        
        if text == "⚙️ تنظیم سکه" and is_admin(user_id):
            send_message(chat_id, "⚙️ **تنظیم سکه**:", settings_keyboard())
            return
        if text == "⚙️ تنظیم همه چیز" and is_admin(user_id):
            send_message(chat_id, "⚙️ **تنظیم همه چیز**:", all_settings_keyboard())
            return
        if text == "👁️ سکه دیدم" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "seen_reward"}; save_db_async()
            send_message(chat_id, f"👁️ فعلی: {get_setting('seen_reward', 1)}\n\nجدید:", settings_keyboard()); return
        if text == "📝 سکه سفارش سین" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "sin_cost"}; save_db_async()
            send_message(chat_id, f"📝 فعلی: {get_setting('sin_cost', 1)}\n\nجدید:", settings_keyboard()); return
        if text == "👥 سکه سفارش عضو" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "member_cost"}; save_db_async()
            send_message(chat_id, f"👥 فعلی: {get_setting('member_cost', 5)}\n\nجدید:", settings_keyboard()); return
        if text == "🪙 سکه عضو معمولی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "member_normal_reward"}; save_db_async()
            send_message(chat_id, f"🪙 فعلی: {get_setting('member_normal_reward', 3)}\n\nجدید:", settings_keyboard()); return
        if text == "🛡️ سکه عضو تضمینی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "member_guaranteed_reward"}; save_db_async()
            send_message(chat_id, f"🛡️ فعلی: {get_setting('member_guaranteed_reward', 7)}\n\nجدید:", settings_keyboard()); return
        if text == "💸 کارمزد انتقال" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "transfer_fee"}; save_db_async()
            send_message(chat_id, f"💸 فعلی: {get_setting('transfer_fee', 2)}\n\nجدید:", settings_keyboard()); return
        if text == "🎁 هدیه شروع" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "start_gift"}; save_db_async()
            send_message(chat_id, f"🎁 فعلی: {get_setting('start_gift', 25)}\n\nجدید:", settings_keyboard()); return
        if text == "📅 هدیه روزانه" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "daily_gift"}; save_db_async()
            send_message(chat_id, f"📅 فعلی: {get_setting('daily_gift', 10)}\n\nجدید:", settings_keyboard()); return
        if text == "👥 سکه دعوت" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "invite_reward"}; save_db_async()
            send_message(chat_id, f"👥 فعلی: {get_setting('invite_reward', 15)}\n\nجدید:", settings_keyboard()); return
        if text == "🎡 زمان گردونه" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "wheel_cooldown"}; save_db_async()
            send_message(chat_id, f"🎡 فعلی: {get_setting('wheel_cooldown', 43200)}\n\nجدید:", settings_keyboard()); return
        if text == "⏰ مدت تضمینی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "guaranteed_hours"}; save_db_async()
            send_message(chat_id, f"⏰ فعلی: {get_setting('guaranteed_hours', 48)}\n\nجدید:", settings_keyboard()); return
        if text == "💸 جریمه تضمینی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "guaranteed_penalty"}; save_db_async()
            send_message(chat_id, f"💸 فعلی: {get_setting('guaranteed_penalty', 7)}\n\nجدید:", settings_keyboard()); return
        if text == "↩️ برگشت تضمینی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "guaranteed_refund"}; save_db_async()
            send_message(chat_id, f"↩️ فعلی: {get_setting('guaranteed_refund', 5)}\n\nجدید:", settings_keyboard()); return
        if text == "⏳ کول‌داون تضمینی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "guaranteed_cooldown"}; save_db_async()
            send_message(chat_id, f"⏳ فعلی: {get_setting('guaranteed_cooldown', 300)}\n\nجدید:", settings_keyboard()); return
        if text == "👥 هزینه عضو تضمینی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "guaranteed_cost"}; save_db_async()
            send_message(chat_id, f"👥 فعلی: {get_setting('guaranteed_cost', 10)}\n\nجدید:", settings_keyboard()); return
        if text == "⚠️ جریمه عضو معمولی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "normal_member_penalty"}; save_db_async()
            send_message(chat_id, f"⚠️ فعلی: {get_setting('normal_member_penalty', 0)}\n\nجدید:", settings_keyboard()); return
        if text == "⏰ مدت عضو معمولی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "normal_member_hours"}; save_db_async()
            send_message(chat_id, f"⏰ فعلی: {get_setting('normal_member_hours', 0)}\n\nجدید:", settings_keyboard()); return
        if text == "🪙 سکه جریمه معمولی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "normal_member_coin_penalty"}; save_db_async()
            send_message(chat_id, f"🪙 فعلی: {get_setting('normal_member_coin_penalty', 0)}\n\nجدید:", settings_keyboard()); return
        
        pcs = db["pending_coin_setting"].get(user_id, {})
        if pcs.get("type"):
            try:
                val = int(convert_number(text))
                db["settings"][pcs["type"]] = val
                del db["pending_coin_setting"][user_id]; save_db_async()
                send_message(chat_id, f"✅ ذخیره شد: {val}", owner_keyboard())
            except: send_message(chat_id, "❌ عدد معتبر!", settings_keyboard())
            return
        
        # 🚫 مسدود
        if text == "🚫 مسدود کردن" and is_admin(user_id):
            db["pending_ban"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "🚫 آیدی:", cancel_keyboard()); return
        if text == "✅ رفع مسدودیت" and is_admin(user_id):
            db["pending_unban"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "✅ آیدی:", cancel_keyboard()); return
        
        if text == "👑 افزودن ادمین" and user_id == str(OWNER_ID):
            db["pending_admin"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "👑 آیدی:", cancel_keyboard()); return
        if text == "🗑️ حذف ادمین" and user_id == str(OWNER_ID):
            db["pending_remove_admin"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "🗑️ آیدی:", cancel_keyboard()); return
        if text == "📨 پیام به کاربر" and is_admin(user_id):
            db["pending_pm"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "📨 آیدی:", cancel_keyboard()); return
        if text == "💻 اجرای کد" and is_admin(user_id):
            db["pending_execute"][user_id] = {"step": "waiting_code"}; save_db_async()
            send_message(chat_id, "💻 کد:", cancel_keyboard()); return
        if text == "💻 اجرای قابلیت" and is_admin(user_id):
            db["pending_feature"][user_id] = {"step": "waiting_code"}; save_db_async()
            send_message(chat_id, "💻 کد قابلیت:", cancel_keyboard()); return
        if text == "👤 مشخصات کاربر" and is_admin(user_id):
            db["pending_user_info"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "🆔 آیدی:", cancel_keyboard()); return
        if text == "🎁 سکه پاکت" and is_admin(user_id):
            db["pending_packet"][user_id] = {"step": "waiting_coins"}; save_db_async()
            send_message(chat_id, "💰 چند سکه؟", owner_keyboard()); return
        if text == "🛡️ ضدتقلب" and is_admin(user_id):
            banned_count = len(db.get("banned", []))
            send_message(chat_id, f"🛡️ **ضدتقلب**\n\n🚫 مسدود: {banned_count}", owner_keyboard()); return
        
        if text == "📊 آمار پیشرفته" and is_admin(user_id):
            total_users = len(db['users'])
            total_coins = sum(u.get('coins', 0) for u in db['users'].values())
            spent = db["stats"].get("total_coins_spent", 0)
            active_orders = len([o for o in db['orders'].values() if o['status'] == 'active'])
            active_members = len([o for o in db['member_orders'].values() if o['status'] == 'active'])
            guaranteed_count = len([o for o in db['member_orders'].values() if o.get('order_type') == 'guaranteed' and o['status'] == 'active'])
            send_message(chat_id, f"📊 **آمار پیشرفته**\n\n"
                f"👥 کاربران: {total_users}\n"
                f"💰 سکه در گردش: {total_coins:,}\n"
                f"💸 سکه خرج: {spent:,}\n"
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
            send_message(chat_id, "💰 چند سکه؟", owner_keyboard()); return
        if text == "💰 افزودن سکه به همه" and is_admin(user_id):
            db["pending_add_coins"][user_id] = {"step": "waiting_amount"}; save_db_async()
            send_message(chat_id, "💰 چند سکه؟", owner_keyboard()); return
        if text == "🎁 تغییر سکه دعوت" and is_admin(user_id):
            db["pending_gift"][user_id] = {"step": "waiting_invite_reward"}; save_db_async()
            send_message(chat_id, f"🎁 فعلی: {get_setting('invite_reward', 15)}\n\nجدید:", owner_keyboard()); return
        
        if text == "📢 ارسال به کانال" and is_admin(user_id):
            db["pending_send_to_channel"][user_id] = {"step": "waiting_link"}; save_db_async()
            send_message(chat_id, "📢 **لینک کانال:**", cancel_keyboard()); return
        if text == "📊 نظرسنجی" and is_admin(user_id):
            db["pending_poll"][user_id] = {"step": "waiting_question"}; save_db_async()
            send_message(chat_id, "📊 **سوال نظرسنجی:**", cancel_keyboard()); return
        
        # 🎮 شروع بازی
        if text == "🎮 شروع بازی" and is_admin(user_id):
            db["pending_game"][user_id] = {"step": "waiting_name"}; save_db_async()
            send_message(chat_id, "🎮 **اسم بازی چیه؟**", cancel_keyboard()); return
        
        # 🛑 توقف بازی
        if text == "🛑 توقف بازی" and is_admin(user_id):
            active_games = db.get("active_games", {})
            if not active_games:
                send_message(chat_id, "❌ **بازی فعالی نیست!**", owner_keyboard()); return
            for gid, game in list(active_games.items()):
                game["status"] = "stopped"
            save_db_async()
            send_message(chat_id, "🛑 **همه بازی‌ها متوقف شدند!**", owner_keyboard()); return
        
        # 📋 لیست کانال‌های ادمین
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
        
        # 👥 کاربران کانال
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
            send_message(chat_id, "🚀 **پیام فوروارد کن:**", cancel_keyboard()); return
        if text == "📢 پیام به گروه‌ها" and user_id == str(OWNER_ID):
            db["pending_broadcast_groups"][user_id] = {"step": "waiting_message"}; save_db_async()
            send_message(chat_id, "📢 **متن پیام:**", cancel_keyboard()); return
        
        if text == "💸 انتقال سکه" and user_id == str(OWNER_ID):
            fee = get_setting('transfer_fee', 2)
            db["pending_transfer"][user_id] = {"step": "waiting_id"}
            save_db_async()
            send_message(chat_id, f"🆔 **آیدی مقصد:**\n\n💸 کارمزد: {fee}", cancel_keyboard())
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
        
        # ═══ pending مالک ═══
        pb = db["pending_ban"].get(user_id, {})
        if pb.get("step") == "waiting_id":
            uid = text.strip()
            if uid not in db.get("banned", []): db.setdefault("banned", []).append(uid)
            del db["pending_ban"][user_id]; save_db_async()
            send_message(chat_id, f"🚫 مسدود شد!", owner_keyboard())
            try: send_message(int(uid), "🚫 مسدود شدی!")
            except: pass
            return
        
        pu2 = db["pending_unban"].get(user_id, {})
        if pu2.get("step") == "waiting_id":
            uid = text.strip()
            if uid in db.get("banned", []):
                db["banned"].remove(uid)
                del db["pending_unban"][user_id]; save_db_async()
                send_message(chat_id, f"✅ آزاد شد!", owner_keyboard())
                try: send_message(int(uid), "🎉 آزاد شدی!")
                except: pass
            else: send_message(chat_id, "❌ نبود!", owner_keyboard()); del db["pending_unban"][user_id]; save_db_async()
            return
        
        pa = db["pending_admin"].get(user_id, {})
        if pa.get("step") == "waiting_id":
            uid = text.strip()
            if uid not in db.get("admins", []): db["admins"].append(uid)
            del db["pending_admin"][user_id]; save_db_async()
            send_message(chat_id, "👑 ادمین شد!", owner_keyboard())
            try: send_message(int(uid), "👑 ادمین شدی!", owner_keyboard())
            except: pass
            return
        
        pra = db["pending_remove_admin"].get(user_id, {})
        if pra.get("step") == "waiting_id":
            uid = text.strip()
            if uid in db.get("admins", []):
                db["admins"].remove(uid); save_db_async()
                send_message(chat_id, "🗑️ حذف شد!", owner_keyboard())
                try: send_message(int(uid), "🗑️ پنل مالک گرفته شد!", main_keyboard())
                except: pass
            else: send_message(chat_id, "❌ ادمین نبود!", owner_keyboard())
            del db["pending_remove_admin"][user_id]; save_db_async()
            return
        
        ppm = db["pending_pm"].get(user_id, {})
        if ppm.get("step") == "waiting_id":
            db["pending_pm"][user_id] = {"step": "waiting_text", "id": text.strip()}; save_db_async()
            send_message(chat_id, "📝 متن:", cancel_keyboard()); return
        if ppm.get("step") == "waiting_text":
            uid = ppm["id"]
            try:
                send_message(int(uid), text)
                send_message(chat_id, "✅ ارسال شد!", owner_keyboard())
            except: send_message(chat_id, "❌ خطا!", owner_keyboard())
            del db["pending_pm"][user_id]; save_db_async()
            return
        
        pe = db["pending_execute"].get(user_id, {})
        if pe.get("step") == "waiting_code":
            try:
                eg = {'threading': threading, 'get_chat_member': get_chat_member, 'get_setting': get_setting, 'save_db_async': save_db_async, 'db': db, 'send_message': send_message, 'get_user': get_user, 'add_coins': add_coins, 'remove_coins': remove_coins, 'get_coins': get_coins, 'delete_message': delete_message, 'forward_message': forward_message, 'OWNER_ID': OWNER_ID, 'CHANNEL_ID': CHANNEL_ID, 'time': time, 'datetime': datetime, 'random': random, 'json': json, 'TOKEN': TOKEN}
                exec(text.strip(), eg)
                send_message(chat_id, "✅ اجرا شد!", owner_keyboard())
            except Exception as e: send_message(chat_id, f"❌ خطا: `{str(e)[:200]}`", owner_keyboard())
            del db["pending_execute"][user_id]; save_db_async(); return
        
        pf = db["pending_feature"].get(user_id, {})
        if pf.get("step") == "waiting_code":
            try:
                eg = {'threading': threading, 'get_chat_member': get_chat_member, 'get_setting': get_setting, 'save_db_async': save_db_async, 'db': db, 'send_message': send_message, 'get_user': get_user, 'add_coins': add_coins, 'remove_coins': remove_coins, 'get_coins': get_coins, 'delete_message': delete_message, 'forward_message': forward_message, 'OWNER_ID': OWNER_ID, 'CHANNEL_ID': CHANNEL_ID, 'time': time, 'datetime': datetime, 'random': random, 'json': json, 'TOKEN': TOKEN}
                if "custom_features" not in db: db["custom_features"] = []
                db["custom_features"].append(text.strip())
                save_db_async()
                try: exec(text.strip(), eg)
                except Exception as e: send_message(chat_id, f"⚠️ ذخیره شد ولی خطا: `{str(e)[:200]}`", owner_keyboard()); del db["pending_feature"][user_id]; save_db_async(); return
                send_message(chat_id, "✅ قابلیت اضافه و اجرا شد!", owner_keyboard())
            except Exception as e: send_message(chat_id, f"❌ خطا: `{str(e)[:200]}`", owner_keyboard())
            del db["pending_feature"][user_id]; save_db_async(); return
        
        pui = db["pending_user_info"].get(user_id, {})
        if pui.get("step") == "waiting_id":
            target = text.strip()
            if target not in db["users"]:
                send_message(chat_id, "❌ پیدا نشد!", owner_keyboard())
                db["pending_user_info"].pop(user_id, None); save_db_async(); return
            u = get_user(target)
            sin_orders = sum(1 for o in db["orders"].values() if o["user_id"] == target)
            mem_orders = sum(1 for o in db["member_orders"].values() if o["user_id"] == target)
            banned = "🚫 بن" if target in db.get("banned", []) else "✅ فعال"
            warns = db.get("admin_warnings", {}).get(target, {}).get("count", 0)
            send_message(chat_id, f"👤 **مشخصات**\n\n🆔 {target}\n📛 @{u.get('username') or 'ندارد'}\n🪙 {u.get('coins', 0):,}\n👥 دعوت: {u.get('invite_count', 0)}\n📊 سین: {sin_orders}\n👥 عضو: {mem_orders}\n🚫 {banned}\n⚠️ اخطار: {warns}\n📅 {u.get('joined_at', '?')}", owner_keyboard())
            db["pending_user_info"].pop(user_id, None); save_db_async(); return
        
        pp = db["pending_packet"].get(user_id, {})
        if pp.get("step") == "waiting_coins":
            try:
                db["pending_packet"][user_id] = {"step": "waiting_capacity", "coins": int(convert_number(text))}
                save_db_async(); send_message(chat_id, "👥 ظرفیت؟", owner_keyboard())
            except: send_message(chat_id, "❌ عدد!", owner_keyboard())
            return
        if pp.get("step") == "waiting_capacity":
            try:
                cap = int(convert_number(text))
                db["pending_packet"][user_id]["step"] = "waiting_text"
                db["pending_packet"][user_id]["capacity"] = cap
                save_db_async()
                send_message(chat_id, f"📝 متن پاکت:", owner_keyboard())
            except: send_message(chat_id, "❌ عدد!", owner_keyboard())
            return
        if pp.get("step") == "waiting_text":
            ptext = text.strip()
            pid = str(int(time.time() * 1000))
            coins = pp["coins"]; cap = pp["capacity"]
            db["coin_packets"][pid] = {"coins": coins, "capacity": cap, "text": ptext, "used_by": []}
            kb = {"inline_keyboard": [[{"text": "🎁 باز کردن پاکت", "callback_data": f"packet_{pid}"}]]}
            send_message(CHANNEL_ID, f"🎁 **سکه پاکت**\n\n{ptext}\n\n💰 هر نفر: {coins} سکه\n👥 ظرفیت: {cap}", kb)
            db["pending_packet"].pop(user_id, None); save_db_async()
            send_message(chat_id, "✅ پاکت گذاشته شد!", owner_keyboard()); return
        
        pg = db["pending_gift"].get(user_id, {})
        if pg.get("step") == "waiting_coins":
            try:
                db["pending_gift"][user_id] = {"step": "waiting_capacity", "coins": int(convert_number(text))}
                save_db_async(); send_message(chat_id, "👥 ظرفیت؟", owner_keyboard())
            except: send_message(chat_id, "❌ عدد!", owner_keyboard())
            return
        if pg.get("step") == "waiting_capacity":
            try:
                cap = int(convert_number(text))
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                db["gift_codes"][code] = {"coins": pg["coins"], "capacity": cap, "used_by": []}
                del db["pending_gift"][user_id]; save_db_async()
                send_message(chat_id, f"🎁 کد: `{code}`\n💰 {pg['coins']:,} سکه\n👥 {cap} نفر", owner_keyboard())
            except: send_message(chat_id, "❌ عدد!", owner_keyboard())
            return
        if pg.get("step") == "waiting_invite_reward":
            try:
                val = int(convert_number(text))
                db["settings"]["invite_reward"] = val
                del db["pending_gift"][user_id]; save_db_async()
                send_message(chat_id, f"✅ سکه دعوت = {val}", owner_keyboard())
            except: send_message(chat_id, "❌ عدد!", owner_keyboard())
            return
        
        pac = db["pending_add_coins"].get(user_id, {})
        if pac.get("step") == "waiting_amount":
            try:
                amount = int(convert_number(text))
                count = 0
                for uid in db["users"]:
                    add_coins(uid, amount); count += 1
                del db["pending_add_coins"][user_id]; save_db_async()
                send_message(chat_id, f"✅ {amount} سکه به {count} کاربر اضافه شد!", owner_keyboard())
            except: send_message(chat_id, "❌ عدد!", owner_keyboard())
            return
        
        # 🎮 شروع بازی - مرحله به مرحله
        pgame = db["pending_game"].get(user_id, {})
        if pgame.get("step") == "waiting_name":
            db["pending_game"][user_id] = {"step": "waiting_capacity", "name": text}
            save_db_async()
            send_message(chat_id, "👥 **ظرفیت چند نفر؟**", cancel_keyboard()); return
        if pgame.get("step") == "waiting_capacity":
            try:
                cap = int(convert_number(text))
                db["pending_game"][user_id]["capacity"] = cap
                db["pending_game"][user_id]["step"] = "waiting_needed"
                save_db_async()
                send_message(chat_id, "👥 **هر نفر چند دعوت کنه؟**", cancel_keyboard())
            except: send_message(chat_id, "❌ عدد!", cancel_keyboard())
            return
        if pgame.get("step") == "waiting_needed":
            try:
                needed = int(convert_number(text))
                db["pending_game"][user_id]["needed"] = needed
                db["pending_game"][user_id]["step"] = "waiting_reward"
                save_db_async()
                send_message(chat_id, "💰 **جایزه برنده چند سکه باشه؟**", cancel_keyboard())
            except: send_message(chat_id, "❌ عدد!", cancel_keyboard())
            return
        if pgame.get("step") == "waiting_reward":
            try:
                reward = int(convert_number(text))
                gname = pgame["name"]
                cap = pgame["capacity"]
                needed = pgame["needed"]
                
                db["game_counter"] = db.get("game_counter", 0) + 1
                gid = str(db["game_counter"])
                db["active_games"][gid] = {
                    "name": gname,
                    "capacity": cap,
                    "needed": needed,
                    "reward": reward,
                    "players": {},
                    "status": "active",
                    "created_at": str(datetime.now()),
                    "creator": user_id
                }
                
                # ارسال پیام به کانال
                kb = {"inline_keyboard": [[
                    {"text": "📝 ثبت‌نام", "callback_data": f"game_join_{gid}"}
                ]]}
                sent = send_message(CHANNEL_ID,
                    f"🎮 **بازی شروع شد!**\n\n"
                    f"🎯 اسم بازی: {gname}\n"
                    f"👥 ظرفیت: {cap} نفر\n"
                    f"👥 هر نفر: {needed} دعوت\n"
                    f"🪙 جایزه برنده: {reward} سکه\n\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"🏆 **اولین کسی که به {needed} دعوت برسه، برنده‌ست!**\n"
                    f"━━━━━━━━━━━━━━━━\n\n"
                    f"🔘 برای ثبت‌نام دکمه زیر رو بزن:",
                    kb)
                
                if sent.get("ok"):
                    db["active_games"][gid]["message_id"] = sent["result"]["message_id"]
                
                save_db_async()
                del db["pending_game"][user_id]; save_db_async()
                send_message(chat_id, f"✅ **بازی ساخته شد!** 🎉\n\n🎯 {gname}", owner_keyboard())
            except: send_message(chat_id, "❌ عدد!", cancel_keyboard())
            return
        
        # 📋 کاربران کانال
        put = db["pending_utility"].get(user_id, {})
        if put.get("step") == "waiting_channel_id":
            cid = text.strip()
            ci = get_chat(cid)
            if not ci.get("ok"):
                send_message(chat_id, "❌ کانال پیدا نشد!", owner_keyboard())
                del db["pending_utility"][user_id]; save_db_async(); return
            tcid = ci["result"]["id"]
            
            # لیست کاربرانی که تو کانال هستن
            users_in_channel = []
            for uid, udata in db["users"].items():
                r = get_chat_member(tcid, int(uid))
                if r.get("ok") and r["result"]["status"] in ["member", "administrator", "creator"]:
                    users_in_channel.append(udata.get("username") or uid)
            
            msg = f"👥 **کاربران کانال:**\n\n"
            if users_in_channel:
                for i, un in enumerate(users_in_channel[:50], 1):
                    msg += f"{i}. @{un}\n"
                if len(users_in_channel) > 50:
                    msg += f"\n... و {len(users_in_channel) - 50} نفر دیگه"
            else:
                msg += "❌ هیچ کاربری نیست!"
            msg += f"\n\n📊 کل: {len(users_in_channel)}"
            send_message(chat_id, msg, owner_keyboard())
            del db["pending_utility"][user_id]; save_db_async()
            return
        
        # ارسال به کانال دلخواه
        psc = db["pending_send_to_channel"].get(user_id, {})
        if psc.get("step") == "waiting_link":
            link = text.strip()
            if "ble.ir/" in link:
                cu = "@" + link.split("ble.ir/")[-1]
            elif link.startswith("@"):
                cu = link
            else:
                send_message(chat_id, "❌ **لینک نامعتبر!**", cancel_keyboard())
                return
            ci = get_chat(cu)
            if not ci.get("ok"):
                send_message(chat_id, "❌ **کانال پیدا نشد!**", cancel_keyboard())
                return
            tcid = ci["result"]["id"]
            bot_id = int(TOKEN.split(":")[0])
            ms = get_chat_member(tcid, bot_id)
            if not (ms.get("ok") and ms["result"]["status"] in ["administrator", "creator"]):
                send_message(chat_id, "❌ **ربات توی این کانال ادمین نیست!**", cancel_keyboard())
                return
            db["pending_send_to_channel"][user_id] = {"step": "waiting_text", "chat_id": tcid}
            save_db_async()
            send_message(chat_id, "📝 **متن پیام:**", cancel_keyboard())
            return
        if psc.get("step") == "waiting_text":
            db["pending_send_to_channel"][user_id]["text"] = text
            db["pending_send_to_channel"][user_id]["step"] = "waiting_keyboard"
            save_db_async()
            send_message(chat_id, "🔘 **دکمه‌ها:**\n\n`متن | url | لینک`\n`متن | coins | تعداد`\n\nیا `ندارد`:", cancel_keyboard())
            return
        if psc.get("step") == "waiting_keyboard":
            tcid = psc.get("chat_id")
            text_msg = psc.get("text", "")
            keyboard = None
            if text.strip() != "ندارد":
                try:
                    rows = []
                    for line in text.strip().split("\n"):
                        parts = [p.strip() for p in line.split("|")]
                        if len(parts) >= 3:
                            bt, bt_type, bv = parts[0], parts[1], parts[2]
                            if bt_type == "url": rows.append([{"text": bt, "url": bv}])
                            elif bt_type == "coins":
                                cb_id = f"bc_gift_{int(bv)}_{random.randint(1000,9999)}"
                                db.setdefault("bc_gifts", {})[cb_id] = {"coins": int(bv), "used": []}
                                rows.append([{"text": bt, "callback_data": cb_id}])
                    if rows: keyboard = {"inline_keyboard": rows}
                except Exception as e:
                    send_message(chat_id, f"❌ خطا: {e}", owner_keyboard())
                    del db["pending_send_to_channel"][user_id]; save_db_async(); return
            result = send_message(tcid, text_msg, keyboard)
            if result.get("ok"):
                send_message(chat_id, "✅ **ارسال شد!**", owner_keyboard())
            else:
                send_message(chat_id, f"❌ **خطا:** `{result}`", owner_keyboard())
            db["pending_send_to_channel"].pop(user_id, None); save_db_async()
            return
        
        # نظرسنجی
        ppo = db["pending_poll"].get(user_id, {})
        if ppo.get("step") == "waiting_question":
            db["pending_poll"][user_id] = {"step": "waiting_options", "question": text}
            save_db_async()
            send_message(chat_id, "📝 **جواب‌ها (هر خط یه جواب):**", cancel_keyboard())
            return
        if ppo.get("step") == "waiting_options":
            options = [opt.strip() for opt in text.strip().split("\n") if opt.strip()]
            if len(options) < 2:
                send_message(chat_id, "❌ **حداقل ۲ جواب!**", cancel_keyboard())
                return
            if len(options) > 10:
                send_message(chat_id, "❌ **حداکثر ۱۰ جواب!**", cancel_keyboard())
                return
            db["poll_counter"] = db.get("poll_counter", 0) + 1
            poll_id = str(db["poll_counter"])
            db.setdefault("polls", {})[poll_id] = {
                "question": ppo["question"],
                "options": options,
                "votes": {opt: [] for opt in options},
                "creator": user_id,
                "created_at": str(datetime.now())
            }
            save_db_async()
            kb_rows = []
            for i, opt in enumerate(options):
                kb_rows.append([{"text": opt, "callback_data": f"poll_vote_{poll_id}_{i}"}])
            kb = {"inline_keyboard": kb_rows}
            sent = send_message(CHANNEL_ID,
                f"📊 **نظرسنجی**\n\n❓ {ppo['question']}\n\n"
                f"━━━━━━━━━━━━━━━━\n👥 کل رای: 0\n━━━━━━━━━━━━━━━━\n\n🔘 **رای بده:**",
                kb)
            if sent.get("ok"):
                db["polls"][poll_id]["message_id"] = sent["result"]["message_id"]
                save_db_async()
            del db["pending_poll"][user_id]; save_db_async()
            send_message(chat_id, f"✅ **نظرسنجی ساخته شد!**", owner_keyboard())
            return
        
        pbc = db["pending_broadcast"].get(user_id, {})
        if pbc.get("step") == "waiting_message":
            del db["pending_broadcast"][user_id]; save_db_async()
            executor.submit(broadcast_worker, user_id, text)
            send_message(chat_id, "📢 **شروع...**", owner_keyboard()); return
        
        pbf = db["pending_broadcast_format"].get(user_id, {})
        if pbf.get("step") == "waiting_text":
            db["pending_broadcast_format"][user_id]["text"] = text
            db["pending_broadcast_format"][user_id]["step"] = "waiting_keyboard"
            save_db_async()
            send_message(chat_id, "🔘 دکمه‌ها یا `ندارد`:", cancel_keyboard()); return
        if pbf.get("step") == "waiting_keyboard":
            text_msg = pbf.get("text", "")
            keyboard = None
            if text.strip() != "ندارد":
                try:
                    rows = []
                    for line in text.strip().split("\n"):
                        parts = [p.strip() for p in line.split("|")]
                        if len(parts) >= 3:
                            bt, bt_type, bv = parts[0], parts[1], parts[2]
                            if bt_type == "url": rows.append([{"text": bt, "url": bv}])
                            elif bt_type == "coins":
                                cb_id = f"bc_gift_{int(bv)}_{random.randint(1000,9999)}"
                                db.setdefault("bc_gifts", {})[cb_id] = {"coins": int(bv), "used": []}
                                rows.append([{"text": bt, "callback_data": cb_id}])
                    if rows: keyboard = {"inline_keyboard": rows}
                except Exception as e:
                    send_message(chat_id, f"❌ خطا: {e}", owner_keyboard())
                    del db["pending_broadcast_format"][user_id]; save_db_async(); return
            del db["pending_broadcast_format"][user_id]; save_db_async()
            executor.submit(broadcast_worker_advanced, user_id, text_msg, keyboard)
            send_message(chat_id, "📢 **شروع پیشرفته...**", owner_keyboard()); return
        
        pfa = db["pending_forward_all"].get(user_id, {})
        if pfa.get("step") == "waiting_forward":
            if "forward_from_chat" in message:
                from_chat_id = message["forward_from_chat"]["id"]
                msg_id = message["message_id"]
                del db["pending_forward_all"][user_id]; save_db_async()
                executor.submit(forward_to_all_worker, user_id, from_chat_id, msg_id)
                send_message(chat_id, "🚀 **شروع...**", owner_keyboard())
            else: send_message(chat_id, "❌ فوروارد کن!", cancel_keyboard())
            return
        
        pbg = db["pending_broadcast_groups"].get(user_id, {})
        if pbg.get("step") == "waiting_message":
            del db["pending_broadcast_groups"][user_id]; save_db_async()
            executor.submit(broadcast_to_groups_worker, user_id, text)
            send_message(chat_id, "📢 **شروع...**", owner_keyboard()); return
        
        psr = db["pending_support_reply"].get(user_id, {})
        if psr.get("step") == "waiting_reply":
            tid = psr.get("ticket_id")
            if tid and str(tid) in db.get("support_tickets", {}):
                ticket = db["support_tickets"][str(tid)]
                try:
                    send_message(int(ticket["user_id"]), f"📩 **جواب پشتیبانی:**\n\n{text}")
                    ticket["status"] = "answered"; save_db_async()
                    send_message(chat_id, "✅ ارسال شد!", owner_keyboard())
                except: send_message(chat_id, "❌ خطا!", owner_keyboard())
            db["pending_support_reply"].pop(user_id, None); save_db_async(); return
        
        # ═══ ۷. دکمه‌های اصلی ═══
        if text == "🪙 کسب سکه":
            kb = {"inline_keyboard": [[{"text": "👁️ برو به کانال", "url": CHANNEL_LINK}]]}
            send_message(chat_id, f"🔗 **برو کانال و «دیدم» بزن!** 💰\n\n{CHANNEL_LINK}", kb)
            return
        
        if text == "💰 سکه‌های من":
            send_message(chat_id, f"💰 **موجودی:** {get_coins(user_id):,} سکه 🪙")
            return
        
        if text == "📖 راهنما":
            send_message(chat_id, f"📖 **راهنمای هایپرسین ⚡**\n\n"
                f"👁️ هر سین = {get_setting('sin_cost', 1)} سکه\n"
                f"👥 هر عضو = {get_setting('member_cost', 5)} سکه\n"
                f"🎡 گردونه: تا ۲۵ سکه\n"
                f"👥 دعوت: {get_setting('invite_reward', 15)} سکه\n"
                f"🎁 هدیه روزانه: {get_setting('daily_gift', 10)} سکه\n\n"
                f"✨ هایپرسین")
            return
        
        if text == "👤 حساب کاربری":
            u = get_user(user_id)
            send_message(chat_id, f"👤 **حساب کاربری:**\n\n"
                f"👤 {name}\n"
                f"🆔 {user_id}\n"
                f"📛 @{u['username'] if u['username'] else 'ندارد'}\n"
                f"🪙 {u['coins']:,} سکه\n"
                f"👥 دعوت: {u.get('invite_count', 0)} نفر",
                {"inline_keyboard": [[{"text": "📋 کپی آیدی", "callback_data": "copy_id"}], [{"text": "🔙 بازگشت", "callback_data": "back_to_main"}]]})
            return
        
        if text == "👥 دعوت دوستان":
            link = f"https://ble.ir/{BOT_USERNAME}?start={user_id}"
            invite_text = (f"🔥 **هایپرسین**\n\n"
                f"👁️ سین بزن | 👥 عضو بگیر\n\n"
                f"🎁 همه‌چی رایگان!\n\n"
                f"🔗 {link}")
            result = send_message(chat_id, invite_text)
            if result.get("ok"):
                msg_id = result["result"]["message_id"]
                u = get_user(user_id)
                invite_count = u.get("invite_count", 0)
                send_reply(chat_id, msg_id, f"🪙 هر دعوت = {get_setting('invite_reward', INVITE_REWARD)} سکه 🎁🔥\n\n👥 تعداد دعوت‌های تو: {invite_count} نفر")
            return
        
        if text == "👁️ ثبت سفارش سین":
            db["pending_orders"][user_id] = {"step": "waiting_forward"}
            save_db_async()
            send_message(chat_id, "📩 **پیام رو از کانال فوروارد کن.**", cancel_keyboard())
            return
        
        if text == "👥 ثبت سفارش عضو":
            db["pending_members"][user_id] = {"step": "waiting_link"}
            save_db_async()
            send_message(chat_id, "📩 **لینک کانال:**\n\n⚠️ فقط کانال!", cancel_keyboard())
            return
        
        if text == "🎁 زدن کد هدیه":
            db["pending_orders"][user_id] = {"step": "waiting_gift_code"}
            save_db_async()
            send_message(chat_id, "🎁 **کد هدیه:**", cancel_keyboard())
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
                    send_message(chat_id, f"⏰ {h} ساعت و {m} دقیقه دیگه بیا!")
                    return
            daily = get_setting("daily_gift", DAILY_GIFT)
            add_coins(user_id, daily)
            user["last_daily"] = str(now)
            save_db_async()
            send_message(chat_id, f"🎁 **هدیه روزانه!**\n\n🪙 +{daily} سکه\n💰 {get_coins(user_id):,}")
            return
        
        if text == "🎡 گردونه شانس":
            can, remaining = can_spin_wheel(user_id)
            if not can:
                h = remaining // 3600
                m = (remaining % 3600) // 60
                send_message(chat_id, f"⏰ {h} ساعت و {m} دقیقه دیگه بیا!")
                return
            kb = {"inline_keyboard": [[{"text": "🎡 بچرخون!", "callback_data": "spin_wheel"}]]}
            send_message(chat_id, f"🎡 **گردونه شانس**\n\nجوایز: 💰۲۵ 💵۲۰ 📩۱۰ 🌟۵ 🎵پوچ\n\n🔘 بزن:", kb)
            return
        
        if text == "💬 پشتیبانی":
            db["pending_support"][user_id] = {"step": "waiting"}
            save_db_async()
            send_message(chat_id, "💬 **پیامت رو بفرست:**", cancel_keyboard())
            return
        
        send_message(chat_id, f"👋 **سلام {name} جان!** 😎", main_keyboard(user_id))
    
    except Exception as e:
        print(f"⚠️ خطا: {e}")

# ─── پایان بخش ۵ ───
# ═══════════════════════════════════════
# 🔘 Callback
# ═══════════════════════════════════════
def handle_callback(callback):
    try:
        callback_id = callback["id"]
        data = callback["data"]
        user_id = str(callback["from"]["id"])
        message = callback.get("message", {})
        chat_id = message.get("chat", {}).get("id", CHANNEL_ID)
        
        if is_banned(user_id):
            answer_callback(callback_id, "🚫 مسدود شدی!", show_alert=True); return
        
        # ═══ چک عضویت ═══
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
                    send_message(user_id, "✅ حالا استفاده کن!", main_keyboard(user_id))
            else:
                answer_callback(callback_id, "❌ هنوز عضو نشدی!", show_alert=True)
                must_join(user_id)
            return
        
        if data == "back_to_main":
            send_message(user_id, "🏠 منوی اصلی:", main_keyboard(user_id))
            answer_callback(callback_id); return
        if data == "back_to_owner":
            send_message(user_id, "👑 پنل مالک:", owner_keyboard())
            answer_callback(callback_id); return
        if data == "copy_id":
            answer_callback(callback_id, f"✅ آیدی: {user_id}", show_alert=True); return
        
        # ═══ 🎮 بازی: ثبت‌نام ═══
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
            
            # ✅ ثبت‌نام کاربر
            game.setdefault("players", {})[user_id] = {
                "name": callback["from"].get("first_name", "کاربر"),
                "username": callback["from"].get("username", ""),
                "invites": 0
            }
            save_db_async()
            
            # لینک دعوت کاربر
            user_link = f"https://ble.ir/{BOT_USERNAME}?start={user_id}"
            needed = game.get("needed", 10)
            reward = game.get("reward", 500)
            
            answer_callback(callback_id, "✅ ثبت‌نام شدی!", show_alert=True)
            
            # پیام به پیوی کاربر
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
            
            # آپدیت پیام کانال
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
        
        # ═══ سکه پاکت ═══
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
        
        # ═══ گردونه ═══
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
        
        # ═══ دکمه سکه‌ای پیام همگانی ═══
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
        
        # ═══ پیام همگانی - نوع ═══
        if data == "bc_simple":
            db["pending_broadcast"][user_id] = {"step": "waiting_message"}; save_db_async()
            send_message(user_id, "📝 **متن:**", cancel_keyboard()); return
        if data in ["bc_buttons", "bc_link", "bc_coins"]:
            db["pending_broadcast_format"][user_id] = {"step": "waiting_text"}; save_db_async()
            send_message(user_id, "📝 **متن:**", cancel_keyboard()); return
        
        # ═══ جوین اجباری ═══
        if data == "join_add":
            db["pending_join_channel"][user_id] = {"step": "waiting_link"}; save_db_async()
            send_message(user_id, "🔗 **لینک کانال:**", cancel_keyboard())
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
                send_message(user_id, "👑 پنل مالک:", owner_keyboard())
            return
        
        # ═══ دیدم ═══
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
                # 🗑️ حذف پیام از کانال
                try:
                    delete_message(CHANNEL_ID, order["message_id"])
                    db["stats"]["deleted_messages"] += 1
                except: pass
                try:
                    if order.get("reply_message_id"): delete_message(CHANNEL_ID, order["reply_message_id"])
                except: pass
                # 📩 پیام به کاربر
                try:
                    send_message(int(order["user_id"]),
                        f"🎉 **تبریک!**\n\n"
                        f"🔢 **{count}** سین کامل خورد!\n"
                        f"📩 پیام از کانال حذف شد.",
                        main_keyboard(order["user_id"]))
                except: pass
            save_db_async(); return
        
        # ═══ گزارش سین ═══
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
        
        # ═══ info عضو ═══
        if data.startswith("info_"):
            mid = data.replace("info_", "")
            o = db["member_orders"].get(mid, {})
            reward = o.get("reward", 3); otype = o.get("order_type", "normal")
            if otype == "guaranteed":
                answer_callback(callback_id, f"🪙 {reward} سکه! باید {get_setting('guaranteed_hours', 48)} ساعت بمونی!", show_alert=True)
            else:
                answer_callback(callback_id, f"🪙 {reward} سکه!", show_alert=True)
            return
        
        # ═══ عضو شدن ═══
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
                    # 🗑️ حذف پیام از کانال
                    try: delete_message(CHANNEL_ID, order["message_id"])
                    except: pass
                    # 📩 پیام به کاربر
                    try:
                        send_message(int(order["user_id"]),
                            f"🎉 **تبریک!**\n\n👥 **{count}** عضو کامل شد!\n📩 پیام از کانال حذف شد.",
                            main_keyboard(order["user_id"]))
                    except: pass
            else:
                answer_callback(callback_id, "❌ هنوز عضو نشدی! اول عضو شو.", show_alert=True)
            save_db_async(); return
        
        # ═══ گزارش عضو ═══
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
        
        # ═══ نظرسنجی ═══
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
        
        # ═══ تیکت پشتیبانی ═══
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
            send_message(user_id, "📝 **جواب:**", cancel_keyboard()); return
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

# ═══════════════════════════════════════
# 🚀 حلقه اصلی
# ═══════════════════════════════════════
last_update_id = 0

def main():
    global last_update_id, INVITE_REWARD
    INVITE_REWARD = db.get("invite_reward", INVITE_REWARD)
    print("⚡ هایپرسین بله - نسخه فوق سریع!")
    print(f"🤖 @{BOT_USERNAME}")
    print(f"💓 Cache | ThreadPool(2000)")
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

# ═══════════════════════════════════════
# 💓 Keep-Alive
# ═══════════════════════════════════════
def keep_alive():
    while True:
        try:
            time.sleep(240)
            requests.get(f"{RENDER_URL}/ping", timeout=15)
            print(f"💓 پینگ | {datetime.now().strftime('%H:%M:%S')}")
        except: time.sleep(60)

# ═══════════════════════════════════════
# 🌐 Flask
# ═══════════════════════════════════════
app = Flask(__name__)

@app.route('/')
def home(): return "🤖 Hypersin Bale Bot!"

@app.route('/ping')
def ping(): return "pong ✅"

@app.route('/health')
def health():
    return jsonify({"status": "online", "users": len(db.get("users", {})), "cache": len(CACHE)})

# ═══════════════════════════════════════
# 🚀 اجرا
# ═══════════════════════════════════════
if __name__ == "__main__":
    threading.Thread(target=save_worker, daemon=True).start()
    threading.Thread(target=cache_cleanup, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    threading.Thread(target=check_guaranteed_members, daemon=True).start()
    threading.Thread(target=check_admin_orders, daemon=True).start()
    threading.Thread(target=main, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)

# ─── پایان کد کامل ───
# ═══════════════════════════════════════
# ✅ تمام شد!
# ═══════════════════════════════════════