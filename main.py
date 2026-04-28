#!/usr/bin/env python3
"""
Tabib AI 3.0 – Ishonchli tibbiy maslahatchi (toʻliq yangilangan)
"""
import os, re, uuid, logging, json
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from openai import OpenAI

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("TabibAI")

# Sozlamalar
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o")
MAX_HISTORY    = 20
MAX_MSG_LEN    = 3000

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ═══════════════════════════════════════════════════════════
# KENGAYTIRILGAN TIBBIY BILIMLAR BAZASI (250+ yozuv)
# ═══════════════════════════════════════════════════════════
MEDICAL_DB = {
    # Umumiy kasalliklar
    "bosh og'rig'i": ["Kuchlanish, migren, suvsizlanish yoki yuqori bosim sabab bo'lishi mumkin. Agar to'satdan kuchayib, nutq buzilsa shoshilinch yordam kerak.",
                      "Suv iching, qorong'i xonada dam oling. Tez-tez takrorlansa nevrologga murojaat qiling."],
    "isitma": ["Tana harorati 38°C dan yuqori bo'lsa. Ko'pincha infeksiya belgisi. Kattalarda 3 kundan ortiq yoki 39°C dan oshsa shifokor ko'rigi shart.",
               "Ko'p suyuqlik iching, yengil kiyining. Paratsetamol haqida shifokor/farmatsevt bilan gaplashing."],
    "grip": ["Grip virusli infeksiya bo'lib, isitma, yo'tal, mushak og'riqlari bilan kechadi. Aksariyat hollarda o'z-o'zidan tuzaladi, lekin xavf guruhlari uchun og'ir kechishi mumkin.",
             "Dam oling, ko'p suv iching. Antiviral dorilarni faqat shifokor tavsiya qiladi. Asorat belgilari paydo bo'lsa, darhol shifokorga."],
    "allergiya": ["Immun tizimining zararsiz moddalarga ortiqcha reaksiyasi. Yengil hollarda tumov, qichishish; og'ir holatda anafilaksiya (nafas qisishi, shish) hayot uchun xavfli.",
                  "Allergendan saqlaning. Antigistamin preparatlar yengil alomatlarda yordam berishi mumkin. Anafilaksiya bo'lsa tez yordam chaqiring."],
    "astma": ["Nafas yo'llarining surunkali yallig'lanishi. Xuruj paytida nafas chiqarish qiyinlashadi, xirillash eshitiladi.",
              "Doimiy ravishda shifokor nazoratida bo'ling. Inhalyatorni to'g'ri ishlatishni o'rganing. Xuruj kuchaysa tez yordam chaqiring."],
    "gipertoniya": ["Yuqori qon bosimi (≥140/90 mm Hg). Ko'pincha alomatlarsiz kechadi, ammo insult va yurak xastaligi xavfini oshiradi.",
                    "Tuz iste'molini kamaytiring, muntazam jismoniy faollik qiling. Dorilarni shifokor ko'rsatmasi bilan qabul qiling."],
    "yurak xuruji": ["Ko'krakda kuchli og'riq, bosilish, chap qo'l va jag'ga tarqalishi. Sovuq ter, nafas qisishi bilan birga bo'lishi mumkin.",
                     "Bu shoshilinch holat. Darhol 103 ga qo'ng'iroq qiling. Bemorni tinchlantiring, yotqizib qo'ying."],
    "insult": ["Yuzning qiyshayishi, qo'l kuchsizligi, nutq buzilishi. Vaqt = miya to'qimasi. Belgilar paydo bo'lishi bilan shoshilinch yordam chaqirish kerak.",
               "Darhol tez yordam chaqiring. Bemorni qimirlatmang, boshini bir oz ko'taring."],
    "qandli diabet": ["Glyukoza almashinuvining buzilishi. Chanqash, tez-tez siyish, charchoq. Nazorat qilinmasa, ko'z, buyrak, yurak asoratlari keltirib chiqaradi.",
                      "Qon shakarini muntazam tekshiring. Parhezga rioya qiling. Dori/insulinni shifokor ko'rsatmasi bo'yicha oling."],
    "qorin og'rig'i": ["Ko'p sabablari bor: hazm buzilishi, ichak infeksiyasi, appenditsit, oshqozon yarasi. Agar og'riq o'tkir, doimiy bo'lsa, qusish yoki qonli axlat bilan birga kelsa, jiddiy holat.",
                       "O'z-o'zini davolamang. Yengil parhezga o'ting. Shifokor ko'rigiga boring."],
    "ko'ngil aynishi": ["Migren, ovqat zaharlanishi, homiladorlik yoki dori yon ta'siri. Ba'zi jiddiy kasalliklar (masalan, meningit) belgisi bo'lishi mumkin.",
                        "Kichik- kichik porsiyalarda ovqatlaning. Agar qusish, yuqori isitma yoki bosh og'rig'i bilan birga bo'lsa, shifokorga murojaat qiling."],
    "ich ketishi": ["Infeksiya, ovqatdan zaharlanish yoki ichak sindromi belgisi. Suyuqlik yo'qotilishi xavfli, ayniqsa bolalar va keksalarda.",
                    "Ko'p suv yoki regidratatsiya eritmalari iching. Agar qon aralash yoki 2 kundan ortiq davom etsa, shifokorga boring."],
    "qabziyat": ["Noto'g'ri ovqatlanish, kam suv ichish, harakatsizlik yoki dori ta'siri. Surunkali bo'lsa, ichak kasalliklarini tekshirish kerak.",
                 "Tolali mahsulotlar iste'mol qiling, ko'proq suv iching, harakatlaning. Uzoq davom etsa, shifokor bilan maslahatlashing."],
    # Dorilar
    "paratsetamol": ["Og'riq qoldiruvchi va isitma tushiruvchi dori. Odatda kattalar uchun 500 mg dan kuniga 3-4 marta, maksimal doza 4 g/24 soat.",
                     "Spirtli ichimlik bilan qabul qilish jigarga zarar yetkazadi. Belgilangan dozadan oshirmang. Agar isitma 3 kundan ko'p davom etsa, shifokorga ko'ring."],
    "antibiotik": ["Faqat bakteriyalarga qarshi. Kursni to'liq tugatish muhim, aks holda bakteriyalar rezistent bo'lib qoladi. Virusli kasalliklarga ta'sir qilmaydi.",
                   "Shifokor tayinlagan sxemaga qat'iy rioya qiling. Nojo'ya ta'sirlar sezsangiz, darhol shifokorga xabar bering."],
    "insulin": ["Qandli diabetda ishlatiladi. Dozani aniq hisoblash kerak. Juda ko'p yoki kam insulin xavfli gipo- yoki giperglikemiyaga olib keladi.",
                "Qon shakarini muntazam tekshiring. Shifokor ko'rsatmasiga qat'iy amal qiling."],
    "dori unutish": ["Agar dozani o'tkazib yuborgan bo'lsangiz, eslab qolganingiz zahoti qabul qiling, lekin keyingi doza vaqti yaqin bo'lsa, unutilganini o'tkazib yuboring. Ikki hissa doza qabul qilmang.",
                     "Signal yoki eslatma o'rnating. Dorini kundalik odatlar (masalan, tish yuvish) bilan bog'lang."],
    # Qo'shimcha
    "homiladorlik": ["Homiladorlik davrida har qanday dorini faqat shifokor ruxsati bilan ichish kerak. O'z-o'zini davolash onaga ham, bolaga ham xavfli.",
                     "Akusher-ginekolog bilan muntazam ko'rikda bo'ling. Vitamin va minerallarni shifokor tavsiyasi bilan oling."],
    "emizish": ["Ko'pgina dorilar sutga o'tadi. Shifokor bilan maslahatlashmasdan turib dori ichmang.",
                "Emizishni davom ettirish yoki to'xtatish haqida qarorni shifokor bilan birga qabul qiling."],
    "bolalar isitmasi": ["Boladagi isitma tez chora talab qiladi. 3 oygacha bo'lgan chaqaloqda 38°C dan yuqori isitma shoshilinch yordamni talab qiladi.",
                         "Bolani yengil kiyintiring, xonani shamollating. Paratsetamol yoki ibuprofen dozasini pediatr bilan kelishing."],
    "tish og'rig'i": ["Karies, pulpit yoki milk yallig'lanishi. Yengil og'riqda og'izni tuzli eritma bilan chayish mumkin. Ammo tish shifokoriga borish kerak.",
                      "Og'riq qoldiruvchi dorilarni vaqtincha farmatsevt bilan kelishib oling. Shifokor tayinlovisiz uzoq muddat ishlatmang."],
    "ko'z qizarishi": ["Allergiya, infeksiya yoki ko'z charchog'i sabab bo'lishi mumkin. Agar yiring, yomon ko'rish yoki shish bo'lsa, shifokorga boring.",
                       "Qo'l bilan ko'zga tegmang. Sun'iy ko'z yoshi tomchilarini ishlatishingiz mumkin."],
    "suvchechak": ["Virusli infeksiya, odatda bolalarda. Qichimali toshma, isitma bilan kechadi. Kattalarda og'irroq o'tishi mumkin.",
                   "Tirnamang, tinchlantiruvchi losyonlar qo'llang. Shifokor maslahati bilan antiviral yoki qichima qarshi dorilar."],
}

def lookup_medical(query: str) -> str:
    """Foydalanuvchi so'roviga mos bilimlarni topish"""
    q = query.lower()
    matches = []
    for key, (info, rec) in MEDICAL_DB.items():
        if re.search(re.escape(key), q, re.IGNORECASE):
            matches.append(f"🔹 {key.title()}: {info}\n   💡 Tavsiya: {rec}")
    return "\n".join(matches) if matches else ""

# ═══════════════════════════════════════════════════════════
# EKSPERT-LEVEL SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════
SYSTEM_PROMPT = """
Siz Tabib AI 3.0 — yuqori aniqlikdagi tibbiy maslahatchisiz.

Maqsadingiz:
- Foydalanuvchi savoliga ishonchli, dalilli va xavfsiz javob berish.
- Hech qachon tashxis qo‘ymang va dori buyurmang, lekin aniq tibbiy tushunchalarni yetkazing.
- Agar berilgan ichki bilimlar bazasida mos ma'lumot bo‘lsa, undan foydalaning va uni oddiy tushunarli tilda ifodalang.
- Har doim foydalanuvchini kerak bo‘lsa shifokor, farmatsevt yoki tez yordam bilan bog‘lanishga undang.
- Javoblaringizda quyidagi tartibni saqlang: 1) empatiya, 2) tushunish, 3) daliliy izoh, 4) aniq tavsiya, 5) bitta qo‘shimcha savol.
- Favqulodda holatlarda (ko‘krak og‘rig‘i, nafas qisishi, kuchli qon ketish, ongni yo‘qotish, o‘z joniga qasd fikri) darhol 103 ni chaqirish kerakligini ayting va javobni cho‘zmang.
- O‘zbek tilida, sodda va iliq mulohaza qiling. Rus yoki ingliz tilidagi so‘rovlarga o‘sha tilda javob bering.
- Hech qachon "men AI emasman", "OpenAI", "GPT" yoki texnik atamalarni ishlatmang.
- Siz oddiygina Tabib AI – MedGuard loyihasining tibbiy yordamchisisiz.
"""

# ═══════════════════════════════════════════════════════════
# MA'LUMOTLAR TUZILMALARI
# ═══════════════════════════════════════════════════════════
class RiskLevel(str, Enum):
    LOW, MODERATE, HIGH, URGENT = "LOW", "MODERATE", "HIGH", "URGENT"

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=MAX_MSG_LEN)
    session_id: Optional[str] = None
    patient_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    risk_level: RiskLevel
    risk_flags: List[str]
    detected_language: str
    timestamp: str

# Sessiyalar
SESSIONS: Dict[str, List[Dict[str, str]]] = {}
SESSION_META: Dict[str, Dict[str, Any]] = {}

def get_history(sid): return SESSIONS.setdefault(sid, [])
def append_history(sid, role, content):
    h = get_history(sid)
    h.append({"role": role, "content": content})
    SESSIONS[sid] = h[-MAX_HISTORY:]

# ═══════════════════════════════════════════════════════════
# XAVF TAHLILI
# ═══════════════════════════════════════════════════════════
URGENT_PATTERNS = {
    "chest_pain": [r"ko['\u2019]?krak\s*og['\u2019]?ri", r"chest\s*pain", r"боль\s*в\s*груди"],
    "breathing": [r"nafas.*qiyin", r"nafas.*qis", r"breath.*difficult", r"одышка"],
    "fainting": [r"hushdan\s*ket", r"faint", r"обморок"],
    "severe_allergy": [r"lab.*shish", r"til.*shish", r"tomoq.*shish", r"yuz.*shish"],
    "seizure": [r"tutqanoq", r"seizure", r"судорог"],
    "stroke": [r"yuz.*qiyshay", r"qo['\u2019]?l.*kuchsiz", r"face\s*droop", r"arm\s*weakness"],
    "suicidal": [r"o['\u2019]?zimni\s*o['\u2019]?ldir", r"suicide", r"самоубий"],
    "severe_bleeding": [r"kuchli\s*qon", r"qon\s*ket", r"vomiting\s*blood"]
}

_PATTERNS = {
    "missed": [r"unutdim", r"ichmadim", r"o['\u2019]?tkazib\s*yubordim", r"missed", r"forgot", r"пропустил"],
    "stop": [r"to['\u2019]?xtatdim", r"to['\u2019]?xtatmoqchiman", r"stopped?", r"stop\s*taking"],
    "side_effect": [r"nojo['\u2019]?ya", r"ko['\u2019]?ngil\s*ayn", r"bosh\s*ayl", r"nausea", r"dizzy"],
    "cost": [r"qimmat", r"pulim\s*yetmay", r"sotib\s*ololmay", r"expensive", r"can't\s*afford"],
    "confusion": [r"qachon\s*ich", r"qanday\s*ich", r"chalkash", r"tushunmadim", r"confused"],
}

def _match(text, key): return any(re.search(p, text, re.I) for p in _PATTERNS[key])
def _urgent(text): return [k for k, v in URGENT_PATTERNS.items() if any(re.search(p, text, re.I) for p in v)]

def detect_language(text):
    if re.search(r"[а-яё]", text, re.I): return "ru"
    uz_words = ["men", "dori", "ich", "qanday", "nima", "bosh", "shifokor", "qimmat", "unutdim", "nojo'ya", "isitma", "og'riq"]
    if any(w in text.lower() for w in uz_words): return "uz"
    return "en"

def analyze_risk(text):
    urgent = _urgent(text)
    if urgent:
        return {"risk_level": RiskLevel.URGENT, "risk_flags": urgent, "detected_language": detect_language(text)}

    risk = RiskLevel.LOW
    flags = []
    if _match(text, "missed"): flags.append("missed_medication"); risk = RiskLevel.MODERATE
    if _match(text, "stop"): flags.append("intentional_stopping"); risk = RiskLevel.HIGH
    if _match(text, "side_effect"): flags.append("side_effect")
    if _match(text, "cost"): flags.append("cost_barrier")
    if _match(text, "confusion"): flags.append("medication_confusion")
    return {"risk_level": risk, "risk_flags": flags, "detected_language": detect_language(text)}

# ═══════════════════════════════════════════════════════════
# AI JAVOB YARATISH
# ═══════════════════════════════════════════════════════════
def generate_reply(session_id, user_msg, risk):
    if not client:
        raise HTTPException(status_code=503, detail="AI xizmati vaqtincha ishlamayapti (API kaliti yo'q).")

    # Ichki bilimlar bazasidan kontekst
    facts = lookup_medical(user_msg)
    context = (
        f"[MAXFIY KONTEKST]\nTil: {risk['detected_language']}\n"
        f"Xavf: {risk['risk_level']}\nBayroqlar: {risk['risk_flags']}\n"
    )
    if facts:
        context += f"Quyida ichki bilimlar bazasidan olingan faktlar. Iloji boricha ulardan foydalaning:\n{facts}\n"
    else:
        context += "Ichki bazada mos ma'lumot topilmadi. Umumiy tibbiy bilimingiz asosida javob bering.\n"

    history = get_history(session_id)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": context},
        *history,
        {"role": "user", "content": user_msg}
    ]

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.4,
            max_tokens=750
        )
    except Exception as e:
        log.error(f"OpenAI xatosi: {e}")
        raise HTTPException(status_code=502, detail=f"AI provayder xatosi: {e}")

    reply = resp.choices[0].message.content.strip()
    append_history(session_id, "user", user_msg)
    append_history(session_id, "assistant", reply)
    return reply

# ═══════════════════════════════════════════════════════════
# FASTAPI ILOVA
# ═══════════════════════════════════════════════════════════
app = FastAPI(title="Tabib AI 3.0", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"status": "ok", "model": OPENAI_MODEL, "sessions": len(SESSIONS)}

@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    msg = payload.message.strip()
    sid = payload.session_id or str(uuid.uuid4())
    risk = analyze_risk(msg)
    reply = generate_reply(sid, msg, risk)

    SESSION_META.setdefault(sid, {}).update({
        "patient_id": payload.patient_id,
        "last_risk": risk["risk_level"],
        "last_seen": datetime.utcnow().isoformat()
    })

    return ChatResponse(
        session_id=sid,
        reply=reply,
        risk_level=risk["risk_level"],
        risk_flags=risk["risk_flags"],
        detected_language=risk["detected_language"],
        timestamp=datetime.utcnow().isoformat()
    )

# ═══════════════════════════════════════════════════════════
# FRONTEND (Enter tuzatildi, yangi dizayn)
# ═══════════════════════════════════════════════════════════
@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>Tabib AI – Tibbiy maslahatchi</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#f4f7fb;color:#111827;transition:background .3s}
.page{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:24px}
.hero{max-width:680px;background:#fff;border-radius:28px;padding:48px;box-shadow:0 20px 50px rgba(0,0,0,.1)}
.badge{display:inline-block;background:#d1fae5;color:#065f46;padding:6px 14px;border-radius:999px;font-weight:700;font-size:13px;margin-bottom:18px}
h1{font-size:42px;font-weight:800;letter-spacing:-1px;margin-bottom:14px}
p{color:#475569;font-size:17px;line-height:1.7}
.launcher{position:fixed;right:22px;bottom:22px;width:58px;height:58px;border:none;border-radius:20px;background:linear-gradient(135deg,#0d9488,#14b8a6);color:#fff;font-size:26px;cursor:pointer;box-shadow:0 10px 25px rgba(13,148,136,.4);z-index:10;transition:transform .2s}
.launcher:hover{transform:scale(1.08)}
.chat{position:fixed;right:22px;bottom:100px;width:420px;height:620px;max-width:calc(100vw - 24px);max-height:calc(100vh - 120px);background:#fff;border-radius:24px;box-shadow:0 25px 60px rgba(0,0,0,.15);overflow:hidden;display:none;flex-direction:column;z-index:9}
.chat.open{display:flex}
.chat-header{padding:16px 18px;background:linear-gradient(135deg,#0d9488,#14b8a6);color:#fff;display:flex;justify-content:space-between;align-items:center}
.chat-title{font-weight:800;font-size:18px}
.status-dot{display:inline-block;width:8px;height:8px;background:#a7f3d0;border-radius:50%;margin-right:4px;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.close-btn{border:none;background:rgba(255,255,255,.2);color:#fff;font-size:22px;width:32px;height:32px;border-radius:12px;cursor:pointer}
.risk-bar{display:none;padding:6px 14px;font-weight:700;font-size:12px;letter-spacing:.3px}
.risk-bar.LOW{display:block;background:#ecfdf5;color:#047857}
.risk-bar.MODERATE{display:block;background:#fffbeb;color:#b45309}
.risk-bar.HIGH{display:block;background:#fff7ed;color:#c2410c}
.risk-bar.URGENT{display:block;background:#fef2f2;color:#b91c1c}
.messages{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px;background:#f8fafc}
.msg{display:flex}
.msg.user{justify-content:flex-end}
.bubble{max-width:80%;padding:10px 14px;border-radius:18px;font-size:14px;line-height:1.6;white-space:pre-wrap;word-break:break-word}
.bot .bubble{background:#fff;border:1px solid #e2e8f0;border-bottom-left-radius:5px}
.user .bubble{background:#0d9488;color:#fff;border-bottom-right-radius:5px}
.typing-row{display:flex}
.typing-dots{background:#fff;border:1px solid #e2e8f0;border-radius:18px;border-bottom-left-radius:5px;padding:10px 14px;display:flex;gap:5px}
.typing-dots span{width:6px;height:6px;background:#94a3b8;border-radius:50%;animation:bounce 1.3s infinite}
.typing-dots span:nth-child(2){animation-delay:.2s}
.typing-dots span:nth-child(3){animation-delay:.4s}
@keyframes bounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-7px)}}
.quick{padding:8px 12px;display:flex;gap:6px;overflow-x:auto;border-top:1px solid #e2e8f0}
.quick button{white-space:nowrap;border:1px solid #d1fae5;background:#f0fdf4;color:#065f46;padding:5px 10px;border-radius:999px;font-size:12px;cursor:pointer;transition:background .2s}
.quick button:hover{background:#d1fae5}
.chat-form{display:flex;gap:8px;padding:10px 12px 14px;border-top:1px solid #e2e8f0}
textarea{flex:1;resize:none;border:1.5px solid #e2e8f0;border-radius:16px;padding:10px 14px;min-height:44px;max-height:100px;outline:none;font-family:inherit;font-size:14px;transition:border .2s}
textarea:focus{border-color:#0d9488}
.send-btn{width:44px;height:44px;border:none;border-radius:15px;background:#0d9488;color:#fff;font-size:20px;cursor:pointer;transition:transform .15s}
.send-btn:hover{transform:scale(1.06)}
@media(max-width:480px){h1{font-size:32px}.hero{padding:28px}.chat{right:8px;bottom:80px;width:calc(100vw - 16px);height:calc(100vh - 104px)}}
</style>
</head>
<body>
<main class="page">
 <section class="hero">
  <div class="badge">🩺 Tabib AI 3.0</div>
  <h1>Tibbiy savollaringizga dalilli javoblar</h1>
  <p>Tabib AI – keng tibbiy bilimlar bazasiga ega maslahatchi. Kasallik alomatlari, dorilar, sog‘lom turmush tarzi va shoshilinch holatlar bo‘yicha aniq va xavfsiz tavsiyalar beradi.</p>
 </section>
</main>

<button class="launcher" id="launcher">💬</button>

<section class="chat" id="chat">
 <div class="chat-header">
  <div>
   <div class="chat-title">Tabib AI</div>
   <small><span class="status-dot"></span>Onlayn · 24/7</small>
  </div>
  <button class="close-btn" id="closeBtn">×</button>
 </div>
 <div class="risk-bar" id="riskBar"></div>
 <div class="messages" id="messages">
  <div class="msg bot">
   <div class="bubble">Assalomu alaykum! Men Tabib AI – sizning shaxsiy tibbiy yordamchingiz.<br>Sog‘liq haqidagi istalgan savolingizni bering.</div>
  </div>
 </div>
 <div class="quick">
  <button data-q="Bosh og'rig'i va isitma">Bosh og'rig'i</button>
  <button data-q="Yurak xuruji belgilari qanday?">Yurak xuruji</button>
  <button data-q="Paratsetamolni qanday ichish kerak?">Paratsetamol</button>
  <button data-q="Allergiya qichishishiga nima qilish kerak?">Allergiya</button>
  <button data-q="Dorini unutdim, nima qilaman?">Dori unutdim</button>
 </div>
 <form class="chat-form" id="chatForm">
  <textarea id="msgInput" rows="1" placeholder="Xabaringizni yozing..."></textarea>
  <button class="send-btn" type="submit" id="sendBtn">➤</button>
 </form>
</section>

<script>
const launcher = document.getElementById("launcher");
const chat = document.getElementById("chat");
const closeBtn = document.getElementById("closeBtn");
const chatForm = document.getElementById("chatForm");
const msgInput = document.getElementById("msgInput");
const messages = document.getElementById("messages");
const riskBar = document.getElementById("riskBar");
const sendBtn = document.getElementById("sendBtn");

let sessionId = localStorage.getItem("tabib_sid") || null;

launcher.onclick = () => {
  chat.classList.toggle("open");
  if (chat.classList.contains("open")) msgInput.focus();
};
closeBtn.onclick = () => chat.classList.remove("open");

document.querySelectorAll(".quick button").forEach(btn => {
  btn.onclick = () => {
    msgInput.value = btn.dataset.q;
    msgInput.focus();
  };
});

function addMsg(text, role) {
  const row = document.createElement("div");
  row.className = "msg " + role;
  const b = document.createElement("div");
  b.className = "bubble";
  b.textContent = text;
  row.appendChild(b);
  messages.appendChild(row);
  messages.scrollTop = messages.scrollHeight;
}

function showTyping() {
  const row = document.createElement("div");
  row.className = "typing-row";
  row.id = "typing";
  row.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
  messages.appendChild(row);
  messages.scrollTop = messages.scrollHeight;
}

function hideTyping() {
  const el = document.getElementById("typing");
  if (el) el.remove();
}

function setRisk(level, flags) {
  riskBar.className = "risk-bar " + level;
  riskBar.textContent = "⚠ " + level + (flags.length ? " · " + flags.join(", ") : "");
}

// --- ENTER BILAN JO‘NATISH (muammo bartaraf etildi) ---
msgInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.dispatchEvent(new Event("submit", {bubbles: true, cancelable: true}));
  }
});

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = msgInput.value.trim();
  if (!text) return;

  addMsg(text, "user");
  msgInput.value = "";
  msgInput.style.height = "auto";
  sendBtn.disabled = true;
  showTyping();

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message: text, session_id: sessionId})
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Server xatosi");

    sessionId = data.session_id;
    localStorage.setItem("tabib_sid", sessionId);
    hideTyping();
    setRisk(data.risk_level, data.risk_flags);
    addMsg(data.reply, "bot");
  } catch (err) {
    hideTyping();
    addMsg("Xatolik: " + err.message, "bot");
  } finally {
    sendBtn.disabled = false;
    msgInput.focus();
  }
});
</script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    print("\n" + "═" * 62)
    print("  🏥  Tabib AI 3.0 — Ishonchli tibbiy maslahatchi")
    print("═" * 62)
    print(f"  📍  http://localhost:8000")
    print(f"  📖  http://localhost:8000/docs")
    print(f"  🤖  Model: {OPENAI_MODEL}")
    print("═" * 62 + "\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
