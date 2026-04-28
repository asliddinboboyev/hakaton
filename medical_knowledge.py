"""
TABIB AI — TIBBIY BILIMLAR BAZASI
Manbalar: WHO, MedlinePlus, UpToDate klinik ko'rsatmalar,
O'zbekiston SSV protokollari asosida tuzilgan.

Bu fayl main.py ga import qilinadi va har bir so'rovda
tegishli ma'lumot AI ga kontekst sifatida beriladi.
"""

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
