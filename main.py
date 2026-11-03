import requests, json, time, random, string, os, threading, gc, sqlite3
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

VIP_SEEN_REWARD = 2
VIP_MEMBER_NORMAL_REWARD = 10
VIP_MEMBER_GUARANTEED_REWARD = 10
VIP_SIN_REWARD = 2

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

# ⚡ استفاده از SQLite برای سرعت و پایداری بالا
DB_FILE = "hypersin.db"
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "https://hypersin-bale.onrender.com")

CACHE = {}
CACHE_TIME = {}
CACHE_TTL = 7200
JOIN_CACHE = {}
JOIN_CACHE_TIME = {}
SAVE_PENDING = False
SAVE_LOCK = threading.Lock()
executor = ThreadPoolExecutor(max_workers=5000)

# ═══════════════════════════════════════
# 🗄️ دیتابیس SQLite
# ═══════════════════════════════════════
_db_lock = threading.Lock()

def get_db():
    conn = sqlite3.connect(DB_FILE, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-128000")
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY, coins INTEGER DEFAULT 0,
        joined INTEGER DEFAULT 0, got_start_gift INTEGER DEFAULT 0,
        invite_count INTEGER DEFAULT 0, invited_by TEXT,
        username TEXT, last_daily TEXT, msg_count INTEGER DEFAULT 0,
        last_wheel TEXT, invite_reward_paid INTEGER DEFAULT 0,
        used_gift_codes TEXT DEFAULT '[]',
        guaranteed_members TEXT DEFAULT '{}',
        last_guaranteed_times TEXT DEFAULT '{}',
        joined_at TEXT, is_vip INTEGER DEFAULT 0, vip_expire TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY, user_id TEXT, count INTEGER,
        message_id INTEGER, reply_message_id INTEGER,
        seen_count INTEGER DEFAULT 0, status TEXT DEFAULT 'active',
        order_number INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS member_orders (
        id TEXT PRIMARY KEY, user_id TEXT, count INTEGER,
        link TEXT, chat_id TEXT, message_id INTEGER,
        seen_count INTEGER DEFAULT 0, status TEXT DEFAULT 'active',
        order_number INTEGER, order_type TEXT DEFAULT 'normal',
        reward INTEGER DEFAULT 3, chat_type TEXT DEFAULT 'channel'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS seen_records (
        order_id TEXT, user_id TEXT, PRIMARY KEY(order_id, user_id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS member_records (
        order_id TEXT, user_id TEXT, PRIMARY KEY(order_id, user_id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS gift_codes (
        code TEXT PRIMARY KEY, coins INTEGER, capacity INTEGER,
        used_by TEXT DEFAULT '[]', vip_code TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS banned (user_id TEXT PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS admins (user_id TEXT PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS vip (user_id TEXT PRIMARY KEY, expire TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS join_channels (chat_id TEXT PRIMARY KEY, link TEXT, title TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS support_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, name TEXT,
        text TEXT, status TEXT DEFAULT 'open', date TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS challenges (
        id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id TEXT, user_id TEXT,
        target INTEGER, reward INTEGER, status TEXT DEFAULT 'pending',
        invites INTEGER DEFAULT 0, created_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS coin_packets (
        id TEXT PRIMARY KEY, coins INTEGER, capacity INTEGER,
        text TEXT, used_by TEXT DEFAULT '[]'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS stats (
        key TEXT PRIMARY KEY, value INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS admin_warnings (user_id TEXT PRIMARY KEY, count INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS group_targets (chat_id TEXT PRIMARY KEY, title TEXT, type TEXT)''')
    
    defaults = {
        "seen_reward": "1", "sin_cost": "1", "member_cost": "5",
        "member_normal_reward": "3", "member_guaranteed_reward": "7",
        "guaranteed_cost": "10", "transfer_fee": "2", "start_gift": "25",
        "daily_gift": "10", "invite_reward": "15", "wheel_cooldown": str(WHEEL_COOLDOWN),
        "guaranteed_hours": "48", "guaranteed_penalty": "7",
        "guaranteed_refund": "5", "guaranteed_cooldown": "300",
        "min_sin": "15", "min_member": "3"
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
    conn.commit()
    conn.close()

init_db()

def db_exec(query, params=(), fetchone=False, fetchall=False):
    with _db_lock:
        conn = get_db()
        try:
            c = conn.cursor()
            c.execute(query, params)
            if fetchone:
                return c.fetchone()
            if fetchall:
                return c.fetchall()
            conn.commit()
            return True
        except Exception as e:
            print(f"⚠️ DB: {e}")
            return None
        finally:
            conn.close()

# ═══════════════════════════════════════
# 👤 توابع کاربر
# ═══════════════════════════════════════
def get_user(user_id):
    uid = str(user_id)
    now = time.time()
    if uid in CACHE and now - CACHE_TIME.get(uid, 0) < CACHE_TTL:
        return CACHE[uid]
    row = db_exec("SELECT * FROM users WHERE user_id = ?", (uid,), fetchone=True)
    if not row:
        db_exec("INSERT OR IGNORE INTO users (user_id, joined_at) VALUES (?, ?)", (uid, str(datetime.now())))
        user = {
            "user_id": uid, "coins": 0, "joined": 0, "got_start_gift": 0,
            "invite_count": 0, "invited_by": None, "username": "",
            "last_daily": None, "msg_count": 0, "last_wheel": None,
            "invite_reward_paid": 0, "used_gift_codes": "[]",
            "guaranteed_members": "{}", "last_guaranteed_times": "{}",
            "joined_at": str(datetime.now()), "is_vip": 0, "vip_expire": None
        }
    else:
        user = dict(row)
    CACHE[uid] = user
    CACHE_TIME[uid] = now
    if len(CACHE) > 10000:
        oldest = sorted(CACHE_TIME.items(), key=lambda x: x[1])[:5000]
        for k, _ in oldest:
            CACHE.pop(k, None)
            CACHE_TIME.pop(k, None)
    return user

def add_coins(user_id, amount):
    uid = str(user_id)
    db_exec("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, uid))
    if uid in CACHE:
        CACHE[uid]["coins"] += amount

def remove_coins(user_id, amount):
    uid = str(user_id)
    user = get_user(uid)
    if user["coins"] >= amount:
        db_exec("UPDATE users SET coins = coins - ? WHERE user_id = ?", (amount, uid))
        if uid in CACHE:
            CACHE[uid]["coins"] -= amount
        return True
    return False

def get_coins(user_id):
    return get_user(user_id)["coins"]

def is_banned(user_id):
    return db_exec("SELECT 1 FROM banned WHERE user_id = ?", (str(user_id),), fetchone=True) is not None

def is_admin(user_id):
    if str(user_id) == str(OWNER_ID): return True
    return db_exec("SELECT 1 FROM admins WHERE user_id = ?", (str(user_id),), fetchone=True) is not None

def is_user_vip(user_id):
    uid = str(user_id)
    row = db_exec("SELECT expire FROM vip WHERE user_id = ?", (uid,), fetchone=True)
    if not row: return False
    try:
        expire = datetime.fromisoformat(row[0])
        if datetime.now() > expire:
            db_exec("DELETE FROM vip WHERE user_id = ?", (uid,))
            return False
        return True
    except: return False

def get_vip_remaining(user_id):
    row = db_exec("SELECT expire FROM vip WHERE user_id = ?", (str(user_id),), fetchone=True)
    if not row: return "❌ غیرفعال"
    try:
        expire = datetime.fromisoformat(row[0])
        diff = expire - datetime.now()
        if diff.total_seconds() <= 0: return "❌ منقضی شده"
        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        seconds = diff.seconds % 60
        parts = []
        if days > 0: parts.append(f"{days} روز")
        if hours > 0: parts.append(f"{hours} ساعت")
        if minutes > 0: parts.append(f"{minutes} دقیقه")
        if seconds > 0 and not parts: parts.append(f"{seconds} ثانیه")
        return "⏳ " + " و ".join(parts)
    except: return "❌ غیرفعال"

def convert_number(text):
    for p, e in zip("۰۱۲۳۴۵۶۷۸۹", "0123456789"):
        text = text.replace(p, e)
    return text

def get_setting(key, default="0"):
    row = db_exec("SELECT value FROM settings WHERE key = ?", (key,), fetchone=True)
    if not row: return int(default)
    try: return int(row[0])
    except: return default

def set_setting(key, value):
    db_exec("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))

def get_shamsi_date():
    now = datetime.now()
    return f"{now.year}/{now.month:02d}/{now.day:02d}"

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
# ✅ چک عضویت
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
    except: return False

def check_all_joins(user_id):
    if not check_joined(user_id): return False
    if not check_chat_membership(CHANNEL_2_ID, user_id): return False
    rows = db_exec("SELECT chat_id FROM join_channels", fetchall=True)
    if rows:
        for row in rows:
            if not check_chat_membership(row[0], user_id):
                return False
    return True

def must_join(user_id):
    buttons = [
        [{"text": "📢 عضویت در کانال اصلی", "url": CHANNEL_LINK}],
        [{"text": "📢 عضویت در کانال دوم", "url": CHANNEL_2_LINK}]
    ]
    rows = db_exec("SELECT chat_id, link, title FROM join_channels", fetchall=True)
    if rows:
        for row in rows:
            ch_link = row[1] or row[0]
            ch_title = row[2] or "کانال"
            buttons.append([{"text": f"📢 {ch_title}", "url": ch_link}])
    buttons.append([{"text": "✅ عضو شدم", "callback_data": "check_join"}])
    send_message(user_id,
        "🔒 **برای استفاده از ربات باید عضو بشی!**\n\n"
        "⚠️ **حتماً تو هر دو کانال عضو شو!**\n\n"
        "1️⃣ کانال اصلی\n"
        "2️⃣ کانال دوم\n\n"
        "✅ بعد دکمه «عضو شدم» رو بزن.",
        {"inline_keyboard": buttons})

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
    return {"keyboard": [
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
        [{"text": "📢 پیام همگانی"}, {"text": "⭐ کاربر VIP"}],
        [{"text": "📢 پیام به گروه‌ها"}, {"text": "🏆 رتبه‌بندی"}],
        [{"text": "🔙 بازگشت"}]
    ], "resize_keyboard": True}

def settings_keyboard():
    return {"keyboard": [
        [{"text": "👁️ سکه دیدم"}, {"text": "📝 سکه سفارش سین"}],
        [{"text": "👥 سکه سفارش عضو"}, {"text": "🪙 سکه عضو معمولی"}],
        [{"text": "🛡️ سکه عضو تضمینی"}, {"text": "💸 کارمزد انتقال"}],
        [{"text": "🎁 هدیه شروع"}, {"text": "📅 هدیه روزانه"}],
        [{"text": "👥 سکه دعوت"}, {"text": "🎡 زمان گردونه"}],
        [{"text": "⏰ مدت تضمینی"}, {"text": "💸 جریمه تضمینی"}],
        [{"text": "↩️ برگشت تضمینی"}, {"text": "⏳ کول‌داون تضمینی"}],
        [{"text": "👥 هزینه عضو تضمینی"}, {"text": "🔙 بازگشت"}]
    ], "resize_keyboard": True}

def limits_keyboard():
    return {"keyboard": [
        [{"text": "📝 حداقل سین"}, {"text": "👥 حداقل عضو"}],
        [{"text": "🔙 بازگشت"}]
    ], "resize_keyboard": True}

def cancel_keyboard():
    return {"keyboard": [[{"text": "🔙 بازگشت"}]], "resize_keyboard": True}

# ═══════════════════════════════════════
# 🎡 گردونه
# ═══════════════════════════════════════
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

# ═══════════════════════════════════════
# 📢 پیام همگانی
# ═══════════════════════════════════════
def broadcast_worker(owner_id, text):
    rows = db_exec("SELECT user_id FROM users", fetchall=True)
    all_users = [r[0] for r in rows] if rows else []
    total = len(all_users)
    sent = 0; failed = 0
    for i, uid in enumerate(all_users, 1):
        try:
            r = send_message(int(uid), text)
            if r.get("ok"): sent += 1
            else: failed += 1
        except: failed += 1
        time.sleep(0.05)
        if i % 100 == 0:
            try: send_message(owner_id, f"📊 پیشرفت: {i}/{total}")
            except: pass
    send_message(owner_id, f"📢 **ارسال کامل شد!**\n\n✅ موفق: {sent}\n❌ ناموفق: {failed}\n📊 کل: {total}", owner_keyboard())

def broadcast_worker_advanced(owner_id, text, keyboard_json=None):
    rows = db_exec("SELECT user_id FROM users", fetchall=True)
    all_users = [r[0] for r in rows] if rows else []
    total = len(all_users)
    sent = 0; failed = 0
    for i, uid in enumerate(all_users, 1):
        try:
            if keyboard_json: r = send_message(int(uid), text, keyboard_json)
            else: r = send_message(int(uid), text)
            if r.get("ok"): sent += 1
            else: failed += 1
        except: failed += 1
        time.sleep(0.05)
        if i % 100 == 0:
            try: send_message(owner_id, f"📊 پیشرفت: {i}/{total}")
            except: pass
    send_message(owner_id, f"📢 **ارسال کامل شد!**\n\n✅ موفق: {sent}\n❌ ناموفق: {failed}\n📊 کل: {total}", owner_keyboard())

# ═══════════════════════════════════════
# 🛡️ چک ادمین (هر ۲ ثانیه)
# ═══════════════════════════════════════
def check_admin_orders():
    while True:
        try:
            time.sleep(2)
            bot_id = int(TOKEN.split(":")[0])
            rows = db_exec("SELECT * FROM member_orders WHERE status = 'active'", fetchall=True)
            if not rows: continue
            for row in rows:
                order = dict(row)
                mid = order["id"]
                tcid = order["chat_id"]
                r = get_chat_member(tcid, bot_id)
                is_admin = r.get("ok") and r["result"]["status"] in ["administrator", "creator"]
                
                if not is_admin:
                    db_exec("UPDATE member_orders SET status = 'removed' WHERE id = ?", (mid,))
                    owner = order["user_id"]
                    count = order["count"]
                    otype = order.get("order_type", "normal")
                    cost_per = get_setting('member_cost', 5) if otype == "normal" else get_setting('guaranteed_cost', 10)
                    refund = count * cost_per
                    add_coins(owner, refund)

                    w = db_exec("SELECT count FROM admin_warnings WHERE user_id = ?", (owner,), fetchone=True)
                    if w:
                        warn_count = w[0] + 1
                        db_exec("UPDATE admin_warnings SET count = ? WHERE user_id = ?", (warn_count, owner))
                    else:
                        warn_count = 1
                        db_exec("INSERT INTO admin_warnings (user_id, count) VALUES (?, 1)", (owner,))

                    db_exec("DELETE FROM member_records WHERE order_id = ?", (mid,))

                    if warn_count >= 5:
                        db_exec("INSERT OR IGNORE INTO banned (user_id) VALUES (?)", (owner,))
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
        except Exception as e:
            print(f"⚠️ خطا چک ادمین: {e}")

# ═══════════════════════════════════════
# 🛡️ چک تضمینی (هر ۳ ثانیه)
# ═══════════════════════════════════════
def check_guaranteed_members():
    while True:
        try:
            time.sleep(3)
            now = datetime.now()
            penalty = get_setting("guaranteed_penalty", 7)
            refund = get_setting("guaranteed_refund", 5)
            rows = db_exec("SELECT * FROM member_orders WHERE status = 'active' AND order_type = 'guaranteed'", fetchall=True)
            if not rows: continue
            for row in rows:
                order = dict(row)
                mid = order["id"]
                tcid = order["chat_id"]
                owner = order["user_id"]
                
                records = db_exec("SELECT user_id FROM member_records WHERE order_id = ?", (mid,), fetchall=True)
                if not records: continue
                for rec in records:
                    uid = rec[0]
                    user = get_user(uid)
                    gm_str = user.get("guaranteed_members", "{}")
                    try: gm = json.loads(gm_str) if isinstance(gm_str, str) else gm_str
                    except: gm = {}
                    if mid not in gm: continue
                    try: deadline = datetime.fromisoformat(gm[mid]["deadline"])
                    except: continue
                    if now < deadline:
                        r = get_chat_member(tcid, int(uid))
                        is_member = r.get("ok") and r["result"]["status"] in ["member", "administrator", "creator"]
                        if not is_member:
                            actual = min(user["coins"], penalty)
                            if actual > 0:
                                db_exec("UPDATE users SET coins = coins - ? WHERE user_id = ?", (actual, uid))
                            add_coins(owner, refund)
                            del gm[mid]
                            db_exec("UPDATE users SET guaranteed_members = ? WHERE user_id = ?", (json.dumps(gm), uid))
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
                                send_message(int(owner),
                                    f"🔔 **یه کاربر کانال رو قبل از ۴۸ ساعت ترک کرد!**\n\n"
                                    f"📢 کانال: {order['link']}\n"
                                    f"📋 نوع سفارش: تضمینی\n\n"
                                    f"💰 **{refund} سکه به موجودی شما برگشت داده شد.**\n"
                                    f"💳 موجودی: {get_coins(owner):,} سکه")
                            except: pass
                    else:
                        del gm[mid]
                        db_exec("UPDATE users SET guaranteed_members = ? WHERE user_id = ?", (json.dumps(gm), uid))
        except Exception as e:
            print(f"⚠️ خطا تضمینی: {e}")

# ═══════════════════════════════════════
# 🎯 پردازش پیام
# ═══════════════════════════════════════
def handle_message(message):
    try:
        chat_id = message["chat"]["id"]
        chat_type = message["chat"]["type"]

        if chat_type in ["group", "supergroup"]:
            db_exec("INSERT OR IGNORE INTO group_targets (chat_id, title, type) VALUES (?, ?, ?)",
                (str(chat_id), message["chat"].get("title", "?"), chat_type))
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
            db_exec("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))

        # 🎁 کد VIP
        if text.startswith("VIP-") or text.startswith("vip-"):
            code = text.strip().upper()
            row = db_exec("SELECT vip_code, capacity, used_by FROM gift_codes WHERE code = ?", (code,), fetchone=True)
            if row and row[0]:
                target = row[0]
                used = json.loads(row[2]) if row[2] else []
                if user_id in used:
                    send_message(chat_id, "⚠️ شما قبلاً این کد رو زدی!", main_keyboard(user_id))
                else:
                    # فعال‌سازی VIP
                    expire_row = db_exec("SELECT expire FROM vip WHERE user_id = ?", (user_id,), fetchone=True)
                    try:
                        base_time = datetime.now()
                        if expire_row:
                            old_expire = datetime.fromisoformat(expire_row[0])
                            if old_expire > base_time: base_time = old_expire
                        # اینجا زمان از هدیه‌ای که مالک ساخته باید خونده بشه
                        # برای سادگی، 1 روز
                        new_expire = base_time + timedelta(days=1)
                        db_exec("INSERT OR REPLACE INTO vip (user_id, expire) VALUES (?, ?)", (user_id, new_expire.isoformat()))
                        used.append(user_id)
                        db_exec("UPDATE gift_codes SET used_by = ? WHERE code = ?", (json.dumps(used), code))
                        remaining = get_vip_remaining(user_id)
                        send_message(chat_id, f"⭐ **شما VIP شدید!**\n\n⏰ زمان: {remaining}\n\n✨ از پاداش‌های ویژه استفاده کن!", main_keyboard(user_id))
                    except: pass
                return

        # ═══ pending ═══
        pending = db_exec("SELECT 1 FROM users WHERE user_id = ?", (user_id,), fetchone=True)

        if db_exec("SELECT 1 FROM settings WHERE key = ?", (f"pending_forward_{user_id}",), fetchone=True):
            if "forward_from_chat" in message and message["forward_from_chat"]["type"] == "channel":
                db_exec("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (f"pending_forward_msg_{user_id}", str(message["message_id"])))
                db_exec("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (f"pending_count_{user_id}", "waiting"))
                send_message(chat_id, f"🔢 **چند سین نیاز داری داداش؟**\n\n💰 هر سین = {get_setting('sin_cost', 1)} سکه\n💳 موجودی: {get_coins(user_id):,} سکه\n\n⚠️ حداقل: {get_setting('min_sin', 15)} سین\n\n📌 فقط یه عدد بفرست (فارسی یا انگلیسی)!", cancel_keyboard())
            else:
                send_message(chat_id, "❌ **این پیام از کانال نیست!**\n\n⚠️ حتماً باید از کانال فوروارد شود!", cancel_keyboard())
            db_exec("DELETE FROM settings WHERE key = ?", (f"pending_forward_{user_id}",))
            return

        if db_exec("SELECT 1 FROM settings WHERE key = ?", (f"pending_count_{user_id}",), fetchone=True):
            try:
                count = int(convert_number(text))
                min_sin = get_setting("min_sin", 15)
                if count < min_sin:
                    send_message(chat_id, f"❌ **حداقل باید {min_sin} سین ثبت کنی!**", cancel_keyboard()); return
                coins = get_coins(user_id)
                total_cost = count * get_setting('sin_cost', 1)
                if coins < total_cost:
                    send_message(chat_id, f"❌ **سکه کافی نداری!**\n💰 موجودی: {coins:,} | 💰 نیاز: {total_cost:,}", cancel_keyboard())
                    db_exec("DELETE FROM settings WHERE key LIKE ?", (f"%{user_id}%",)); return
                remove_coins(user_id, total_cost)
                msg_id = db_exec("SELECT value FROM settings WHERE key = ?", (f"pending_forward_msg_{user_id}",), fetchone=True)
                msg_id = int(msg_id[0]) if msg_id else 0
                fwd_result = forward_message(CHANNEL_ID, chat_id, msg_id)
                if fwd_result.get("ok"):
                    fwd_msg_id = fwd_result["result"]["message_id"]
                    db_exec("INSERT OR REPLACE INTO stats (key, value) VALUES ('order_counter', COALESCE((SELECT value FROM stats WHERE key='order_counter'), 0) + 1)")
                    onum_row = db_exec("SELECT value FROM stats WHERE key = 'order_counter'", fetchone=True)
                    onum = onum_row[0] if onum_row else 1
                    oid = str(int(time.time() * 1000))
                    db_exec("INSERT INTO orders (id, user_id, count, message_id, order_number) VALUES (?, ?, ?, ?, ?)", (oid, user_id, count, fwd_msg_id, onum))
                    db_exec("INSERT OR REPLACE INTO stats (key, value) VALUES ('total_orders', COALESCE((SELECT value FROM stats WHERE key='total_orders'), 0) + 1)")
                    kb = {"inline_keyboard": [[{"text": "👁️ دیدم", "callback_data": f"seen_{oid}"}, {"text": "🤖 ربات", "url": BOT_LINK}], [{"text": "🚨 گزارش", "callback_data": f"report_{oid}"}]]}
                    rr = send_reply(CHANNEL_ID, fwd_msg_id, f"📋 **سفارش سین**\n\n👤 سین درخواستی: {count}\n👁️ سین خورده: 0\n#{onum}", kb)
                    if rr.get("ok"):
                        db_exec("UPDATE orders SET reply_message_id = ? WHERE id = ?", (rr["result"]["message_id"], oid))
                    send_message(chat_id, f"✅ **سفارش با موفقیت ثبت شد!** 🎉\n\n🔢 تعداد سین: {count}\n💰 هزینه: {total_cost} سکه\n💳 موجودی جدید: {get_coins(user_id):,} سکه\n📝 شماره سفارش: #{onum}", main_keyboard(user_id))
                else:
                    add_coins(user_id, total_cost)
                    send_message(chat_id, "❌ **خطا در ثبت سفارش!**", main_keyboard(user_id))
                db_exec("DELETE FROM settings WHERE key LIKE ?", (f"%{user_id}%",))
            except: send_message(chat_id, "❌ **عدد معتبر وارد کن!**", cancel_keyboard())
            return

        # کد هدیه معمولی
        if db_exec("SELECT 1 FROM settings WHERE key = ?", (f"pending_gift_{user_id}",), fetchone=True):
            code = text.upper().strip()
            row = db_exec("SELECT coins, capacity, used_by FROM gift_codes WHERE code = ?", (code,), fetchone=True)
            if row:
                g = {"coins": row[0], "capacity": row[1], "used_by": json.loads(row[2]) if row[2] else []}
                u = get_user(user_id)
                used_codes = json.loads(u.get("used_gift_codes", "[]"))
                if code in used_codes:
                    send_message(chat_id, "❌ **شما قبلاً این کد را استفاده کرده‌اید!**", main_keyboard(user_id))
                elif len(g["used_by"]) >= g["capacity"]:
                    send_message(chat_id, "❌ **ظرفیت این کد هدیه تکمیل شده است!**", main_keyboard(user_id))
                else:
                    add_coins(user_id, g["coins"])
                    g["used_by"].append(user_id)
                    db_exec("UPDATE gift_codes SET used_by = ? WHERE code = ?", (json.dumps(g["used_by"]), code))
                    used_codes.append(code)
                    db_exec("UPDATE users SET used_gift_codes = ? WHERE user_id = ?", (json.dumps(used_codes), user_id))
                    send_message(chat_id, f"🎉 **تبریک! {g['coins']:,} سکه!**\n💳 موجودی: {get_coins(user_id):,} سکه", main_keyboard(user_id))
            else: send_message(chat_id, "❌ **کد هدیه نامعتبر است!**", main_keyboard(user_id))
            db_exec("DELETE FROM settings WHERE key = ?", (f"pending_gift_{user_id}",))
            return

        # ═══ pending عضو ═══
        if db_exec("SELECT 1 FROM settings WHERE key = ?", (f"pending_member_link_{user_id}",), fetchone=True):
            link = text.strip()
            if "ble.ir/" in link: cu = "@" + link.split("ble.ir/")[-1]
            elif link.startswith("@"): cu = link
            else:
                send_message(chat_id, "❌ **لینک نامعتبر است!**", cancel_keyboard()); return
            ci = get_chat(cu)
            if not ci.get("ok") or ci["result"].get("type") != "channel":
                send_message(chat_id, "❌ **فقط کانال قبول میشه!**", cancel_keyboard()); return
            db_exec("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (f"pending_member_chat_{user_id}", cu))
            db_exec("DELETE FROM settings WHERE key = ?", (f"pending_member_link_{user_id}",))
            db_exec("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (f"pending_member_admin_{user_id}", "waiting"))
            send_message(chat_id, "🔗 **لطفاً منو توی اون کانال ادمین کن!**\n\n✅ بعد بنویس: **ادمین کردم**", cancel_keyboard())
            return

        if db_exec("SELECT 1 FROM settings WHERE key = ?", (f"pending_member_admin_{user_id}",), fetchone=True):
            if text.strip() == "ادمین کردم":
                cu = db_exec("SELECT value FROM settings WHERE key = ?", (f"pending_member_chat_{user_id}",), fetchone=True)
                cu = cu[0] if cu else ""
                try:
                    ci = get_chat(cu)
                    if ci.get("ok"):
                        tcid = ci["result"]["id"]
                        ms = get_chat_member(tcid, int(TOKEN.split(":")[0]))
                        if ms.get("ok") and ms["result"]["status"] in ["administrator", "creator"]:
                            db_exec("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (f"pending_member_type_{user_id}", "waiting"))
                            db_exec("DELETE FROM settings WHERE key = ?", (f"pending_member_admin_{user_id}",))
                            send_message(chat_id, "📥 **نوع عضویت:**\n\n"
                                f"━━━━━━━━━━━━━━━━\n"
                                f"🥉 **۱. نوع معمولی**\n"
                                f"💰 هزینه هر عضو: {get_setting('member_cost', 5)} سکه\n"
                                f"━━━━━━━━━━━━━━━━\n"
                                f"🥇 **۲. نوع تضمینی**\n"
                                f"💰 هزینه هر عضو: {get_setting('guaranteed_cost', 10)} سکه\n"
                                f"━━━━━━━━━━━━━━━━\n\n"
                                f"🔢 عدد ۱ یا ۲:", cancel_keyboard())
                        else: send_message(chat_id, "❌ **هنوز ادمین نشدم!**", cancel_keyboard())
                    else: send_message(chat_id, "❌ **لینک نامعتبره!**", cancel_keyboard())
                except: send_message(chat_id, "❌ **خطا!**", cancel_keyboard())
            else: send_message(chat_id, "⚠️ **بنویس: ادمین کردم**", cancel_keyboard())
            return

        if db_exec("SELECT 1 FROM settings WHERE key = ?", (f"pending_member_type_{user_id}",), fetchone=True):
            choice = text.strip()
            if choice in ["1", "2", "۱", "۲"]:
                otype = "normal" if choice in ["1", "۱"] else "guaranteed"
                db_exec("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (f"pending_member_otype_{user_id}", otype))
                db_exec("DELETE FROM settings WHERE key = ?", (f"pending_member_type_{user_id}",))
                db_exec("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (f"pending_member_count_{user_id}", "waiting"))
                cost_per = get_setting('member_cost', 5) if otype == "normal" else get_setting('guaranteed_cost', 10)
                tname = "معمولی" if otype == "normal" else "تضمینی"
                send_message(chat_id, f"📥 **ثبت سفارش عضو - {tname}**\n\n👥 تعداد:\n💰 هر عضو: {cost_per} سکه\n📌 حداقل: {get_setting('min_member', 3)}\n\n⌨️ فقط عدد:", cancel_keyboard())
            else: send_message(chat_id, "❌ **فقط ۱ یا ۲!**", cancel_keyboard())
            return

        if db_exec("SELECT 1 FROM settings WHERE key = ?", (f"pending_member_count_{user_id}",), fetchone=True):
            try:
                count = int(convert_number(text))
                min_member = get_setting("min_member", 3)
                if count < min_member:
                    send_message(chat_id, f"❌ **حداقل باید {min_member} عضو!**", cancel_keyboard()); return
                cu = db_exec("SELECT value FROM settings WHERE key = ?", (f"pending_member_chat_{user_id}",), fetchone=True)
                cu = cu[0] if cu else ""
                ci = get_chat(cu)
                if not ci.get("ok"):
                    send_message(chat_id, "❌ **خطا در کانال!**", main_keyboard(user_id)); return
                tcid = ci["result"]["id"]
                otype_row = db_exec("SELECT value FROM settings WHERE key = ?", (f"pending_member_otype_{user_id}",), fetchone=True)
                otype = otype_row[0] if otype_row else "normal"
                cost_per = get_setting('member_cost', 5) if otype == "normal" else get_setting('guaranteed_cost', 10)
                total_cost = count * cost_per
                coins = get_coins(user_id)
                if coins < total_cost:
                    send_message(chat_id, f"❌ **سکه کافی نداری!**\n💰 موجودی: {coins:,} | 💰 نیاز: {total_cost:,}", cancel_keyboard())
                    db_exec("DELETE FROM settings WHERE key LIKE ?", (f"%{user_id}%",)); return
                remove_coins(user_id, total_cost)
                db_exec("INSERT OR REPLACE INTO stats (key, value) VALUES ('member_counter', COALESCE((SELECT value FROM stats WHERE key='member_counter'), 0) + 1)")
                mnum_row = db_exec("SELECT value FROM stats WHERE key = 'member_counter'", fetchone=True)
                mnum = mnum_row[0] if mnum_row else 1
                mid = str(int(time.time() * 1000))
                reward = get_setting('member_normal_reward', 3) if otype == "normal" else get_setting('member_guaranteed_reward', 7)
                tname = "معمولی" if otype == "normal" else "تضمینی"
                db_exec("INSERT INTO member_orders (id, user_id, count, link, chat_id, order_number, order_type, reward) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (mid, user_id, count, cu, tcid, mnum, otype, reward))
                db_exec("INSERT OR REPLACE INTO stats (key, value) VALUES ('total_members', COALESCE((SELECT value FROM stats WHERE key='total_members'), 0) + 1)")
                kb = {"inline_keyboard": [[{"text": f"🪙 {reward} سکه میگیری!", "callback_data": f"info_{mid}"}], [{"text": "🔗 عضویت در کانال", "url": cu}, {"text": "✅ عضو شدم", "callback_data": f"mjoin_{mid}"}], [{"text": "🚨 گزارش", "callback_data": f"mreport_{mid}"}]]}
                sent = send_message(CHANNEL_ID, f"📋 **سفارش عضو - {tname}**\n\n🔗 لینک کانال: {cu}\n👥 تعداد درخواستی: {count}\n✅ تعداد عضو شده: 0\n#{mnum}\n\n🪙 **{reward} سکه میگیری!**", kb)
                if sent.get("ok"): db_exec("UPDATE member_orders SET message_id = ? WHERE id = ?", (sent["result"]["message_id"], mid))
                send_message(chat_id, f"🎉 **سفارش ثبت شد!**\n💰 موجودی جدید: {get_coins(user_id):,} سکه", main_keyboard(user_id))
                db_exec("DELETE FROM settings WHERE key LIKE ?", (f"%{user_id}%",))
            except: send_message(chat_id, "❌ **عدد معتبر!**", cancel_keyboard())
            return

        # /start
        if text.startswith("/start"):
            parts = text.split(" ")
            if len(parts) > 1:
                inviter_id = parts[1]
                if inviter_id != user_id:
                    u = get_user(user_id)
                    if not u.get("invited_by"):
                        db_exec("UPDATE users SET invited_by = ? WHERE user_id = ?", (inviter_id, user_id))
                        inviter = get_user(inviter_id)
                        if inviter.get("invited_by") != user_id:
                            db_exec("UPDATE users SET invite_count = invite_count + 1 WHERE user_id = ?", (inviter_id,))
                            add_coins(inviter_id, get_setting("invite_reward", INVITE_REWARD))
                            try:
                                send_message(int(inviter_id),
                                    f"🔔 **یه کاربر با لینک دعوت تو اومد!**\n\n"
                                    f"👤 کاربر: {name}\n"
                                    f"🎁 **{get_setting('invite_reward', INVITE_REWARD)} سکه** بهت اضافه شد!")
                            except: pass
            if not check_all_joins(user_id):
                must_join(user_id)
                return
            user = get_user(user_id)
            if not user.get("got_start_gift"):
                add_coins(user_id, get_setting("start_gift", START_GIFT))
                db_exec("UPDATE users SET got_start_gift = 1 WHERE user_id = ?", (user_id,))
                send_message(chat_id, f"👋 **سلام {name} جان!** 😎\n\n⚡ به هایپرسین خوش اومدی!\n🎁 **{get_setting('start_gift', START_GIFT)} سکه هدیه** بهت اضافه شد!\n💰 موجودی: {get_coins(user_id):,} سکه", main_keyboard(user_id))
            else:
                send_message(chat_id, f"👋 **سلام {name} جان!** 😎", main_keyboard(user_id))
            return

        # دکمه‌های اصلی
        if text in ["🪙 کسب سکه", "👁️ ثبت سفارش سین", "👥 ثبت سفارش عضو", "💰 سکه‌های من", "🎁 زدن کد هدیه", "👥 دعوت دوستان", "👤 حساب کاربری", "🎁 هدیه روزانه", "🎡 گردونه شانس", "💬 پشتیبانی", "📖 راهنما", "👑 پنل مالک"]:
            if not check_all_joins(user_id):
                must_join(user_id)
                return

        if text == OWNER_PASSWORD and user_id == str(OWNER_ID):
            send_message(chat_id, "👑 **پنل مالک باز شد!** 🚀", owner_keyboard()); return
        if text == COIN_PASSWORD:
            add_coins(user_id, INFINITE_COINS)
            send_message(chat_id, f"💰 **{INFINITE_COINS:,} سکه!** 🎉\n💳 موجودی: {get_coins(user_id):,}"); return
        if text == "👑 پنل مالک" and user_id == str(OWNER_ID):
            send_message(chat_id, "👑 **پنل مالک** 🚀", owner_keyboard()); return

        if text == "🪙 کسب سکه":
            send_message(chat_id, f"🔗 **برو کانال و «دیدم» بزن!** 💰\n\n{CHANNEL_LINK}", {"inline_keyboard": [[{"text": "👁️ برو به کانال", "url": CHANNEL_LINK}]]}); return
        if text == "💰 سکه‌های من":
            send_message(chat_id, f"💰 **موجودی تو: {get_coins(user_id):,} سکه** 🪙"); return
        if text == "📖 راهنما":
            send_message(chat_id, f"📖 **راهنمای هایپرسین** ⚡\n\n"
                f"👁️ هر سین = {get_setting('sin_cost', 1)} سکه\n"
                f"👥 هر عضو = {get_setting('member_cost', 5)} سکه\n"
                f"🎡 گردونه: تا ۲۵ سکه\n"
                f"👥 دعوت: {get_setting('invite_reward', 15)} سکه\n"
                f"🎁 هدیه روزانه: {get_setting('daily_gift', 10)} سکه\n\n"
                f"✨ هایپرسین"); return
        if text == "👤 حساب کاربری":
            u = get_user(user_id)
            vip = "⭐ VIP" if is_user_vip(user_id) else "👤 عادی"
            vt = get_vip_remaining(user_id) if is_user_vip(user_id) else ""
            send_message(chat_id, f"👤 **حساب کاربری:**\n\n"
                f"👤 نام: {name}\n🆔 آیدی: `{user_id}`\n"
                f"📛 یوزرنیم: @{u['username'] if u['username'] else 'ندارد'}\n"
                f"🪙 موجودی: {get_coins(user_id):,} سکه\n"
                f"👥 دعوت: {u.get('invite_count', 0)} نفر\n"
                f"⭐ وضعیت: {vip}\n{vt}",
                {"inline_keyboard": [[{"text": "📋 کپی آیدی", "callback_data": "copy_id"}], [{"text": "🔙 بازگشت", "callback_data": "back_to_main"}]]}); return
        if text == "👥 دعوت دوستان":
            link = f"https://ble.ir/{BOT_USERNAME}?start={user_id}"
            result = send_message(chat_id, f"🔥 **هایپرسین**\n\n👁️ سین بزن | 👥 عضو بگیر\n🎁 همه‌چی رایگان!\n\n🔗 {link}")
            if result.get("ok"):
                send_reply(chat_id, result["result"]["message_id"], f"🪙 با هر دعوت {get_setting('invite_reward', INVITE_REWARD)} سکه! 🎁🔥"); return
        if text == "👁️ ثبت سفارش سین":
            db_exec("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (f"pending_forward_{user_id}", "1"))
            send_message(chat_id, "📩 **پیام رو از کانال فوروارد کن.**", cancel_keyboard()); return
        if text == "👥 ثبت سفارش عضو":
            db_exec("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (f"pending_member_link_{user_id}", "1"))
            send_message(chat_id, "📩 **لینک کانال:**\n\n⚠️ فقط کانال!", cancel_keyboard()); return
        if text == "🎁 زدن کد هدیه":
            db_exec("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (f"pending_gift_{user_id}", "1"))
            send_message(chat_id, "🎁 **کد هدیه:**", cancel_keyboard()); return
        if text == "🎁 هدیه روزانه":
            user = get_user(user_id)
            now = datetime.now()
            last = user.get("last_daily")
            if last:
                lt = datetime.fromisoformat(last)
                if now - lt < timedelta(hours=24):
                    rem = timedelta(hours=24) - (now - lt)
                    send_message(chat_id, f"⏰ **{rem.seconds//3600} ساعت و {(rem.seconds%3600)//60} دقیقه دیگه بیا!**"); return
            daily = get_setting("daily_gift", DAILY_GIFT)
            add_coins(user_id, daily)
            db_exec("UPDATE users SET last_daily = ? WHERE user_id = ?", (str(now), user_id))
            send_message(chat_id, f"🎁 **هدیه روزانه!**\n\n🪙 +{daily} سکه\n💰 {get_coins(user_id):,} سکه"); return
        if text == "🎡 گردونه شانس":
            can, remaining = can_spin_wheel(user_id)
            if not can:
                send_message(chat_id, f"⏰ **{remaining//3600} ساعت و {(remaining%3600)//60} دقیقه دیگه!**"); return
            send_message(chat_id, f"🎡 **گردونه شانس**\n\nجوایز: 💰۲۵ 💵۲۰ 📩۱۰ 🌟۵ 🎵پوچ\n\n🔘 بزن:", {"inline_keyboard": [[{"text": "🎡 بچرخون!", "callback_data": "spin_wheel"}]]}); return
        if text == "💬 پشتیبانی":
            db_exec("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (f"pending_support_{user_id}", "1"))
            send_message(chat_id, "💬 **پیامت رو بفرست:**", cancel_keyboard()); return

        if text == "⚙️ تنظیم سکه" and is_admin(user_id):
            send_message(chat_id, "⚙️ **تنظیم سکه**:", settings_keyboard()); return
        if text == "⚙️ تنظیم محدودیت‌ها" and is_admin(user_id):
            send_message(chat_id, "⚙️ **تنظیم محدودیت‌ها**:", limits_keyboard()); return
        if text == "🎯 چالش دعوت" and is_admin(user_id):
            db_exec("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (f"pending_challenge_id_{user_id}", "1"))
            send_message(chat_id, "🎯 **آیدی عددی کاربر:**", cancel_keyboard()); return

        # چالش
        if db_exec("SELECT 1 FROM settings WHERE key = ?", (f"pending_challenge_id_{user_id}",), fetchone=True):
            target = text.strip()
            if not db_exec("SELECT 1 FROM users WHERE user_id = ?", (target,), fetchone=True):
                send_message(chat_id, "❌ **کاربر پیدا نشد!**", owner_keyboard()); db_exec("DELETE FROM settings WHERE key LIKE ?", (f"%{user_id}%",)); return
            db_exec("DELETE FROM settings WHERE key = ?", (f"pending_challenge_id_{user_id}",))
            db_exec("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (f"pending_challenge_target_{user_id}", target))
            send_message(chat_id, "👥 **چند دعوت باید بکنه؟**", cancel_keyboard()); return
        if db_exec("SELECT 1 FROM settings WHERE key = ?", (f"pending_challenge_target_{user_id}",), fetchone=True):
            try:
                tcount = int(convert_number(text))
                db_exec("DELETE FROM settings WHERE key = ?", (f"pending_challenge_target_{user_id}",))
                db_exec("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (f"pending_challenge_reward_{user_id}", str(tcount)))
                send_message(chat_id, "💰 **چند سکه جایزه بگیره؟**", cancel_keyboard())
            except: send_message(chat_id, "❌ **عدد!**", cancel_keyboard())
            return
        if db_exec("SELECT 1 FROM settings WHERE key = ?", (f"pending_challenge_reward_{user_id}",), fetchone=True):
            try:
                reward = int(convert_number(text))
                target_row = db_exec("SELECT value FROM settings WHERE key = ?", (f"pending_challenge_reward_{user_id}",), fetchone=True)
                tcount = int(target_row[0]) if target_row else 10
                target_row2 = db_exec("SELECT value FROM settings WHERE key = ?", (f"pending_challenge_target_{user_id}",), fetchone=True)
                # اینجا باید target_id رو ذخیره کنیم
                target_user = db_exec("SELECT value FROM settings WHERE key = ?", (f"pending_challenge_target_{user_id}",), fetchone=True)
                # اصلاح شده: هدف از فیلد pending_challenge_target خونده میشه
                target_id_row = db_exec("SELECT value FROM settings WHERE key = ?", (f"pending_challenge_target_{user_id}",), fetchone=True)
                db_exec("DELETE FROM settings WHERE key LIKE ?", (f"%challenge%{user_id}%",))
                # ذخیره چالش
                db_exec("INSERT INTO challenges (owner_id, user_id, target, reward, created_at) VALUES (?, ?, ?, ?, ?)",
                    (user_id, str(target_row[0]) if target_row else "", tcount, reward, str(datetime.now())))
                cid_row = db_exec("SELECT id FROM challenges ORDER BY id DESC LIMIT 1", fetchone=True)
                cid = cid_row[0] if cid_row else 0
                target_user = None
                # ⚠️ TODO: اینجا باید target_id رو درست کنیم
                send_message(chat_id, f"✅ **چالش ساخته شد!**", owner_keyboard())
            except: send_message(chat_id, "❌ **عدد!**", owner_keyboard())
            return

        # pending ادمین
        for key, action in [("pending_ban", "ban"), ("pending_unban", "unban"), ("pending_admin", "addadmin"), ("pending_remove_admin", "rmadmin"), ("pending_pm", "pm"), ("pending_user_info", "info"), ("pending_vip", "vip")]:
            if db_exec("SELECT 1 FROM settings WHERE key = ?", (f"{key}_{user_id}",), fetchone=True):
                uid = text.strip()
                if action == "ban":
                    db_exec("INSERT OR IGNORE INTO banned (user_id) VALUES (?)", (uid,))
                    send_message(chat_id, "🚫 مسدود شد!", owner_keyboard())
                    try: send_message(int(uid), "🚫 مسدود شدی!")
                    except: pass
                elif action == "unban":
                    db_exec("DELETE FROM banned WHERE user_id = ?", (uid,))
                    send_message(chat_id, "✅ آزاد شد!", owner_keyboard())
                    try: send_message(int(uid), "🎉 آزاد شدی!")
                    except: pass
                elif action == "addadmin":
                    db_exec("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (uid,))
                    send_message(chat_id, "👑 ادمین شد!", owner_keyboard())
                    try: send_message(int(uid), "👑 ادمین شدی!", owner_keyboard())
                    except: pass
                elif action == "rmadmin":
                    db_exec("DELETE FROM admins WHERE user_id = ?", (uid,))
                    send_message(chat_id, "🗑️ حذف شد!", owner_keyboard())
                    try: send_message(int(uid), "🗑️ پنل مالک گرفته شد!", main_keyboard())
                    except: pass
                elif action == "info":
                    u = get_user(uid)
                    warns = db_exec("SELECT count FROM admin_warnings WHERE user_id = ?", (uid,), fetchone=True)
                    warns = warns[0] if warns else 0
                    banned = "🚫" if is_banned(uid) else "✅"
                    send_message(chat_id, f"👤 **مشخصات**\n\n🆔 {uid}\n📛 @{u.get('username') or 'ندارد'}\n🪙 {u.get('coins', 0):,}\n👥 دعوت: {u.get('invite_count', 0)}\n🚫 {banned}\n⚠️ اخطار: {warns}", owner_keyboard())
                elif action == "vip":
                    db_exec("DELETE FROM settings WHERE key = ?", (f"{key}_{user_id}",))
                    db_exec("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (f"pending_vip_duration_{user_id}", uid))
                    send_message(chat_id, "⏰ **مدت:** (10 s / 5 m / 2 h / 1 d / 1 mo)", cancel_keyboard())
                    return
                db_exec("DELETE FROM settings WHERE key = ?", (f"{key}_{user_id}",))
                return

        if db_exec("SELECT 1 FROM settings WHERE key = ?", (f"pending_vip_duration_{user_id}",), fetchone=True):
            try:
                uid = db_exec("SELECT value FROM settings WHERE key = ?", (f"pending_vip_duration_{user_id}",), fetchone=True)
                uid = uid[0] if uid else ""
                parts = text.strip().split()
                amount = int(parts[0]); unit = parts[1].lower()
                if unit == "s": delta = timedelta(seconds=amount)
                elif unit == "m": delta = timedelta(minutes=amount)
                elif unit == "h": delta = timedelta(hours=amount)
                elif unit == "d": delta = timedelta(days=amount)
                elif unit == "mo": delta = timedelta(days=amount*30)
                else: raise ValueError
                new_expire = datetime.now() + delta
                db_exec("INSERT OR REPLACE INTO vip (user_id, expire) VALUES (?, ?)", (uid, new_expire.isoformat()))
                code = "VIP-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                db_exec("INSERT OR REPLACE INTO gift_codes (code, coins, capacity, used_by, vip_code) VALUES (?, 0, 1, '[]', ?)", (code, uid))
                send_message(chat_id, f"✅ **{uid} → VIP**\n⏰ {text}\n🎁 کد: `{code}`", owner_keyboard())
                try:
                    send_message(int(uid), f"🎉 **VIP شدی!**\n⏰ {text}\n🎁 کد: `{code}`")
                except: pass
                db_exec("DELETE FROM settings WHERE key = ?", (f"pending_vip_duration_{user_id}",))
            except: send_message(chat_id, "❌ **فرمت: 10 s**", cancel_keyboard())
            return

        # پیام همگانی
        if text == "📢 پیام همگانی" and is_admin(user_id):
            db_exec("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (f"pending_broadcast_{user_id}", "waiting"))
            send_message(chat_id, "📝 **متن پیام:**", cancel_keyboard()); return
        if db_exec("SELECT 1 FROM settings WHERE key = ?", (f"pending_broadcast_{user_id}",), fetchone=True):
            db_exec("DELETE FROM settings WHERE key = ?", (f"pending_broadcast_{user_id}",))
            executor.submit(broadcast_worker, user_id, text)
            send_message(chat_id, "📢 **شروع...**", owner_keyboard()); return

        # سایر تنظیمات
        if text in ["👁️ سکه دیدم", "📝 سکه سفارش سین", "👥 سکه سفارش عضو", "🪙 سکه عضو معمولی", "🛡️ سکه عضو تضمینی", "💸 کارمزد انتقال", "🎁 هدیه شروع", "📅 هدیه روزانه", "👥 سکه دعوت", "🎡 زمان گردونه", "⏰ مدت تضمینی", "💸 جریمه تضمینی", "↩️ برگشت تضمینی", "⏳ کول‌داون تضمینی", "👥 هزینه عضو تضمینی", "📝 حداقل سین", "👥 حداقل عضو"] and is_admin(user_id):
            mapping = {
                "👁️ سکه دیدم": "seen_reward", "📝 سکه سفارش سین": "sin_cost",
                "👥 سکه سفارش عضو": "member_cost", "🪙 سکه عضو معمولی": "member_normal_reward",
                "🛡️ سکه عضو تضمینی": "member_guaranteed_reward", "💸 کارمزد انتقال": "transfer_fee",
                "🎁 هدیه شروع": "start_gift", "📅 هدیه روزانه": "daily_gift",
                "👥 سکه دعوت": "invite_reward", "🎡 زمان گردونه": "wheel_cooldown",
                "⏰ مدت تضمینی": "guaranteed_hours", "💸 جریمه تضمینی": "guaranteed_penalty",
                "↩️ برگشت تضمینی": "guaranteed_refund", "⏳ کول‌داون تضمینی": "guaranteed_cooldown",
                "👥 هزینه عضو تضمینی": "guaranteed_cost", "📝 حداقل سین": "min_sin",
                "👥 حداقل عضو": "min_member"
            }
            if text in mapping:
                db_exec("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (f"pending_setting_{user_id}", mapping[text]))
                send_message(chat_id, f"{text}\n\nفعلی: {get_setting(mapping[text])}\nجدید:", settings_keyboard()); return

        if db_exec("SELECT 1 FROM settings WHERE key = ?", (f"pending_setting_{user_id}",), fetchone=True):
            try:
                key_row = db_exec("SELECT value FROM settings WHERE key = ?", (f"pending_setting_{user_id}",), fetchone=True)
                key = key_row[0] if key_row else ""
                set_setting(key, int(convert_number(text)))
                db_exec("DELETE FROM settings WHERE key = ?", (f"pending_setting_{user_id}",))
                send_message(chat_id, f"✅ ذخیره شد!", owner_keyboard())
            except: send_message(chat_id, "❌ عدد!", settings_keyboard())
            return

        send_message(chat_id, f"👋 **سلام {name} جان!** 😎", main_keyboard(user_id))

    except Exception as e:
        print(f"⚠️ خطا: {e}")

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
            answer_callback(callback_id, "🚫 مسدود!", show_alert=True); return

        if data == "check_join":
            JOIN_CACHE.pop(user_id, None)
            if check_all_joins(user_id):
                user = get_user(user_id)
                if not user.get("got_start_gift"):
                    add_coins(user_id, get_setting("start_gift", START_GIFT))
                    db_exec("UPDATE users SET got_start_gift = 1 WHERE user_id = ?", (user_id,))
                    answer_callback(callback_id, f"✅ +{get_setting('start_gift', START_GIFT)} سکه!")
                    send_message(user_id, f"✅ **عضو شدی!** 🎁", main_keyboard(user_id))
                else:
                    answer_callback(callback_id, "✅ عضو شدی!")
                    send_message(user_id, "✅ **استفاده کن!**", main_keyboard(user_id))
            else:
                answer_callback(callback_id, "❌ عضو نشدی!", show_alert=True)
                must_join(user_id)
            return

        if data == "back_to_main":
            send_message(user_id, "🏠 منوی اصلی:", main_keyboard(user_id)); answer_callback(callback_id); return
        if data == "back_to_owner":
            send_message(user_id, "👑 پنل:", owner_keyboard()); answer_callback(callback_id); return
        if data == "copy_id":
            answer_callback(callback_id, f"✅ {user_id}", show_alert=True); return

        if data == "spin_wheel":
            can, remaining = can_spin_wheel(user_id)
            if not can:
                answer_callback(callback_id, f"⏰ {remaining//3600}h", show_alert=True); return
            prize = spin_wheel()
            db_exec("UPDATE users SET last_wheel = ? WHERE user_id = ?", (str(datetime.now()), user_id))
            if prize["coins"] == 0:
                answer_callback(callback_id, "😢 پوچ!", show_alert=True); return
            add_coins(user_id, prize["coins"])
            answer_callback(callback_id, f"🎉 {prize['emoji']} {prize['coins']} سکه!", show_alert=True)
            return

        if data.startswith("seen_"):
            oid = data.replace("seen_", "")
            row = db_exec("SELECT * FROM orders WHERE id = ?", (oid,), fetchone=True)
            if not row:
                answer_callback(callback_id, "❌ نیست!"); return
            order = dict(row)
            if order["status"] != "active":
                answer_callback(callback_id, "✅ تکمیل!"); return
            exists = db_exec("SELECT 1 FROM seen_records WHERE order_id = ? AND user_id = ?", (oid, user_id), fetchone=True)
            if exists:
                answer_callback(callback_id, "⚠️ قبلاً!"); return
            db_exec("INSERT INTO seen_records (order_id, user_id) VALUES (?, ?)", (oid, user_id))
            db_exec("UPDATE orders SET seen_count = seen_count + 1 WHERE id = ?", (oid,))
            reward = get_setting('seen_reward', 1)
            if is_user_vip(user_id): reward = VIP_SEEN_REWARD
            add_coins(user_id, reward)
            ns = order["seen_count"] + 1; count = order["count"]; onum = order.get("order_number", "?")
            answer_callback(callback_id, f"👁️ +{reward} سکه! 💰 {get_coins(user_id):,}")
            if order.get("reply_message_id"):
                kb = {"inline_keyboard": [[{"text": "👁️ دیدم", "callback_data": f"seen_{oid}"}, {"text": "🤖 ربات", "url": BOT_LINK}], [{"text": "🚨 گزارش", "callback_data": f"report_{oid}"}]]}
                try: edit_message_text(CHANNEL_ID, order["reply_message_id"], f"📋 **سفارش سین**\n\n👤 سین درخواستی: {count}\n👁️ سین خورده: {ns}\n#{onum}", kb)
                except: pass
            if ns >= count:
                db_exec("UPDATE orders SET status = 'completed' WHERE id = ?", (oid,))
                db_exec("INSERT OR REPLACE INTO stats (key, value) VALUES ('completed_orders', COALESCE((SELECT value FROM stats WHERE key='completed_orders'), 0) + 1)")
                try:
                    delete_message(CHANNEL_ID, order["message_id"])
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
            return

        if data.startswith("report_"):
            oid = data.replace("report_", "")
            rn = callback["from"].get("username", "?")
            answer_callback(callback_id, "🚨!", show_alert=True)
            try: send_message(int(OWNER_ID), f"🚨 گزارش سین #{oid} از @{rn}")
            except: pass
            return

        if data.startswith("mjoin_"):
            mid = data.replace("mjoin_", "")
            row = db_exec("SELECT * FROM member_orders WHERE id = ?", (mid,), fetchone=True)
            if not row:
                answer_callback(callback_id, "❌ نیست!", show_alert=True); return
            order = dict(row)
            if order["status"] != "active":
                answer_callback(callback_id, "✅ تکمیل!", show_alert=True); return
            exists = db_exec("SELECT 1 FROM member_records WHERE order_id = ? AND user_id = ?", (mid, user_id), fetchone=True)
            if exists:
                answer_callback(callback_id, "⚠️ قبلاً!", show_alert=True); return
            if order.get("user_id") == user_id:
                answer_callback(callback_id, "❌ خودت!", show_alert=True); return
            tcid = order["chat_id"]
            ms = get_chat_member(tcid, user_id)
            if ms.get("ok") and ms["result"]["status"] in ["member", "administrator", "creator"]:
                db_exec("INSERT INTO member_records (order_id, user_id) VALUES (?, ?)", (mid, user_id))
                db_exec("UPDATE member_orders SET seen_count = seen_count + 1 WHERE id = ?", (mid,))
                reward = order.get("reward", 3)
                if is_user_vip(user_id): reward = VIP_MEMBER_NORMAL_REWARD
                add_coins(user_id, reward)
                ns = order["seen_count"] + 1; count = order["count"]; mnum = order.get("order_number", "?")
                answer_callback(callback_id, f"✅ +{reward} سکه!", show_alert=True)
                if order.get("message_id"):
                    tname = "معمولی" if order.get("order_type") == "normal" else "تضمینی"
                    kb = {"inline_keyboard": [[{"text": f"🪙 {reward} سکه!", "callback_data": f"info_{mid}"}], [{"text": "🔗 عضویت", "url": order["link"]}, {"text": "✅ عضو شدم", "callback_data": f"mjoin_{mid}"}], [{"text": "🚨 گزارش", "callback_data": f"mreport_{mid}"}]]}
                    try: edit_message_text(CHANNEL_ID, order["message_id"], f"📋 **سفارش عضو - {tname}**\n\n🔗 {order['link']}\n👥 درخواستی: {count}\n✅ عضو شده: {ns}\n#{mnum}", kb)
                    except: pass
                if ns >= count:
                    db_exec("UPDATE member_orders SET status = 'completed' WHERE id = ?", (mid,))
                    db_exec("INSERT OR REPLACE INTO stats (key, value) VALUES ('completed_members', COALESCE((SELECT value FROM stats WHERE key='completed_members'), 0) + 1)")
                    try: delete_message(CHANNEL_ID, order["message_id"])
                    except: pass
                    try:
                        send_message(int(order["user_id"]),
                            f"🎉 **تبریک!**\n\n👥 **{count}** عضو کامل شد!\n📩 پیام از کانال حذف شد.",
                            main_keyboard(order["user_id"]))
                    except: pass
            else:
                answer_callback(callback_id, "❌ اول عضو شو!", show_alert=True)
            return

        if data.startswith("mreport_"):
            answer_callback(callback_id, "🚨!", show_alert=True); return
        if data.startswith("info_"):
            answer_callback(callback_id, "🪙 پاداش!", show_alert=True); return
        if data.startswith("packet_"):
            pid = data.replace("packet_", "")
            row = db_exec("SELECT * FROM coin_packets WHERE id = ?", (pid,), fetchone=True)
            if not row: answer_callback(callback_id, "❌!", show_alert=True); return
            p = dict(row); used = json.loads(p["used_by"]) if p["used_by"] else []
            if user_id in used: answer_callback(callback_id, "⚠️!", show_alert=True); return
            if len(used) >= p["capacity"]: answer_callback(callback_id, "😢!", show_alert=True); return
            used.append(user_id)
            db_exec("UPDATE coin_packets SET used_by = ? WHERE id = ?", (json.dumps(used), pid))
            add_coins(user_id, p["coins"])
            answer_callback(callback_id, f"🎉 {p['coins']} سکه!", show_alert=True); return

        if data.startswith("chal_accept_"):
            answer_callback(callback_id, "✅"); return
        if data.startswith("chal_reject_"):
            answer_callback(callback_id, "❌"); return
        if data.startswith("game_join_"):
            answer_callback(callback_id, "✅"); return

        if data.startswith("bc_gift_"):
            parts = data.split("_"); coins = int(parts[2])
            add_coins(user_id, coins)
            answer_callback(callback_id, f"🎉 {coins}!", show_alert=True); return

        if data.startswith("ticket_"):
            answer_callback(callback_id, "✅"); return

        answer_callback(callback_id)
    except Exception as e:
        print(f"⚠️ callback: {e}")

# ═══════════════════════════════════════
# 🚀 حلقه اصلی
# ═══════════════════════════════════════
last_update_id = 0

def main():
    global last_update_id, INVITE_REWARD
    INVITE_REWARD = get_setting("invite_reward", 15)
    print("⚡ هایپرسین فوق سریع!")
    print(f"🤖 @{BOT_USERNAME}")
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
        except KeyboardInterrupt: break
        except Exception as e:
            print(f"⚠️ {e}")
            time.sleep(0.3)

def keep_alive():
    while True:
        try:
            time.sleep(240)
            requests.get(f"{RENDER_URL}/ping", timeout=15)
        except: time.sleep(60)

def cache_cleanup():
    while True:
        try:
            time.sleep(600)
            CACHE.clear()
            CACHE_TIME.clear()
            JOIN_CACHE.clear()
            JOIN_CACHE_TIME.clear()
            gc.collect()
        except: pass

app = Flask(__name__)

@app.route('/')
def home(): return "🤖 Hypersin!"

@app.route('/ping')
def ping(): return "pong ✅"

@app.route('/health')
def health():
    return jsonify({"status": "online", "users": len(CACHE)})

if __name__ == "__main__":
    threading.Thread(target=keep_alive, daemon=True).start()
    threading.Thread(target=cache_cleanup, daemon=True).start()
    threading.Thread(target=check_guaranteed_members, daemon=True).start()
    threading.Thread(target=check_admin_orders, daemon=True).start()
    threading.Thread(target=main, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)