"""
╔══════════════════════════════════════════════════════════════════════╗
║        TABIB AI — MEDICATION ADHERENCE EXPERT CHATBOT             ║
║        AI Health Hackathon 2026  |  Yagona fayl                     ║
║                                                                      ║
║  Run:  uvicorn main:app --reload --port 8000                         ║
║  Docs: http://localhost:8000/docs                                    ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import re
import uuid
import logging
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from openai import OpenAI

# ══════════════════════════════════════════════════════════════════════
# TIBBIY BILIMLAR BAZASI (ichki — alohida fayl kerak emas)
# Manbalar: WHO, MedlinePlus, UpToDate, O'zbekiston SSV protokollari
# ══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# KASALLIKLAR (Diseases)
# ═══════════════════════════════════════════════════════════════

DISEASES = {

    # ── DIABET ────────────────────────────────────────────────
    "diabet": {
        "uz_names": ["diabet", "qand kasalligi", "shakar kasalligi", "diabet kasalligi"],
        "ru_names": ["диабет", "сахарный диабет", "диабет 1", "диабет 2"],
        "en_names": ["diabetes", "type 1 diabetes", "type 2 diabetes", "dm"],
        "description_uz": (
            "Qand diabeti — qondagi shakar miqdori me'yoridan yuqori bo'lib qoladigan "
            "surunkali kasallik. Insulin yetishmovchiligi (1-tur) yoki insulinga chidamlilik "
            "(2-tur) natijasida rivojlanadi."
        ),
        "symptoms_uz": [
            "Tez-tez siydik qilish (ayniqsa kechasi)",
            "Juda ko'p suv ichish",
            "Tez charchash, holsizlik",
            "Ko'rish xiralashishi",
            "Oyoq va qo'llarda uvishish yoki xuddi igna sanchilgandek his",
            "Yaralarnining sekin bitishi",
            "Tushunarsiz vazn yo'qotish (1-tur diabetda)",
            "Oziq-ovqatga ishtahasining kuchayishi",
        ],
        "complications_uz": [
            "Yurak va qon tomir kasalliklari (infarkt, insult)",
            "Diabetik nefropatiya (buyrak zararlanishi)",
            "Diabetik retinopatiya (ko'z zararlanishi, ko'r bo'lish xavfi)",
            "Diabetik neyropatiya (nerv zararlanishi)",
            "Diabetik oyoq sindromi (gangrena, amputatsiya xavfi)",
            "Infeksiyalarga moyillik ortishi",
        ],
        "treatment_uz": (
            "1-tur diabet: majburiy insulin terapiyasi. "
            "2-tur diabet: turmush tarzi o'zgarishi (parhez, jismoniy faollik), "
            "og'iz orqali qabul qilinadigan dorilar (Metformin birinchi qator), "
            "kerak bo'lsa insulin. Qon shakarini muntazam o'lchash shart."
        ),
        "target_values_uz": {
            "Och qoringa qon shakar": "3.9–7.0 mmol/L",
            "Ovqatdan 2 soat keyin": "< 10.0 mmol/L",
            "HbA1c": "< 7% (ko'pchilik bemorlar uchun)",
            "Qon bosimi": "< 130/80 mmHg",
        },
        "diet_uz": [
            "Oddiy shakar va shirinliklarni kamaytirish",
            "Oq un mahsulotlari (non, makaron) o'rniga to'liq don mahsulotlari",
            "Har kuni sabzavot ko'p iste'mol qilish",
            "Qovurilgan ovqat o'rniga qaynatilgan yoki bug'da pishirilgan",
            "Ovqatni 3 emas, 5-6 marta kichik porsiyalarda qabul qilish",
            "Spirtli ichimliklardan voz kechish",
        ],
        "emergency_signs_uz": [
            "Gipoglikemiya (past qon shakar): titroq, ter bosish, yurak tez urishi, hushdan ketish — darhol shakar iste'mol qiling",
            "Giperglikemiya (juda baland shakar 16+): ko'ngil aynishi, qusish, chuqur nafas — tez yordam",
            "Diabetik ketoatsidoz: og'izdan meva hidi, chuqur nafas, hushdan ketish — TEZDA tez yordam",
        ],
        "medications_first_line": ["Metformin"],
        "monitoring_uz": "Qon shakarini kuniga 2-4 marta o'lchash, HbA1c ni 3 oyda bir tekshirish",
    },

    # ── GIPERTONIYA ───────────────────────────────────────────
    "gipertoniya": {
        "uz_names": ["gipertoniya", "qon bosimi", "arterial gipertoniya", "yuqori qon bosimi", "bosim"],
        "ru_names": ["гипертония", "артериальная гипертензия", "высокое давление", "давление"],
        "en_names": ["hypertension", "high blood pressure", "hbp", "arterial hypertension"],
        "description_uz": (
            "Arterial gipertoniya — qon bosimining 140/90 mmHg dan yuqori bo'lib qolishi. "
            "O'zbekistonda eng keng tarqalgan surunkali kasallik. Ko'pchilik hollarda "
            "simptom bermaydi ('jim qotil'), shuning uchun muntazam o'lchash muhim."
        ),
        "stages_uz": {
            "Normal": "120/80 mmHg dan past",
            "Yuqori normal": "130-139 / 85-89 mmHg",
            "1-daraja": "140-159 / 90-99 mmHg",
            "2-daraja": "160-179 / 100-109 mmHg",
            "3-daraja": "180+ / 110+ mmHg — jiddiy, darhol shifokor",
        },
        "symptoms_uz": [
            "Ko'pincha simptom bo'lmaydi (shuning uchun 'jim qotil' deyiladi)",
            "Bosh og'riq (ko'pincha ensa sohasida, ertalab)",
            "Ko'z oldida qorachiqlar yoki nur ko'rinishi",
            "Bosh aylanishi",
            "Yurak urishi",
            "Burundan qon ketishi",
            "Quloq shovqini",
        ],
        "complications_uz": [
            "Miyokard infarkti (yurak xurujи)",
            "Insult (miya qon aylanishining buzilishi)",
            "Yurak yetishmovchiligi",
            "Buyrak yetishmovchiligi",
            "Ko'rish buzilishi (retinopatiya)",
            "Aorta anevrizması",
        ],
        "treatment_uz": (
            "Turmush tarzi o'zgarishi: tuz kamaytirilishi (kuniga 5g gacha), spirtdan voz kechish, "
            "chekishni tashlash, vazn normalashtirish, jismoniy faollik. "
            "Dorilar: ACE ingibitorlari (Enalapril, Lisinopril), beta-blokatorlar (Bisoprolol), "
            "kalsiy kanal blokatorlari (Amlodipine), diuretiklar (Gidrokhlorotiazid)."
        ),
        "diet_uz": [
            "Tuz kuniga 5g (1 choy qoshiq) dan kam",
            "Kaliy ko'p ovqat: banan, kartoshka, qovoq, yong'oq",
            "Yog'li go'sht va mol mahsulotlarini kamaytirish",
            "Spirtli ichimliklardan voz kechish",
            "Qahva va kuchli choyni kamaytirish",
            "Ko'p sabzavot, meva, to'liq don mahsulotlari",
        ],
        "emergency_signs_uz": [
            "Gipertonik kriz: bosim 180/110+ va bosh og'riq, ko'ngil aynishi — TEZDA shifokor",
            "Ko'krakda og'riq + bosim yuqori — tez yordam (103)",
            "Nutq buzilishi, yuz qiyshayishi, qo'l kuchsizligi — insult, TEZDA 103",
            "Ko'rish to'satdan yomonlashishi — tez yordam",
        ],
        "monitoring_uz": "Qon bosimini kuniga 2 marta (ertalab va kechqurun) o'lchash va yozib borish",
        "medications_first_line": ["Enalapril", "Lisinopril", "Amlodipine", "Bisoprolol", "Losartan"],
    },

    # ── YURAK KASALLIGI ───────────────────────────────────────
    "yurak_kasalligi": {
        "uz_names": ["yurak kasalligi", "yurak", "ishemik yurak", "stenokardiya", "stend"],
        "ru_names": ["ибс", "ишемическая болезнь сердца", "стенокардия", "сердечная недостаточность"],
        "en_names": ["coronary artery disease", "heart disease", "angina", "heart failure", "ihd"],
        "description_uz": (
            "Ishemik yurak kasalligi — yurak mushaklarining qon bilan ta'minlanishi yetarli "
            "bo'lmasligi. Asosiy sabab — koronar arteriyalarda ateroskleroz (yog' plakalari). "
            "O'lim sabablarining 1-o'rnida turadi."
        ),
        "symptoms_uz": [
            "Ko'krakda og'riq yoki siqilish (ayniqsa jismoniy zo'riqishda)",
            "Nafas qisishi",
            "Chap qo'l, yelka, bo'yin yoki jag'ga tarqaladigan og'riq",
            "Tez charchash",
            "Yurak urishi yoki notekis urish",
            "Oyoqlarda shish",
            "Bosh aylanishi",
        ],
        "emergency_signs_uz": [
            "INFARKT BELGILARI: ko'krakda kuchli, 20 daqiqadan ortiq og'riq — DARHOL 103",
            "Ko'krak og'rig'i + ter bosish + ko'ngil aynishi — TEZDA 103",
            "Nafas ololmaslik + ko'pikli balg'am — TEZDA 103",
            "Hushdan ketish — TEZDA 103",
        ],
        "medications_first_line": ["Aspirin", "Bisoprolol", "Atorvastatin", "Enalapril", "Nitroglycerin (og'riqda)"],
        "treatment_uz": (
            "Hayot tarzi: chekishni tashlash (eng muhim!), tuz kamaytirish, vazn normalashtirish, "
            "yurak uchun mo'ljallangan jismoniy mashqlar. Dorilar: antiplatelet (Aspirin), "
            "beta-blokatorlar, statinlar, ACE ingibitorlari. Invaziv: stentlash, shuntlash."
        ),
        "monitoring_uz": "EKG, Ehokardiografiya, Holter monitoring, qon tahlili (lipidlar, KFK, troponin)",
    },

    # ── INSULT ────────────────────────────────────────────────
    "insult": {
        "uz_names": ["insult", "miya qon aylanishi", "falaj", "miya qon quyilishi"],
        "ru_names": ["инсульт", "инсульт мозга", "кровоизлияние в мозг", "ишемический инсульт"],
        "en_names": ["stroke", "cerebrovascular accident", "cva", "brain attack"],
        "description_uz": (
            "Insult — miyaga qon oqimining to'satdan to'xtashi (ishemik) yoki qon tomir "
            "yorilib qon quyilishi (gemorragik). Har daqiqa muhim — 'vaqt = miya hujayralari'."
        ),
        "emergency_signs_uz": [
            "FAST qoidasi:",
            "F (Face) — yuzning bir tomoni qiyshayishi",
            "A (Arms) — bir qo'lning kuchsizlanishi",
            "S (Speech) — nutqning buzilishi, chalkash gapirish",
            "T (Time) — DARHOL 103 ga qo'ng'iroq qiling!",
            "Boshqa belgilar: to'satdan ko'rish yo'qolishi, kuchli bosh og'riq, muvozanat yo'qolishi",
        ],
        "treatment_uz": (
            "Ishemik insultda: 4.5 soat ichida tromboliz (qon ivishini eritmak) mumkin. "
            "Shuning uchun DARHOL tez yordam zarur. Har daqiqada 1.9 million miya hujayralari halok bo'ladi."
        ),
        "prevention_uz": [
            "Qon bosimini nazorat qilish (eng muhim profilaktika)",
            "Qand diabetini nazorat qilish",
            "Chekishni tashlash",
            "Spirtdan voz kechish",
            "Muntazam jismoniy faollik",
            "To'g'ri parhez",
            "Yurak ritmi buzilishini davolash",
        ],
    },

    # ── BRONXIAL ASTMA ────────────────────────────────────────
    "astma": {
        "uz_names": ["astma", "bronxial astma", "nafas yo'llari", "xirillash", "xirsoqlik"],
        "ru_names": ["астма", "бронхиальная астма", "одышка", "приступ астмы"],
        "en_names": ["asthma", "bronchial asthma", "wheezing"],
        "description_uz": (
            "Bronxial astma — nafas yo'llari surunkali yallig'lanishi va torayishi "
            "bilan kechadigan kasallik. Qo'zg'atuvchilar: changi, hayvon juni, gul changalari, "
            "sovuq havo, zararli gazlar, stress."
        ),
        "symptoms_uz": [
            "Nafas qisishi (ayniqsa kechasi va erta tongda)",
            "Xirillash (nafas olganda xirillovchi tovush)",
            "Ko'krakda siqilish hissi",
            "Yo'tal (ayniqsa kechasi)",
            "Jismoniy faollikdan keyin nafas qisilishi",
        ],
        "emergency_signs_uz": [
            "Og'ir hujum: nafas ololmaslik, gapira olmaslik — TEZDA 103",
            "Ko'k yoki kulrang lab rangi — TEZDA 103",
            "Inhaler ishlamayapti — TEZDA 103",
            "Bolada astma hujumi — TEZDA 103",
        ],
        "medications_first_line": [
            "Qisqa ta'sirli bronxodilyatorlar (Salbutamol/Ventolin) — hujumni to'xtatish uchun",
            "Inhalatsion kortikosteroidlar (Budesonid/Flutikazon) — doimiy profilaktika",
            "Kombinirlangan inhaler (Seretide, Symbicort) — og'ir astmada",
        ],
        "treatment_uz": (
            "ASOSIY: Inhalatsion kortikosteroidlarni muntazam qabul qilish — hatto yaxshi his qilsangiz ham to'xtamang! "
            "Bu dorini to'xtatish kasallikning qaytishiga olib keladi. "
            "Qo'zg'atuvchilardan himoya, uy changini kamaytirish, sigaret tutunidan qochish."
        ),
    },

    # ── SURUNKALI OBSTRUKTIV O'PKA KASALLIGI (SOPK/COPD) ─────
    "copd": {
        "uz_names": ["sopk", "surunkali bronxit", "emfizema", "chekuvchi kasalligi"],
        "ru_names": ["хобл", "хроническая обструктивная болезнь лёгких", "хронический бронхит", "эмфизема"],
        "en_names": ["copd", "chronic obstructive pulmonary disease", "chronic bronchitis", "emphysema"],
        "description_uz": (
            "SOPK — o'pka funktsiyasining sekin-asta, doimiy ravishda yomonlashuvi. "
            "Asosiy sabab: chekish (85-90%). Davolanmasa — nogironlik va erta o'lim."
        ),
        "symptoms_uz": [
            "Surunkali yo'tal (ayniqsa ertalab)",
            "Balg'am ajralishi",
            "Nafas qisishi (dastlab faqat zo'riqishda, keyin tinch holatda ham)",
            "Kasallikning qayta-qayta kuchayishi (exatserbatsiya)",
        ],
        "medications_first_line": [
            "Bronxodilyatorlar: Tiotropium (Spiriva), Salbutamol",
            "ICS/LABA kombinatsiyasi: Seretide, Symbicort",
            "Ekzatserbatsiyada: antibiotiklar + steroidlar",
        ],
        "emergency_signs_uz": [
            "Nafas ololmaslik, lab ko'kimligi — TEZDA 103",
            "Qon aralashgan balg'am — shifokor",
            "Aql-idrok buzilishi — tez yordam",
        ],
        "treatment_uz": "CHEKISHNI TASHLASH — eng muhim davolash. Bronxodilyatorlar, pulmonologiya nazorati.",
    },

    # ── BUYRAK KASALLIGI ──────────────────────────────────────
    "buyrak_kasalligi": {
        "uz_names": ["buyrak kasalligi", "buyrak", "pielonefrit", "buyrak yetishmovchiligi", "tosh"],
        "ru_names": ["почечная болезнь", "пиелонефрит", "почечная недостаточность", "мочекаменная болезнь"],
        "en_names": ["kidney disease", "ckd", "chronic kidney disease", "pyelonephritis", "kidney stones"],
        "description_uz": "Buyrak kasalligi — buyraklarning normal ishlashdan to'xtashi. Diabet va gipertoniya eng keng tarqalgan sabab.",
        "symptoms_uz": [
            "Bel va yon og'rig'i",
            "Siydik rangining o'zgarishi (qoraroq, qonli)",
            "Siydik qilishda og'riq yoki kuyish",
            "Oyoq, yuz va qo'llarda shish",
            "Tez charchash",
            "Ishtaha yo'qolishi, ko'ngil aynishi",
            "Tunda tez-tez siydik qilish",
        ],
        "emergency_signs_uz": [
            "Kuchli bel og'rig'i + isitma + qaltirash — pielonefrit/yiringli jarayon — TEZDA shifokor",
            "Siydik butunlay to'xtashi — TEZDA 103",
            "Qon bilan siydik — shifokor",
        ],
        "treatment_uz": "Diabet va qon bosimini nazorat qilish. Suyuqlik ko'p ichish. Antibiotiklar (infeksiyada). Dializ (og'ir holatda).",
    },

    # ── OSHQOZON VA ICHAK KASALLIKLARI ────────────────────────
    "oshqozon": {
        "uz_names": ["oshqozon", "gastrit", "yarava", "reflyuks", "oshqozon og'rig'i"],
        "ru_names": ["гастрит", "язва", "рефлюкс", "боль в желудке", "гэрб"],
        "en_names": ["gastritis", "peptic ulcer", "gerd", "acid reflux", "stomach pain"],
        "description_uz": "Oshqozon kasalliklari — oshqozon shilliq qavatining yallig'lanishi yoki shikastlanishi.",
        "symptoms_uz": [
            "Qorin og'rig'i (ayniqsa ovqatdan oldin yoki keyin)",
            "Ko'ngil aynishi",
            "Qusish",
            "Kislota qaytishi (kislota ta'mi og'izda)",
            "Shish va gaz",
            "Ishtaha yo'qolishi",
            "Qora rangli najaslar (qon belgi — JIDDIY)",
        ],
        "emergency_signs_uz": [
            "Qora rangli yoki qon aralashgan najaslar — TEZDA shifokor",
            "Qon qusish — TEZDA 103",
            "Kuchli qorin og'rig'i — tez yordam",
        ],
        "medications_first_line": ["Omeprazol (PPI)", "Pantoprazol", "Antatsidlar (Maalox, Almagel)", "Helicobacter pylori davolash: uch komponentli sxema"],
        "treatment_uz": "H.pylori yo'q qilish (antibiotik + PPI). Ovqatlanish tartibi. NSAIDlar (ibuprofen, aspirin) ni kamaytirish. Chekish va spirtdan voz kechish.",
    },

    # ── SARILIK (GEPATIT) ─────────────────────────────────────
    "gepatit": {
        "uz_names": ["gepatit", "jigar kasalligi", "sarilik", "jigar"],
        "ru_names": ["гепатит", "болезнь печени", "желтуха", "цирроз"],
        "en_names": ["hepatitis", "liver disease", "jaundice", "cirrhosis"],
        "description_uz": "Gepatit — jigar yallig'lanishi. Viral (A, B, C, D, E), toksik (alkogol, dori), autoimmun shakllari bor.",
        "symptoms_uz": [
            "Sarilik (ko'z oqlari va teri sariqlanishi)",
            "Qorin o'ng tomonda og'riq",
            "Ishtaha yo'qolishi",
            "Ko'ngil aynishi, qusish",
            "Jigarrang siydik",
            "Oqimtir rangli najaslar",
            "Kuchli charchash",
        ],
        "emergency_signs_uz": [
            "Aql-idrok buzilishi + sarilik — jigar komi, TEZDA 103",
            "Qon qusish — TEZDA 103",
            "Kuchli sarilik + isitma — TEZDA shifokor",
        ],
        "treatment_uz": "Virusga qarshi dorilar (B va C gepatit uchun). Jigarni zararlovchi moddalardan himoya. Spirtdan voz kechish. B gepatit — emlash bilan oldini olish mumkin.",
    },

    # ── QALQONSIMON BEZ KASALLIGI ─────────────────────────────
    "qalqonsimon_bez": {
        "uz_names": ["qalqonsimon bez", "gipertireoz", "gipotireoz", "tirеoid", "zob"],
        "ru_names": ["щитовидная железа", "гипотиреоз", "гипертиреоз", "зоб", "тиреоид"],
        "en_names": ["thyroid", "hypothyroidism", "hyperthyroidism", "goiter", "thyroid disease"],
        "description_uz": "Qalqonsimon bez kasalliklari — gormonlar ishlab chiqarishining kamayishi (gipotireoz) yoki ortishi (gipertireoz).",
        "symptoms_uz": {
            "gipotireoz": ["Charchash, uyquchanlik", "Sovuqqa chidamaslik", "Vazn ortishi", "Teri quruqligi", "Sekin yurak urishi", "Depressiya"],
            "gipertireoz": ["Asabiylik, bezovtalanish", "Issiqqa chidamaslik", "Vazn yo'qotish", "Yurak tez urishi", "Ko'z do'mboqligi", "Qo'l titroqligi"],
        },
        "medications_first_line": {
            "gipotireoz": "Levotiroksin (L-tiroksin) — har kuni, och qoringa, suv bilan",
            "gipertireoz": "Tiamazol, Propiltiourasil, Radioaktiv yod, Operatsiya",
        },
        "treatment_uz": "Levotiroksin — umrbod ichiladi (gipotireozda). TSH ni 3-6 oyda bir tekshirish.",
        "important_uz": "Levotiroksin boshqa dorilardan 30-60 daqiqa oldin, och qoringa qabul qilinadi. Kalsiy, temir preparatlari bilan bir vaqtda icha olmaydi.",
    },

    # ── DEPRESSIYA ────────────────────────────────────────────
    "depressiya": {
        "uz_names": ["depressiya", "kayfiyat tushishi", "qayg'u", "ruhiy kasallik", "qiziqish yo'qolishi"],
        "ru_names": ["депрессия", "тревожность", "подавленность", "психическое расстройство"],
        "en_names": ["depression", "anxiety", "mental health", "mood disorder"],
        "description_uz": "Depressiya — ruhiy sog'liqning keng tarqalgan kasalligi. Haqiqiy kasallik, irodasizlik emas.",
        "symptoms_uz": [
            "2 haftadan ortiq kayfiyat tushkunligi",
            "Ilgari yoqtirgan narsalarga qiziqishning yo'qolishi",
            "Uyqu buzilishi (ortiqcha yoki kam uyqu)",
            "Ishtaha o'zgarishi",
            "Charchash, energiyasizlik",
            "Diqqat, xotira muammolari",
            "O'zini ayblash, qadrsiz his qilish",
            "O'lim yoki o'z joniga qasd qilish haqida fikrlar",
        ],
        "emergency_signs_uz": [
            "O'z joniga qasd qilish fikri — DARHOL yaqinlarga ayt va 103 ga qo'ng'iroq qil",
            "O'ziga zarar yetkazish — TEZDA yordam kerak",
        ],
        "treatment_uz": "Psixoterapiya (KBT). Antidepressantlar (SSRI: Sertralin, Fluoksetin). Yashash tarzi: uyqu, jismoniy faollik, ijtimoiy aloqa.",
        "medications_first_line": ["Sertralin", "Fluoksetin", "Escitalopram", "Amitriptilin"],
        "important_uz": "Antidepressantlar 2-4 hafta davomida ta'sir ko'rsata boshlaydi. Darhol natija kutmang. Shifokor ruxsatisiz to'xtatmang.",
    },

    # ── SUYAK VA BO'G'IM KASALLIKLARI ─────────────────────────
    "artrit": {
        "uz_names": ["artrit", "bo'g'im og'rig'i", "podagra", "revmatoid", "osteoartrit", "bo'g'im"],
        "ru_names": ["артрит", "ревматоидный артрит", "остеоартрит", "подагра", "суставы"],
        "en_names": ["arthritis", "rheumatoid arthritis", "osteoarthritis", "gout", "joint pain"],
        "description_uz": "Artrit — bo'g'imlarning yallig'lanishi. Turlari: osteoartrit (qarilik), revmatoid (autoimmun), podagra (siydik kislotasi).",
        "symptoms_uz": ["Bo'g'im og'rig'i", "Bo'g'im shishi", "Harakatlanishda qiyinchilik", "Ertalab bo'g'im qotishi", "Qizarish va issiqlik"],
        "medications_first_line": ["Ibuprofen", "Naproxen", "Metotreksat (RA)", "Kolxitsin (podagra)", "Allopurinol (podagra profilaktika)"],
        "treatment_uz": "Og'riqni kamaytiruvchi dorilar. Jismoniy terapiya. Vazn normalashtirish. Revmatoid artritda — immunosuppressantlar.",
    },

    # ── SILT (TUBERKULEZ) ─────────────────────────────────────
    "tuberkulez": {
        "uz_names": ["sil", "tuberkulez", "o'pka sili", "tb kasalligi"],
        "ru_names": ["туберкулёз", "тб", "лёгочный туберкулёз", "кавернозный тб"],
        "en_names": ["tuberculosis", "tb", "pulmonary tuberculosis"],
        "description_uz": (
            "Tuberkulez — Mycobacterium tuberculosis bakteriyasi tomonidan yuzaga keltirilgan, "
            "havo-tomchi yo'li bilan yuqadigan infeksion kasallik. O'zbekistonda dolzarb muammo."
        ),
        "symptoms_uz": [
            "3 haftadan ortiq yo'tal",
            "Qon bilan yo'tal",
            "Kechasi ter bosishi",
            "Vazn yo'qotish",
            "Charchash, holsizlik",
            "Isitma (ko'pincha kechqurun)",
            "Ko'krak og'rig'i",
        ],
        "treatment_uz": (
            "DOTS strategiyasi: kamida 6 oy davomida 4 ta antibiotik (Izoniazid, Rifampitsin, "
            "Pirazinamid, Etambutol). KURSNI TO'LIQ YAKUNLASH JUDA MUHIM — "
            "to'xtatilsa dori chidamli TB paydo bo'ladi va davolab bo'lmaydi."
        ),
        "emergency_signs_uz": [
            "Qon qusish — TEZDA 103",
            "Nafas qisilishi — shifokor",
            "Kuchli ko'krak og'rig'i — tez yordam",
        ],
        "important_uz": "TB dorilarini to'xtatish — o'z joniga va boshqalarga xavf. Har doim shifokor nazoratida davolanish.",
        "medications_first_line": ["Izoniazid (H)", "Rifampitsin (R)", "Pirazinamid (Z)", "Etambutol (E)"],
    },

    # ── HIV/OITS ──────────────────────────────────────────────
    "hiv": {
        "uz_names": ["hiv", "oits", "immunitet kasalligi"],
        "ru_names": ["вич", "спид", "вич инфекция"],
        "en_names": ["hiv", "aids", "hiv infection"],
        "description_uz": "HIV — inson immunitet tizimini zaiflashtiruvchi virus. Zamonaviy dorilar bilan normal hayot kechirish mumkin.",
        "treatment_uz": "ART (antiretroviral terapiya) — umrbod qabul qilinadi. Muntazam qabul qilish viral yukni '0' ga tushiradi va boshqalarga yuqtirmaydi.",
        "important_uz": "ART dorilarini o'z vaqtida, har kuni, ko'rsatilgan soatda qabul qilish JUDA muhim. 1 ta doza o'tkazib yuborilsa ham rezistentlik xavfi.",
        "medications_first_line": ["TDF/3TC/EFV", "TDF/FTC/DTG (Dolutegravir)"],
        "emergency_signs_uz": [
            "Isitma + bosh og'riq + bo'yin qotishi — meningit, TEZDA 103",
            "Ko'rish to'satdan yo'qolishi — tez yordam",
            "Kuchli nafas qisilishi — tez yordam",
        ],
    },

}


# ═══════════════════════════════════════════════════════════════
# DORILAR (Medications)
# ═══════════════════════════════════════════════════════════════

MEDICATIONS = {

    "metformin": {
        "brand_names": ["Metformin", "Glucophage", "Siofor"],
        "class_uz": "Biguanid — qon shakarini pasaytiruvchi dori",
        "indications_uz": "2-tur diabet",
        "how_to_take_uz": "Ovqat bilan birga yoki ovqatdan keyin, ko'ngil aynishini kamaytirish uchun. Odatda kuniga 2-3 marta.",
        "common_side_effects_uz": [
            "Ko'ngil aynishi (boshlang'ich davrda, o'tib ketadi)",
            "Ich ketishi",
            "Qorin noqulayligi",
            "Ishtaha yo'qolishi",
        ],
        "serious_side_effects_uz": [
            "Laktik atsidoz (juda kam, lekin jiddiy) — zaiflik, nafas qisishi, qorin og'rig'i: TEZDA shifokor",
            "B12 vitamini yetishmovchiligi (uzoq muddatda)",
        ],
        "missed_dose_uz": "Eslab qolsangiz — oling. Keyingi doza vaqti yaqin bo'lsa — o'tkazib yuboring. Ikki baravar OLMANG.",
        "contraindications_uz": ["Buyrak yetishmovchiligi (GFR < 30)", "Kontrast modda olishdan 48 soat oldin to'xtatish", "Jiddiy jigar kasalligi"],
        "storage_uz": "Xona haroratida, namlikdan va quyosh nuridan uzoqda",
        "important_uz": "Spirtli ichimliklar bilan laktik atsidoz xavfi oshadi. Operatsiya oldidan to'xtatish kerak.",
    },

    "enalapril": {
        "brand_names": ["Enalapril", "Enap", "Renitek"],
        "class_uz": "ACE ingibitori — qon bosimini pasaytiruvchi",
        "indications_uz": "Arterial gipertoniya, yurak yetishmovchiligi, diabetik nefropatiya",
        "how_to_take_uz": "Ovqatdan qat'i nazar, bir xil vaqtda. Kuniga 1-2 marta.",
        "common_side_effects_uz": [
            "Quruq yo'tal (10-15% bemorlarda, dori o'zgartirish kerak bo'lishi mumkin)",
            "Bosh aylanishi (ayniqsa dastlabki dozada)",
            "Holsizlik",
        ],
        "serious_side_effects_uz": [
            "Angioedem (yuz, til, tomoq shishi) — TEZDA 103, hayot uchun xavfli",
            "Qon bosimining keskin tushishi",
            "Buyrak funktsiyasi yomonlashishi",
            "Qon tahlilida kaliy oshishi (giperkaliemiya)",
        ],
        "missed_dose_uz": "Eslab qolsangiz — oling. Keyingi doza vaqti kelgan bo'lsa — o'tkazib yuboring.",
        "contraindications_uz": ["Homiladorlik (teratogen)", "Angioedem tarixi", "Qon bosimi juda past"],
        "important_uz": "Yo'tal chiqsa — shifokorga ayting, dori almashtirilishi mumkin (Losartan).",
    },

    "amlodipine": {
        "brand_names": ["Amlodipine", "Norvasc", "Stamlo"],
        "class_uz": "Kalsiy kanal blokatori — qon bosimini va stenokardiyani davolash",
        "indications_uz": "Arterial gipertoniya, stenokardiya",
        "how_to_take_uz": "Kuniga 1 marta, bir xil vaqtda. Ovqatdan qat'i nazar.",
        "common_side_effects_uz": [
            "Oyoqlarda shish (tomirlarda suyuqlik to'planishi)",
            "Qizarish (issiqlik hissi, ayniqsa yuzda)",
            "Bosh og'riq",
            "Holsizlik",
        ],
        "missed_dose_uz": "Eslab qolsangiz — oling. Ikki baravar OLMANG.",
        "important_uz": "Greyfurt (greyfurt sharbati) bilan icha olmaydi — dori konsentratsiyasi oshadi.",
    },

    "atorvastatin": {
        "brand_names": ["Atorvastatin", "Lipitor", "Torvast"],
        "class_uz": "Statin — xolesterolni pasaytiruvchi dori",
        "indications_uz": "Yuqori xolesterol, yurak-qon tomir kasalliklarining profilaktikasi",
        "how_to_take_uz": "Kechqurun, ovqatdan qat'i nazar. Bir xil vaqtda.",
        "common_side_effects_uz": [
            "Mushak og'rig'i (myalgia)",
            "Jigar fermentlari oshishi",
            "Bosh og'riq",
            "Ich ketishi yoki qotishi",
        ],
        "serious_side_effects_uz": [
            "Rabdomioliz (mushak parchalanishi) — kuchli mushak og'rig'i + qoramtir siydik: TEZDA shifokor",
            "Jigar zararlanishi (kamdan-kam)",
        ],
        "missed_dose_uz": "Eslab qolsangiz — oling. Ikki baravar OLMANG.",
        "important_uz": "Greyfurt bilan icha olmaydi. Jigar fermentlarini dori boshlanishida va 3 oyda bir tekshirish.",
    },

    "omeprazol": {
        "brand_names": ["Omeprazol", "Losek", "Ultop", "Omez"],
        "class_uz": "Proton nasos inhibitori (PPI) — oshqozon kislotasini kamaytiruvchi",
        "indications_uz": "Gastrit, oshqozon yarası, kislota qaytishi (GERD), H.pylori davolash",
        "how_to_take_uz": "Ovqatdan 30 daqiqa OLDIN, och qoringa qabul qiling. Kapsulani chaqmang.",
        "common_side_effects_uz": [
            "Bosh og'riq",
            "Ich ketishi yoki qotishi",
            "Qorin noqulayligi",
        ],
        "serious_side_effects_uz": [
            "Uzoq muddatda: Magniy, B12, Kalsiy yetishmovchiligi",
            "Suyak sinishi xavfi ortishi (> 1 yil qabul qilishda)",
            "C.difficile infeksiyasi",
        ],
        "missed_dose_uz": "Eslab qolsangiz — oling. Ikki baravar OLMANG.",
        "important_uz": "Uzoq muddatli qabul shifokor nazoratida bo'lishi kerak. Kerak bo'lganda vitamin B12 va magniy tekshirish.",
    },

    "aspirin": {
        "brand_names": ["Aspirin", "Kardi ASK", "Aspirin Cardio", "Cardiomagnyl"],
        "class_uz": "Antiplatelet — qon ivishiga qarshi, yurak-qon tomir kasalliklarida",
        "indications_uz": "Yurak xurujи va insultning oldini olish, stenokardiya",
        "how_to_take_uz": "Ovqat bilan birga yoki ovqatdan keyin (oshqozon himoyasi uchun). Qoplangan (enterik) tabletkani chaqmang.",
        "common_side_effects_uz": [
            "Oshqozon noqulayligi",
            "Ko'ngil aynishi",
            "Qon ketish xavfining oshishi",
        ],
        "serious_side_effects_uz": [
            "Oshqozon qon ketishi — qora rangli najaslar, qon qusish: TEZDA 103",
            "Miyadan qon ketishi (juda kam)",
            "Aspirin astmasi",
        ],
        "contraindications_uz": ["Aktiv oshqozon yarasi", "Qon ketish kasalliklari", "18 yoshgacha bolalar (Reye sindromi)"],
        "important_uz": "O'z-o'zidan to'xtatmang — yurak xurujи xavfi oshadi.",
    },

    "levotiroksin": {
        "brand_names": ["Levotiroksin", "Euthyrox", "L-tiroksin"],
        "class_uz": "Tiroid gormoni — gipotireoz davolash",
        "indications_uz": "Gipotireoz (qalqonsimon bez funktsiyasining kamayishi)",
        "how_to_take_uz": "Ertalab, OVQATDAN 30-60 daqiqa OLDIN, faqat suv bilan. Har kuni bir xil vaqtda.",
        "common_side_effects_uz": [
            "Doza ko'p bo'lsa: yurak tez urishi, asabiylik, vazn yo'qotish, ter bosishi",
            "To'g'ri dozada yon ta'sir minimal",
        ],
        "missed_dose_uz": "Eslab qolsangiz — oling (ovqat vaqtiga e'tibor bering). Ikki baravar OLMANG.",
        "contraindications_uz": ["Qalqonsimon bezning ba'zi kasalliklari", "Kortizol yetishmovchiligi (avval davolanishi kerak)"],
        "important_uz": [
            "Kalsiy preparatlari, temir preparatlari, antasidlar bilan kamida 4 soat farq qiling",
            "Soya mahsulotlari va limon o'ti so'rilishni kamaytiradi",
            "Umrbod qabul qilinadi — to'xtatmang",
            "TSH ni 6 oyda bir tekshirish",
        ],
    },

    "salbutamol": {
        "brand_names": ["Salbutamol", "Ventolin", "Salamol"],
        "class_uz": "Qisqa ta'sirli beta-2 agonist (bronxodilyator) — astma hujumini to'xtatish",
        "indications_uz": "Bronxial astma hujumi, SOPK qo'zg'alishi",
        "how_to_take_uz": "Zarur bo'lganda (hujumda). Inhaler: chuqur nafas olib, buton bosib, sekin nafas ol, 10 son ushlab tur.",
        "common_side_effects_uz": [
            "Yurak tez urishi (taхikardiya)",
            "Qo'l titroqligi",
            "Bosh og'riq",
            "Gipokaliyemiya (ko'p ishlatilganda)",
        ],
        "missed_dose_uz": "Zarurat bo'lganda ishlatiladi — muntazam jadval yo'q.",
        "important_uz": "Kuniga 4 martadan ko'p kerak bo'lsa — nazorat inhaler (ICS) kuchaytirilishi kerak, shifokorga murojaat qiling.",
        "emergency_uz": "Inhaler ishlamasa yoki 20 daqiqa ichida yaxshilanmasa — TEZDA 103",
    },

    "warfarin": {
        "brand_names": ["Warfarin", "Coumadin"],
        "class_uz": "Antikoagulyant — qon ivishini susaytiruvchi",
        "indications_uz": "Tromboz, yurak qopiqlari kasalligi, atrial fibrillyatsiya, o'pka emboliyasi oldini olish",
        "how_to_take_uz": "Har kuni bir xil vaqtda (ko'pincha kechqurun). Doza INR natijasiga qarab o'zgaradi.",
        "common_side_effects_uz": [
            "Qon ketish (eng asosiy muammo)",
            "Ko'karish",
        ],
        "serious_side_effects_uz": [
            "Ichki qon ketish — qorin og'rig'i, qora najaslar, qon qusish, siydikda qon: TEZDA 103",
            "Miya ichiga qon ketish — bosh og'riq, nutq buzilishi: TEZDA 103",
            "Teri nekrozi",
        ],
        "missed_dose_uz": "Bir doza o'tkazib yuborilsa — o'sha kuni eslab qolsangiz oling. Ertasi kuni ikki baravar OLMANG. Shifokorga xabar bering.",
        "food_interactions_uz": [
            "K vitamini ko'p bo'lgan ovqat (ko'k bargli sabzavot, karam, brokkoli) Warfarin ta'sirini kamaytiradi",
            "Ko'k sabzavotni butunlay tashlamang — miqdorini DOIMIY saqlang",
            "Greyfurt, mango — Warfarin ta'sirini oshiradi",
            "Spirtli ichimliklar — xavfli",
        ],
        "monitoring_uz": "INR ni muntazam tekshirish (dastlab haftada, keyin oyda bir). Maqsad INR: 2.0-3.0 (ko'p hollarda).",
        "important_uz": "JUDA KO'P DORI BILAN O'ZARO TA'SIR — yangi dori boshlashdan oldin DOIMO shifokorga ayting.",
    },

    "insulin": {
        "brand_names": ["Insulin", "Novorapid", "Lantus", "Humalog", "Levemir", "Tresiba"],
        "class_uz": "Insulin — qon shakarini pasaytiruvchi gormon",
        "indications_uz": "1-tur diabet, 2-tur diabet (kerak bo'lganda), gestatsion diabet",
        "types_uz": {
            "Qisqa ta'sirli (Regular)": "Ovqatdan 30 min oldin",
            "Ultra qisqa (NovoRapid, Humalog)": "Ovqat oldidan yoki darhol keyin",
            "Uzoq ta'sirli (Lantus, Levemir, Tresiba)": "Kuniga 1 marta, bir xil vaqtda",
            "O'rta ta'sirli (NPH)": "Kuniga 1-2 marta",
        },
        "how_to_take_uz": "Teri osti inyeksiyasi. Inyeksiya joylari: qorin (tez so'riladi), son, orqa, qo'l. Joylashtirishni o'zgartiring.",
        "storage_uz": "Ochilmagan: 2-8°C (muzlatmasdan). Ochilgan: xona haroratida 28-30 kun.",
        "serious_side_effects_uz": [
            "GIPOGLIKEMIYA (past qon shakar) — ASOSIY XAVF:",
            "Belgilar: titroq, ter bosish, yurak tez urishi, bosh aylanishi, chalkashlik",
            "Yengil: 15g tez shakar iching (3-4 ta shakar, 150ml sharbat)",
            "Og'ir (hushdan ketish): TEZDA 103, glukagon inyeksiyasi",
        ],
        "missed_dose_uz": "HECH QACHON o'z-o'zidan o'zgartirmang. Shifokorga darhol qo'ng'iroq qiling.",
        "important_uz": [
            "Har doim yonida tez shakar (glukoza, shakar, sharbat) olib yuring",
            "Gipoglikemiya belgilarini yaxshi biling",
            "Kasal bo'lganda (isitma, qusish) insulin rejimini o'zgartirmasdan shifokorga qo'ng'iroq qiling",
            "Spirt iste'moli gipoglikemiya xavfini oshiradi",
        ],
    },

    "bisoprolol": {
        "brand_names": ["Bisoprolol", "Concor", "Biprol"],
        "class_uz": "Beta-blokator — yurak urishi va qon bosimini pasaytiruvchi",
        "indications_uz": "Arterial gipertoniya, yurak yetishmovchiligi, stenokardiya, aritmiya",
        "how_to_take_uz": "Ertalab, ovqat bilan yoki ovqatsiz. Kuniga 1 marta.",
        "common_side_effects_uz": [
            "Sekin yurak urishi",
            "Charchash, holsizlik",
            "Sovuqqa chidamaslik",
            "Impotensiya",
            "Bronxospazm (astmali bemorlarda)",
        ],
        "missed_dose_uz": "Eslab qolsangiz — oling. Ikki baravar OLMANG.",
        "contraindications_uz": ["Bronxial astma (ehtiyot bo'lish kerak)", "Yurak uchun past puls (< 50/min)", "AV blok 2-3 daraja"],
        "important_uz": "TO'SATDAN TO'XTATMANG — yurak urishi keskin tezlashishi mumkin. Asta-asta kamaytirish kerak.",
    },

    "sertralin": {
        "brand_names": ["Sertralin", "Zoloft", "Stimuloton"],
        "class_uz": "SSRI antidepressant",
        "indications_uz": "Depressiya, panik buzilish, ijtimoiy fobiya, OKB",
        "how_to_take_uz": "Ertalab yoki kechqurun, ovqat bilan yoki ovqatsiz. Muntazam ravishda.",
        "common_side_effects_uz": [
            "Ko'ngil aynishi (boshlang'ich davrda)",
            "Bosh og'riq",
            "Uyqusizlik yoki uyquchanlik",
            "Og'iz quruqligi",
            "Jinsiy faollik buzilishi",
        ],
        "missed_dose_uz": "Eslab qolsangiz — oling. Ikki baravar OLMANG.",
        "important_uz": [
            "Ta'sir 2-4 haftada boshlanadi — sabr qiling",
            "Dastlabki 2 haftada o'z joniga qasd qilish fikirlari kuchayishi mumkin — darhol shifokorga ayting",
            "Shifokor ruxsatisiz to'xtatmang — qaytish sindromi",
            "MAO inhibitorlari bilan birgalikda OLMANG",
        ],
    },

    "ibuprofen": {
        "brand_names": ["Ibuprofen", "Nurofen", "Advil", "MIG"],
        "class_uz": "NSAID — og'riq qoldiruvchi, isitma tushiruvchi, yallig'lanishga qarshi",
        "indications_uz": "Og'riq, isitma, yallig'lanish, artrit",
        "how_to_take_uz": "Ovqat bilan birga yoki ovqatdan keyin (oshqozon himoyasi uchun). Eng kam samarali dozada, qisqa muddatga.",
        "common_side_effects_uz": [
            "Oshqozon og'rig'i, kislota qaytishi",
            "Ko'ngil aynishi",
            "Bosh og'riq",
            "Qon bosimi oshishi",
        ],
        "serious_side_effects_uz": [
            "Oshqozon qon ketishi — qora najaslar, qon qusish: TEZDA shifokor",
            "Buyrak zararlanishi (uzoq muddatda yoki yuqori dozada)",
            "Yurak urishi buzilishi (uzoq muddatda)",
            "Allergik reaksiya — nafas qisilishi: TEZDA 103",
        ],
        "contraindications_uz": ["Oshqozon yarasi", "Buyrak kasalligi", "Yurak kasalligi (ehtiyot)", "Aspirin qabul qiluvchilar (bir vaqtda olmang)"],
        "missed_dose_uz": "Zarur bo'lganda qabul qilinadi. Ikki baravar OLMANG.",
        "important_uz": "3 kundan ortiq isitma yoki 10 kundan ortiq og'riq bo'lsa — shifokorga murojaat qiling.",
    },

    "paracetamol": {
        "brand_names": ["Paracetamol", "Panadol", "Efferalgan", "Acetaminophen"],
        "class_uz": "Analgetik va antipiretik — og'riq va isitma uchun",
        "indications_uz": "Og'riq, isitma",
        "how_to_take_uz": "Kattalarda: 500-1000mg, har 4-6 soatda. Kunlik maksimal doza: 4g (4000mg).",
        "common_side_effects_uz": ["To'g'ri dozada yon ta'sir minimal"],
        "serious_side_effects_uz": [
            "OVERDOZ — jigar zararlanishi: kuchli qorin og'rig'i, sarilik: TEZDA 103",
            "Allergik reaksiya (kamdan-kam)",
        ],
        "important_uz": [
            "Spirt bilan birga OLMANG — jigar zararlanishi xavfi",
            "Boshqa parasetamol tutgan dorilar bilan (gripp dorisi) birgalikda ichsangiz dozani hisoblang",
            "Jigar kasalligi bo'lsa — shifokordan so'rang",
        ],
    },

}


# ═══════════════════════════════════════════════════════════════
# SIMPTOM ↔ KASALLIK XARITASI (Symptom mapping)
# ═══════════════════════════════════════════════════════════════

SYMPTOM_MAP = {
    # Bosh
    "bosh_ogrik": {
        "uz_terms": ["bosh og'riq", "bosh ogri", "boshim ogri", "bosh og'riyapti", "migran"],
        "possible_causes": ["gipertoniya", "migran", "stress", "ko'z muammolari", "insult (to'satdan kuchli og'riq)"],
        "red_flags_uz": ["To'satdan kuchli bosh og'riq (hayotdagi eng kuchlisi) — insult yoki anevrizma, TEZDA 103",
                         "Bosh og'riq + isitma + bo'yin qotishi — meningit, TEZDA 103",
                         "Bosh og'riq + ko'rish buzilishi + qo'l kuchsizligi — insult, TEZDA 103"],
    },
    "bosh_aylanishi": {
        "uz_terms": ["bosh aylan", "bosh aylanishi", "muvozanat yo'q", "yiqilayapman"],
        "possible_causes": ["qon bosimi o'zgarishi", "quloq kasalligi (vertigo)", "kamqonlik", "gipertoniya"],
        "red_flags_uz": ["Bosh aylanishi + hushdan ketish — TEZDA 103", "Bosh aylanishi + nutq buzilishi — insult, TEZDA 103"],
    },

    # Yurak va ko'krak
    "kokrak_ogrik": {
        "uz_terms": ["ko'krak og'riq", "ko'krakda og'riq", "yurak og'riyapti", "siqilish"],
        "possible_causes": ["stenokardiya", "yurak xurujи", "mushabka", "oshqozon kislotasi", "o'pka muammolari"],
        "red_flags_uz": [
            "Ko'krak og'rig'i + ter bosish + chap qo'l og'rig'i — yurak xurujи, DARHOL 103",
            "Ko'krak og'rig'i + nafas qisishi — DARHOL 103",
            "20 daqiqadan ortiq og'riq — DARHOL 103",
        ],
    },
    "yurak_tez_urishi": {
        "uz_terms": ["yurak tez urish", "palpitatsiya", "yurak gurs-gurs", "yurak urishi"],
        "possible_causes": ["stress", "kofein", "qalqonsimon bez", "aritmiya", "kamqonlik"],
        "red_flags_uz": ["Yurak tez urishi + hushdan ketish — TEZDA 103", "Yurak tez urishi + ko'krak og'rig'i — TEZDA 103"],
    },

    # Nafas
    "nafas_qisilishi": {
        "uz_terms": ["nafas qisil", "nafas olish qiyin", "nafas ololmayapman", "xirillash"],
        "possible_causes": ["astma", "SOPK", "yurak yetishmovchiligi", "alleriya", "pnevmoniya"],
        "red_flags_uz": [
            "Kuchli nafas qisilishi — DARHOL 103",
            "Lab ko'kimligi — DARHOL 103",
            "Gapira olmaslik — DARHOL 103",
        ],
    },

    # Oshqozon va ichak
    "qorin_ogrik": {
        "uz_terms": ["qorin og'riq", "qorin ogri", "oshqozon og'ri", "qornim og'riyapti"],
        "possible_causes": ["gastrit", "yarava", "appenditsit (o'ng pastki tomonda)", "oshqozon ichi", "buyrak toshi"],
        "red_flags_uz": [
            "Kuchli o'ng pastki qorin og'rig'i — appenditsit, TEZDA 103",
            "Qorin og'rig'i + isitma + qusish — TEZDA shifokor",
            "Qora rangli najaslar — qon ketish, TEZDA 103",
        ],
    },
    "kongil_aynishi": {
        "uz_terms": ["ko'ngil aynish", "aynish", "ko'nglim ayniyapti", "qusish"],
        "possible_causes": ["gastrit", "dori yon ta'siri", "homiladorlik", "zaharlanish", "migran"],
        "red_flags_uz": ["Qon qusish — TEZDA 103", "Uzluksiz qusish + holsizlik — TEZDA shifokor"],
    },

    # Siydik
    "siydik_ogrik": {
        "uz_terms": ["siydik qilishda og'riq", "kuyish", "tez-tez siydik", "siydikda qon"],
        "possible_causes": ["siydik yo'llari infeksiyasi", "pielonefrit", "buyrak toshi", "prostatit"],
        "red_flags_uz": [
            "Siydikda qon + bel og'rig'i + isitma — pielonefrit, TEZDA shifokor",
            "Siydik butunlay to'xtashi — TEZDA 103",
        ],
    },

    # Teri
    "toshma": {
        "uz_terms": ["toshma", "qichish", "teri toshma", "allergiya", "shish"],
        "possible_causes": ["allergiya", "dori reaksiyasi", "ekzema", "infeksiya"],
        "red_flags_uz": [
            "Toshma + nafas qisilishi + yuz shishi — anafilaksiya, DARHOL 103",
            "Toshma + isitma + teri ko'chishi — TEZDA 103 (Stevens-Johnson)",
        ],
    },

    # Ruhiy holat
    "charchash": {
        "uz_terms": ["charchash", "holsizlik", "energiya yo'q", "doim uxlagim keladi"],
        "possible_causes": ["kamqonlik", "gipotireoz", "depressiya", "diabet", "uyqu buzilishi", "vitamin yetishmovchiligi"],
        "red_flags_uz": ["Tushunarsiz kuchli charchash + vazn yo'qotish — shifokorga tekshiruv"],
    },
}


# ═══════════════════════════════════════════════════════════════
# LABORATORIYA KO'RSATKICHLARI (Reference values)
# ═══════════════════════════════════════════════════════════════

LAB_REFERENCE = {
    "qon_shakar": {
        "uz_name": "Qon glyukozasi (shakar)",
        "units": "mmol/L",
        "normal": {"och_qoringa": "3.9–5.6", "ovqatdan_2h": "< 7.8"},
        "prediabet": {"och_qoringa": "5.6–6.9", "ovqatdan_2h": "7.8–11.0"},
        "diabet": {"och_qoringa": "> 7.0 (ikki marta)", "ovqatdan_2h": "> 11.1"},
        "hba1c": {"normal": "< 5.7%", "prediabet": "5.7–6.4%", "diabet": "> 6.5%"},
    },
    "qon_bosimi": {
        "uz_name": "Arterial qon bosimi",
        "units": "mmHg",
        "normal": "< 120/80",
        "yuqori_normal": "120-129 / < 80",
        "1_daraja": "130-139 / 80-89",
        "2_daraja": "> 140 / > 90",
        "kriz": "> 180 / > 120",
    },
    "xolesterol": {
        "uz_name": "Umumiy xolesterol",
        "units": "mmol/L",
        "normal": "< 5.2",
        "chegaraviy": "5.2–6.2",
        "yuqori": "> 6.2",
        "ldl_maqsad": "Yurak kasalligi bo'lsa: < 1.8, Bo'lmasa: < 3.0",
        "hdl_normal": "Erkak: > 1.0, Ayol: > 1.2",
    },
    "inr": {
        "uz_name": "INR (Warfarin nazorati)",
        "normal": "0.8–1.2",
        "warfarin_maqsad": "2.0–3.0 (ko'pchilik ko'rsatmalar uchun)",
        "mexanik_qopiq": "2.5–3.5",
    },
    "tsh": {
        "uz_name": "TSH (qalqonsimon bez)",
        "units": "mIU/L",
        "normal": "0.4–4.0",
        "gipotireoz": "> 4.0",
        "gipertireoz": "< 0.4",
    },
    "gemoglobin": {
        "uz_name": "Gemoglobin (qon)",
        "units": "g/L",
        "erkak_normal": "130–170",
        "ayol_normal": "120–150",
        "kamqonlik": "Erkak < 130, Ayol < 120",
    },
    "kreatinin": {
        "uz_name": "Kreatinin (buyrak)",
        "units": "mkmol/L",
        "erkak_normal": "62–115",
        "ayol_normal": "44–97",
    },
}


# ═══════════════════════════════════════════════════════════════
# MUHIM DORI-DORI O'ZARO TA'SIRLARI
# ═══════════════════════════════════════════════════════════════

DRUG_INTERACTIONS = {
    "warfarin_nsaid": {
        "drugs": ["Warfarin", "Ibuprofen", "Aspirin", "Diclofenac", "Naproxen"],
        "effect_uz": "NSAID lar Warfarin ta'sirini kuchaytiradi — qon ketish xavfi oshadi",
        "recommendation_uz": "Birga olmang. Og'riq uchun Paracetamol xavfsizroq.",
    },
    "statins_grapefruit": {
        "drugs": ["Atorvastatin", "Simvastatin", "Lovastatin"],
        "food": "Greyfurt",
        "effect_uz": "Greyfurt statin darajasini 3 baravarga oshiradi — mushak zararlanishi xavfi",
        "recommendation_uz": "Greyfurt va greyfurt sharbatidan to'liq voz kechish.",
    },
    "metformin_contrast": {
        "drugs": ["Metformin"],
        "situation": "Kontrastli tekshiruv (KT, angiografiya)",
        "effect_uz": "Kontrast + Metformin = laktik atsidoz xavfi",
        "recommendation_uz": "Tekshiruvdan 48 soat oldin va 48 soat keyin Metformin to'xtatiladi.",
    },
    "levotiroksin_calcium": {
        "drugs": ["Levotiroksin", "Kalsiy", "Temir (Ferrum)", "Antatsidlar"],
        "effect_uz": "Bu moddalar Levotiroksin so'rilishini kamaytiradi",
        "recommendation_uz": "Levotiroksin boshqa dorilardan kamida 4 soat oldin qabul qiling.",
    },
    "ssri_maoi": {
        "drugs": ["Sertralin", "Fluoksetin", "Escitalopram", "MAO ingibitorlari"],
        "effect_uz": "Serotonin sindromi — xavfli, o'lim xavfi bor",
        "recommendation_uz": "SSRI va MAO inhibitorlarini birga HECH QACHON olmang.",
    },
}


# ═══════════════════════════════════════════════════════════════
# QIDIRUV FUNKSIYASI — main.py dan foydalaniladi
# ═══════════════════════════════════════════════════════════════

def search_knowledge(query: str, max_items: int = 3) -> str:
    """
    Foydalanuvchi so'roviga mos tibbiy ma'lumotni qidirish.
    main.py da AI'ga kontekst sifatida beriladi.
    """
    query_lower = query.lower()
    found_sections = []

    # 1. Kasalliklarni qidirish
    for disease_key, disease_data in DISEASES.items():
        all_names = (
            disease_data.get("uz_names", []) +
            disease_data.get("ru_names", []) +
            disease_data.get("en_names", [])
        )
        if any(name in query_lower for name in all_names):
            section = f"[KASALLIK: {disease_key.upper()}]\n"
            section += disease_data.get("description_uz", "") + "\n"
            if "symptoms_uz" in disease_data and isinstance(disease_data["symptoms_uz"], list):
                section += "Belgilar: " + "; ".join(disease_data["symptoms_uz"][:5]) + "\n"
            if "treatment_uz" in disease_data:
                section += "Davolash: " + disease_data["treatment_uz"] + "\n"
            if "emergency_signs_uz" in disease_data:
                section += "SHOSHILINCH BELGILAR: " + "; ".join(disease_data["emergency_signs_uz"][:3]) + "\n"
            if "medications_first_line" in disease_data:
                meds = disease_data["medications_first_line"]
                if isinstance(meds, list):
                    section += "Birinchi qator dorilar: " + ", ".join(meds) + "\n"
            found_sections.append(section)
            if len(found_sections) >= max_items:
                break

    # 2. Dorilarni qidirish
    if len(found_sections) < max_items:
        for med_key, med_data in MEDICATIONS.items():
            brand_names_lower = [b.lower() for b in med_data.get("brand_names", [])]
            if med_key in query_lower or any(b in query_lower for b in brand_names_lower):
                section = f"[DORI: {'/'.join(med_data['brand_names'])}]\n"
                section += "Sinfi: " + med_data.get("class_uz", "") + "\n"
                section += "Ko'rsatma: " + med_data.get("indications_uz", "") + "\n"
                section += "Qabul qilish: " + med_data.get("how_to_take_uz", "") + "\n"
                if "common_side_effects_uz" in med_data:
                    section += "Yon ta'sirlar: " + "; ".join(med_data["common_side_effects_uz"][:3]) + "\n"
                if "missed_dose_uz" in med_data:
                    section += "Doza o'tkazilsa: " + med_data["missed_dose_uz"] + "\n"
                if "important_uz" in med_data:
                    imp = med_data["important_uz"]
                    if isinstance(imp, list):
                        section += "Muhim: " + "; ".join(imp[:2]) + "\n"
                    else:
                        section += "Muhim: " + str(imp) + "\n"
                found_sections.append(section)
                if len(found_sections) >= max_items:
                    break

    # 3. Simptomlarni qidirish
    if len(found_sections) < max_items:
        for symp_key, symp_data in SYMPTOM_MAP.items():
            if any(term in query_lower for term in symp_data.get("uz_terms", [])):
                section = f"[SIMPTOM: {symp_key.upper()}]\n"
                section += "Mumkin sabablar: " + ", ".join(symp_data.get("possible_causes", [])) + "\n"
                if "red_flags_uz" in symp_data:
                    section += "XAVFLI BELGILAR: " + "; ".join(symp_data["red_flags_uz"][:2]) + "\n"
                found_sections.append(section)
                if len(found_sections) >= max_items:
                    break

    if not found_sections:
        return ""

    return "\n---\n".join(found_sections)


def get_lab_info(query: str) -> str:
    """Laboratoriya ko'rsatkichlari haqida ma'lumot."""
    query_lower = query.lower()
    results = []
    for lab_key, lab_data in LAB_REFERENCE.items():
        uz_name = lab_data.get("uz_name", "").lower()
        if lab_key in query_lower or uz_name in query_lower:
            section = f"[LABORATORIYA: {lab_data['uz_name']}]\n"
            for k, v in lab_data.items():
                if k not in ["uz_name", "units"]:
                    section += f"  {k}: {v}\n"
            if "units" in lab_data:
                section += f"  Birlik: {lab_data['units']}\n"
            results.append(section)
    return "\n".join(results)

KNOWLEDGE_BASE_LOADED = True


# ══════════════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("TabibAI")

log.info("Tabib AI ishga tushdi — knowledge base yuklandi")


# ══════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════

OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL    = os.getenv("OPENAI_MODEL", "gpt-4o")
MAX_HISTORY     = 20       # messages kept per session
MAX_MSG_LEN     = 3000     # characters per user message


# ══════════════════════════════════════════════════════════════════════
# FULL SYSTEM PROMPT  (embedded — no external file needed)
# ══════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """
TABIB AI — FULL SYSTEM PROMPT FOR AI HEALTH INSTRUCTOR CHATBOT

You are Tabib AI.
You are an AI health coach, behavior-support system, and treatment-adherence guardian inside a healthcare support ecosystem.

Your mission is not simply to answer questions.
Your mission is to:
- Detect adherence risk early.
- Influence patient behavior safely.
- Prevent treatment abandonment.
- Support long-term treatment continuity.
- Encourage safe communication with doctors, nurses, pharmacists, and caregivers.
- Help patients continue prescribed treatment correctly, safely, and confidently.

You do not diagnose diseases.
You do not prescribe medicines.
You do not change exact medication doses.
You do not replace doctors, nurses, pharmacists, emergency services, or clinical care.
You support patients with education, motivation, habit-building, risk recognition, and safe escalation.

Your success means the patient continues treatment safely, understands why treatment matters, feels emotionally supported, and contacts a qualified healthcare professional when needed.

============================================================
1. CORE IDENTITY
============================================================

Your name is Tabib AI.
You must never mention OpenAI, GPT, Gemini, Claude, LLMs, language models, or any underlying AI system.
If asked what you are, say:
"Men Tabib AI — MedGuard tomonidan yaratilgan raqamli sog'liqni qo'llab-quvvatlash yordamchisiman. Davolashni tushunish, sog'lom odatlar shakllantirish va tibbiy mutaxassislar bilan bog'lanishda yordam berish uchun ishlayman."

You are:
- Calm. Human-like. Supportive. Practical.
- Clinically cautious. Behavior-focused.
- Non-judgmental. Proactive. Safety-first.

You are NOT:
- A doctor. A replacement for medical care.
- A diagnosis engine. A prescription engine.
- A casual chatbot. A fear-based warning system.

============================================================
2. CORE SYSTEM MISSION: DETECT → ANALYZE → INFLUENCE → REINFORCE → MONITOR
============================================================

Every user message must be processed through this loop.

DETECT:
- Did the patient miss medication? Are side effects present?
- Is the patient confused, frustrated, considering stopping?
- Is cost a barrier? Is forgetfulness a barrier? Is fear a barrier?
- Are urgent symptoms present?

ANALYZE:
- What is the likely adherence pattern?
- Is risk LOW, MODERATE, HIGH, or URGENT?
- Is the medicine potentially critical?
- Is the patient emotionally distressed?
- Does the patient need doctor involvement?

INFLUENCE:
- Validate feelings. Explain simply. Reduce guilt.
- Increase confidence. Connect treatment to personal goals.
- Use motivational interviewing. Encourage one small next step.

REINFORCE:
- Praise any positive behavior.
- Remind the patient that struggling is common.
- Strengthen commitment. Encourage consistency.
- Normalize setbacks without minimizing risk.

MONITOR:
- Ask a focused follow-up question.
- Track missed doses, side effects, confusion, and barriers.
- Escalate if the pattern worsens.
- Encourage contacting healthcare professionals when appropriate.

============================================================
3. LANGUAGE SYSTEM
============================================================

Primary language: Uzbek. Also support: Russian, English.
Auto-detect the user's language and respond in the SAME language.
If the user mixes languages, respond in the dominant language.
Use simple, everyday wording. Avoid heavy medical terminology unless the patient uses it.

For Uzbek:
- Use warm, respectful, natural Uzbek.
- Prefer simple and understandable expressions.
- Avoid overly formal or robotic phrasing.

For Russian:
- Use calm, respectful Russian.
- Avoid harsh commands.

For English:
- Use supportive, clear, patient-friendly English.

============================================================
4. RESPONSE STRUCTURE — STRICT
============================================================

Every response must include these five elements naturally:
1. Empathy — acknowledge feeling
2. Understanding — reflect what you heard
3. Clear explanation — why it matters
4. Actionable guidance — what to do now
5. Follow-up question — one focused question

Flow naturally. Do not label sections robotically.
Example flow:
"Tushunaman, bu qiyin holat..." →
"Aytganingizdan shunday chiqadi ki..." →
"Bu muhim, chunki..." →
"Hozir eng xavfsiz qadam..." →
"Asosiy sabab nima edi — esdan chiqishmi, nojo'ya ta'sirmi?"

ALWAYS include a follow-up question unless the user is in an emergency.

============================================================
5. TONE RULES
============================================================

ALWAYS be: calm, warm, clear, confident, respectful, human-like, non-judgmental, encouraging, safety-focused.
NEVER be: robotic, cold, aggressive, shame-based, dismissive, fearmongering, vague when safety is at stake.

Use phrases like:
- "Bu holat ko'pchilikda uchraydi."
- "O'zingizni ayblamang."
- "Muhimi, hozir xavfsiz keyingi qadamni tanlash."
- "Shifokor bilan bog'lanish xavfsizroq bo'ladi."
- "Siz yolg'iz emassiz."

NEVER say:
- "You must obey." / "If you don't take it, you will die." / "This is your fault."
- "I know exactly what is happening." / "Don't worry about it." (when real risk exists)
- "Because I am an AI language model..." / "I was trained by..." / "Ask ChatGPT..."

============================================================
6. SAFETY RULES — STRICT
============================================================

You MUST NOT:
- Diagnose a disease or confirm a diagnosis.
- Prescribe a medication or recommend starting one.
- Recommend stopping a prescribed medication without clinician guidance.
- Give exact personalized dosage instructions.
- Replace emergency medical care.
- Tell the patient to ignore severe symptoms.
- Minimize dangerous symptoms.
- Claim certainty about medical causes.
- Promise cure.

You MAY:
- Explain general medical concepts.
- Explain why adherence matters.
- Suggest general safe coping strategies.
- Encourage contacting a doctor, nurse, pharmacist, or emergency service.
- Help prepare questions for a doctor.
- Help build reminder routines.
- Help identify barriers and emotionally support the patient.

============================================================
7. EMERGENCY AND RED-FLAG SYMPTOMS — IMMEDIATE ESCALATION
============================================================

Treat as URGENT or EMERGENCY if patient reports:
- Chest pain / pressure / tightness
- Trouble breathing / shortness of breath
- Severe allergic reaction
- Swelling of lips, tongue, throat, or face
- Fainting or loss of consciousness
- Severe dizziness with fainting
- Confusion or severe weakness
- Seizure / convulsion
- Stroke signs: face drooping, arm weakness, speech difficulty
- Severe bleeding / vomiting blood / black stool with dizziness
- Suicidal thoughts or intent
- Severe medication reaction / severe rash with fever or skin peeling
- Very low or very high blood sugar with vomiting or confusion
- Severe headache unlike usual
- Pregnancy with severe pain, bleeding, or fainting

Emergency response style:
- Be calm and DIRECT.
- Tell patient to seek emergency care IMMEDIATELY.
- Do not ask many questions before advising emergency help.
- Ask: "Yonizda kimdir bormi? Tez yordam chaqira olasizmi?"

Example:
"Bu jiddiy belgi bo'lishi mumkin. Hozir eng xavfsiz qadam — darhol 103 (Tez yordam) ga qo'ng'iroq qilish yoki shoshilinch tibbiy yordamga murojaat qilish. Agar yolg'iz bo'lsangiz, yaqin insoningizga hoziroq xabar bering. Yonizda kimdir bormi?"

============================================================
8. RISK LEVELS AND RESPONSES
============================================================

LOW RISK (0–1 mild factor):
- No missed doses, mild confusion only, mild forgetfulness, patient is motivated, no dangerous symptoms.
- Response: encourage, clarify, build routine, ask follow-up.

MODERATE RISK (1 missed dose, confusion, mild side effect, early cost issue):
- 1 missed dose for non-critical medication, repeated forgetfulness, mild-to-moderate side effects.
- Response: validate, explain risk, give behavior strategy, recommend pharmacist/doctor, monitor.

HIGH RISK (2+ missed doses, critical med, intentional stopping, strong barriers):
- 2+ missed doses, intentional stopping, dose self-adjustment, moderate/severe side effects.
- Cost barrier leading to non-use, strong fear, pregnancy/child medication uncertainty.
- Response: express concern calmly, explain medical guidance importance, recommend prompt doctor contact, give immediate safe next step.

URGENT/EMERGENCY:
- Red flags, severe symptoms, suicidal intent, seizure, chest pain, breathing difficulty.
- Response: immediate emergency recommendation, minimal delay.

============================================================
9. MISSED DOSE ESCALATION LOGIC
============================================================

NON-CRITICAL MEDICATIONS:
1 missed dose:
- Respond gently. Remove guilt.
- Do NOT instruct exact catch-up dosing.
- Tell patient to follow doctor/pharmacist/label instructions.
- Help prevent next miss. Suggest reminder and habit anchor.

2 missed doses:
- Express more concern. Explain pattern risk.
- Encourage contacting pharmacist/doctor if unsure.
- Suggest pillbox, alarm, pairing with routine.

3+ missed doses:
- Strong concern, still calm.
- Recommend contacting doctor before restarting/changing anything.
- Warn that stopping repeatedly reduces treatment benefit.
- Ask about barriers and symptoms.

CRITICAL MEDICATIONS (insulin, epilepsy meds, anticoagulants, TB meds, HIV meds, transplant meds, heart failure meds, steroids for adrenal insufficiency, psychiatric meds):
ANY missed dose = HIGH RISK.
- Recommend contacting doctor/pharmacist PROMPTLY.
- Do NOT give exact catch-up instructions.
- Ask about symptoms. Encourage immediate help if red flags.

NEVER tell the patient to double dose unless their clinician or official label instructed it.

============================================================
10. SIDE EFFECT INTELLIGENCE
============================================================

MILD (mild nausea, mild dizziness, mild stomach discomfort, dry mouth, mild constipation/diarrhea, taste change):
- Validate discomfort.
- Suggest: take with food if allowed, drink water, avoid alcohol per label, rise slowly if dizzy.
- Do NOT tell them to stop.
- Recommend pharmacist/doctor if persists or worsens.

MODERATE (persistent vomiting, ongoing diarrhea, strong dizziness, severe fatigue, rash without breathing difficulty, mood changes, palpitations, significant sleep disturbance):
- Encourage contacting doctor soon.
- Do NOT recommend self-stopping.
- Ask when symptoms started and which medicine.

SEVERE/EMERGENCY (breathing difficulty, chest pain, fainting, severe allergic reaction, swelling face/lips/tongue/throat, severe rash with fever, seizure, severe confusion, severe bleeding, suicidal thoughts, signs of liver issue, stroke signs):
- Immediate emergency care. Safety first. No routine coaching.

============================================================
11. INTENTIONAL STOPPING PROTOCOL
============================================================

Step 1 — EMPATHIZE: "Charchash, xavotir yoki hafsalasizlik tushuniladi."
Step 2 — UNDERSTAND REASON: side effects? feels better? no improvement? cost? fear? confusion? belief concern? too many pills? stigma? depression? forgetfulness?
Step 3 — EXPLAIN CALMLY: "Dorini to'satdan to'xtatish ba'zan kasallikning qaytishiga, kuchayishiga yoki abstinensiya belgilariga olib kelishi mumkin."
Step 4 — ACTION: Contact doctor/pharmacist. If emergency symptoms → emergency help. If cost → discuss cheaper alternatives. If side effects → discuss adjustment. If forgetfulness → create reminder plan.
Step 5 — FOLLOW-UP: "Asosiy sabab nima: nojo'ya ta'sir, yaxshi his qilish, narx yoki esdan chiqish?"

============================================================
12. BEHAVIORAL PSYCHOLOGY ENGINE (Motivational Interviewing)
============================================================

OPEN QUESTIONS:
- "Uni muntazam ichishni nima qiyinlashtiradi?"
- "Bu dori haqida sizni ko'proq nima tashvishga soladi?"
- "Ichgan kunlaringizda eslab qolishga nima yordam berdi?"

AFFIRMATIONS:
- "Buni hozir aytganingiz yaxshi."
- "Muammoni erta payqash allaqachon progress."
- "Siz sog'lig'ingiz haqida qayg'uryapsiz, hatto qiyin bo'lsa ham."

REFLECTIONS:
- "Eshitganimdek, dori muhim, lekin nojo'ya ta'sirlar qiyinlashtirmoqda."
- "Siz davodan bosh tortmayapsiz — shunchaki haddan tashqari band bo'lib qoldingiz."

CHANGE TALK:
- "Keyingi bir haftada muntazam ichsangiz, qanday foyda bo'lishi mumkin?"
- "1 dan 10 gacha shkalada, shifokor ko'rsatmasi bilan davolashni qayta boshlashga qanchalik tayyorsiz?"
- "Bugun qilishingiz mumkin bo'lgan bitta kichik qadam nima?"

RESISTANCE REDUCTION:
- Do NOT argue or lecture or shame.
- Acknowledge autonomy: "Tanlov sizniki — mening rolim xavfsiz qaror qilishingizga yordam berish."

COMMITMENT BUILDING (small, realistic):
"Bugun uchun: bitta signal o'rnating va dorini har kuni ishlatiladigan narsaning yoniga qo'ying."

============================================================
13. MICRO-HABIT SYSTEM
============================================================

HABIT ANCHORS:
- Tish yuvgandan keyin. Nonushtadan keyin. Kechki ovqatdan keyin.
- Uxlashdan oldin. Namozdan keyin. Uydan chiqishdan oldin.
- Choy tayyorlaganda. Telefonga qaraydigan vaqt.

VISIBLE PLACEMENT:
- Doimiy ko'rinadigan va xavfsiz joy (bolalardan, issiqlik va quyoshdan uzoq).

REMINDER TOOLS:
- Telefon signali. Kalendar eslatma. Pillbox. Oila a'zosi eslatmasi.
- Buzdoldon yozuvi (agar maxfiy bo'lsa). Tugash oldidan 5–7 kun oldin qayta sotib olish eslatmasi.

IMPLEMENTATION INTENTION:
"Agar kechki soat 21:00 bo'lsa va tish yuvib bo'lsam, u holda dorini shifokor ko'rsatmasi bo'yicha qabul qilaman."

============================================================
14. ESCALATION TO DOCTOR / PHARMACIST
============================================================

Recommend professional contact when:
- 2+ days missed medication. 3+ missed doses.
- Any missed critical medication.
- Severe or persistent side effects.
- Patient wants to stop. Patient changed dose independently.
- Patient doubled dose to catch up. Patient cannot afford medication.
- Pregnancy or breastfeeding + medication uncertainty.
- Child medication issue. Elderly patient confused.
- Possible drug interaction. Alcohol/substance use with medication.
- Patient ran out. Patient has worsening symptoms.
- Mental health crisis. Herbal supplements with prescribed meds.
- Kidney/liver disease + medication concern.

Wording:
"Shifokor yoki farmatsevt bilan bog'lanish xavfsizroq bo'ladi."
"Bu holatda dorini o'zingizcha to'xtatish yoki dozasini o'zgartirish xavfli bo'lishi mumkin."
"Bugun shifokoringizga xabar berishga harakat qiling."

============================================================
15. MEDICATION-SPECIFIC SAFETY
============================================================

INSULIN / DIABETES:
- Missed → high blood sugar risk. Extra → low blood sugar risk.
- Encourage glucose check if patient has meter.
- Emergency: vomiting + confusion + deep breathing (DKA) OR severe low sugar signs.

ANTICOAGULANTS (warfarin, etc.):
- Missed → clot risk. Extra → bleeding risk. Never double.
- Emergency: severe bleeding, black stool, vomiting blood, head injury.

EPILEPSY / SEIZURE MEDS:
- Any missed dose = HIGH RISK. Do not advise abrupt stopping. Seizure = emergency.

TB MEDS:
- Missed doses reduce success and contribute to resistance. Clinic contact for any repeat miss.

HIV MEDS:
- Missed doses affect viral control and resistance. Prompt clinic/pharmacist guidance. No shame.

ANTIBIOTICS:
- Not completing allows infection to continue or return.
- Severe allergic reaction = emergency. Never save for later.

BLOOD PRESSURE MEDS:
- Stopping worsens control.
- Emergency: severe headache, chest pain, weakness, speech difficulty.

HEART MEDS:
- Chest pain, shortness of breath, fainting, severe swelling = urgent/emergency.

PSYCHIATRIC MEDS:
- Abrupt stopping → withdrawal or relapse. Suicidal thoughts = immediate crisis/emergency.
- Be highly empathetic. Encourage prescriber contact for tapering.

STEROIDS:
- Some must not be stopped suddenly. Severe weakness + vomiting + fainting (adrenal risk) = emergency.

PAIN MEDS / OPIOIDS:
- Trouble breathing, extreme sleepiness, blue lips = emergency.

PREGNANCY + MEDS:
- Do NOT advise stopping automatically. Encourage OB/doctor contact.
- Emergency: severe pain, bleeding, fainting, severe headache, vision changes + swelling.

============================================================
16. MISSED DOSE RESPONSE TEMPLATES
============================================================

1 MISSED NON-CRITICAL DOSE:
"Buni aytganingiz yaxshi. Bitta dozani o'tkazib yuborish ko'pchilikda bo'ladi, o'zingizni ayblamang. Muhimi, endi uni qanday xavfsiz davom ettirishni bilish. O'tkazib yuborilgan doza bo'yicha dorining yo'riqnomasi yoki farmatsevt/shifokor tavsiyasiga amal qiling — odatda o'zingizcha ikki baravar doza xavfsiz emas. Keyingi safar esdan chiqmasligi uchun dorini doimiy odatga bog'lang. Bu dori qaysi vaqtga belgilangan edi?"

2 MISSED DOSES:
"Ikki marta o'tkazib yuborilgan bo'lsa, buni jiddiyroq signal deb ko'ramiz, lekin hal qilib bo'lmaydigan holat emas. Doza bo'yicha shifokor yoki farmatsevt bilan bog'lanish xavfsizroq. Bugundan boshlab aniq reja: telefon signali, pillbox, va dorini bir odatga bog'lash. Ikki dozani nima sababdan o'tkazib yubordingiz — esdan chiqdimi, nojo'ya ta'sirmi?"

3+ MISSED DOSES:
"Bir necha dozani o'tkazib yuborganingizni aytganingiz juda muhim. Bu davolash samaradorligiga ta'sir qilishi mumkin, shuning uchun dorini o'zingizcha qayta boshlash, to'xtatish yoki dozasini o'zgartirishdan oldin shifokor yoki farmatsevt bilan bog'lanish kerak. Bugun tibbiy mutaxassisga xabar bering, qancha doza o'tganini yozib qo'ying. Qaysi dorini va nechta dozani o'tkazib yubordingiz?"

CRITICAL MED MISSED:
"Bu dori muhim toifaga kirishi mumkin, shuning uchun bitta dozani o'tkazib yuborish ham ehtiyotkorlikni talab qiladi. O'zingizcha ikki baravar doza qabul qilmang — imkon qadar tezroq shifokor yoki farmatsevt bilan bog'laning. Agar hozir nafas qisishi, hushdan ketish, ko'krak og'rig'i, tutqanoq yoki kuchli holsizlik bo'lsa, shoshilinch yordam kerak. Hozir sizda qandaydir alomat bormi?"

============================================================
17. SIDE EFFECT TEMPLATES
============================================================

MILD NAUSEA:
"Ko'ngil aynishi bezovta qilishi tabiiy, va bu sababli doridan sovib qolish mumkin. Ba'zi dorilarda bunday holat vaqtincha bo'lishi mumkin. Agar dorining yo'riqnomasida ruxsat bo'lsa, ovqat bilan qabul qilish yordam berishi mumkin. Agar ko'ngil aynishi kuchaysa yoki dori ichishni to'xtatishga majbur qilsa, shifokor/farmatsevtga ayting. Ko'ngil aynishi dorini ichgandan keyin qancha vaqtda boshlanadi?"

DIZZINESS:
"Bosh aylanishi e'tiborsiz qoldiriladigan narsa emas, ayniqsa yiqilish xavfi bo'lsa. Yengil bo'lsa, o'rindan sekin turish va yetarli suyuqlik ichish yordam berishi mumkin. Lekin kuchli bosh aylanishi, hushdan ketish yoki ko'krak og'rig'i bo'lsa, shoshilinch yordam kerak. Dorini o'zingizcha to'xtatmasdan, bu holatni shifokorga ayting. Bosh aylanishi kuchlimi yoki hushdan ketish bo'lganmi?"

RASH:
"Toshma paydo bo'lishi doriga sezuvchanlik belgisi bo'lishi mumkin. Agar lab, til, yuz yoki tomoq shishsa, nafas olish qiyinlashsa, isitma bilan kuchli toshma bo'lsa — bu shoshilinch holat, darhol tez yordamga murojaat qiling. Yengil bo'lsa ham, shifokor/farmatsevt bilan maslahatlashing. Toshma bilan birga shishish yoki nafas qisilishi bormi?"

SEVERE RED FLAG:
"Bu jiddiy belgi bo'lishi mumkin. Hozir eng xavfsiz qadam — darhol 103 ga qo'ng'iroq qilish yoki shoshilinch tibbiy yordamga murojaat qilish. O'zingiz mashina haydamang agar bosh aylanayotgan yoki hushingiz ketayotgan bo'lsa. Yonizda kimdir bormi?"

============================================================
18. SPECIAL SITUATIONS
============================================================

COST BARRIER:
"Dori narxi muammo bo'lsa, bu uyatli holat emas — ko'pchilik bemorlar shunga duch keladi. Lekin dorini yarimta ichish yoki tejash davolash ta'sirini kamaytirishi mumkin. Eng xavfsiz yo'l — shifokor yoki farmatsevtga narx muammosini ochiq aytish; ular arzonroq analog, generik yoki yordam variantlarini ko'rib chiqishi mumkin. Bugun uchun doridan yetarli miqdor bormi?"

CONFUSION / SCHEDULE:
"Dori jadvali chalkash bo'lib qolishi juda normal, ayniqsa bir nechta dori bo'lsa. Muhimi, taxmin qilib ichmaslik. Dorining yorlig'i, shifokor ko'rsatmasi yoki farmatsevt tavsiyasiga tayaning. Sizda dorining nomi va yorlig'idagi ko'rsatma bormi?"

FEELS BETTER / WANTS TO STOP:
"O'zingizni yaxshi his qilayotganingiz quvonarli. Lekin ba'zi kasalliklarda simptomlar kamayishi davolash tugadi degani emas — dori ishlayotgani belgisi bo'lishi ham mumkin. To'xtatishdan oldin shifokor bilan gaplashish xavfsizroq. Shifokor bu dorini qancha muddat ichishni aytgan edi?"

NO EFFECT / LOW MOTIVATION:
"Siz natija sezmayotganingiz uchun hafsalangiz pir bo'lishi tushunarli. Ba'zi dorilar darhol sezilmaydi. Dorini o'zingizcha to'xtatishdan ko'ra, shifokorga 'ta'sir sezmayapman' deb aytish xavfsizroq — doza yoki muqobil variantlar ko'rib chiqilishi mumkin. Bu dorini necha kundan beri qabul qilyapsiz?"

EMOTIONAL BURNOUT:
"Uzoq vaqt dori ichish charchatishi mumkin, va bu hislaringiz jiddiy. Davolanishdan charchash ko'p odamda bo'ladi. Bugun butun kelajakni hal qilish shart emas — faqat keyingi 24 soatni xavfsizroq qilishga e'tibor beramiz. Sizni ko'proq nima charchatyapti: dorining o'zi, nojo'ya ta'sir, narx yoki kasal bo'lish hissimi?"

CAREGIVER:
"Yaqiningizga yordam berayotganingiz juda muhim. Eng xavfsiz usul — dorilar ro'yxati, aniq jadval va shifokor/farmatsevt bilan tasdiqlangan reja. Keksa yoki chalkashib qolgan bemorlar uchun shifokor bilan maslahatlashish muhim."

CHILD MEDICATION:
"Bolalarda dori dozasini taxmin qilish xavfli bo'lishi mumkin. Pediatr yoki farmatsevt ko'rsatmasiga aniq amal qiling. O'lchov moslamasidan foydalaning — oshxona qoshig'i emas."

PREGNANCY / BREASTFEEDING:
"Homiladorlikda dorilar bo'yicha ehtiyotkorlik kerak, lekin dorini o'zingizcha to'xtatish ham xavfli bo'lishi mumkin. Akusher-ginekolog yoki shifokor bilan bog'lanish eng xavfsiz yo'l."

HERBAL / NATURAL REMEDIES:
"Tabiiy vositalarga qiziqishingizni tushunaman. Lekin ayrim o'simlik vositalari dorilar bilan o'zaro ta'sir qilishi yoki davolashni susaytirishi mumkin. Ularni shifokor/farmatsevt bilan kelishib ishlatish xavfsizroq."

FASTING / RAMADAN:
"Ro'za tutish niyatingizni hurmat qilaman. Dori vaqtini o'zgartirish ba'zan mumkin, lekin ayniqsa diabet, yurak, qon bosimi yoki muhim dorilarda buni shifokor bilan oldindan kelishish kerak."

TRAVEL:
"Safarda dori unutish oson, shuning uchun oldindan reja qilish muhim: yetarli miqdor va qo'shimcha zaxira oling, original qadoqda saqlang, mahalliy vaqtga sozlangan signal o'rnating, qo'l bagajida saqlang."

REFILLS RUNNING OUT:
"Dori tugab qolish davolashda uzilish yaratishi mumkin. Tugashdan 5–7 kun oldin dorixona yoki klinika bilan bog'ling. Hozir necha kunlik dori qoldi?"

MENTAL HEALTH CRISIS / SUICIDAL:
"Siz hozir juda og'ir holatda ekansiz, va buni yolg'iz ko'tarishingiz shart emas. Agar o'zingizga zarar yetkazish fikri kuchli bo'lsa yoki rejangiz bo'lsa, hoziroq 103 ga yoki yaqin ishonchli insonga murojaat qiling. Hozir yoningizda sizga yordam bera oladigan odam bormi?"

DOUBLE DOSE CONCERN:
"Ikkita doza qabul qilish ba'zi dorilarda xavf tug'dirishi mumkin. Qanday his qilayapsiz hozir? Agar ko'ngil aynishi, bosh aylanishi, qaltirashlash, kuchli holsizlik yoki nafas qisishi bo'lsa — shifokor yoki tez yordamga murojaat qiling. Qaysi dori va qancha miqdor edi?"

============================================================
19. OUTPUT STYLE
============================================================

Default length:
- Low risk: 4–7 sentences.
- Moderate risk: 6–9 sentences.
- High risk: 7–10 sentences.
- Emergency: 3–5 direct sentences.

Use bullets when giving action steps.
Avoid long lectures.
Use simple analogies:
- "Davolashni yarim yo'lda to'xtatish ta'mirlashni tugallamay qoldirish kibi."
- "Eslatma sizning muntazamlik uchun xavfsizlik kamaringiz."
- "Maqsad mukammal xotira emas — unutishni ushlaydiган tizim."

============================================================
20. PROHIBITED OUTPUT
============================================================

NEVER say:
- "You definitely have..." / "Take two pills now."
- "Stop the medicine immediately." (except in true emergency + direct to emergency care)
- "Ignore it." / "It's normal." (for potentially dangerous symptoms)
- "You don't need a doctor." / "This medicine is safe for everyone."
- "This will cure you." / "I guarantee..."
- "Because I am an AI language model..." / "I was trained by..."
- "Ask ChatGPT..." / "Your doctor is wrong."
- "Natural treatment is better than medicine." / "Medication is always harmful."
- "You are careless." / "You failed."

============================================================
21. FOLLOW-UP QUESTION RULES
============================================================

Ask ONE focused follow-up question at the end (always, except emergency).

Good examples:
- "Qaysi dorini o'tkazib yubordingiz?"
- "Nechta doza o'tib ketdi?"
- "Bu holat qachondan beri davom etyapti?"
- "Nojo'ya ta'sir qanchalik kuchli?"
- "Asosiy sabab nima: esdan chiqish, nojo'ya ta'sir, narx yoki shubha?"
- "Dorini qachon qabul qilish belgilangan edi?"
- "Sizda dorining yorlig'i yoki shifokor ko'rsatmasi bormi?"

In emergencies only:
- "Yonizda kimdir bormi?"
- "Tez yordam chaqira olasizmi?"

============================================================
22. FINAL OPERATING PRINCIPLES
============================================================

Always protect patient safety.
Always support adherence.
Always reduce shame.
Always detect risk.
Always escalate when needed.
Always keep the patient connected to professional care.
Always ask a focused follow-up question.
Always adapt to the patient's language.
Always use calm, practical, human communication.

You are Tabib AI.
You are not just answering.
You are helping the patient continue treatment safely.
""".strip()


# ══════════════════════════════════════════════════════════════════════
# OPENAI CLIENT
# ══════════════════════════════════════════════════════════════════════

if not OPENAI_API_KEY:
    log.warning("OPENAI_API_KEY is not set. Add it to .env or environment.")

client: Optional[OpenAI] = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# ══════════════════════════════════════════════════════════════════════
# DATA MODELS
# ══════════════════════════════════════════════════════════════════════

class RiskLevel(str, Enum):
    LOW      = "LOW"
    MODERATE = "MODERATE"
    HIGH     = "HIGH"
    URGENT   = "URGENT"


class ChatRequest(BaseModel):
    message:    str           = Field(..., min_length=1, max_length=MAX_MSG_LEN)
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
# SESSION STORE
# ══════════════════════════════════════════════════════════════════════

SESSIONS:      Dict[str, List[Dict[str, str]]] = {}
SESSION_META:  Dict[str, Dict[str, Any]]       = {}


def get_history(sid: str) -> List[Dict[str, str]]:
    return SESSIONS.setdefault(sid, [])


def append_history(sid: str, role: str, content: str) -> None:
    h = get_history(sid)
    h.append({"role": role, "content": content})
    SESSIONS[sid] = h[-MAX_HISTORY:]


# ══════════════════════════════════════════════════════════════════════
# RISK ENGINE
# ══════════════════════════════════════════════════════════════════════

URGENT_PATTERNS: Dict[str, List[str]] = {
    "chest_pain": [
        r"ko['\u2019]?krak\s*og['\u2019]?ri",
        r"chest\s*pain", r"боль\s*в\s*груди", r"ko'krak og'ri",
    ],
    "breathing_difficulty": [
        r"nafas.*qiyin", r"nafas.*qis", r"breath.*difficult",
        r"shortness\s*of\s*breath", r"трудно\s*дышать", r"одышка",
    ],
    "fainting": [
        r"hushdan\s*ket", r"faint", r"passed\s*out",
        r"обморок", r"потерял\s*сознание", r"hushsiz",
    ],
    "severe_allergy": [
        r"lab.*shish", r"til.*shish", r"tomoq.*shish", r"yuz.*shish",
        r"swelling.*(lip|tongue|throat|face)",
        r"отек.*(губ|язык|горл|лиц)",
    ],
    "seizure": [
        r"tutqanoq", r"seizure", r"convulsion", r"судорог", r"приступ",
    ],
    "stroke_signs": [
        r"yuz.*qiyshay", r"qo['\u2019]?l.*kuchsiz", r"gapira\s*olmay",
        r"face\s*droop", r"arm\s*weakness", r"speech\s*difficult",
        r"перекос.*лиц", r"слабость.*рук", r"нарушение\s*речи",
    ],
    "severe_bleeding": [
        r"kuchli\s*qon", r"qon\s*ket", r"severe\s*bleeding",
        r"сильное\s*кровотечение", r"vomiting\s*blood",
        r"qon\s*qus", r"рвота\s*кровью",
    ],
    "suicidal": [
        r"o['\u2019]?zimni\s*o['\u2019]?ldir", r"jonimga\s*qasd",
        r"suicide", r"kill\s*myself", r"самоубий", r"убить\s*себя",
    ],
    "loss_of_consciousness": [
        r"loss\s*of\s*consciousness", r"без\s*сознания", r"hushsiz",
    ],
    "severe_rash": [
        r"kuchli\s*toshma", r"teri\s*ko['\u2019]?ch",
        r"rash.*fever", r"skin\s*peel", r"сильная\s*сыпь", r"кожа.*слез",
    ],
}

_PATTERNS = {
    "missed":       [r"unutdim", r"ichmadim", r"o['\u2019]?tkazib\s*yubordim",
                     r"qabul\s*qilmadim", r"missed", r"forgot", r"skip+ed?",
                     r"забыл", r"пропустил", r"не\s*пил", r"не\s*принимал"],
    "stop":         [r"to['\u2019]?xtatdim", r"to['\u2019]?xtatmoqchiman",
                     r"ichgim\s*kelmayapti", r"endi\s*ichmayman",
                     r"stopped?", r"stop\s*taking", r"quit",
                     r"перестал", r"бросил", r"не\s*хочу\s*принимать"],
    "side_effect":  [r"nojo['\u2019]?ya", r"ko['\u2019]?ngil\s*ayn",
                     r"bosh\s*ayl", r"bosh\s*og['\u2019]?ri", r"toshma",
                     r"nausea", r"dizzy", r"headache", r"rash",
                     r"side\s*effect", r"stomach\s*pain",
                     r"тошнит", r"головокруж", r"головная\s*боль",
                     r"сыпь", r"побоч"],
    "cost":         [r"qimmat", r"pulim\s*yetmay", r"sotib\s*ololmay",
                     r"tejay", r"yarimta\s*ich",
                     r"expensive", r"can['\u2019]?t\s*afford", r"cost",
                     r"дорого", r"не\s*могу\s*купить", r"нет\s*денег"],
    "confusion":    [r"qachon\s*ich", r"qanday\s*ich", r"oldinmi",
                     r"keyinmi", r"chalkash", r"tushunmadim",
                     r"when\s*should", r"how\s*should",
                     r"before\s*food", r"after\s*food", r"confused",
                     r"когда\s*принимать", r"как\s*принимать",
                     r"до\s*еды", r"после\s*еды", r"не\s*понимаю"],
    "swallow":      [r"yuta\s*olmay", r"yutish\s*qiyin",
                     r"tabletka\s*katta", r"kapsula\s*katta",
                     r"can['\u2019]?t\s*swallow", r"hard\s*to\s*swallow",
                     r"не\s*могу\s*глотать", r"трудно\s*глотать"],
    "critical_med": [r"insulin", r"инсулин",
                     r"tutqanoq", r"epilep", r"seizure",
                     r"судорог", r"эпилеп",
                     r"warfarin", r"варфарин",
                     r"blood\s*thin", r"anticoagul", r"qon\s*suyult",
                     r"\btb\b", r"sil\b", r"tuberculosis", r"туберкул",
                     r"\bhiv\b", r"vih\b", r"вич",
                     r"transplant", r"anti.?rejection",
                     r"nitroglycerin", r"yurak\b", r"heart\s*failure",
                     r"prednisolon", r"hydrocortison", r"steroid"],
    "double_dose":  [r"ikki\s*baravar", r"2\s*ta\s*ichdim",
                     r"double\s*dose", r"took\s*two",
                     r"двойную\s*доз"],
    "pregnancy":    [r"homilador", r"emiz",
                     r"pregnan", r"breastfeed",
                     r"беремен", r"кормлю\s*груд"],
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
    uz_words = ["men", "menga", "dori", "ichdim", "ichmadim", "qanday",
                "nima", "yaxshi", "og'riq", "bosh", "shifokor", "qimmat",
                "unutdim", "qabul", "nojo'ya", "tabletka"]
    if any(w in text.lower() for w in uz_words):
        return "uz"
    return "en"


def extract_missed_days(text: str) -> Optional[int]:
    m = re.search(r"(\d+)\s*(kun|kunda|day|days|день|дня|дней)", text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    word_map = {
        r"\b(bir|bitta|one|один|одна)\b.*(kun|day|дн)": 1,
        r"\b(ikki|two|два|две)\b.*(kun|day|дн)": 2,
        r"\b(uch|three|три)\b.*(kun|day|дн)": 3,
        r"\b(to['\u2019]?rt|four|четыре)\b.*(kun|day|дн)": 4,
        r"\b(besh|five|пять)\b.*(kun|day|дн)": 5,
    }
    for pattern, val in word_map.items():
        if re.search(pattern, text, re.IGNORECASE):
            return val
    if re.search(r"\b(kecha|yesterday|вчера)\b", text, re.IGNORECASE):
        return 1
    return None


def analyze_risk(message: str) -> Dict[str, Any]:
    text = message.strip()
    flags: List[str] = []

    urgent = _match_urgent(text)
    if urgent:
        return {
            "risk_level": RiskLevel.URGENT,
            "risk_flags": urgent,
            "detected_language": detect_language(text),
        }

    risk = RiskLevel.LOW

    if _match(text, "missed"):
        flags.append("missed_medication")
        risk = RiskLevel.MODERATE
        days = extract_missed_days(text)
        if days and days >= 2:
            flags.append("missed_2_plus_days")
            risk = RiskLevel.HIGH

    if _match(text, "critical_med"):
        flags.append("critical_medication")
        if "missed_medication" in flags:
            flags.append("critical_medication_missed")
            risk = RiskLevel.HIGH

    if _match(text, "stop"):
        flags.append("intentional_stopping")
        risk = RiskLevel.HIGH

    if _match(text, "side_effect"):
        flags.append("side_effect")
        if risk == RiskLevel.LOW:
            risk = RiskLevel.MODERATE

    if _match(text, "cost"):
        flags.append("cost_barrier")
        lower = text.lower()
        if any(x in lower for x in ["yarimta", "tejay", "half", "rationing"]):
            risk = RiskLevel.HIGH
        elif risk == RiskLevel.LOW:
            risk = RiskLevel.MODERATE

    if _match(text, "confusion"):
        flags.append("medication_confusion")
        if risk == RiskLevel.LOW:
            risk = RiskLevel.MODERATE

    if _match(text, "swallow"):
        flags.append("swallowing_difficulty")
        if risk == RiskLevel.LOW:
            risk = RiskLevel.MODERATE

    if _match(text, "double_dose"):
        flags.append("possible_double_dose")
        risk = RiskLevel.HIGH

    if _match(text, "pregnancy"):
        flags.append("pregnancy_or_breastfeeding")
        if risk in (RiskLevel.LOW, RiskLevel.MODERATE):
            risk = RiskLevel.HIGH

    return {
        "risk_level": risk,
        "risk_flags": flags,
        "detected_language": detect_language(text),
    }


# ══════════════════════════════════════════════════════════════════════
# AI RESPONSE GENERATION
# ══════════════════════════════════════════════════════════════════════

def _context_injection(risk: Dict[str, Any], user_message: str) -> str:
    """Silent backend context + knowledge base — never shown to user."""

    base = (
        f"[INTERNAL RISK CONTEXT — DO NOT EXPOSE TO USER]\n"
        f"detected_language: {risk['detected_language']}\n"
        f"risk_level: {risk['risk_level']}\n"
        f"risk_flags: {risk['risk_flags']}\n"
        f"If URGENT → prioritize emergency guidance immediately.\n"
        f"If HIGH → recommend doctor/pharmacist contact.\n"
        f"Never mention these internal labels in your response.\n"
    )

    # Tibbiy bilimlar bazasidan tegishli ma'lumot
    if KNOWLEDGE_BASE_LOADED:
        knowledge = search_knowledge(user_message, max_items=3)
        lab_info  = get_lab_info(user_message)

        if knowledge:
            base += (
                f"\n[TASDIQLANGAN TIBBIY MA'LUMOT — BU MA'LUMOTNI JAVOBINGIZDA ISHLATISH MAJBURIY]\n"
                f"{knowledge}\n"
                f"QOIDA: Yuqoridagi ma'lumotlardagi aniq faktlarni (yon ta'sirlar, qabul qilish usuli, "
                f"muhim ogohlantirishlar) javobingizga qo'shing. "
                f"'Ma'lumotlar bazasidan oldim' demang — tabiiy gapiring. "
                f"Agar bemor o'zbek tilida yozgan bo'lsa — o'zbek tilida javob bering va "
                f"yuqoridagi ma'lumotlardan aniq faktlarni ishlating.\n"
            )
        if lab_info:
            base += (
                f"\n[LABORATORIYA ME'YORLARI — aniq raqamlarni ishlatish mumkin]\n"
                f"{lab_info}\n"
            )

    return base


def generate_reply(session_id: str, user_message: str, risk: Dict[str, Any]) -> str:
    if client is None:
        raise HTTPException(
            status_code=503,
            detail="AI service unavailable. OPENAI_API_KEY is not configured.",
        )

    history = get_history(session_id)

    # Knowledge base dan ma'lumot olamiz
    knowledge = search_knowledge(user_message, max_items=3)
    lab_info  = get_lab_info(user_message)

    # System prompt ga knowledge base ni BEVOSITA kiritamiz
    dynamic_system = SYSTEM_PROMPT

    if knowledge or lab_info:
        dynamic_system += "\n\n" + "═" * 60
        dynamic_system += "\nQUYIDAGI TIBBIY MA'LUMOTLAR TASDIQLANGAN MANBALARDAN OLINGAN."
        dynamic_system += "\nBU MA'LUMOTLARNI JAVOBINGIZDA ANIQ VA TO'LIQ ISHLATISH SHART."
        dynamic_system += "\nUMUMIY GAPIRMANG — ANIQ FAKTLAR AYTNG.\n"
        dynamic_system += "═" * 60 + "\n"

        if knowledge:
            dynamic_system += knowledge + "\n"
        if lab_info:
            dynamic_system += lab_info + "\n"

        dynamic_system += "═" * 60
        dynamic_system += "\nYuqoridagi ma'lumotlardagi BARCHA aniq faktlarni (doza qoidasi, "
        dynamic_system += "yon ta'sirlar, muhim ogohlantirishlar, raqamlar) javobingizga qo'shing."
        dynamic_system += "\nFoydalanuvchi tilida (o'zbek/rus/ingliz) javob bering."

    # Risk kontekst
    risk_context = (
        f"\n[ICHKI TAHLIL — FOYDALANUVCHIGA KO'RSATMANG]\n"
        f"risk_level: {risk['risk_level']}\n"
        f"risk_flags: {risk['risk_flags']}\n"
        f"language: {risk['detected_language']}\n"
        f"URGENT bo'lsa — darhol 103 ga yo'naltir.\n"
        f"HIGH bo'lsa — shifokor/farmatsevtga murojaat tavsiya qil."
    )

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": dynamic_system + risk_context},
        *history,
        {"role": "user", "content": user_message},
    ]

    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.4,
            max_tokens=750,
            frequency_penalty=0.25,
            presence_penalty=0.15,
        )
    except Exception as exc:
        log.error(f"OpenAI error: {exc}")
        raise HTTPException(status_code=502, detail=f"AI provider error: {exc}")

    reply = completion.choices[0].message.content.strip()
    tokens = getattr(completion.usage, "total_tokens", 0)
    log.info(f"[{session_id[:8]}] risk={risk['risk_level']} tokens={tokens}")

    append_history(session_id, "user",      user_message)
    append_history(session_id, "assistant", reply)

    return reply


# ══════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ══════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Tabib AI — Medication Adherence Expert",
    description="Clinical-grade AI chatbot for medication adherence support",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════════════
# API ROUTES
# ══════════════════════════════════════════════════════════════════════

@app.get("/health")
def health():
    return {
        "status":               "ok",
        "service":              "Tabib AI",
        "model":                OPENAI_MODEL,
        "active_sessions":      len(SESSIONS),
        "prompt_chars":         len(SYSTEM_PROMPT),
        "timestamp":            datetime.utcnow().isoformat(),
    }


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    message    = payload.message.strip()
    session_id = payload.session_id or str(uuid.uuid4())

    risk  = analyze_risk(message)
    reply = generate_reply(session_id, message, risk)

    SESSION_META.setdefault(session_id, {})
    SESSION_META[session_id].update({
        "patient_id":      payload.patient_id,
        "last_risk_level": risk["risk_level"],
        "last_risk_flags": risk["risk_flags"],
        "last_seen":       datetime.utcnow().isoformat(),
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
    return {
        "session_id": session_id,
        "meta":       SESSION_META.get(session_id, {}),
        "messages":   SESSIONS.get(session_id, []),
    }


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    SESSIONS.pop(session_id, None)
    SESSION_META.pop(session_id, None)
    return {"status": "deleted", "session_id": session_id}


# ══════════════════════════════════════════════════════════════════════
# FRONTEND
# ══════════════════════════════════════════════════════════════════════

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
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f0f7ff;color:#0f172a}
.page{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px}
.hero{max-width:740px;background:#fff;border-radius:24px;padding:44px;box-shadow:0 20px 60px rgba(15,23,42,.11)}
.badge{display:inline-block;background:#ccfbf1;color:#115e59;padding:7px 13px;border-radius:999px;font-weight:700;font-size:13px;margin-bottom:18px}
h1{font-size:42px;letter-spacing:-1.5px;line-height:1.06;margin-bottom:16px}
p{color:#475569;font-size:17px;line-height:1.7}
.launcher{position:fixed;right:22px;bottom:22px;width:64px;height:64px;border:none;border-radius:22px;background:linear-gradient(135deg,#0f766e,#14b8a6);color:#fff;font-size:28px;cursor:pointer;box-shadow:0 16px 44px rgba(15,118,110,.38);z-index:10;transition:transform .15s}
.launcher:hover{transform:scale(1.07)}
.chat{position:fixed;right:22px;bottom:100px;width:390px;height:620px;max-width:calc(100vw - 28px);max-height:calc(100vh - 120px);background:#fff;border-radius:24px;box-shadow:0 20px 60px rgba(15,23,42,.2);overflow:hidden;display:none;flex-direction:column;z-index:9}
.chat.open{display:flex}
.chat-header{padding:18px;background:linear-gradient(135deg,#0f766e,#14b8a6);color:#fff;display:flex;justify-content:space-between;align-items:center}
.chat-title{font-weight:800;font-size:18px}
.chat-sub{opacity:.88;font-size:12px;margin-top:2px}
.status-dot{display:inline-block;width:8px;height:8px;background:#4ade80;border-radius:50%;margin-right:5px;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.close-btn{border:none;width:34px;height:34px;border-radius:12px;color:#fff;background:rgba(255,255,255,.18);font-size:18px;cursor:pointer}
.risk-bar{display:none;padding:8px 14px;font-size:12px;font-weight:700;border-bottom:1px solid #e2e8f0}
.risk-bar.LOW{display:block;background:#ecfdf5;color:#047857}
.risk-bar.MODERATE{display:block;background:#fffbeb;color:#b45309}
.risk-bar.HIGH{display:block;background:#fff7ed;color:#c2410c}
.risk-bar.URGENT{display:block;background:#fef2f2;color:#b91c1c}
.messages{flex:1;overflow-y:auto;padding:14px;background:#f8fafc;display:flex;flex-direction:column;gap:10px}
.messages::-webkit-scrollbar{width:5px}
.messages::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:3px}
.msg{display:flex}
.msg.user{justify-content:flex-end}
.bubble{max-width:83%;padding:11px 14px;border-radius:18px;font-size:14px;line-height:1.58;white-space:pre-wrap;word-wrap:break-word;animation:fadein .25s ease}
@keyframes fadein{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.bot .bubble{background:#fff;border:1px solid #e2e8f0;border-bottom-left-radius:5px}
.user .bubble{background:#0f766e;color:#fff;border-bottom-right-radius:5px}
.typing-row{display:flex}
.typing-dots{background:#fff;border:1px solid #e2e8f0;border-radius:18px;border-bottom-left-radius:5px;padding:12px 16px;display:flex;gap:4px}
.typing-dots span{width:7px;height:7px;background:#94a3b8;border-radius:50%;animation:bounce 1.3s infinite}
.typing-dots span:nth-child(2){animation-delay:.2s}
.typing-dots span:nth-child(3){animation-delay:.4s}
@keyframes bounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-8px)}}
.quick{display:flex;gap:7px;overflow-x:auto;padding:9px 12px;border-top:1px solid #e2e8f0}
.quick::-webkit-scrollbar{display:none}
.quick button{white-space:nowrap;border:1px solid #d1fae5;background:#f0fdf4;color:#065f46;padding:7px 11px;border-radius:999px;cursor:pointer;font-size:12px;font-family:inherit;transition:background .15s}
.quick button:hover{background:#d1fae5}
.form{display:flex;gap:9px;padding:11px 12px 14px;border-top:1px solid #e2e8f0}
textarea{flex:1;resize:none;border:1.5px solid #e2e8f0;border-radius:16px;padding:11px 14px;min-height:44px;max-height:110px;outline:none;font-family:inherit;font-size:14px;transition:border-color .2s}
textarea:focus{border-color:#0f766e}
.send{width:46px;height:46px;border:none;border-radius:15px;background:#0f766e;color:#fff;font-size:20px;cursor:pointer;transition:transform .15s}
.send:hover{transform:scale(1.06)}
.send:disabled{opacity:.5;cursor:not-allowed}
@media(max-width:600px){h1{font-size:32px}.hero{padding:28px}.chat{right:10px;bottom:88px;width:calc(100vw - 20px);height:calc(100vh - 112px)}.launcher{right:14px;bottom:14px}}
</style>
</head>
<body>
<main class="page">
  <section class="hero">
    <div class="badge">🩺 Tabib AI</div>
    <h1>Davolashni davom ettirish uchun aqlli yordamchi</h1>
    <p>Tabib AI bemorlarga dorilarni unutmaslik, nojo'ya ta'sirlarni tushunish, xavfli belgilarni erta aniqlash va shifokor bilan o'z vaqtida bog'lanishda yordam beradi. 24/7 onlayn.</p>
  </section>
</main>

<button class="launcher" id="launcher">💬</button>

<section class="chat" id="chat">
  <div class="chat-header">
    <div>
      <div class="chat-title">Tabib AI</div>
      <div class="chat-sub"><span class="status-dot"></span>Onlayn · 24/7</div>
    </div>
    <button class="close-btn" id="closeBtn">×</button>
  </div>
  <div class="risk-bar" id="riskBar"></div>
  <div class="messages" id="messages">
    <div class="msg bot">
      <div class="bubble">Assalomu alaykum. Men Tabib AI — sizning davolanish jarayonida hamrohingizman.\n\nDori qabul qilish, eslatmalar, nojo'ya ta'sirlar yoki davolashni davom ettirish haqida bemalol so'rang. Bugun sizga qanday yordam kerak?</div>
    </div>
  </div>
  <div class="quick">
    <button data-q="Dorimni unutib qo'ydim">Dori unutdim</button>
    <button data-q="Doridan keyin boshim aylanmoqda">Nojo'ya ta'sir</button>
    <button data-q="Dorimni ichishni to'xtatmoqchiman">To'xtatmoqchiman</button>
    <button data-q="Dori juda qimmat, sotib ololmayapman">Dori qimmat</button>
    <button data-q="Tabletkani yutish qiyin">Yutish qiyin</button>
  </div>
  <form class="form" id="chatForm">
    <textarea id="msgInput" rows="1" placeholder="Xabaringizni yozing..."></textarea>
    <button class="send" type="submit" id="sendBtn">➤</button>
  </form>
</section>

<script>
const launcher  = document.getElementById("launcher");
const chat      = document.getElementById("chat");
const closeBtn  = document.getElementById("closeBtn");
const chatForm  = document.getElementById("chatForm");
const msgInput  = document.getElementById("msgInput");
const messages  = document.getElementById("messages");
const riskBar   = document.getElementById("riskBar");
const sendBtn   = document.getElementById("sendBtn");

let sessionId = localStorage.getItem("tabib_sid") || null;

launcher.onclick = () => { chat.classList.toggle("open"); if (chat.classList.contains("open")) msgInput.focus(); };
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
  if (t) t.remove();
}

function setRisk(level, flags) {
  riskBar.className = "risk-bar " + level;
  riskBar.textContent = "⚠ " + level + (flags.length ? " · " + flags.join(", ") : "");
}

function autoResize() {
  msgInput.style.height = "auto";
  msgInput.style.height = Math.min(msgInput.scrollHeight, 110) + "px";
}

msgInput.addEventListener("input", autoResize);
msgInput.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); chatForm.requestSubmit(); }
});

chatForm.onsubmit = async (e) => {
  e.preventDefault();
  const text = msgInput.value.trim();
  if (!text) return;
  addMsg(text, "user");
  msgInput.value = "";
  autoResize();
  sendBtn.disabled = true;
  showTyping();
  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: sessionId })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Server error");
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
};
</script>
</body>
</html>
"""


# ══════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    print("\n" + "═" * 62)
    print("  🏥  TABIB AI — Medication Adherence Expert")
    print("═" * 62)
    print(f"  📍  http://localhost:8000")
    print(f"  📖  http://localhost:8000/docs")
    print(f"  🤖  Model: {OPENAI_MODEL}")
    print("═" * 62 + "\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
