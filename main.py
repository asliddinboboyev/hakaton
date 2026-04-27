import os
import re
import uuid
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# ENV
# ============================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# ============================================================
# PROMPT LOADER
# ============================================================

DEFAULT_SYSTEM_PROMPT = """
You are Tabib AI.

You are a professional AI health adherence coach and patient-support assistant.

You help patients continue prescribed treatment safely, avoid treatment abandonment,
understand medicine routines, manage missed doses, side effects, confusion, cost,
and emotional burnout.

You are not a doctor. You do not diagnose diseases. You do not prescribe medication.
You do not provide exact personalized dosage instructions. You do not override doctor instructions.

Always respond with:
1. Empathy
2. Understanding
3. Clear explanation
4. Actionable guidance
5. Follow-up question

Primary language: Uzbek. Also support Russian and English.
Auto-detect user language and respond in the same language.

Escalate emergency symptoms immediately.
"""


def load_system_prompt() -> str:
    """
    Reads the full Tabib AI prompt from prompt.txt.
    If prompt.txt does not exist, uses DEFAULT_SYSTEM_PROMPT.
    """
    prompt_path = os.getenv("TABIB_PROMPT_FILE", "prompt.txt")

    if not os.path.exists(prompt_path):
        print(f"WARNING: {prompt_path} not found. Using DEFAULT_SYSTEM_PROMPT.")
        return DEFAULT_SYSTEM_PROMPT

    try:
        with open(prompt_path, "r", encoding="utf-8") as file:
            content = file.read().strip()

        if not content:
            print(f"WARNING: {prompt_path} is empty. Using DEFAULT_SYSTEM_PROMPT.")
            return DEFAULT_SYSTEM_PROMPT

        return content

    except Exception as exc:
        print(f"WARNING: Could not read {prompt_path}: {exc}. Using DEFAULT_SYSTEM_PROMPT.")
        return DEFAULT_SYSTEM_PROMPT


TABIB_SYSTEM_PROMPT = load_system_prompt()


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Tabib AI Expert Chatbot",
    description="Clinical-grade medication adherence chatbot backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATA MODELS
# ============================================================

class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    URGENT = "URGENT"


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    patient_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    risk_level: RiskLevel
    risk_flags: List[str]
    detected_language: str
    timestamp: str


# ============================================================
# MEMORY
# ============================================================

SESSIONS: Dict[str, List[Dict[str, str]]] = {}
SESSION_META: Dict[str, Dict[str, Any]] = {}

MAX_HISTORY_MESSAGES = 12


# ============================================================
# RISK ENGINE
# ============================================================

URGENT_PATTERNS = {
    "chest_pain": [
        r"ko[‘']?krak og[‘']?rig", r"chest pain", r"боль в груди",
    ],
    "breathing_difficulty": [
        r"nafas.*qiyin", r"nafas.*qis", r"breath.*difficult", r"shortness of breath",
        r"трудно дышать", r"одышка",
    ],
    "fainting": [
        r"hushdan ket", r"faint", r"passed out", r"обморок", r"потерял сознание",
    ],
    "severe_allergy": [
        r"lab.*shish", r"til.*shish", r"tomoq.*shish", r"yuz.*shish",
        r"swelling.*lip", r"swelling.*tongue", r"swelling.*throat",
        r"отек.*губ", r"отек.*язык", r"отек.*горл",
    ],
    "seizure": [
        r"tutqanoq", r"seizure", r"convulsion", r"судорог", r"приступ",
    ],
    "stroke_signs": [
        r"yuz.*qiyshay", r"qo[‘']?l.*kuchsiz", r"gapira olmay",
        r"face droop", r"arm weakness", r"speech difficulty",
        r"перекос.*лиц", r"слабость.*рук", r"нарушение речи",
    ],
    "severe_bleeding": [
        r"kuchli qon", r"qon ket", r"severe bleeding", r"сильное кровотечение",
        r"vomiting blood", r"qon qus", r"рвота кровью",
    ],
    "suicidal": [
        r"o[‘']?zimni o[‘']?ldir", r"jonimga qasd", r"suicide", r"kill myself",
        r"самоубий", r"убить себя",
    ],
    "loss_of_consciousness": [
        r"loss of consciousness", r"без сознания", r"hushsiz",
    ],
    "severe_rash": [
        r"kuchli toshma", r"teri ko[‘']?ch", r"rash.*fever", r"skin peeling",
        r"сильная сыпь", r"кожа.*слез",
    ],
}


MISSED_PATTERNS = [
    r"unutdim", r"ichmadim", r"o[‘']?tkazib yubordim", r"qabul qilmadim",
    r"missed", r"forgot", r"skip", r"skipped",
    r"забыл", r"пропустил", r"не пил", r"не принимал",
]

STOP_PATTERNS = [
    r"to[‘']?xtatdim", r"to[‘']?xtatmoqchiman", r"ichgim kelmayapti", r"endi ichmayman",
    r"stopped", r"stop taking", r"quit", r"don[’']?t want to take",
    r"перестал", r"бросил", r"не хочу принимать",
]

SIDE_EFFECT_PATTERNS = [
    r"nojo[‘']?ya", r"ko[‘']?ngil ayn", r"bosh ayl", r"bosh og[‘']?ri", r"toshma",
    r"nausea", r"dizzy", r"headache", r"rash", r"side effect", r"stomach pain",
    r"тошнит", r"головокруж", r"головная боль", r"сыпь", r"побоч",
]

COST_PATTERNS = [
    r"qimmat", r"pulim yetmay", r"sotib ololmay", r"tejay", r"yarimta ich",
    r"expensive", r"can[’']?t afford", r"cost", r"ration",
    r"дорого", r"не могу купить", r"нет денег",
]

CONFUSION_PATTERNS = [
    r"qachon ich", r"qanday ich", r"oldinmi", r"keyinmi", r"chalkash", r"tushunmadim",
    r"when should", r"how should", r"before food", r"after food", r"confused",
    r"когда принимать", r"как принимать", r"до еды", r"после еды", r"не понимаю",
]

SWALLOW_PATTERNS = [
    r"yuta olmay", r"yutish qiyin", r"tabletka katta", r"kapsula katta",
    r"can[’']?t swallow", r"hard to swallow", r"pill too big",
    r"не могу глотать", r"трудно глотать", r"таблетка большая",
]

CRITICAL_MED_PATTERNS = [
    r"insulin", r"инсулин",
    r"tutqanoq", r"epilep", r"seizure", r"судорог", r"эпилеп",
    r"warfarin", r"варфарин", r"blood thinner", r"anticoagulant", r"qon suyult",
    r"\btb\b", r"sil", r"tuberculosis", r"туберкул",
    r"\bhiv\b", r"vih", r"вич",
    r"transplant", r"anti-rejection",
    r"nitroglycerin", r"yurak", r"heart failure",
    r"prednisolone", r"hydrocortisone", r"steroid",
]

DOUBLE_DOSE_PATTERNS = [
    r"ikki baravar", r"2 ta ichdim", r"double dose", r"took two", r"двойную доз",
]

PREGNANCY_PATTERNS = [
    r"homilador", r"emiz", r"pregnan", r"breastfeed", r"беремен", r"кормлю груд",
]


def match_any(text: str, patterns: List[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def detect_language(text: str) -> str:
    lower = text.lower()

    if re.search(r"[а-яё]", lower):
        return "ru"

    uz_words = [
        "men", "menga", "dori", "ichdim", "ichmadim", "qanday", "nima",
        "yaxshi", "og‘riq", "og'riq", "bosh", "ko‘ngil", "ko'ngil",
        "shifokor", "farmatsevt", "qimmat", "unutdim", "qabul",
    ]

    if any(word in lower for word in uz_words):
        return "uz"

    return "en"


def extract_missed_days(text: str) -> Optional[int]:
    lower = text.lower()

    digit_match = re.search(r"(\d+)\s*(kun|kunda|kundan|day|days|день|дня|дней)", lower)
    if digit_match:
        return int(digit_match.group(1))

    word_numbers = {
        "bir": 1,
        "bitta": 1,
        "one": 1,
        "один": 1,
        "одна": 1,
        "ikki": 2,
        "two": 2,
        "два": 2,
        "две": 2,
        "uch": 3,
        "three": 3,
        "три": 3,
        "to‘rt": 4,
        "to'rt": 4,
        "tort": 4,
        "four": 4,
        "четыре": 4,
        "besh": 5,
        "five": 5,
        "пять": 5,
    }

    for word, number in word_numbers.items():
        if re.search(rf"\b{re.escape(word)}\b.*(kun|day|дн)", lower):
            return number

    if any(x in lower for x in ["kecha", "yesterday", "вчера"]):
        return 1

    return None


def analyze_risk(message: str) -> Dict[str, Any]:
    text = message.strip().lower()
    flags: List[str] = []

    urgent_found = []
    for flag, patterns in URGENT_PATTERNS.items():
        if match_any(text, patterns):
            urgent_found.append(flag)

    if urgent_found:
        return {
            "risk_level": RiskLevel.URGENT,
            "risk_flags": urgent_found,
            "detected_language": detect_language(message),
        }

    risk = RiskLevel.LOW

    if match_any(text, MISSED_PATTERNS):
        flags.append("missed_medication")
        risk = RiskLevel.MODERATE

        missed_days = extract_missed_days(text)
        if missed_days and missed_days >= 2:
            flags.append("missed_2_plus_days")
            risk = RiskLevel.HIGH

    if match_any(text, CRITICAL_MED_PATTERNS):
        flags.append("critical_medication_possible")
        if "missed_medication" in flags:
            flags.append("critical_medication_missed")
            risk = RiskLevel.HIGH

    if match_any(text, STOP_PATTERNS):
        flags.append("intentional_stopping")
        risk = RiskLevel.HIGH

    if match_any(text, SIDE_EFFECT_PATTERNS):
        flags.append("side_effect")
        if risk == RiskLevel.LOW:
            risk = RiskLevel.MODERATE

    if match_any(text, COST_PATTERNS):
        flags.append("cost_barrier")
        if any(x in text for x in ["yarimta", "ration", "tejay", "half"]):
            risk = RiskLevel.HIGH
        elif risk == RiskLevel.LOW:
            risk = RiskLevel.MODERATE

    if match_any(text, CONFUSION_PATTERNS):
        flags.append("medication_confusion")
        if risk == RiskLevel.LOW:
            risk = RiskLevel.MODERATE

    if match_any(text, SWALLOW_PATTERNS):
        flags.append("swallowing_difficulty")
        if risk == RiskLevel.LOW:
            risk = RiskLevel.MODERATE

    if match_any(text, DOUBLE_DOSE_PATTERNS):
        flags.append("possible_double_dose")
        risk = RiskLevel.HIGH

    if match_any(text, PREGNANCY_PATTERNS):
        flags.append("pregnancy_or_breastfeeding")
        if risk in [RiskLevel.LOW, RiskLevel.MODERATE]:
            risk = RiskLevel.HIGH

    return {
        "risk_level": risk,
        "risk_flags": flags,
        "detected_language": detect_language(message),
    }


# ============================================================
# AI RESPONSE
# ============================================================

def trim_history(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return messages[-MAX_HISTORY_MESSAGES:]


def build_context_prompt(risk_data: Dict[str, Any]) -> str:
    return f"""
CURRENT BACKEND SAFETY ANALYSIS:
detected_language: {risk_data["detected_language"]}
risk_level: {risk_data["risk_level"]}
risk_flags: {risk_data["risk_flags"]}

Use this analysis silently.
Do not expose internal risk analysis unless directly useful.
If URGENT, prioritize emergency guidance.
If HIGH, recommend doctor/pharmacist contact.
Do not diagnose, prescribe, or give exact dosage.
"""


def generate_reply(session_id: str, user_message: str, risk_data: Dict[str, Any]) -> str:
    if client is None:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not configured. Add it to .env file.",
        )

    if session_id not in SESSIONS:
        SESSIONS[session_id] = []

    history = trim_history(SESSIONS[session_id])

    messages = [
        {"role": "system", "content": TABIB_SYSTEM_PROMPT},
        {"role": "system", "content": build_context_prompt(risk_data)},
    ]

    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.35,
            max_tokens=700,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI provider error: {str(exc)}")

    reply = completion.choices[0].message.content.strip()

    SESSIONS[session_id].append({"role": "user", "content": user_message})
    SESSIONS[session_id].append({"role": "assistant", "content": reply})
    SESSIONS[session_id] = trim_history(SESSIONS[session_id])

    return reply


# ============================================================
# API ROUTES
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "Tabib AI",
        "model": OPENAI_MODEL,
        "prompt_loaded_chars": len(TABIB_SYSTEM_PROMPT),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    message = payload.message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    session_id = payload.session_id or str(uuid.uuid4())

    risk_data = analyze_risk(message)
    reply = generate_reply(session_id, message, risk_data)

    SESSION_META.setdefault(session_id, {})
    SESSION_META[session_id].update({
        "patient_id": payload.patient_id,
        "last_risk_level": risk_data["risk_level"],
        "last_risk_flags": risk_data["risk_flags"],
        "last_seen": datetime.utcnow().isoformat(),
    })

    return ChatResponse(
        session_id=session_id,
        reply=reply,
        risk_level=risk_data["risk_level"],
        risk_flags=risk_data["risk_flags"],
        detected_language=risk_data["detected_language"],
        timestamp=datetime.utcnow().isoformat(),
    )


@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    return {
        "session_id": session_id,
        "meta": SESSION_META.get(session_id, {}),
        "messages": SESSIONS.get(session_id, []),
    }


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    SESSIONS.pop(session_id, None)
    SESSION_META.pop(session_id, None)

    return {
        "status": "deleted",
        "session_id": session_id,
    }


# ============================================================
# SIMPLE FRONTEND
# ============================================================

@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <title>Tabib AI</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f3f7f7;
            color: #0f172a;
        }

        .page {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }

        .hero {
            max-width: 760px;
            background: white;
            border-radius: 28px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(15, 23, 42, 0.12);
        }

        .badge {
            display: inline-block;
            background: #ccfbf1;
            color: #115e59;
            padding: 8px 12px;
            border-radius: 999px;
            font-weight: 700;
            font-size: 13px;
            margin-bottom: 18px;
        }

        h1 {
            margin: 0 0 16px;
            font-size: 44px;
            letter-spacing: -1.5px;
            line-height: 1.05;
        }

        p {
            color: #475569;
            font-size: 17px;
            line-height: 1.7;
        }

        .launcher {
            position: fixed;
            right: 22px;
            bottom: 22px;
            width: 68px;
            height: 68px;
            border: none;
            border-radius: 24px;
            background: linear-gradient(135deg, #0f766e, #14b8a6);
            color: white;
            font-size: 30px;
            cursor: pointer;
            box-shadow: 0 18px 50px rgba(15, 118, 110, 0.35);
            z-index: 10;
        }

        .chat {
            position: fixed;
            right: 22px;
            bottom: 104px;
            width: 390px;
            height: 620px;
            max-width: calc(100vw - 28px);
            max-height: calc(100vh - 125px);
            background: white;
            border-radius: 28px;
            box-shadow: 0 18px 60px rgba(15, 23, 42, 0.22);
            overflow: hidden;
            display: none;
            flex-direction: column;
            z-index: 9;
        }

        .chat.open {
            display: flex;
        }

        .chat-header {
            padding: 18px;
            background: linear-gradient(135deg, #115e59, #0f766e);
            color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .chat-title {
            font-weight: 800;
            font-size: 18px;
        }

        .chat-subtitle {
            opacity: .85;
            font-size: 12px;
            margin-top: 3px;
        }

        .close {
            border: none;
            width: 34px;
            height: 34px;
            border-radius: 12px;
            color: white;
            background: rgba(255,255,255,.16);
            font-size: 18px;
            cursor: pointer;
        }

        .risk {
            display: none;
            padding: 9px 14px;
            font-size: 12px;
            font-weight: 700;
            border-bottom: 1px solid #e2e8f0;
        }

        .risk.LOW {
            display: block;
            background: #ecfdf5;
            color: #047857;
        }

        .risk.MODERATE {
            display: block;
            background: #fffbeb;
            color: #b45309;
        }

        .risk.HIGH {
            display: block;
            background: #fff7ed;
            color: #c2410c;
        }

        .risk.URGENT {
            display: block;
            background: #fef2f2;
            color: #b91c1c;
        }

        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 14px;
            background: #f8fafc;
        }

        .msg {
            display: flex;
            margin-bottom: 12px;
        }

        .msg.user {
            justify-content: flex-end;
        }

        .bubble {
            max-width: 82%;
            padding: 12px 14px;
            border-radius: 18px;
            font-size: 14px;
            line-height: 1.55;
            white-space: pre-wrap;
        }

        .bot .bubble {
            background: white;
            border: 1px solid #e2e8f0;
            border-bottom-left-radius: 6px;
        }

        .user .bubble {
            background: #0f766e;
            color: white;
            border-bottom-right-radius: 6px;
        }

        .typing {
            display: none;
            padding: 8px 14px;
            background: #f8fafc;
            color: #64748b;
            font-size: 13px;
        }

        .typing.show {
            display: block;
        }

        .quick {
            display: flex;
            gap: 8px;
            overflow-x: auto;
            padding: 10px 12px;
            border-top: 1px solid #e2e8f0;
        }

        .quick button {
            white-space: nowrap;
            border: 1px solid #e2e8f0;
            background: white;
            padding: 8px 10px;
            border-radius: 999px;
            cursor: pointer;
            font-size: 12px;
        }

        .form {
            display: flex;
            gap: 10px;
            padding: 12px;
            border-top: 1px solid #e2e8f0;
        }

        textarea {
            flex: 1;
            resize: none;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 12px;
            min-height: 46px;
            max-height: 110px;
            outline: none;
            font-family: inherit;
        }

        textarea:focus {
            border-color: #0f766e;
        }

        .send {
            width: 48px;
            height: 48px;
            border: none;
            border-radius: 16px;
            background: #0f766e;
            color: white;
            font-size: 20px;
            cursor: pointer;
        }

        @media (max-width: 640px) {
            h1 {
                font-size: 34px;
            }

            .hero {
                padding: 28px;
            }

            .chat {
                right: 12px;
                bottom: 90px;
                width: calc(100vw - 24px);
                height: calc(100vh - 115px);
            }

            .launcher {
                right: 16px;
                bottom: 16px;
            }
        }
    </style>
</head>

<body>
    <main class="page">
        <section class="hero">
            <div class="badge">🩺 Tabib AI</div>
            <h1>Davolanishni davom ettirish uchun aqlli yordamchi</h1>
            <p>
                Tabib AI bemorlarga dorilarni unutmaslik, nojo‘ya ta’sirlarni tushunish,
                xavfli belgilarni erta aniqlash va shifokor bilan o‘z vaqtida bog‘lanishda yordam beradi.
            </p>
        </section>
    </main>

    <button class="launcher" id="launcher">💬</button>

    <section class="chat" id="chat">
        <div class="chat-header">
            <div>
                <div class="chat-title">Tabib AI</div>
                <div class="chat-subtitle">Medication adherence assistant</div>
            </div>
            <button class="close" id="close">×</button>
        </div>

        <div class="risk" id="risk"></div>

        <div class="messages" id="messages">
            <div class="msg bot">
                <div class="bubble">Assalomu alaykum. Men Tabib AI. Dori qabul qilish, eslatmalar, nojo‘ya ta’sirlar yoki davolanishni davom ettirish bo‘yicha yordam bera olaman. Bugun sizga nima bo‘yicha yordam kerak?</div>
            </div>
        </div>

        <div class="typing" id="typing">Tabib AI yozmoqda...</div>

        <div class="quick">
            <button data-text="Men dorimni unutib qo‘ydim">Dorimni unutdim</button>
            <button data-text="Doridan keyin boshim aylanmoqda">Nojo‘ya ta’sir</button>
            <button data-text="Dorimni ichishni to‘xtatmoqchiman">To‘xtatmoqchiman</button>
            <button data-text="Tabletkani yutish qiyin">Yutish qiyin</button>
        </div>

        <form class="form" id="form">
            <textarea id="input" rows="1" placeholder="Xabaringizni yozing..."></textarea>
            <button class="send" type="submit">➤</button>
        </form>
    </section>

    <script>
        const launcher = document.getElementById("launcher");
        const chat = document.getElementById("chat");
        const closeBtn = document.getElementById("close");
        const form = document.getElementById("form");
        const input = document.getElementById("input");
        const messages = document.getElementById("messages");
        const typing = document.getElementById("typing");
        const risk = document.getElementById("risk");

        let sessionId = localStorage.getItem("tabib_session_id");

        launcher.onclick = () => {
            chat.classList.toggle("open");
            input.focus();
        };

        closeBtn.onclick = () => {
            chat.classList.remove("open");
        };

        document.querySelectorAll(".quick button").forEach(button => {
            button.onclick = () => {
                input.value = button.dataset.text;
                input.focus();
            };
        });

        function addMessage(text, role) {
            const row = document.createElement("div");
            row.className = "msg " + role;

            const bubble = document.createElement("div");
            bubble.className = "bubble";
            bubble.textContent = text;

            row.appendChild(bubble);
            messages.appendChild(row);
            messages.scrollTop = messages.scrollHeight;
        }

        function setRisk(level, flags) {
            risk.className = "risk " + level;
            risk.textContent = "Risk: " + level + (flags && flags.length ? " · " + flags.join(", ") : "");
        }

        async function sendMessage(text) {
            typing.classList.add("show");

            try {
                const res = await fetch("/chat", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        message: text,
                        session_id: sessionId
                    })
                });

                const data = await res.json();

                if (!res.ok) {
                    throw new Error(data.detail || "Server error");
                }

                sessionId = data.session_id;
                localStorage.setItem("tabib_session_id", sessionId);

                setRisk(data.risk_level, data.risk_flags);
                addMessage(data.reply, "bot");

            } catch (err) {
                addMessage("Xatolik yuz berdi: " + err.message, "bot");
            } finally {
                typing.classList.remove("show");
            }
        }

        form.onsubmit = async (e) => {
            e.preventDefault();

            const text = input.value.trim();
            if (!text) return;

            addMessage(text, "user");
            input.value = "";

            await sendMessage(text);
        };
    </script>
</body>
</html>
    """


# ============================================================
# RUN:
# uvicorn main:app --reload
# ============================================================
