"""
╔══════════════════════════════════════════════════════════════════════╗
║           TABIB AI 2.0 — KENG QAMROVLI TIBBIY MASLAHATCHI           ║
║           AI Health Hackathon 2026                                   ║
║                                                                      ║
║  Run:   uvicorn main:app --reload --port 8000                        ║
║  Docs:  http://localhost:8000/docs                                   ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import re
import uuid
import logging
import json
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from openai import OpenAI

# ══════════════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════════════
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("TabibAI")

# ══════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o")
MAX_HISTORY    = 20
MAX_MSG_LEN    = 3000

if not OPENAI_API_KEY:
    log.warning("OPENAI_API_KEY o‘rnatilmagan. Iltimos, .env yoki muhit o‘zgaruvchisiga qo‘ying.")

client: Optional[OpenAI] = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ══════════════════════════════════════════════════════════════════════
# TIBBIY MA'LUMOTLAR BAZASI (ichki o‘rnatilgan)
# ══════════════════════════════════════════════════════════════════════
MEDICAL_KNOWLEDGE = {
    "bosh og'rig'i": {
        "info": "Bosh og'rig'i ko'p sabablarga ko'ra bo'lishi mumkin: stress, kuchlanish, migren, suvsizlanish, yuqori qon bosimi yoki ko'z zo'riqishi. Agar bosh og'rig'i to'satdan va juda kuchli bo'lsa, nutq buzilishi yoki holsizlik bilan birga kelsa, darhol shifokorga murojaat qiling.",
        "recommendation": "Suv iching, qorong'i xonada dam oling, yumshoq og'riq qoldiruvchi vositalar haqida shifokor/farmatsevt bilan gaplashing. Agar tez-tez takrorlansa, nevrolog ko'rigidan o'ting."
    },
    "isitma": {
        "info": "Isitma organizmning infeksiyaga qarshi himoya mexanizmi. Odatda 38°C dan yuqori harorat isitma hisoblanadi. Kattalarda 3 kundan ortiq davom etsa yoki 39°C dan oshsa, shifokor ko'rigi zarur.",
        "recommendation": "Ko'proq suyuqlik iching, yengil kiyining, xonani ventilyatsiya qiling. Paratsetamol kabi isitma tushiruvchi dorilar haqida shifokoringizga murojaat qiling."
    },
    "tish og'rig'i": {
        "info": "Tish og'rig'i karies, pulpit, milk yallig'lanishi yoki jag' bo'g'imi muammolari sabab bo'lishi mumkin.",
        "recommendation": "Tish shifokoriga ko'rinish eng to'g'ri yo'l. Og'riqni vaqtincha qoldiruvchi vositalar haqida farmatsevt bilan gaplashing."
    },
    "allergiya": {
        "info": "Allergiya — immun tizimining zararsiz moddalarga ortiqcha reaksiyasi. Alomatlar: tumov, aksirish, qichishish, toshma. Og'ir holatlarda anafilaksiya (nafas qisishi, shish) shoshilinch yordam talab qiladi.",
        "recommendation": "Allergenni aniqlang va undan saqlaning. Antigistamin dorilar yengil alomatlarda yordam berishi mumkin. Shifokor ko'rigidan o'ting."
    },
    "qorin og'rig'i": {
        "info": "Qorin og'rig'i hazm buzilishi, gaz, ichak infeksiyasi, appenditsit yoki oshqozon yarasi kabi sabablardan bo'lishi mumkin. Agar og'riq o'tkir, doimiy bo'lsa, qusish yoki qonli axlat bilan birga kelsa, kechiktirmasdan shifokorga murojaat qiling.",
        "recommendation": "Yengil parhezga o'ting, ko'p suv iching. Dori-darmonlarni shifokor tavsiyasisiz qabul qilmang."
    },
    "paratsetamol": {
        "info": "Paratsetamol og'riq qoldiruvchi va isitma tushiruvchi vosita. Kattalar uchun odatdagi doza 500 mg dan kuniga 3-4 marta, ammo maksimal sutkalik doza 4 g dan oshmasligi kerak.",
        "recommendation": "Spirtli ichimliklar bilan birga qabul qilish jigar uchun xavfli. Dozani oshirib yubormang. Agar isitma 3 kundan ortiq davom etsa, shifokorga murojaat qiling."
    },
    "antibiotik": {
        "info": "Antibiotiklar faqat bakterial infeksiyalarni davolaydi. Viruslarga qarshi ta'sirsiz. Kursni to'liq tugatish juda muhim, aks holda bakteriyalar chidamli bo'lib qolishi mumkin.",
        "recommendation": "Shifokor ko'rsatmasi bo'yicha qabul qiling, o'zboshimchalik bilan to'xtatmang. Nojo'ya ta'sirlar yuzaga kelsa, darhol shifokorga xabar bering."
    },
    "dori unutish": {
        "info": "Agar dorini o'z vaqtida ichishni unutgan bo'lsangiz, eslab qolgan zahoti qabul qiling, lekin keyingi dozaga yaqin vaqt qolgan bo'lsa, unutilgan dozani o'tkazib yuboring va odatdagi jadvalga qayting. Hech qachon ikki hissa doza qabul qilmang.",
        "recommendation": "Telefoningizga eslatma o'rnating yoki dorini kundalik odatlaringizga bog'lang (masalan, tish yuvishdan keyin)."
    },
    "gipertoniya": {
        "info": "Gipertoniya (yuqori qon bosimi) ko'pincha alomatsiz kechadi, ammo insult, yurak xuruji va buyrak kasalligi xavfini oshiradi.",
        "recommendation": "Doimiy ravishda shifokor ko'rigida bo'ling, tuz iste'molini kamaytiring, muntazam jismoniy faollik qiling."
    },
    "diabet": {
        "info": "Qandli diabet — qonda glyukoza miqdori yuqori bo'lgan holat. Asosiy belgilari: chanqash, tez-tez siyish, charchoq. Nazoratsiz qolsa, yurak-qon tomir, ko'z, buyrak asoratlariga olib keladi.",
        "recommendation": "Parhezga rioya qiling, qon qandini muntazam tekshirib turing, insulin yoki tabletkalarni shifokor ko'rsatmasi asosida qabul qiling."
    },
    "yo'tal": {
        "info": "Yo'tal shamollash, bronxit, allergiya yoki o'pka infeksiyasi belgisi bo'lishi mumkin. 2 haftadan ortiq davom etsa, surunkali bo'lishi mumkin.",
        "recommendation": "Ko'p suyuqlik iching, iliq bug' bilan nafas oling. Kuchli yo'talda shifokor ko'rigi zarur."
    },
    "ko'ngil aynishi": {
        "info": "Ko'ngil aynishi ovqat zaharlanishi, migren, homiladorlik yoki dori yon ta'siri bo'lishi mumkin.",
        "recommendation": "Kichik- kichik porsiyalarda ovqatlang, yog'li va achchiq taomlardan saqlaning. Agar qusish bilan birga kuchli bosh og'rig'i yoki hushdan ketish bo'lsa, tez yordam chaqiring."
    },
    "find_job": {
        "info": "Bu tibbiy yordamchi. Ish qidirish bo'yicha maslahat bera olmayman.",
        "recommendation": "Iltimos, sog'liq masalalari bo'yicha so'rang."
    }
}


def search_medical_facts(query: str) -> str:
    """Foydalanuvchi matnidan tibbiy faktlarni qidiradi va topilgan ma'lumotlarni qaytaradi."""
    q = query.lower()
    results = []
    for key, fact in MEDICAL_KNOWLEDGE.items():
        # agar kalit so'z so'rovda bo'lsa yoki soha bo'yicha mos kelsa
        if re.search(re.escape(key), q, re.IGNORECASE):
            results.append(f"🧠 {key}: {fact['info']} 💡 Tavsiya: {fact['recommendation']}")
    return "\n".join(results) if results else ""


# ══════════════════════════════════════════════════════════════════════
# YANGI TIZIM PROMPTI: TIBBIY EKSPERT
# ══════════════════════════════════════════════════════════════════════
SYSTEM_PROMPT = """
# Tabib AI 2.0 – Keng qamrovli tibbiy maslahatchi

Siz Tabib AI’siz. Siz **tibbiyot bo‘yicha keng bilimga ega raqamli yordamchisiz**. Sizning vazifangiz – foydalanuvchilarga tibbiy masalalar bo‘yicha **aniq, dalillarga asoslangan, amaliy va xavfsiz tavsiyalar** berishdir.

## Asosiy tamoyillar:
- Siz **shifokor emassiz**, tashxis qo‘ymaysiz, dori tavsiya qilmaysiz, lekin umumiy tibbiy ma’lumotlar va xavfsiz qadamlar haqida gapira olasiz.
- Har doim **odamni shifokor yoki farmatsevt bilan bog‘lanishga undang** – ayniqsa, alomat jiddiy bo‘lsa.
- **Foydalanuvchining tilida, oddiy va iliq uslubda** gapiring.
- **Tibbiy bilimlaringizni eng so‘nggi va ishonchli manbalarga asoslang**, kerak bo‘lsa ichki bazadan olingan faktlarni ishlating.
- **Xavfli holatlarda darhol tez yordam chaqirish kerakligini ayting**, boshqa gaplarni cho‘zmang.

## Qachon shoshilinch yordam kerak (qizil bayroqlar):
Agar bemor quyidagilardan birini aytsa, darhol 103 raqamiga qo‘ng‘iroq qilish yoki shoshilinch tibbiy yordamga murojaat qilishni qat’iy tavsiya qiling:
- Ko‘krak og‘rig‘i / bosilish / siqilish
- Nafas olishda og‘ir qiyinchilik
- Hushdan ketish yoki kuchli bosh aylanishi
- Yuz, lab, til shishishi va nafas qisishi
- Tutqanoq (talvasa)
- Insult belgilari (yuzning qiyshayishi, qo‘l kuchsizligi, nutq buzilishi)
- Kuchli qon ketish yoki qusish qon bilan
- O‘z joniga qasd qilish fikrlari
- Dori qabul qilgandan keyin to‘satdan paydo bo‘lgan kuchli allergik reaksiya

Bunday hollarda juda qisqa va aniq javob bering, masalan: “Bu shoshilinch tibbiy yordam talab qiladigan holat. Iltimos, hoziroq 103 ga qo‘ng‘iroq qiling. Yoningizda kimdir bormi?”

## Qanday javob berish kerak:
Har bir javobingizda quyidagi qismlar bo‘lishi kerak (tabiiy ravishda, raqamlab emas):
1. **Empatiya** – his-tuyg‘ularini tushuning.
2. **Tushunish aks-sadosi** – eshitganingizni qisqacha izohlang.
3. **Dalilli izoh** – nima uchun bunday bo‘layotgani haqida oddiy tibbiy tushuntirish bering.
4. **Amaliy tavsiya** – xavfsiz va aniq birinchi qadam.
5. **Kuzatuvchi savol** – suhbatni davom ettirish uchun bitta savol bering (shoshilinch holatlardan tashqari).

## Tibbiy faktlar bazasidan qanday foydalanish:
Foydalanuvchi so‘roviga qarab, ichki bazamizdan topilgan **aniq tibbiy ma’lumotlar** sizga alohida kontekst sifatida taqdim etiladi. Siz bu faktlardan foydalaning, lekin ularni ko‘chirma qilib emas, o‘z so‘zlaringiz bilan bering. “Bazaga ko‘ra...” deb yozmang, odam tilida gapiring.

## Dori-darmonga oid maslahatlar:
- Agar bemor dori ichishni unutgan bo‘lsa, xavfsiz qoidalarni tushuntiring: hech qachon ikki doza qabul qilmaslik, shifokor ko‘rsatmasiga amal qilish.
- Nojo‘ya ta’sir haqida so‘rasa, alomat darajasiga qarab shifokorga murojaat qilish kerakligini uqtiring.
- Dori narxi muammosi bo‘lsa, arzonroq muqobil variantlar haqida shifokor bilan gaplashishni tavsiya eting.

## Taqiqlangan harakatlar:
- “Aniq bilaman...” demang.
- “Tashvishlanmang” jiddiy alomatlar uchun ishlatmang.
- “Dorini to‘xtating” deyolmaysiz (faqat shoshilinch holatda va tez yordamga yo‘naltirgan holatda).
- Hech qachon o‘zingizni sun’iy intellekt ekanligingizni aytib, OpenAI, GPT, model kabi so‘zlarni ishlatmang.
- Tibbiy maslahatni bemorning shifokoridan yuqori qo‘ymang.

Esingizda bo‘lsin: siz **Tabib AI**siz, odamlarga sog‘lom qaror qabul qilishda ko‘mak berasiz, ammo ularning asosiy tayanchi – haqiqiy tibbiyot xodimlari.
"""

# ══════════════════════════════════════════════════════════════════════
# DATA MODELS
# ══════════════════════════════════════════════════════════════════════
class RiskLevel(str, Enum):
    LOW      = "LOW"
    MODERATE = "MODERATE"
    HIGH     = "HIGH"
    URGENT   = "URGENT"

class ChatRequest(BaseModel):
    message:    str = Field(..., min_length=1, max_length=MAX_MSG_LEN)
    session_id: Optional[str] = None
    patient_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id:        str
    reply:             str
    risk_level:        RiskLevel
    risk_flags:        List[str]
    detected_language: str
    timestamp:         str

# ══════════════════════════════════════════════════════════════════════
# SESSIONS
# ══════════════════════════════════════════════════════════════════════
SESSIONS:      Dict[str, List[Dict[str, str]]] = {}
SESSION_META:  Dict[str, Dict[str, Any]]       = {}

def get_history(sid: str) -> List[Dict[str, str]]:
    return SESSIONS.setdefault(sid, [])

def append_history(sid: str, role: str, content: str):
    h = get_history(sid)
    h.append({"role": role, "content": content})
    SESSIONS[sid] = h[-MAX_HISTORY:]

# ══════════════════════════════════════════════════════════════════════
# RISK ANALYSIS (xavf tahlili – o‘zgarishsiz)
# ══════════════════════════════════════════════════════════════════════
URGENT_PATTERNS = {
    "chest_pain": [r"ko['\u2019]?krak\s*og['\u2019]?ri", r"chest\s*pain", r"боль\s*в\s*груди"],
    "breathing_difficulty": [r"nafas.*qiyin", r"nafas.*qis", r"breath.*difficult", r"shortness\s*of\s*breath", r"трудно\s*дышать"],
    "fainting": [r"hushdan\s*ket", r"faint", r"passed\s*out", r"обморок", r"hushsiz"],
    "severe_allergy": [r"lab.*shish", r"til.*shish", r"tomoq.*shish", r"yuz.*shish", r"swelling.*(lip|tongue|throat|face)", r"отек.*(губ|язык|горл|лиц)"],
    "seizure": [r"tutqanoq", r"seizure", r"convulsion", r"судорог", r"приступ"],
    "stroke_signs": [r"yuz.*qiyshay", r"qo['\u2019]?l.*kuchsiz", r"gapira\s*olmay", r"face\s*droop", r"arm\s*weakness", r"speech\s*difficult", r"перекос.*лиц"],
    "severe_bleeding": [r"kuchli\s*qon", r"qon\s*ket", r"severe\s*bleeding", r"сильное\s*кровотечение"],
    "suicidal": [r"o['\u2019]?zimni\s*o['\u2019]?ldir", r"jonimga\s*qasd", r"suicide", r"kill\s*myself", r"самоубий"],
}

_PATTERNS = {
    "missed":       [r"unutdim", r"ichmadim", r"o['\u2019]?tkazib\s*yubordim", r"missed", r"forgot", r"skip+ed?", r"забыл", r"пропустил"],
    "stop":         [r"to['\u2019]?xtatdim", r"to['\u2019]?xtatmoqchiman", r"ichgim\s*kelmayapti", r"stopped?", r"stop\s*taking", r"перестал"],
    "side_effect":  [r"nojo['\u2019]?ya", r"ko['\u2019]?ngil\s*ayn", r"bosh\s*ayl", r"bosh\s*og['\u2019]?ri", r"toshma", r"nausea", r"dizzy", r"side\s*effect"],
    "cost":         [r"qimmat", r"pulim\s*yetmay", r"sotib\s*ololmay", r"tejay", r"expensive", r"can't\s*afford"],
    "confusion":    [r"qachon\s*ich", r"qanday\s*ich", r"chalkash", r"tushunmadim", r"when\s*should", r"how\s*should", r"confused"],
    "double_dose":  [r"ikki\s*baravar", r"2\s*ta\s*ichdim", r"double\s*dose", r"took\s*two"],
    "pregnancy":    [r"homilador", r"emiz", r"pregnan", r"breastfeed"],
}

def _match(text: str, key: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in _PATTERNS[key])

def _match_urgent(text: str) -> List[str]:
    found = []
    for label, pats in URGENT_PATTERNS.items():
        if any(re.search(p, text, re.IGNORECASE) for p in pats):
            found.append(label)
    return found

def detect_language(text: str) -> str:
    if re.search(r"[а-яё]", text, re.IGNORECASE):
        return "ru"
    uz_words = ["men", "dori", "ich", "qanday", "nima", "bosh", "shifokor", "qimmat", "unutdim", "nojo'ya", "isitma", "og'riq"]
    if any(w in text.lower() for w in uz_words):
        return "uz"
    return "en"

def analyze_risk(message: str) -> Dict[str, Any]:
    text = message.strip()
    flags = []
    urgent = _match_urgent(text)
    if urgent:
        return {"risk_level": RiskLevel.URGENT, "risk_flags": urgent, "detected_language": detect_language(text)}
    risk = RiskLevel.LOW
    if _match(text, "missed"):
        flags.append("missed_medication")
        risk = RiskLevel.MODERATE
    if _match(text, "stop"):
        flags.append("intentional_stopping")
        risk = RiskLevel.HIGH
    if _match(text, "side_effect"):
        flags.append("side_effect")
        if risk == RiskLevel.LOW: risk = RiskLevel.MODERATE
    if _match(text, "cost"):
        flags.append("cost_barrier")
        if risk == RiskLevel.LOW: risk = RiskLevel.MODERATE
    if _match(text, "confusion"):
        flags.append("medication_confusion")
        if risk == RiskLevel.LOW: risk = RiskLevel.MODERATE
    if _match(text, "double_dose"):
        flags.append("possible_double_dose")
        risk = RiskLevel.HIGH
    if _match(text, "pregnancy"):
        flags.append("pregnancy_or_breastfeeding")
        risk = RiskLevel.HIGH if risk in (RiskLevel.LOW, RiskLevel.MODERATE) else risk
    return {"risk_level": risk, "risk_flags": flags, "detected_language": detect_language(text)}

# ══════════════════════════════════════════════════════════════════════
# AI JAVOB YARATISH
# ══════════════════════════════════════════════════════════════════════
def generate_reply(session_id: str, user_message: str, risk: Dict[str, Any]) -> str:
    if client is None:
        raise HTTPException(status_code=503, detail="AI xizmati vaqtincha ishlamayapti (API kaliti yo‘q).")
    # Ichki bilimlar bazasidan qo‘shimcha kontekst
    facts = search_medical_facts(user_message)
    internal_context = f"[TIZIM UCHUN MAXFIY KONTEKST]\nTil: {risk['detected_language']}\nXavf: {risk['risk_level']}\nBayroqlar: {risk['risk_flags']}\n"
    if facts:
        internal_context += f"Quyidagi tibbiy ma'lumotlardan foydalaning (agar mos kelsa):\n{facts}\n"
    else:
        internal_context += "Maxsus tibbiy fakt topilmadi, umumiy bilimingiz asosida javob bering.\n"
    history = get_history(session_id)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": internal_context},
        *history,
        {"role": "user", "content": user_message},
    ]
    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.5,
            max_tokens=750,
            frequency_penalty=0.2,
            presence_penalty=0.2,
        )
    except Exception as exc:
        log.error(f"OpenAI xatosi: {exc}")
        raise HTTPException(status_code=502, detail=f"AI provayder xatosi: {exc}")
    reply = completion.choices[0].message.content.strip()
    log.info(f"[{session_id[:8]}] risk={risk['risk_level']} tokens={completion.usage.total_tokens if completion.usage else '?'}")
    append_history(session_id, "user", user_message)
    append_history(session_id, "assistant", reply)
    return reply

# ══════════════════════════════════════════════════════════════════════
# FASTAPI
# ══════════════════════════════════════════════════════════════════════
app = FastAPI(title="Tabib AI 2.0 — Keng qamrovli tibbiy maslahatchi", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"status": "ok", "model": OPENAI_MODEL, "active_sessions": len(SESSIONS)}

@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    message = payload.message.strip()
    session_id = payload.session_id or str(uuid.uuid4())
    risk = analyze_risk(message)
    reply = generate_reply(session_id, message, risk)
    SESSION_META.setdefault(session_id, {}).update({
        "patient_id": payload.patient_id,
        "last_risk": risk["risk_level"],
        "last_seen": datetime.utcnow().isoformat()
    })
    return ChatResponse(
        session_id=session_id,
        reply=reply,
        risk_level=risk["risk_level"],
        risk_flags=risk["risk_flags"],
        detected_language=risk["detected_language"],
        timestamp=datetime.utcnow().isoformat(),
    )

@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    return {"session_id": session_id, "meta": SESSION_META.get(session_id, {}), "messages": SESSIONS.get(session_id, [])}

@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    SESSIONS.pop(session_id, None)
    SESSION_META.pop(session_id, None)
    return {"status": "deleted"}

# ══════════════════════════════════════════════════════════════════════
# YANGI FRONTEND (Enter muammosi hal qilindi, UI yaxshilandi)
# ══════════════════════════════════════════════════════════════════════
@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tabib AI – Tibbiy maslahatchi</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,sans-serif;background:#eef2f5;color:#1e293b;transition:background .3s}
.page{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px}
.hero{max-width:680px;background:#fff;border-radius:28px;padding:48px;box-shadow:0 25px 50px -12px rgba(0,0,0,.15)}
.badge{display:inline-block;background:#d1fae5;color:#065f46;padding:6px 14px;border-radius:999px;font-weight:700;font-size:13px;margin-bottom:18px}
h1{font-size:42px;font-weight:800;letter-spacing:-0.5px;margin-bottom:14px}
p{color:#475569;font-size:17px;line-height:1.7}
.launcher{position:fixed;right:22px;bottom:22px;width:60px;height:60px;border:none;border-radius:20px;background:linear-gradient(135deg,#0d9488,#14b8a6);color:#fff;font-size:26px;cursor:pointer;box-shadow:0 10px 25px rgba(13,148,136,.4);z-index:10;transition:transform .2s}
.launcher:hover{transform:scale(1.08)}
.chat{position:fixed;right:22px;bottom:100px;width:400px;height:620px;max-width:calc(100vw - 24px);max-height:calc(100vh - 120px);background:#fff;border-radius:24px;box-shadow:0 20px 50px rgba(0,0,0,.2);overflow:hidden;display:none;flex-direction:column;z-index:9}
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
.chat-form textarea{flex:1;resize:none;border:1.5px solid #e2e8f0;border-radius:16px;padding:10px 14px;min-height:42px;max-height:100px;outline:none;font-family:inherit;font-size:14px}
.chat-form textarea:focus{border-color:#0d9488}
.send-btn{width:44px;height:44px;border:none;border-radius:15px;background:#0d9488;color:#fff;font-size:20px;cursor:pointer;transition:transform .15s}
.send-btn:hover{transform:scale(1.05)}
@media(max-width:540px){h1{font-size:30px}.hero{padding:28px}.chat{right:8px;bottom:88px;width:calc(100vw - 16px)}}
</style>
</head>
<body>
<main class="page">
 <section class="hero">
  <div class="badge">🩺 Tabib AI 2.0</div>
  <h1>Tibbiy savollaringizga ishonchli javoblar</h1>
  <p>Tabib AI – zamonaviy tibbiy yordamchi. Sizga dori-darmon, alomatlar, sog‘lom turmush tarzi va shifokorga murojaat qilish bo‘yicha aniq, dalilli tavsiyalar beradi. 24/7 onlayn.</p>
 </section>
</main>

<button class="launcher" id="launcher">💬</button>

<section class="chat" id="chat">
 <div class="chat-header">
  <div>
   <div class="chat-title">Tabib AI</div>
   <small><span class="status-dot"></span>Onlayn</small>
  </div>
  <button class="close-btn" id="closeBtn">×</button>
 </div>
 <div class="risk-bar" id="riskBar"></div>
 <div class="messages" id="messages">
  <div class="msg bot">
   <div class="bubble">Assalomu alaykum! Men Tabib AI – tibbiy maslahatchi yordamchingizman.<br>Alomatlar, dori-darmon, sog‘lom odatlar yoki shifokorga qachon murojaat qilish haqida so‘rang.</div>
  </div>
 </div>
 <div class="quick">
  <button data-q="Menda bosh og'rig'i va isitma bor">Bosh og'rig'i + isitma</button>
  <button data-q="Yo'tal va ko'krak qisishi">Yo'tal</button>
  <button data-q="Allergiyadan shish paydo bo'ldi">Allergiya</button>
  <button data-q="Qandli diabetda parhez qanday bo'ladi?">Diabet parhez</button>
  <button data-q="Dori ichishni unutdim, nima qilish kerak?">Dori unutdim</button>
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

launcher.onclick = () => { chat.classList.toggle("open"); if(chat.classList.contains("open")) msgInput.focus(); };
closeBtn.onclick = () => chat.classList.remove("open");

document.querySelectorAll(".quick button").forEach(btn => {
  btn.onclick = () => { msgInput.value = btn.dataset.q; msgInput.focus(); };
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
  const t = document.getElementById("typing");
  if(t) t.remove();
}

function setRisk(level, flags) {
  riskBar.className = "risk-bar " + level;
  riskBar.textContent = "⚠ " + level + (flags.length ? " · " + flags.join(", ") : "");
}

msgInput.addEventListener("keydown", function(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.dispatchEvent(new Event('submit', {bubbles: true, cancelable: true}));
  }
});

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = msgInput.value.trim();
  if(!text) return;
  addMsg(text, "user");
  msgInput.value = "";
  msgInput.style.height = "auto";
  sendBtn.disabled = true;
  showTyping();
  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({message: text, session_id: sessionId})
    });
    const data = await res.json();
    if(!res.ok) throw new Error(data.detail || "Server xatosi");
    sessionId = data.session_id;
    localStorage.setItem("tabib_sid", sessionId);
    hideTyping();
    setRisk(data.risk_level, data.risk_flags);
    addMsg(data.reply, "bot");
  } catch(err) {
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
    print("  🏥  TABIB AI 2.0 — Keng qamrovli tibbiy maslahatchi")
    print("═" * 62)
    print(f"  📍  http://localhost:8000")
    print(f"  📖  http://localhost:8000/docs")
    print(f"  🤖  Model: {OPENAI_MODEL}")
    print("═" * 62 + "\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
