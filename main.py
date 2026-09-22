import requests, json, time, random, string, os, threading, gc
from datetime import datetime, timedelta
from flask import Flask, jsonify
from concurrent.futures import ThreadPoolExecutor

# ═══════════════════════════════════════
# 🔧 تنظیمات
# ═══════════════════════════════════════
TOKEN = "1224499710:Whyt_329-tLCDsbZMEq82FGdVMVsVcmK0rM"
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

CHANNEL_ID = "@SCYVu"
CHANNEL_LINK = "https://ble.ir/SCYVu"
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
SEEN_REWARD = 3
SIN_COST = 1
INVITE_REWARD = 15
DAILY_GIFT = 10
MEMBER_NORMAL_REWARD = 7
MEMBER_GUARANTEED_REWARD = 15
TRANSFER_FEE = 2

GUARANTEED_HOURS = 48
GUARANTEED_PENALTY = 7
GUARANTEED_REFUND = 5
GUARANTEED_COOLDOWN = 300

WHEEL_PRIZES = [
    {"emoji": "🏆", "coins": 100, "weight": 5},
    {"emoji": "💰", "coins": 60, "weight": 10},
    {"emoji": "💵", "coins": 40, "weight": 15},
    {"emoji": "🥈", "coins": 15, "weight": 20},
    {"emoji": "📩", "coins": 10, "weight": 20},
    {"emoji": "🌟", "coins": 5, "weight": 15},
    {"emoji": "🎵", "coins": 0, "weight": 10},
    {"emoji": "🔄", "coins": -1, "weight": 5}
]
WHEEL_COOLDOWN = 12 * 3600

DB_FILE = "hypersin_bale.json"
RENDER_URL = "https://hypersin-bale.onrender.com"

CACHE = {}
CACHE_TIME = {}
CACHE_TTL = 3600
JOIN_CACHE = {}
JOIN_CACHE_TIME = {}
SAVE_PENDING = False
SAVE_LOCK = threading.Lock()
executor = ThreadPoolExecutor(max_workers=500)

def load_db():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except: pass
    return {
        "users": {}, "orders": {}, "member_orders": {}, "gift_codes": {},
        "seen_records": {}, "member_records": {}, "invited_users": {},
        "order_counter": 0, "member_counter": 0,
        "stats": {
            "total_orders": 0, "completed_orders": 0, "deleted_messages": 0,
            "total_members": 0, "completed_members": 0,
            "total_transfers": 0, "owner_earnings": 0,
            "total_coins_spent": 0, "total_coins_in_circulation": 0
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
        "coin_packets": {}, "bc_gifts": {},
        "banned": [], "admins": [], "vip": {},
        "join_channels": {},
        "games": {}, "game_counter": 0,
        "support_tickets": {}, "ticket_counter": 0,
        "guaranteed_times": {},
        "settings": {
            "seen_reward": SEEN_REWARD, "sin_cost": SIN_COST,
            "member_cost": MEMBER_COST,
            "member_normal_reward": MEMBER_NORMAL_REWARD,
            "member_guaranteed_reward": MEMBER_GUARANTEED_REWARD,
            "transfer_fee": TRANSFER_FEE,
            "start_gift": START_GIFT,
            "daily_gift": DAILY_GIFT,
            "invite_reward": INVITE_REWARD,
            "wheel_cooldown": WHEEL_COOLDOWN,
            "guaranteed_hours": GUARANTEED_HOURS,
            "guaranteed_penalty": GUARANTEED_PENALTY,
            "guaranteed_refund": GUARANTEED_REFUND,
            "guaranteed_cooldown": GUARANTEED_COOLDOWN
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
                    with open(DB_FILE, "w", encoding="utf-8") as f:
                        json.dump(db, f, ensure_ascii=False)
                    with open(f"{DB_FILE}.backup", "w", encoding="utf-8") as f:
                        json.dump(db, f, ensure_ascii=False)
                    SAVE_PENDING = False
                except: pass
        time.sleep(5)

def save_db(): save_db_async()

db = load_db()

# ─── پایان بخش ۱ ───
# ═══════════════════════════════════════
# 💰 توابع با Cache
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
# 📡 API
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
# ✅ چک عضویت (گروه + کانال)
# ═══════════════════════════════════════
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

def check_all_joins(user_id):
    if not check_joined(user_id): return False
    for ch_id, ch_info in db.get("join_channels", {}).items():
        try:
            r = get_chat_member(ch_id, user_id)
            if not r.get("ok"): return False
            if r["result"]["status"] not in ["member", "administrator", "creator"]: return False
        except: return False
    return True

def must_join(user_id):
    buttons = [[{"text": "🔗 عضویت در کانال اصلی", "url": CHANNEL_LINK}]]
    for ch_id, ch_info in db.get("join_channels", {}).items():
        ch_link = ch_info.get("link", ch_id)
        ch_type = ch_info.get("type", "کانال")
        label = "گروه" if ch_type == "گروه" else "کانال"
        buttons.append([{"text": f"🔗 عضویت در {label}", "url": ch_link}])
    buttons.append([{"text": "✅ عضو شدم", "callback_data": "check_join"}])
    keyboard = {"inline_keyboard": buttons}
    send_message(user_id, "🔒 **برای استفاده از ربات باید عضو بشی!**\n\nلطفاً عضو شو بعد روی «عضو شدم» بزن.", keyboard)
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
        [{"text": "💰 انتقال سکه"}, {"text": "🎁 هدیه روزانه"}],
        [{"text": "🎡 گردونه شانس"}, {"text": "💬 پشتیبانی"}],
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
            [{"text": "🎁 سکه پاکت"}, {"text": "🎁 پاکت به کاربر"}],
            [{"text": "🛡️ ضدتقلب"}, {"text": "📊 آمار پیشرفته"}],
            [{"text": "📊 آمار کل"}, {"text": "🔒 جوین اجباری"}],
            [{"text": "🎁 ساخت کد هدیه"}, {"text": "💰 افزودن سکه به همه"}],
            [{"text": "🎁 تغییر سکه دعوت"}, {"text": "💸 کارمزد انتقال"}],
            [{"text": "📢 پیام همگانی"}, {"text": "🏆 رتبه‌بندی"}],
            [{"text": "🔙 بازگشت"}]
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
            [{"text": "🔙 بازگشت"}]
        ],
        "resize_keyboard": True
    }

def all_settings_keyboard():
    return settings_keyboard()

def join_settings_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "➕ افزودن کانال/گروه", "callback_data": "join_add"}],
            [{"text": "🗑️ حذف از لیست", "callback_data": "join_remove"}],
            [{"text": "📋 لیست", "callback_data": "join_list"}],
            [{"text": "🔙 بازگشت", "callback_data": "back_to_owner"}]
        ]
    }

def cancel_keyboard():
    return {"keyboard": [[{"text": "🔙 بازگشت"}]], "resize_keyboard": True}

# ─── پایان بخش ۳ ───
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

# ═══════════════════════════════════════
# 📢 پیام همگانی
# ═══════════════════════════════════════
def broadcast_worker(user_id, text):
    sent = 0
    failed = 0
    all_users = list(db["users"].keys())
    total = len(all_users)
    for i, uid in enumerate(all_users, 1):
        try:
            r = send_message(int(uid), text)
            if r.get("ok"): sent += 1
            else: failed += 1
        except: failed += 1
        time.sleep(2)
        if i % 10 == 0:
            try: send_message(user_id, f"📊 پیشرفت: {i}/{total}")
            except: pass
    send_message(user_id, f"📢 **ارسال کامل شد!**\n\n✅ موفق: {sent}\n❌ ناموفق: {failed}\n📊 کل: {total}", owner_keyboard())

def broadcast_worker_advanced(user_id, text, keyboard_json=None):
    sent = 0
    failed = 0
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
        time.sleep(0.1)
        if i % 100 == 0:
            try: send_message(user_id, f"📊 پیشرفت: {i}/{total}")
            except: pass
    send_message(user_id, f"📢 **ارسال کامل شد!**\n\n✅ موفق: {sent}\n❌ ناموفق: {failed}\n📊 کل: {total}", owner_keyboard())

# ═══════════════════════════════════════
# 🛡️ چک تضمینی
# ═══════════════════════════════════════
def check_guaranteed_members():
    while True:
        try:
            time.sleep(300)
            now = datetime.now()
            hours = get_setting("guaranteed_hours", GUARANTEED_HOURS)
            penalty = get_setting("guaranteed_penalty", GUARANTEED_PENALTY)
            refund = get_setting("guaranteed_refund", GUARANTEED_REFUND)
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
# 🛡️ چک ادمین سفارش‌ها
# ═══════════════════════════════════════
def check_admin_orders():
    while True:
        try:
            time.sleep(5)
            bot_id = int(TOKEN.split(":")[0])
            for mid, order in list(db.get("member_orders", {}).items()):
                if order["status"] != "active": continue
                tcid = order["chat_id"]
                r = get_chat_member(tcid, bot_id)
                is_admin = r.get("ok") and r["result"]["status"] == "administrator"
                if not is_admin:
                    order["status"] = "removed"
                    save_db_async()
                    try:
                        send_message(int(order["user_id"]),
                            f"⚠️ **ربات رو از ادمینی درآوردی!**\n\n"
                            f"🗑️ سفارشت حذف شد\n"
                            f"❌ سکه‌هات برنمی‌گرده")
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
                      f"🤖 من **ربات عضوگیر و سین‌زن** هستم!\n"
                      f"👥 می‌تونم برات عضو بیارم\n"
                      f"👁️ می‌تونم برات سین بزنم\n\n"
                      f"🚀 اگه خواستی کانال یا گروهت رو رشد بدی،\n"
                      f"بیا توی پیوی من:\n"
                      f"🤖 @Idnuedobot\n\n"
                      f"🐺 تیم DeepParse")
                send_message(chat_id, wt)
            return
        
        if chat_type == "channel": return
        
        user_id = str(message["from"]["id"])
        text = message.get("text", "").strip()
        name = message["from"].get("first_name", "داداش")
        
        if is_banned(user_id):
            send_message(chat_id, "🚫 دسترسی شما مسدود شد!\n\n⏳ نگران نباش؛ ممکنه تا چند ساعت دیگه رفع بشه.")
            return
        
        username = message["from"].get("username", "")
        if username:
            get_user(user_id)["username"] = username
            save_db_async()
        
        get_user(user_id)["msg_count"] = get_user(user_id).get("msg_count", 0) + 1
        
        # پشتیبانی
        if db.get("pending_support", {}).get(user_id, {}).get("step") == "waiting":
            try:
                # ذخیره تیکت
                db["ticket_counter"] = db.get("ticket_counter", 0) + 1
                tid = db["ticket_counter"]
                db.setdefault("support_tickets", {})[str(tid)] = {
                    "user_id": user_id, "name": name, "text": text,
                    "status": "open", "date": str(datetime.now())
                }
                save_db_async()
                # ارسال به مالک با دکمه‌های شیشه‌ای
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
                send_message(chat_id, "✅ پیامت برای پشتیبانی ارسال شد!\n\n💚 به زودی جواب می‌گیری.", main_keyboard(user_id))
            except:
                send_message(chat_id, "❌ خطا در ارسال!", main_keyboard(user_id))
            db["pending_support"].pop(user_id, None)
            save_db_async()
            return
        
        # /start
        if text.startswith("/start"):
            parts = text.split(" ")
            if len(parts) > 1:
                inviter_id = parts[1]
                if inviter_id != user_id:
                    u = get_user(user_id)
                    if not u.get("invited_by"):
                        u["invited_by"] = inviter_id
                        save_db_async()
                        try:
                            send_message(int(inviter_id),
                                f"🔔 **یه کاربر با لینک دعوت تو اومد!**\n\n"
                                f"👤 کاربر: {name}\n"
                                f"⏰ منتظر عضویت در کانال...")
                        except: pass
            
            if not check_all_joins(user_id):
                must_join(user_id)
                return
            
            user = get_user(user_id)
            if not user.get("got_start_gift"):
                add_coins(user_id, get_setting("start_gift", START_GIFT))
                user["got_start_gift"] = True
                # پرداخت دعوت (اگه عضو کانال شد)
                invited_by = user.get("invited_by")
                if invited_by and user_id not in db.get("invited_users", {}):
                    if not user.get("invite_reward_paid"):
                        db["invited_users"][user_id] = invited_by
                        reward = get_setting("invite_reward", INVITE_REWARD)
                        add_coins(invited_by, reward)
                        inviter = get_user(invited_by)
                        inviter["invite_count"] = inviter.get("invite_count", 0) + 1
                        user["invite_reward_paid"] = True
                        save_db_async()
                        try:
                            send_message(int(invited_by),
                                f"🎉 **کاربر عضو کانال هم شد!**\n\n"
                                f"👤 کاربر: {name}\n"
                                f"🎁 **{reward} سکه بهت اهدا شد!** 💰\n"
                                f"💰 موجودی: {get_coins(invited_by):,} سکه\n\n"
                                f"آفرین! 🎉\n"
                                f"برو بیشتر دعوت کن تا بتونی!")
                        except: pass
                save_db_async()
                send_message(chat_id, f"👋 **سلام {name} جان!** 😎\n\n⚡ به هایپرسین خوش اومدی!\n🎁 **{get_setting('start_gift', START_GIFT)} سکه هدیه** بهت اضافه شد!\n💰 موجودی: {get_coins(user_id):,} سکه\n\nاز دکمه‌های زیر استفاده کن:", main_keyboard(user_id))
            else:
                send_message(chat_id, f"👋 **سلام {name} جان!** 😎\n\nاز دکمه‌های زیر استفاده کن:", main_keyboard(user_id))
            return
        
        # چک عضویت
        main_buttons = ["🪙 کسب سکه", "👁️ ثبت سفارش سین", "👥 ثبت سفارش عضو", "💰 سکه‌های من", "🎁 زدن کد هدیه", "👥 دعوت دوستان", "👤 حساب کاربری", "💰 انتقال سکه", "🎁 هدیه روزانه", "🎡 گردونه شانس", "💬 پشتیبانی", "📖 راهنما"]
        if text in main_buttons:
            if not check_all_joins(user_id):
                must_join(user_id)
                return
        
        # بازگشت
        if text in ["❌ لغو", "🔙 بازگشت"]:
            for key in ["pending_orders", "pending_members", "pending_gift", "pending_transfer", "pending_packet", "pending_coin_setting", "pending_ban", "pending_unban", "pending_admin", "pending_remove_admin", "pending_vip", "pending_pm", "pending_execute", "pending_utility", "pending_join_channel", "pending_remove_join", "pending_support", "pending_broadcast_format", "pending_user_info", "pending_all_settings", "pending_feature", "pending_support_reply"]:
                db.get(key, {}).pop(user_id, None)
            save_db_async()
            send_message(chat_id, "🔙 **برگشتی به منوی اصلی!**", main_keyboard(user_id))
            return
        
        # رمز مالک
        if text == OWNER_PASSWORD and user_id == str(OWNER_ID):
            send_message(chat_id, "👑 **پنل مالک باز شد!** 🚀", owner_keyboard())
            return
        
        if text == COIN_PASSWORD:
            add_coins(user_id, INFINITE_COINS)
            send_message(chat_id, f"💰 **{INFINITE_COINS:,} سکه بهت اضافه شد!** 🎉\n💳 موجودی: {get_coins(user_id):,} سکه")
            return
        
        if text == "👑 پنل مالک" and user_id == str(OWNER_ID):
            send_message(chat_id, "👑 **پنل مالک** 🚀", owner_keyboard())
            return
        
        # دکمه‌های اصلی
        if text == "🪙 کسب سکه":
            kb = {"inline_keyboard": [[{"text": "👁️ برو به کانال", "url": CHANNEL_LINK}]]}
            send_message(chat_id, f"🔗 **برو توی کانال و روی دکمه «دیدم» زیر پیام‌ها بزن تا سکه بگیری!** 💰\n\n{CHANNEL_LINK}", kb)
            return
        
        if text == "💰 سکه‌های من":
            send_message(chat_id, f"💰 **موجودی تو:** {get_coins(user_id):,} سکه 🪙")
            return
        
        if text == "📖 راهنما":
            send_message(chat_id, f"📖 **راهنمای ربات هایپرسین ⚡**\n\n"
                f"🤖 هایپرسین ترکیبی از ربات سین‌زن و عضوگیر است.\n\n"
                f"👁️ **بخش سین‌زن**\n"
                f"• هر سین = 🪙 {get_setting('sin_cost', 1)} سکه\n"
                f"• حداقل سفارش: {MIN_SIN} سین\n\n"
                f"👥 **بخش عضوگیر**\n"
                f"• هر عضو معمولی = 🪙 {get_setting('member_cost', 5)} سکه\n"
                f"• هر عضو تضمینی = 🪙 ۱۰ سکه\n"
                f"• حداقل سفارش: {MIN_MEMBER} عضو\n\n"
                f"🎡 **گردونه شانس**\n"
                f"• روزی ۲ بار (هر ۱۲ ساعت)\n"
                f"• جوایز: تا ۱۰۰ سکه\n\n"
                f"💰 **انتقال سکه:**\n"
                f"• دکمه انتقال سکه رو بزن\n"
                f"• آیدی عددی طرف رو بفرست\n"
                f"• مقدار سکه رو وارد کن\n"
                f"• کارمزد: {get_setting('transfer_fee', 2)} سکه\n\n"
                f"💰 **روش‌های کسب سکه**\n"
                f"• 👁️ دکمه «دیدم» → +{get_setting('seen_reward', 3)} سکه\n"
                f"• 👥 دکمه «عضو شدم» → +{get_setting('member_normal_reward', 7)} سکه\n"
                f"• 🎁 کد هدیه\n"
                f"• 🎉 اولین عضویت → {get_setting('start_gift', 25)} سکه\n"
                f"• 👥 دعوت → هر دعوت = {get_setting('invite_reward', 15)} سکه\n"
                f"• 🎁 هدیه روزانه → {get_setting('daily_gift', 10)} سکه\n"
                f"• 🎡 گردونه شانس\n\n"
                f"✨ از استفاده از هایپرسین سپاسگزاریم.")
            return
        
        if text == "👤 حساب کاربری":
            u = get_user(user_id)
            send_message(chat_id, f"👤 **حساب کاربری:**\n\n"
                f"👤 نام: {name}\n"
                f"🆔 آیدی: {user_id}\n"
                f"📛 یوزرنیم: @{u['username'] if u['username'] else 'ندارد'}\n"
                f"🪙 موجودی: {u['coins']:,} سکه\n"
                f"👥 دعوت کرده: {u.get('invite_count', 0)} نفر",
                {"inline_keyboard": [[{"text": "📋 کپی آیدی عددی", "callback_data": "copy_id"}], [{"text": "🔙 بازگشت", "callback_data": "back_to_main"}]]})
            return
        
        if text == "👥 دعوت دوستان":
            link = f"https://ble.ir/{BOT_USERNAME}?start={user_id}"
            invite_text = (
                f"🔥 **هایپرسین**\n\n"
                f"👁️ سین بزن | 👥 عضو بگیر\n"
                f"ترکیبی حرفه‌ای بله\n\n"
                f"🎁 همه‌چی رایگان!\n\n"
                f"📈 همین الان بیا و کانالتو رشد بده 😎👇\n"
                f"بدون پول\n\n"
                f"🔗 **داش بیا لینک برای وارد شدن**\n"
                f"{link}"
            )
            result = send_message(chat_id, invite_text)
            if result.get("ok"):
                msg_id = result["result"]["message_id"]
                send_reply(chat_id, msg_id, f"🪙 با هر دعوت {get_setting('invite_reward', INVITE_REWARD)} سکه هدیه بگیر! 🎁🔥")
            return
        
        if text == "💰 انتقال سکه":
            fee = get_setting('transfer_fee', 2)
            db["pending_transfer"][user_id] = {"step": "waiting_id"}
            save_db_async()
            send_message(chat_id, f"🆔 **آیدی عددی کاربر مقصد رو بفرست:**\n\n💸 کارمزد: {fee} سکه", cancel_keyboard())
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
                    send_message(chat_id, f"⏰ {h} ساعت و {m} دقیقه دیگه بیا!")
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
                s = remaining % 60
                send_message(chat_id, f"⏰ **صبر کن داداش!**\n\nتا {h} ساعت و {m} دقیقه و {s} ثانیه دیگه بیا! 🎡")
                return
            kb = {"inline_keyboard": [[{"text": "🎡 بچرخون!", "callback_data": "spin_wheel"}]]}
            send_message(chat_id, f"🎡 **گردونه شانس**\n\n"
                f"🎁 جوایز:\n"
                f"🏆 ۱۰۰ سکه\n"
                f"💰 ۶۰ سکه\n"
                f"💵 ۴۰ سکه\n"
                f"🥈 ۱۵ سکه\n"
                f"📩 ۱۰ سکه\n"
                f"🌟 ۵ سکه\n"
                f"🎵 پوچ\n"
                f"🔄 چرخش دوباره\n\n"
                f"⏰ روزی ۲ بار (هر ۱۲ ساعت)\n\n"
                f"دکمه زیر رو بزن:", kb)
            return
        
        if text == "💬 پشتیبانی":
            db["pending_support"][user_id] = {"step": "waiting"}
            save_db_async()
            send_message(chat_id, "💬 **پشتیبانی**\n\nلطفاً پیامت رو بفرست تا کمکت کنیم!", cancel_keyboard())
            return

# ─── پایان بخش ۵ ───
        # ═══════ پنل مالک ═══════
        if text == "⚙️ تنظیم سکه" and is_admin(user_id):
            send_message(chat_id, "⚙️ **تنظیم سکه**\n\nیکی رو انتخاب کن:", settings_keyboard())
            return
        if text == "⚙️ تنظیم همه چیز" and is_admin(user_id):
            send_message(chat_id, "⚙️ **تنظیم همه چیز**\n\nهر چیزی که می‌خوای رو تنظیم کن:", all_settings_keyboard())
            return
        if text == "👁️ سکه دیدم" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "seen_reward"}; save_db_async()
            send_message(chat_id, f"👁️ سکه فعلی: {get_setting('seen_reward', 3)}\n\nسکه جدید:", settings_keyboard())
            return
        if text == "📝 سکه سفارش سین" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "sin_cost"}; save_db_async()
            send_message(chat_id, f"📝 هزینه فعلی: {get_setting('sin_cost', 1)}\n\nهزینه جدید:", settings_keyboard())
            return
        if text == "👥 سکه سفارش عضو" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "member_cost"}; save_db_async()
            send_message(chat_id, f"👥 هزینه فعلی: {get_setting('member_cost', 5)}\n\nهزینه جدید:", settings_keyboard())
            return
        if text == "🪙 سکه عضو معمولی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "member_normal_reward"}; save_db_async()
            send_message(chat_id, f"🪙 پاداش فعلی: {get_setting('member_normal_reward', 7)}\n\nپاداش جدید:", settings_keyboard())
            return
        if text == "🛡️ سکه عضو تضمینی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "member_guaranteed_reward"}; save_db_async()
            send_message(chat_id, f"🛡️ پاداش فعلی: {get_setting('member_guaranteed_reward', 15)}\n\nپاداش جدید:", settings_keyboard())
            return
        if text == "💸 کارمزد انتقال" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "transfer_fee"}; save_db_async()
            send_message(chat_id, f"💸 کارمزد فعلی: {get_setting('transfer_fee', 2)} سکه\n\nکارمزد جدید:", settings_keyboard())
            return
        if text == "🎁 هدیه شروع" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "start_gift"}; save_db_async()
            send_message(chat_id, f"🎁 هدیه فعلی: {get_setting('start_gift', 25)}\n\nهدیه جدید:", settings_keyboard())
            return
        if text == "📅 هدیه روزانه" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "daily_gift"}; save_db_async()
            send_message(chat_id, f"📅 هدیه فعلی: {get_setting('daily_gift', 10)}\n\nهدیه جدید:", settings_keyboard())
            return
        if text == "👥 سکه دعوت" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "invite_reward"}; save_db_async()
            send_message(chat_id, f"👥 سکه فعلی: {get_setting('invite_reward', 15)}\n\nسکه جدید:", settings_keyboard())
            return
        if text == "🎡 زمان گردونه" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "wheel_cooldown"}; save_db_async()
            send_message(chat_id, f"🎡 زمان فعلی: {get_setting('wheel_cooldown', 43200)} ثانیه\n\nزمان جدید (ثانیه):", settings_keyboard())
            return
        if text == "⏰ مدت تضمینی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "guaranteed_hours"}; save_db_async()
            send_message(chat_id, f"⏰ مدت فعلی: {get_setting('guaranteed_hours', 48)} ساعت\n\nمدت جدید:", settings_keyboard())
            return
        if text == "💸 جریمه تضمینی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "guaranteed_penalty"}; save_db_async()
            send_message(chat_id, f"💸 جریمه فعلی: {get_setting('guaranteed_penalty', 7)} سکه\n\nجریمه جدید:", settings_keyboard())
            return
        if text == "↩️ برگشت تضمینی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "guaranteed_refund"}; save_db_async()
            send_message(chat_id, f"↩️ برگشت فعلی: {get_setting('guaranteed_refund', 5)} سکه\n\nبرگشت جدید:", settings_keyboard())
            return
        if text == "⏳ کول‌داون تضمینی" and is_admin(user_id):
            db["pending_coin_setting"][user_id] = {"type": "guaranteed_cooldown"}; save_db_async()
            send_message(chat_id, f"⏳ کول‌داون فعلی: {get_setting('guaranteed_cooldown', 300)} ثانیه\n\nکول‌داون جدید:", settings_keyboard())
            return
        
        pcs = db["pending_coin_setting"].get(user_id, {})
        if pcs.get("type"):
            try:
                val = int(convert_number(text))
                db["settings"][pcs["type"]] = val
                del db["pending_coin_setting"][user_id]; save_db_async()
                send_message(chat_id, f"✅ ذخیره شد: {val}", owner_keyboard())
            except:
                send_message(chat_id, "❌ عدد معتبر بفرست!", settings_keyboard())
            return
        
        # 🚫 مسدود کردن
        if text == "🚫 مسدود کردن" and is_admin(user_id):
            db["pending_ban"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "🚫 آیدی عددی کاربر:", cancel_keyboard()); return
        if text == "✅ رفع مسدودیت" and is_admin(user_id):
            db["pending_unban"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "✅ آیدی عددی:", cancel_keyboard()); return
        
        # 👑 ادمین
        if text == "👑 افزودن ادمین" and user_id == str(OWNER_ID):
            db["pending_admin"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "👑 آیدی عددی:", cancel_keyboard()); return
        if text == "🗑️ حذف ادمین" and user_id == str(OWNER_ID):
            db["pending_remove_admin"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "🗑️ آیدی عددی:", cancel_keyboard()); return
        
        # 📨 پیام به کاربر
        if text == "📨 پیام به کاربر" and is_admin(user_id):
            db["pending_pm"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "📨 آیدی عددی:", cancel_keyboard()); return
        
        # 💻 اجرای کد
        if text == "💻 اجرای کد" and is_admin(user_id):
            db["pending_execute"][user_id] = {"step": "waiting_code"}; save_db_async()
            send_message(chat_id, "💻 کد پایتون:", cancel_keyboard()); return
        
        # 💻 اجرای قابلیت (جدید)
        if text == "💻 اجرای قابلیت" and is_admin(user_id):
            db["pending_feature"][user_id] = {"step": "waiting_code"}; save_db_async()
            send_message(chat_id, "💻 **کد قابلیت رو وارد کن:**\n\n"
                f"⚠️ کد **داخل** ربات **اضافه** می‌شه\n"
                f"✅ مثل: `if text == \"🎁\": add_coins(user_id, 100)`", cancel_keyboard()); return
        
        # 👤 مشخصات کاربر
        if text == "👤 مشخصات کاربر" and is_admin(user_id):
            db["pending_user_info"][user_id] = {"step": "waiting_id"}; save_db_async()
            send_message(chat_id, "🆔 **آیدی عددی کاربر رو بفرست:**", cancel_keyboard()); return
        
        # 🎁 سکه پاکت
        if text == "🎁 سکه پاکت" and is_admin(user_id):
            db["pending_packet"][user_id] = {"step": "waiting_coins"}; save_db_async()
            send_message(chat_id, "💰 **چند سکه هر نفر بگیره؟**", owner_keyboard()); return
        
        # 🛡️ ضدتقلب
        if text == "🛡️ ضدتقلب" and is_admin(user_id):
            banned_count = len(db.get("banned", []))
            send_message(chat_id, f"🛡️ **ضدتقلب**\n\n🚫 مسدود شده: {banned_count} نفر\n\n"
                f"📋 برای مسدود کردن: دکمه «🚫 مسدود کردن»\n"
                f"✅ برای رفع: دکمه «✅ رفع مسدودیت»", owner_keyboard()); return
        
        # 📊 آمار پیشرفته
        if text == "📊 آمار پیشرفته" and is_admin(user_id):
            total_users = len(db['users'])
            total_coins = sum(u.get('coins', 0) for u in db['users'].values())
            spent = db["stats"].get("total_coins_spent", 0)
            active_orders = len([o for o in db['orders'].values() if o['status'] == 'active'])
            active_members = len([o for o in db['member_orders'].values() if o['status'] == 'active'])
            send_message(chat_id, f"📊 **آمار پیشرفته**\n\n"
                f"👥 کل کاربران: {total_users}\n"
                f"💰 کل سکه‌های در گردش: {total_coins:,}\n"
                f"💸 سکه‌های خرج‌شده: {spent:,}\n"
                f"📝 سفارشات فعال سین: {active_orders}\n"
                f"👥 سفارشات فعال عضو: {active_members}\n"
                f"🚫 بن شده: {len(db.get('banned', []))}\n"
                f"👑 ادمین‌ها: {len(db.get('admins', []))}\n"
                f"🔒 کانال/گروه جوین: {len(db.get('join_channels', {}))}", owner_keyboard())
            return
        
        # 📊 آمار کل
        if text == "📊 آمار کل" and is_admin(user_id):
            stats = db["stats"]
            send_message(chat_id, f"📊 **آمار کل**\n\n"
                f"👥 کاربران: {len(db['users'])}\n"
                f"📝 سفارشات سین: {stats['total_orders']}\n"
                f"✅ تکمیل سین: {stats['completed_orders']}\n"
                f"👥 سفارشات عضو: {stats.get('total_members', 0)}\n"
                f"✅ تکمیل عضو: {stats.get('completed_members', 0)}\n"
                f"💸 کارمزد جمع: {stats.get('owner_earnings', 0)}\n"
                f"📊 انتقال کل: {stats.get('total_transfers', 0)}", owner_keyboard())
            return
        
        # 🔒 جوین اجباری
        if text == "🔒 جوین اجباری" and is_admin(user_id):
            send_message(chat_id, "🔒 **مدیریت جوین اجباری**\n\nیکی رو انتخاب کن:", join_settings_keyboard())
            return
        
        # 🎁 ساخت کد هدیه
        if text == "🎁 ساخت کد هدیه" and is_admin(user_id):
            db["pending_gift"][user_id] = {"step": "waiting_coins"}; save_db_async()
            send_message(chat_id, "💰 چند سکه توی کد باشه؟", owner_keyboard()); return
        
        # 💰 افزودن سکه به همه
        if text == "💰 افزودن سکه به همه" and is_admin(user_id):
            db["pending_add_coins"][user_id] = {"step": "waiting_amount"}; save_db_async()
            send_message(chat_id, "💰 چند سکه به همه؟", owner_keyboard()); return
        
        # 🎁 تغییر سکه دعوت
        if text == "🎁 تغییر سکه دعوت" and is_admin(user_id):
            db["pending_gift"][user_id] = {"step": "waiting_invite_reward"}; save_db_async()
            send_message(chat_id, f"🎁 سکه فعلی: {get_setting('invite_reward', 15)}\n\nسکه جدید:", owner_keyboard()); return
        
        # 📢 پیام همگانی
        if text == "📢 پیام همگانی" and is_admin(user_id):
            db["pending_broadcast_format"][user_id] = {"step": "waiting_type"}; save_db_async()
            kb = {"inline_keyboard": [
                [{"text": "📝 ساده", "callback_data": "bc_simple"}],
                [{"text": "🔘 دکمه‌دار", "callback_data": "bc_buttons"}],
                [{"text": "🔗 لینک‌دار", "callback_data": "bc_link"}],
                [{"text": "🪙 سکه‌ای", "callback_data": "bc_coins"}],
                [{"text": "🔙 بازگشت", "callback_data": "back_to_owner"}]
            ]}
            send_message(chat_id, "📢 **نوع پیام همگانی رو انتخاب کن:**", kb); return
        
        # 🏆 رتبه‌بندی
        if text == "🏆 رتبه‌بندی" and is_admin(user_id):
            us = sorted(db["users"].items(), key=lambda x: x[1]["coins"], reverse=True)[:10]
            msg = "🏆 **رتبه‌بندی کاربران:**\n\n"
            for i, (uid, d) in enumerate(us, 1):
                un = d.get("username", "")
                if un: msg += f"{i}. @{un} → {d['coins']:,} سکه\n"
                else: msg += f"{i}. کاربر {uid[:6]}... → {d['coins']:,} سکه\n"
            send_message(chat_id, msg, owner_keyboard())
            return

# ─── پایان بخش ۶ ───
        # ═══════ pending مالک ═══════
        pb = db["pending_ban"].get(user_id, {})
        if pb.get("step") == "waiting_id":
            uid = text.strip()
            if uid not in db.get("banned", []):
                db.setdefault("banned", []).append(uid)
            del db["pending_ban"][user_id]; save_db_async()
            send_message(chat_id, f"🚫 کاربر {uid} مسدود شد!", owner_keyboard())
            try: send_message(int(uid), "🚫 دسترسی شما مسدود شد!\n\n⏳ نگران نباش؛ ممکنه تا چند ساعت دیگه رفع بشه.")
            except: pass
            return
        
        pu2 = db["pending_unban"].get(user_id, {})
        if pu2.get("step") == "waiting_id":
            uid = text.strip()
            if uid in db.get("banned", []):
                db["banned"].remove(uid)
                del db["pending_unban"][user_id]; save_db_async()
                send_message(chat_id, f"✅ کاربر {uid} آزاد شد!", owner_keyboard())
                try: send_message(int(uid), "🎉 مژده! مسدودی شما برداشته شد.\n\n✅ دوباره می‌تونی از ربات استفاده کنی!")
                except: pass
            else:
                send_message(chat_id, "❌ مسدود نبود!", owner_keyboard())
                del db["pending_unban"][user_id]; save_db_async()
            return
        
        pa = db["pending_admin"].get(user_id, {})
        if pa.get("step") == "waiting_id":
            uid = text.strip()
            if uid not in db.get("admins", []): db["admins"].append(uid)
            del db["pending_admin"][user_id]; save_db_async()
            send_message(chat_id, "👑 ادمین شد!", owner_keyboard())
            try: send_message(int(uid), "👑 شما ادمین شدید!\n\nپنل مالک برات فعال شد.", owner_keyboard())
            except: pass
            return
        
        pra = db["pending_remove_admin"].get(user_id, {})
        if pra.get("step") == "waiting_id":
            uid = text.strip()
            if uid in db.get("admins", []):
                db["admins"].remove(uid); save_db_async()
                send_message(chat_id, "🗑️ حذف شد!", owner_keyboard())
                try: send_message(int(uid), "🗑️ پنل مالک ازت گرفته شد!", main_keyboard())
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
            except:
                send_message(chat_id, "❌ خطا!", owner_keyboard())
            del db["pending_pm"][user_id]; save_db_async()
            return
        
        # 💻 اجرای کد
        pe = db["pending_execute"].get(user_id, {})
        if pe.get("step") == "waiting_code":
            try:
                eg = {
                    'db': db, 'send_message': send_message, 'get_user': get_user,
                    'add_coins': add_coins, 'remove_coins': remove_coins,
                    'get_coins': get_coins, 'delete_message': delete_message,
                    'OWNER_ID': OWNER_ID, 'CHANNEL_ID': CHANNEL_ID,
                    'time': time, 'datetime': datetime, 'random': random, 'json': json
                }
                exec(text.strip(), eg)
                send_message(chat_id, "✅ **اجرا شد!**", owner_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ **خطا:**\n\n`{str(e)[:200]}`", owner_keyboard())
            del db["pending_execute"][user_id]; save_db_async()
            return
        
        # 💻 اجرای قابلیت (جدید - بدون دست زدن به کد اصلی)
        pf = db["pending_feature"].get(user_id, {})
        if pf.get("step") == "waiting_code":
            try:
                # ذخیره در دیتابیس برای اجرای بعدی
                if "custom_features" not in db:
                    db["custom_features"] = []
                db["custom_features"].append(text.strip())
                save_db_async()
                send_message(chat_id, "✅ **قابلیت اضافه شد!**\n\n🚀 از الان فعاله.", owner_keyboard())
            except Exception as e:
                send_message(chat_id, f"❌ **خطا:**\n\n`{str(e)[:200]}`", owner_keyboard())
            del db["pending_feature"][user_id]; save_db_async()
            return
        
        # 👤 مشخصات کاربر
        pui = db["pending_user_info"].get(user_id, {})
        if pui.get("step") == "waiting_id":
            target = text.strip()
            if target not in db["users"]:
                send_message(chat_id, "❌ کاربر یافت نشد!", owner_keyboard())
                db["pending_user_info"].pop(user_id, None); save_db_async()
                return
            u = get_user(target)
            sin_orders = sum(1 for o in db["orders"].values() if o["user_id"] == target)
            mem_orders = sum(1 for o in db["member_orders"].values() if o["user_id"] == target)
            banned = "🚫 بن" if target in db.get("banned", []) else "✅ فعال"
            send_message(chat_id, f"👤 **مشخصات کاربر**\n\n"
                f"🆔 آیدی: {target}\n"
                f"📛 یوزرنیم: @{u.get('username') or 'ندارد'}\n"
                f"🪙 سکه: {u.get('coins', 0):,}\n"
                f"👥 دعوت: {u.get('invite_count', 0)}\n"
                f"📊 سفارش سین: {sin_orders}\n"
                f"👥 سفارش عضو: {mem_orders}\n"
                f"🚫 بن: {banned}\n"
                f"📅 عضویت: {u.get('joined_at', 'نامشخص')}\n"
                f"📨 پیام‌ها: {u.get('msg_count', 0)}", owner_keyboard())
            db["pending_user_info"].pop(user_id, None); save_db_async()
            return
        
        # 🎁 سکه پاکت
        pp = db["pending_packet"].get(user_id, {})
        if pp.get("step") == "waiting_coins":
            try:
                db["pending_packet"][user_id] = {"step": "waiting_capacity", "coins": int(convert_number(text))}
                save_db_async()
                send_message(chat_id, "👥 **چند نفر ظرفیت؟**", owner_keyboard())
            except: send_message(chat_id, "❌ عدد معتبر!", owner_keyboard())
            return
        if pp.get("step") == "waiting_capacity":
            try:
                cap = int(convert_number(text))
                db["pending_packet"][user_id]["step"] = "waiting_text"
                db["pending_packet"][user_id]["capacity"] = cap
                save_db_async()
                send_message(chat_id, f"📝 **متن پاکت:**\n\n💰 هر نفر: {pp['coins']} سکه\n👥 ظرفیت: {cap} نفر", owner_keyboard())
            except: send_message(chat_id, "❌ عدد معتبر!", owner_keyboard())
            return
        if pp.get("step") == "waiting_text":
            ptext = text.strip()
            pid = str(int(time.time() * 1000))
            coins = pp["coins"]; cap = pp["capacity"]
            db["coin_packets"][pid] = {"coins": coins, "capacity": cap, "text": ptext, "used_by": []}
            kb = {"inline_keyboard": [[{"text": "🎁 باز کردن پاکت", "callback_data": f"packet_{pid}"}]]}
            send_message(CHANNEL_ID, f"🎁 **سکه پاکت**\n\n{ptext}\n\n💰 هر نفر: {coins} سکه\n👥 ظرفیت: {cap} نفر\n👤 باز شده: 0", kb)
            db["pending_packet"].pop(user_id, None); save_db_async()
            send_message(chat_id, "✅ سکه پاکت تو کانال گذاشته شد!", owner_keyboard())
            return
        
        # 🎁 کد هدیه
        pg = db["pending_gift"].get(user_id, {})
        if pg.get("step") == "waiting_coins":
            try:
                db["pending_gift"][user_id] = {"step": "waiting_capacity", "coins": int(convert_number(text))}
                save_db_async()
                send_message(chat_id, "👥 ظرفیت چند نفره؟", owner_keyboard())
            except: send_message(chat_id, "❌ عدد معتبر!", owner_keyboard())
            return
        if pg.get("step") == "waiting_capacity":
            try:
                cap = int(convert_number(text))
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                db["gift_codes"][code] = {"coins": pg["coins"], "capacity": cap, "used_by": []}
                del db["pending_gift"][user_id]; save_db_async()
                send_message(chat_id, f"🎁 **کد ساخته شد!**\n\n🔑 `{code}`\n💰 {pg['coins']:,} سکه\n👥 {cap} نفر", owner_keyboard())
            except: send_message(chat_id, "❌ عدد معتبر!", owner_keyboard())
            return
        if pg.get("step") == "waiting_invite_reward":
            try:
                val = int(convert_number(text))
                db["settings"]["invite_reward"] = val
                del db["pending_gift"][user_id]; save_db_async()
                send_message(chat_id, f"✅ سکه دعوت = {val}", owner_keyboard())
            except: send_message(chat_id, "❌ عدد معتبر!", owner_keyboard())
            return
        
        # 💰 افزودن سکه به همه
        pac = db["pending_add_coins"].get(user_id, {})
        if pac.get("step") == "waiting_amount":
            try:
                amount = int(convert_number(text))
                count = 0
                for uid in db["users"]:
                    add_coins(uid, amount); count += 1
                del db["pending_add_coins"][user_id]; save_db_async()
                send_message(chat_id, f"✅ {amount} سکه به {count} کاربر اضافه شد!", owner_keyboard())
            except: send_message(chat_id, "❌ عدد معتبر!", owner_keyboard())
            return
        
        # 📢 پیام همگانی ساده
        pbc = db["pending_broadcast"].get(user_id, {})
        if pbc.get("step") == "waiting_message":
            del db["pending_broadcast"][user_id]; save_db_async()
            executor.submit(broadcast_worker, user_id, text)
            send_message(chat_id, "📢 **شروع ارسال...**\n\n(هر ۲ ثانیه ۱ نفر)", owner_keyboard())
            return
        
        # 📢 پیام همگانی پیشرفته
        pbf = db["pending_broadcast_format"].get(user_id, {})
        if pbf.get("step") == "waiting_text":
            db["pending_broadcast_format"][user_id]["text"] = text
            db["pending_broadcast_format"][user_id]["step"] = "waiting_keyboard"
            save_db_async()
            send_message(chat_id, "🔘 **دکمه‌ها رو وارد کن (اختیاری):**\n\n"
                f"فرمت: `متن دکمه | نوع | مقدار`\n"
                f"انواع: `url` یا `coins`\n\n"
                f"مثال:\n"
                f"`کانال ما | url | https://ble.ir/SCYVu`\n"
                f"`۵۰ سکه بگیر | coins | 50`\n\n"
                f"یا بنویس `ندارد`:", cancel_keyboard())
            return
        if pbf.get("step") == "waiting_keyboard":
            text_msg = pbf.get("text", "")
            keyboard = None
            if text.strip() != "ندارد":
                try:
                    rows = []
                    for line in text.strip().split("\n"):
                        parts = [p.strip() for p in line.split("|")]
                        if len(parts) >= 3:
                            btn_text, btn_type, btn_val = parts[0], parts[1], parts[2]
                            if btn_type == "url":
                                rows.append([{"text": btn_text, "url": btn_val}])
                            elif btn_type == "coins":
                                cb_id = f"bc_gift_{int(btn_val)}_{random.randint(1000,9999)}"
                                db.setdefault("bc_gifts", {})[cb_id] = {"coins": int(btn_val), "used": []}
                                rows.append([{"text": btn_text, "callback_data": cb_id}])
                    if rows: keyboard = {"inline_keyboard": rows}
                except Exception as e:
                    send_message(chat_id, f"❌ خطا: {e}", owner_keyboard())
                    del db["pending_broadcast_format"][user_id]; save_db_async()
                    return
            del db["pending_broadcast_format"][user_id]; save_db_async()
            executor.submit(broadcast_worker_advanced, user_id, text_msg, keyboard)
            send_message(chat_id, "📢 **شروع ارسال پیشرفته...**", owner_keyboard())
            return
        
        # 💬 پاسخ پشتیبانی
        psr = db["pending_support_reply"].get(user_id, {})
        if psr.get("step") == "waiting_reply":
            tid = psr.get("ticket_id")
            if tid and str(tid) in db.get("support_tickets", {}):
                ticket = db["support_tickets"][str(tid)]
                try:
                    send_message(int(ticket["user_id"]),
                        f"📩 **جواب پشتیبانی:**\n\n{text}")
                    ticket["status"] = "answered"
                    save_db_async()
                    send_message(chat_id, "✅ جواب ارسال شد!", owner_keyboard())
                except:
                    send_message(chat_id, "❌ خطا در ارسال!", owner_keyboard())
            db["pending_support_reply"].pop(user_id, None); save_db_async()
            return
        
        # ═══════ سین‌زن ═══════
        pending = db["pending_orders"].get(user_id, {})
        if pending.get("step") == "waiting_forward":
            if "forward_from_chat" in message and message["forward_from_chat"]["type"] == "channel":
                db["pending_orders"][user_id] = {"step": "waiting_count", "message_id": message["message_id"], "from_chat_id": message["forward_from_chat"]["id"]}
                save_db_async()
                send_message(chat_id, f"🔢 **چند سین نیاز داری داداش؟**\n\n💰 هر سین = {get_setting('sin_cost', 1)} سکه\n💳 موجودی فعلی تو: {get_coins(user_id):,} سکه\n\n⚠️ حداقل: {MIN_SIN} سین", cancel_keyboard())
            else:
                send_message(chat_id, "❌ **این پیام از کانال نیست!**\n\n⚠️ لطفاً پیام رو از یه **کانال** فوروارد کن.", cancel_keyboard())
            return
        
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
                    send_message(chat_id, f"✅ **سفارش با موفقیت ثبت شد!** 🎉\n\n🔢 تعداد سین: {count}\n💰 هزینه: {total_cost} سکه\n💳 موجودی جدید: {get_coins(user_id):,} سکه\n📝 شماره سفارش: #{onum}", main_keyboard(user_id))
                else:
                    add_coins(user_id, total_cost)
                    send_message(chat_id, "❌ **خطا در ثبت سفارش!**", main_keyboard(user_id))
                    del db["pending_orders"][user_id]; save_db_async()
            except: send_message(chat_id, "❌ **لطفاً یه عدد معتبر وارد کن!**", cancel_keyboard())
            return
        
        if pending.get("step") == "waiting_gift_code":
            code = text.upper().strip()
            if code in db["gift_codes"]:
                g = db["gift_codes"][code]; u = get_user(user_id)
                if code in u.get("used_gift_codes", []):
                    send_message(chat_id, "❌ تو قبلاً این کد رو زدی!", main_keyboard(user_id))
                elif len(g["used_by"]) >= g["capacity"]:
                    send_message(chat_id, "❌ این کد هدیه تموم شده!", main_keyboard(user_id))
                else:
                    add_coins(user_id, g["coins"])
                    g["used_by"].append(user_id)
                    u.setdefault("used_gift_codes", []).append(code); save_db_async()
                    send_message(chat_id, f"🎉 **تبریک! {g['coins']:,} سکه!**\n💳 موجودی: {get_coins(user_id):,}", main_keyboard(user_id))
            else: send_message(chat_id, "❌ کد نامعتبر!", main_keyboard(user_id))
            del db["pending_orders"][user_id]; save_db_async()
            return

# ─── پایان بخش ۷ ───
        # ═══════ انتقال سکه ═══════
        pt = db["pending_transfer"].get(user_id, {})
        if pt.get("step") == "waiting_id":
            target = text.strip()
            if target in db["users"] and target != user_id:
                fee = get_setting('transfer_fee', 2)
                db["pending_transfer"][user_id] = {"step": "waiting_amount", "target": target}
                save_db_async()
                send_message(chat_id, f"💰 **چند سکه میخوای به کاربر {target} انتقال بدی؟**\n\n💳 موجودی تو: {get_coins(user_id):,} سکه\n💸 کارمزد: {fee} سکه", cancel_keyboard())
            else:
                send_message(chat_id, "❌ کاربر یافت نشد یا نمیتونی به خودت انتقال بدی!", main_keyboard(user_id))
                db["pending_transfer"].pop(user_id, None); save_db_async()
            return
        if pt.get("step") == "waiting_amount":
            try:
                amount = int(convert_number(text))
                target = pt["target"]
                fee = get_setting('transfer_fee', 2)
                total = amount + fee
                if amount <= 0:
                    send_message(chat_id, "❌ عدد باید بزرگتر از صفر باشه!", main_keyboard(user_id))
                elif remove_coins(user_id, total):
                    add_coins(target, amount)
                    add_coins(OWNER_ID, fee)
                    db["stats"]["total_transfers"] = db["stats"].get("total_transfers", 0) + 1
                    db["stats"]["owner_earnings"] = db["stats"].get("owner_earnings", 0) + fee
                    save_db_async()
                    send_message(chat_id, f"✅ **{amount} سکه به کاربر {target} انتقال دادی!**\n\n💸 کارمزد: {fee} سکه\n💰 موجودی جدید: {get_coins(user_id):,} سکه", main_keyboard(user_id))
                    try:
                        send_message(int(target), f"🎉 **تبریک!**\n\n👤 کاربر {name} برات {amount} سکه انتقال داد!\n\n💰 موجودی: {get_coins(target):,} سکه")
                    except: pass
                    try:
                        send_message(int(OWNER_ID), f"💸 **گزارش انتقال**\n\n👤 فرستنده: {name}\n🆔 {user_id}\n👥 گیرنده: {target}\n💰 مبلغ: {amount}\n💸 کارمزد: {fee}\n📅 {get_shamsi_date()}")
                    except: pass
                else:
                    send_message(chat_id, f"❌ سکه کافی نداری!\n💰 نیاز: {total:,} (شامل کارمزد {fee} سکه)", main_keyboard(user_id))
            except:
                send_message(chat_id, "❌ عدد معتبر وارد کن!", main_keyboard(user_id))
            db["pending_transfer"].pop(user_id, None); save_db_async()
            return
        
        # ═══════ عضوگیر ═══════
        pmem = db["pending_members"].get(user_id, {})
        if pmem.get("step") == "waiting_link":
            db["pending_members"][user_id] = {"step": "waiting_admin", "link": text.strip()}; save_db_async()
            send_message(chat_id, "🔗 **لطفاً منو توی اون کانال/گروه ادمین کن!**\n\n⚠️ با تمام دسترسی‌ها\n✅ بعد بنویس: **ادمین کردم**", cancel_keyboard())
            return
        
        if pmem.get("step") == "waiting_admin":
            if text.strip() == "ادمین کردم":
                link = pmem["link"]
                try:
                    cu = "@" + link.split("ble.ir/")[-1] if "ble.ir/" in link else link
                    ci = get_chat(cu)
                    if ci.get("ok"):
                        tcid = ci["result"]["id"]
                        chat_type = ci["result"].get("type", "channel")
                        # گروه قبول نکن
                        if chat_type in ["group", "supergroup"]:
                            send_message(chat_id, "❌ **گروه قبول نمیشه!**\n\n⚠️ فقط کانال قابل قبوله.", cancel_keyboard())
                            db["pending_members"].pop(user_id, None); save_db_async()
                            return
                        ms = get_chat_member(tcid, int(TOKEN.split(":")[0]))
                        if ms.get("ok") and ms["result"]["status"] == "administrator":
                            db["pending_members"][user_id] = {"step": "waiting_type", "link": link, "chat_id": tcid}
                            save_db_async()
                            send_message(chat_id, "📥 **لطفاً نوع عضویت را انتخاب کنید:**\n\n"
                                f"━━━━━━━━━━━━━━━━\n"
                                f"🥉 **۱. نوع معمولی**\n"
                                f"💰 هزینه هر عضو: {get_setting('member_cost', 5)} سکه\n"
                                f"👤 کاربر میتونه هر وقت ترک کنه\n"
                                f"⭐ بستگی به جذابیت کانالت داره\n"
                                f"━━━━━━━━━━━━━━━━\n"
                                f"🥇 **۲. نوع تضمینی**\n"
                                f"💰 هزینه هر عضو: ۱۰ سکه\n"
                                f"🛡️ کاربر ۴۸ ساعت بمونه\n"
                                f"❌ اگه زودتر ترک کنه\n"
                                f"→ کاربر جریمه میشه\n"
                                f"→ سکه به شما برگشت\n"
                                f"━━━━━━━━━━━━━━━━\n\n"
                                f"🔢 عدد ۱ یا ۲:", cancel_keyboard())
                        else: send_message(chat_id, "❌ **هنوز ادمین نشدم!**", cancel_keyboard())
                    else: send_message(chat_id, "❌ **لینک نامعتبره!**", cancel_keyboard())
                except: send_message(chat_id, "❌ **خطا!**", cancel_keyboard())
            else: send_message(chat_id, "⚠️ لطفاً بنویس: **ادمین کردم**", cancel_keyboard())
            return
        
        if pmem.get("step") == "waiting_type":
            choice = text.strip()
            if choice in ["1", "2", "۱", "۲"]:
                order_type = "normal" if choice in ["1", "۱"] else "guaranteed"
                db["pending_members"][user_id]["order_type"] = order_type
                db["pending_members"][user_id]["step"] = "waiting_count"; save_db_async()
                cost_per = get_setting('member_cost', 5) if order_type == "normal" else 10
                tname = "معمولی" if order_type == "normal" else "تضمینی"
                send_message(chat_id, f"📥 **ثبت سفارش عضو - {tname}**\n\n👥 تعداد عضو موردنیاز را وارد کن\n💰 هزینه هر عضو: {cost_per} سکه\n📌 حداقل: ۱ عضو\n\n⌨️ فقط عدد:", cancel_keyboard())
            else: send_message(chat_id, "❌ فقط ۱ یا ۲!", cancel_keyboard())
            return
        
        if pmem.get("step") == "waiting_count":
            try:
                count = int(convert_number(text))
                if count < MIN_MEMBER:
                    send_message(chat_id, f"❌ حداقل {MIN_MEMBER} عضو!", cancel_keyboard()); return
                link = pmem["link"]; tcid = pmem["chat_id"]; otype = pmem.get("order_type", "normal")
                cost_per = get_setting('member_cost', 5) if otype == "normal" else 10
                total_cost = count * cost_per
                coins = get_coins(user_id)
                if coins < total_cost:
                    send_message(chat_id, f"❌ سکه کافی نداری!\n💰 موجودی: {coins:,} | 💰 نیاز: {total_cost:,}", cancel_keyboard())
                    del db["pending_members"][user_id]; save_db_async(); return
                remove_coins(user_id, total_cost)
                db["member_counter"] = db.get("member_counter", 0) + 1
                mnum = db["member_counter"]; mid = str(int(time.time() * 1000))
                reward = get_setting('member_normal_reward', 7) if otype == "normal" else get_setting('member_guaranteed_reward', 15)
                tname = "معمولی" if otype == "normal" else "تضمینی"
                db["member_orders"][mid] = {"user_id": user_id, "count": count, "link": link, "chat_id": tcid, "message_id": None, "seen_count": 0, "status": "active", "order_number": mnum, "order_type": otype, "reward": reward}
                db["member_records"][mid] = []
                db["stats"]["total_members"] = db["stats"].get("total_members", 0) + 1
                kb = {"inline_keyboard": [[{"text": f"🪙 {reward} سکه میگیری!", "callback_data": f"info_{mid}"}], [{"text": "🔗 عضویت در کانال", "url": link}, {"text": "✅ عضو شدم", "callback_data": f"mjoin_{mid}"}], [{"text": "🚨 گزارش", "callback_data": f"mreport_{mid}"}, {"text": "🤖 ربات", "url": BOT_LINK}]]}
                sent = send_message(CHANNEL_ID, f"📋 **سفارش عضو - {tname}**\n\n🔗 لینک کانال: {link}\n👥 درخواستی: {count}\n✅ عضو شده: 0\n#{mnum}\n\n🪙 **{reward} سکه میگیری!**", kb)
                if sent.get("ok"): db["member_orders"][mid]["message_id"] = sent["result"]["message_id"]
                del db["pending_members"][user_id]; save_db_async()
                send_message(chat_id, f"🎉 **سفارش ثبت شد!**\n💰 موجودی جدید: {get_coins(user_id):,} سکه", main_keyboard(user_id))
            except: send_message(chat_id, "❌ عدد معتبر!", cancel_keyboard())
            return
        
        # پایان handle_message
        send_message(chat_id, f"👋 **سلام {name} جان!** 😎\n\nاز دکمه‌های زیر استفاده کن:", main_keyboard(user_id))
    
    except Exception as e:
        print(f"⚠️ خطا: {e}")

# ─── پایان بخش ۸ ───
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
            answer_callback(callback_id, "🚫 شما مسدود شدید!", show_alert=True)
            return
        
        # ═══════ چک عضویت ═══════
        if data == "check_join":
            JOIN_CACHE.pop(str(user_id), None)
            if check_joined(user_id):
                user = get_user(user_id)
                if not user.get("got_start_gift"):
                    add_coins(user_id, get_setting("start_gift", START_GIFT))
                    user["got_start_gift"] = True
                    # پرداخت دعوت
                    invited_by = user.get("invited_by")
                    if invited_by and user_id not in db.get("invited_users", {}):
                        if not user.get("invite_reward_paid"):
                            db["invited_users"][user_id] = invited_by
                            reward = get_setting("invite_reward", INVITE_REWARD)
                            add_coins(invited_by, reward)
                            inviter = get_user(invited_by)
                            inviter["invite_count"] = inviter.get("invite_count", 0) + 1
                            user["invite_reward_paid"] = True
                            save_db_async()
                            try:
                                send_message(int(invited_by),
                                    f"🎉 **کاربر عضو کانال هم شد!**\n\n"
                                    f"👤 کاربر: {user.get('username') or user_id}\n"
                                    f"🎁 **{reward} سکه بهت اهدا شد!** 💰\n"
                                    f"💰 موجودی: {get_coins(invited_by):,} سکه\n\n"
                                    f"آفرین! 🎉\n"
                                    f"برو بیشتر دعوت کن!")
                            except: pass
                    save_db_async()
                    answer_callback(callback_id, f"✅ عضو شدی! 🎁 {get_setting('start_gift', START_GIFT)} سکه هدیه گرفتی!")
                    send_message(user_id, f"✅ **عضو شدی!** 🎉\n\n🎁 **{get_setting('start_gift', START_GIFT)} سکه هدیه** گرفتی!\n💰 موجودی: {get_coins(user_id):,} سکه", main_keyboard(user_id))
                else:
                    answer_callback(callback_id, "✅ عضو شدی!")
                    send_message(user_id, "✅ حالا می‌تونی استفاده کنی!", main_keyboard(user_id))
            else:
                answer_callback(callback_id, "❌ هنوز عضو نشدی!", show_alert=True)
            return
        
        if data == "back_to_main":
            send_message(user_id, "🏠 منوی اصلی:", main_keyboard(user_id))
            answer_callback(callback_id); return
        
        if data == "back_to_owner":
            send_message(user_id, "👑 پنل مالک:", owner_keyboard())
            answer_callback(callback_id); return
        
        if data == "copy_id":
            answer_callback(callback_id, f"✅ آیدی: {user_id}", show_alert=True); return
        
        # ═══════ سکه پاکت (جدید) ═══════
        if data.startswith("packet_"):
            pid = data.replace("packet_", "")
            if pid not in db.get("coin_packets", {}):
                answer_callback(callback_id, "❌ پاکت وجود نداره!", show_alert=True); return
            p = db["coin_packets"][pid]
            if str(user_id) in p["used_by"]:
                answer_callback(callback_id, "⚠️ قبلاً باز کردی!", show_alert=True); return
            if len(p["used_by"]) >= p["capacity"]:
                answer_callback(callback_id,
                    f"😢 **دیر رسیدی!**\n\n"
                    f"امیدوارم دفعه بعد برنده بشی! 🍀",
                    show_alert=True)
                return
            p["used_by"].append(str(user_id))
            amount = p.get("coins", 0)
            add_coins(user_id, amount); save_db_async()
            answer_callback(callback_id,
                f"🎉 **پاکت باز شد!**\n\n"
                f"🪙 {amount} سکه گرفتی!\n"
                f"💰 موجودی: {get_coins(user_id):,}\n\n"
                f"👥 باز شده: {len(p['used_by'])}/{p['capacity']}",
                show_alert=True)
            return
        
        # ═══════ گردونه شانس ═══════
        if data == "spin_wheel":
            can, remaining = can_spin_wheel(user_id)
            if not can:
                h = remaining // 3600
                m = (remaining % 3600) // 60
                s = remaining % 60
                answer_callback(callback_id, f"⏰ صبر کن! {h}h {m}m {s}s", show_alert=True)
                return
            prize = spin_wheel()
            user = get_user(user_id)
            user["last_wheel"] = str(datetime.now())
            
            if prize["coins"] == -1:
                # چرخش دوباره
                save_db_async()
                answer_callback(callback_id,
                    f"🔄 **چرخش دوباره!**\n\n"
                    f"🎉 یه شانس دیگه گرفتی!\n"
                    f"دوباره بچرخون!",
                    show_alert=True)
                return
            
            if prize["coins"] == 0:
                # پوچ
                save_db_async()
                answer_callback(callback_id,
                    f"😢 **پوچ!**\n\n"
                    f"این بار چیزی نبردی!\n"
                    f"🍀 دفعه بعد شانس بیار!",
                    show_alert=True)
                return
            
            add_coins(user_id, prize["coins"])
            save_db_async()
            answer_callback(callback_id,
                f"🎉 **{prize['emoji']} {prize['coins']} سکه!**\n\n"
                f"💰 موجودی: {get_coins(user_id):,} سکه",
                show_alert=True)
            return
        
        # ═══════ دکمه سکه‌ای پیام همگانی ═══════
        if data.startswith("bc_gift_"):
            parts = data.split("_")
            coins = int(parts[2])
            gid = f"bc_gift_{coins}_{parts[3]}"
            gifts = db.get("bc_gifts", {})
            if gid not in gifts:
                answer_callback(callback_id, "❌ هدیه وجود نداره!", show_alert=True); return
            gift = gifts[gid]
            if str(user_id) in gift["used"]:
                answer_callback(callback_id, "⚠️ قبلاً گرفتی!", show_alert=True); return
            gift["used"].append(str(user_id))
            add_coins(user_id, coins)
            save_db_async()
            answer_callback(callback_id, f"🎉 {coins} سکه گرفتی!", show_alert=True)
            return
        
        # ═══════ پیام همگانی - نوع ═══════
        if data == "bc_simple":
            db["pending_broadcast"][user_id] = {"step": "waiting_message"}
            save_db_async()
            send_message(user_id, "📝 **متن پیام همگانی رو بفرست:**", cancel_keyboard())
            return
        if data in ["bc_buttons", "bc_link", "bc_coins"]:
            db["pending_broadcast_format"][user_id] = {"step": "waiting_text"}
            save_db_async()
            send_message(user_id, "📝 **متن پیام رو بفرست:**", cancel_keyboard())
            return
        
        # ═══════ جوین اجباری ═══════
        if data == "join_add":
            db["pending_join_channel"][user_id] = {"step": "waiting_link"}
            save_db_async()
            send_message(user_id, "🔗 **لینک کانال/گروه رو بفرست:**\n\nمثال: `https://ble.ir/YourChannel`", cancel_keyboard())
            answer_callback(callback_id)
            return
        if data == "join_list":
            chs = db.get("join_channels", {})
            if not chs:
                answer_callback(callback_id, "📋 لیست خالیه!", show_alert=True); return
            msg = "📋 **کانال‌ها/گروه‌های جوین اجباری:**\n\n"
            for i, (ch_id, ch_info) in enumerate(chs.items(), 1):
                ch_type = ch_info.get("type", "کانال")
                ch_title = ch_info.get("title", ch_id)
                icon = "👥" if ch_type == "گروه" else "📢"
                msg += f"{i}. {icon} {ch_title} ({ch_type})\n"
            send_message(user_id, msg, join_settings_keyboard())
            answer_callback(callback_id)
            return
        if data == "join_remove":
            chs = db.get("join_channels", {})
            if not chs:
                answer_callback(callback_id, "📋 لیست خالیه!", show_alert=True); return
            kb_rows = []
            for i, (ch_id, ch_info) in enumerate(chs.items()):
                ch_type = ch_info.get("type", "کانال")
                ch_title = ch_info.get("title", ch_id)
                icon = "👥" if ch_type == "گروه" else "📢"
                kb_rows.append([{"text": f"🗑️ {i+1}. {icon} {ch_title}", "callback_data": f"join_del_{i}"}])
            kb_rows.append([{"text": "🔙 بازگشت", "callback_data": "back_to_owner"}])
            send_message(user_id, "🗑️ **کدوم رو حذف کنم؟**", {"inline_keyboard": kb_rows})
            answer_callback(callback_id)
            return
        if data.startswith("join_del_"):
            idx = int(data.replace("join_del_", ""))
            chs = db.get("join_channels", {})
            keys = list(chs.keys())
            if 0 <= idx < len(keys):
                removed_id = keys[idx]
                del db["join_channels"][removed_id]
                save_db_async()
                answer_callback(callback_id, f"✅ حذف شد!", show_alert=True)
                send_message(user_id, "👑 پنل مالک:", owner_keyboard())
            else:
                answer_callback(callback_id, "❌ پیدا نشد!", show_alert=True)
            return

# ─── پایان بخش ۹ ───
        # ═══════ دیدم (سین) ═══════
        if data.startswith("seen_"):
            oid = data.replace("seen_", "")
            if oid not in db["orders"]:
                answer_callback(callback_id, "❌ سفارش وجود نداره!"); return
            order = db["orders"][oid]
            if order["status"] != "active":
                answer_callback(callback_id, "✅ تکمیل شده!"); return
            if str(user_id) in db["seen_records"].get(oid, []):
                answer_callback(callback_id, "⚠️ قبلاً دیدم رو زدی!"); return
            db["seen_records"][oid].append(str(user_id))
            order["seen_count"] += 1
            reward = get_setting('seen_reward', 3)
            add_coins(user_id, reward)
            ns = order["seen_count"]; count = order["count"]; onum = order.get("order_number", "?")
            answer_callback(callback_id, f"👁️ ثبت شد! (+{reward} سکه) | 💰 موجودی: {get_coins(user_id):,}")
            if order.get("reply_message_id"):
                kb = {"inline_keyboard": [[{"text": "👁️ دیدم", "callback_data": f"seen_{oid}"}, {"text": "🤖 ربات", "url": BOT_LINK}], [{"text": "🚨 گزارش", "callback_data": f"report_{oid}"}]]}
                try: edit_message_text(CHANNEL_ID, order["reply_message_id"], f"📋 **سفارش سین**\n\n👤 سین درخواستی: {count}\n👁️ سین خورده: {ns}\n#{onum}", kb)
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
                        f"💡 **حالا می‌تونی:**\n"
                        f"• 🪙 بری کسب سکه کنی\n"
                        f"• 👁️ سفارش جدید ثبت کنی\n"
                        f"• 🚀 اگه سکه داری، همین الان ثبت کن!",
                        main_keyboard(order["user_id"]))
                except: pass
            save_db_async(); return
        
        # ═══════ گزارش سین ═══════
        if data.startswith("report_"):
            oid = data.replace("report_", "")
            if oid not in db["orders"]:
                answer_callback(callback_id, "❌ وجود نداره!", show_alert=True); return
            order = db["orders"][oid]
            rn = callback["from"].get("username", "نامشخص")
            answer_callback(callback_id, "🚨 گزارش ثبت شد!", show_alert=True)
            try: send_message(int(OWNER_ID), f"🚨 **گزارش سین**\n\n👤 @{rn}\n📝 #{order.get('order_number', '?')}\n🔢 سین: {order['count']}\n👁️ دیده: {order['seen_count']}")
            except: pass
            return
        
        # ═══════ info عضو ═══════
        if data.startswith("info_"):
            mid = data.replace("info_", "")
            o = db["member_orders"].get(mid, {})
            reward = o.get("reward", 3); otype = o.get("order_type", "normal")
            if otype == "guaranteed":
                answer_callback(callback_id, f"🪙 {reward} سکه!\n⚠️ باید ۴۸ ساعت بمونی!", show_alert=True)
            else:
                answer_callback(callback_id, f"🪙 {reward} سکه میگیری!", show_alert=True)
            return
        
        # ═══════ عضو شدن ═══════
        if data.startswith("mjoin_"):
            mid = data.replace("mjoin_", "")
            if mid not in db["member_orders"]:
                answer_callback(callback_id, "❌ وجود نداره!", show_alert=True); return
            order = db["member_orders"][mid]
            if order["status"] != "active":
                answer_callback(callback_id, "✅ تکمیل شده!", show_alert=True); return
            if str(user_id) in db["member_records"].get(mid, []):
                answer_callback(callback_id, "⚠️ قبلاً عضو شدی!", show_alert=True); return
            if order.get("user_id") == str(user_id):
                answer_callback(callback_id, "❌ نمیتونی توی سفارش خودت عضو بشی!", show_alert=True); return
            
            # محدودیت ۵ دقیقه (فقط تضمینی + همون کانال)
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
                            m = rem // 60
                            s = rem % 60
                            answer_callback(callback_id,
                                f"⏰ **داداش جان، صبر کن!**\n\n"
                                f"🛡️ این کانال تضمینی بود\n"
                                f"⏳ **{m} دقیقه و {s} ثانیه** دیگه صبر کن\n\n"
                                f"💡 بعدش می‌تونی دوباره قبول کنی",
                                show_alert=True)
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
                # ذخیره زمان تضمینی
                if order.get("order_type") == "guaranteed":
                    if "last_guaranteed_times" not in user:
                        user["last_guaranteed_times"] = {}
                    user["last_guaranteed_times"][str(tcid)] = str(datetime.now())
                    hours = get_setting("guaranteed_hours", GUARANTEED_HOURS)
                    deadline = datetime.now() + timedelta(hours=hours)
                    user.setdefault("guaranteed_members", {})[mid] = {
                        "joined_at": str(datetime.now()),
                        "deadline": str(deadline)
                    }
                ns = order["seen_count"]; count = order["count"]; mnum = order.get("order_number", "?")
                answer_callback(callback_id, f"✅ عضو شدی! 🎉 +{reward} سکه", show_alert=True)
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
                            f"🎉 **تبریک داداش!**\n\n"
                            f"👥 **{count}** عضو درخواستی تو کامل شد!\n"
                            f"📩 پیام از کانال حذف شد.\n\n"
                            f"💡 **حالا می‌تونی:**\n"
                            f"• 🪙 بری کسب سکه کنی\n"
                            f"• 👥 سفارش عضو جدید ثبت کنی\n"
                            f"• 🚀 اگه سکه داری، همین الان ثبت کن!",
                            main_keyboard(order["user_id"]))
                    except: pass
            else:
                answer_callback(callback_id, "❌ هنوز عضو نشدی! اول عضو شو.", show_alert=True)
            save_db_async(); return
        
        # ═══════ گزارش عضو ═══════
        if data.startswith("mreport_"):
            mid = data.replace("mreport_", "")
            if mid not in db["member_orders"]:
                answer_callback(callback_id, "❌ وجود نداره!", show_alert=True); return
            order = db["member_orders"][mid]
            rn = callback["from"].get("username", "نامشخص")
            answer_callback(callback_id, "🚨 گزارش ثبت شد!", show_alert=True)
            try: send_message(int(OWNER_ID), f"🚨 **گزارش عضو**\n\n👤 @{rn}\n📝 #{order.get('order_number', '?')}\n🔗 {order['link']}")
            except: pass
            return
        
        # ═══════ تیکت پشتیبانی ═══════
        if data.startswith("ticket_reject_"):
            tid = data.replace("ticket_reject_", "")
            if tid in db.get("support_tickets", {}):
                db["support_tickets"][tid]["status"] = "rejected"
                save_db_async()
            answer_callback(callback_id, "❌ رد شد!", show_alert=True)
            return
        
        if data.startswith("ticket_reply_"):
            tid = data.replace("ticket_reply_", "")
            if tid not in db.get("support_tickets", {}):
                answer_callback(callback_id, "❌ تیکت وجود نداره!", show_alert=True); return
            db["pending_support_reply"][user_id] = {"step": "waiting_reply", "ticket_id": tid}
            save_db_async()
            answer_callback(callback_id, "📝 جوابت رو بفرست", show_alert=True)
            send_message(user_id, "📝 **جواب پشتیبانی رو بنویس:**", cancel_keyboard())
            return
        
        if data.startswith("ticket_next_"):
            tid = data.replace("ticket_next_", "")
            # پیدا کردن تیکت بعدی باز
            open_tickets = [(k, v) for k, v in db.get("support_tickets", {}).items() if v.get("status") == "open"]
            if not open_tickets:
                answer_callback(callback_id, "✅ تیکت باز دیگه‌ای نیست!", show_alert=True)
                return
            k, v = open_tickets[0]
            kb = {"inline_keyboard": [
                [{"text": "❌ رد کردن", "callback_data": f"ticket_reject_{k}"}],
                [{"text": "📝 جواب دادن", "callback_data": f"ticket_reply_{k}"}],
                [{"text": "⏳ بعدی", "callback_data": f"ticket_next_{k}"}]
            ]}
            answer_callback(callback_id)
            send_message(user_id,
                f"💬 **پیام پشتیبانی** #{k}\n\n"
                f"👤 از: {v.get('name', '?')}\n"
                f"🆔 آیدی: {v['user_id']}\n\n"
                f"📝 پیام:\n{v['text']}", kb)
            return

# ─── پایان بخش ۱۰ ───
# ═══════════════════════════════════════
# 🚀 حلقه اصلی
# ═══════════════════════════════════════
last_update_id = 0

def main():
    global last_update_id, INVITE_REWARD
    INVITE_REWARD = db.get("invite_reward", INVITE_REWARD)
    print("⚡ هایپرسین بله - نسخه فوق سریع!")
    print(f"🤖 @{BOT_USERNAME}")
    print(f"💓 Cache | Async | ThreadPool(500)")
    print(f"🎯 ظرفیت: ۵۰۰,۰۰۰ تا ۱,۰۰۰,۰۰۰ کاربر")
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

# ─── پایان بخش ۱۱ ───
# ═══════════════════════════════════════
# 🌐 Flask
# ═══════════════════════════════════════
app = Flask(__name__)

@app.route('/')
def home(): return "🤖 Hypersin Bale Bot - Ultra Fast!"

@app.route('/ping')
def ping(): return "pong ✅"

@app.route('/health')
def health():
    return jsonify({"status": "online", "users": len(db.get("users", {})), "cache": len(CACHE)})

# ═══════════════════════════════════════
# 🚀 اجرا
# ═══════════════════════════════════════
if __name__ == "__main__":
    # دیتابیس و کش
    threading.Thread(target=save_worker, daemon=True).start()
    threading.Thread(target=cache_cleanup, daemon=True).start()
    
    # Keep-Alive
    threading.Thread(target=keep_alive, daemon=True).start()
    
    # چک تضمینی + چک ادمین
    threading.Thread(target=check_guaranteed_members, daemon=True).start()
    threading.Thread(target=check_admin_orders, daemon=True).start()
    
    # حلقه اصلی
    threading.Thread(target=main, daemon=True).start()
    
    # Flask
    app.run(host="0.0.0.0", port=10000)

# ─── پایان بخش ۱۲ ───
