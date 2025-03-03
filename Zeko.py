import logging
import re
import json
import threading
import random
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# ------ إعدادات التسجيل ------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ------ ملفات البيانات ------
DATA_FILE = "users_data.json"
AMONG_US_DATA_FILE = "among_us_games.json"

users_data = {}
among_us_games = {}

# ------ بيانات الحزازير (50 حزورة كاملة) ------
RIDDLES = [
    ("ما الشيء الذي يكتب ولا يقرأ؟", "القلم"),
    ("ما الشيء الذي له أسنان ولا يعض؟", "المشط"),
    ("ما الشيء الذي يكسو الناس وهو عار؟", "الإبرة"),
    ("ما الشيء الذي يخترق الزجاج ولا يكسره؟", "الضوء"),
    ("ما الشيء الذي كلما أخذت منه كبر؟", "الحفرة"),
    ("ما الشيء الذي ينام ولا يقوم؟", "الرماد"),
    ("ما الشيء الذي يحملك وتحمله؟", "الحذاء"),
    ("ما الشيء الذي يسمع بلا أذن ويتكلم بلا لسان؟", "الهاتف"),
    ("ما الشيء الذي يتبخر قبل أن يُطبخ؟", "الثلج"),
    ("ما الشيء الذي لا يُؤكل إلا إذا قُلب؟", "العجة"),
    ("ما الشيء الذي ليس له وزن ولا يمكن لمسه؟", "الظل"),
    ("ما الشيء الذي يزيد إذا قُسِم؟", "الحب"),
    ("ما الشيء الذي يشم بلا أنف؟", "الزهرة"),
    ("ما الشيء الذي يدخل الماء ولا يبتل؟", "الظل"),
    ("ما الشيء الذي له رقبة بلا رأس؟", "الزجاجة"),
    ("ما الشيء الذي يتسع لمئات الألوف ولا يتسع لطير واحد؟", "شبكة الصياد"),
    ("ما الشيء الذي يمشي بلا أرجل؟", "السحاب"),
    ("ما الشيء الذي تراه في الليل ثلاث مرات وفي النهار مرة؟", "حرف اللام"),
    ("ما الشيء الذي ينبض بلا قلب؟", "الساعة"),
    ("ما الشيء الذي يأكل ولا يشبع؟", "النار"),
    ("ما الشيء الذي يدور حول نفسه دائمًا؟", "عقرب الساعة"),
    ("ما الشيء الذي يقرصك دون أن تراه؟", "الجوع"),
    ("ما الشيء الذي كلما مشى فقد شيئًا منه؟", "الحذاء"),
    ("ما الشيء الذي يرفع الأثقال ولا يقدر على رفع مسمار؟", "البحر"),
    ("ما الشيء الذي يلبس قبعة لكن بلا رأس؟", "القلم"),
    ("ما الشيء الذي له وجه بلا لسان ويدل الناس على الزمان؟", "الساعة"),
    ("ما الشيء الذي يتكلم كل لغات العالم؟", "الصدى"),
    ("ما الشيء الذي ليس له بداية ولا نهاية؟", "الدائرة"),
    ("ما الشيء الذي لا يمشي إلا بالضرب؟", "المسمار"),
    ("ما الشيء الذي تأكل منه ولا يُؤكل؟", "الطبق"),
    ("ما الشيء الذي يخفي نفسه إذا جاع ويظهر إذا شبع؟", "النار"),
    ("ما الشيء الذي يتحرك حولك دائمًا ولكنك لا تراه؟", "الهواء"),
    ("ما الشيء الذي له أوراق لكنه ليس شجرة؟", "الكتاب"),
    ("ما الشيء الذي إذا أكلت نصفه تموت؟", "السمسم"),
    ("ما الشيء الذي كلما طال قصر؟", "العمر"),
    ("ما الشيء الذي لا يُؤكل في الليل أبدًا؟", "الفطور"),
    ("ما الشيء الذي يولد كل شهر؟", "القمر"),
    ("ما الشيء الذي كلما زاد نقص؟", "العمر"),
    ("ما الشيء الذي يسير بلا رجلين؟", "الوقت"),
    ("ما الشيء الذي يموت إذا أخذت اسمه؟", "الصمت"),
    ("ما الشيء الذي يذهب ولا يرجع؟", "الدخان"),
    ("ما الشيء الذي يخترق الحواجز؟", "الصوت"),
    ("ما الشيء الذي يظهر مرة في العام ومرة في الشهر ومرة في الأسبولم يظهر في اليوم؟", "حرف الألف"),
    ("ما الشيء الذي يحمل طعامه فوق رأسه؟", "القلم"),
    ("ما الشيء الذي يخترق الزجاج؟", "الضوء"),
    ("ما الشيء الذي كلما أسرعت خلفه ابتعد عنك؟", "الأفق"),
    ("ما الشيء الذي يلف حول نفسه؟", "الثعبان"),
    ("ما الشيء الذي ينام مرتين في اليوم؟", "القدم"),
    ("ما الشيء الذي يطلبه الناس ثم يهربون منه إذا جاء؟", "المطر"),
    ("ما الشيء الذي يتبعك أينما ذهبت؟", "ظلك"),
    ("ما الشيء الذي لا يبتل ولو دخل الماء؟", "الضوء")
]

# ------ بيانات الأسماء (28 حرف × 30 اسم) ------
NAMES_GAME = {
    "ا": ["أحمد","أمل","أنس","أميرة","إياد","إيمان","أسامة","أمجد","أشرف","أريج","أكرم","أدب","أحسان","أنور","أمينة","أسماء","أروى","أيمن","أبو بكر","إسلام","إسراء","إيهاب","إخلاص","إيناس","أميمة","أصيل","إيثار","أشجان","أمير","أكمل"],
    "ب": ["بسام","بدر","بلال","بشرى","بهاء","باسل","بلقيس","بسنت","بندر","بتول","بسمة","بشير","بكر","براء","بسيمة","بشر","بنيان","بثينة","بشار","بسكال","بدرية","بشرى","باسم","بتول","بشير","بكر","بلال","بثينة","بسنت","بندر"],
    "ت": ["تامر","تميم","تغريد","تهاني","تقي","تاليا","تحرير","تماضر","توجان","توفيق","تيسير","تولين","تقي الدين","تمارا","تغريد","تهاني","تامر","تميم","تغريد","تهاني","تقي","تاليا","تحرير","تماضر","توجان","توفيق","تيسير","تولين","تمارا","تغريد"],
    "ث": ["ثامر","ثناء","ثروت","ثريا","ثابت","ثمود","ثريا","ثناء","ثامر","ثروت","ثريا","ثابت","ثمود","ثريا","ثناء","ثامر","ثروت","ثريا","ثابت","ثمود","ثريا","ثناء","ثامر","ثروت","ثريا","ثابت","ثمود","ثريا","ثناء","ثامر"],
    "ج": ["جمال","جميلة","جواد","جيهان","جلال","جنان","جابر","جهاد","جليلة","جوهرة","جمال","جميلة","جواد","جيهان","جلال","جنان","جابر","جهاد","جليلة","جوهرة","جمال","جميلة","جواد","جيهان","جلال","جنان","جابر","جهاد","جليلة","جوهرة"],
    "ح": ["حسين","حنان","حسام","حياة","حسن","حليمة","حذيفة","حورية","حمد","حازم","حسين","حنان","حسام","حياة","حسن","حليمة","حذيفة","حورية","حمد","حازم","حسين","حنان","حسام","حياة","حسن","حليمة","حذيفة","حورية","حمد","حازم"],
    "خ": ["خالد","خديجة","خليل","خلود","خطاب","خنساء","خصيب","خضراء","خليل","خلود","خالد","خديجة","خليل","خلود","خطاب","خنساء","خصيب","خضراء","خليل","خلود","خالد","خديجة","خليل","خلود","خطاب","خنساء","خصيب","خضراء","خليل","خلود"],
    "د": ["داليا","دانيال","دريد","ديمة","داني","دلال","داليا","دانيال","دريد","ديمة","داني","دلال","داليا","دانيال","دريد","ديمة","داني","دلال","داليا","دانيال","دريد","ديمة","داني","دلال","داليا","دانيال","دريد","ديمة","داني","دلال"],
    "ذ": ["ذكي","ذكاء","ذكرى","ذو الفقار","ذريعة","ذكي","ذكاء","ذكرى","ذو الفقار","ذريعة","ذكي","ذكاء","ذكرى","ذو الفقار","ذريعة","ذكي","ذكاء","ذكرى","ذو الفقار","ذريعة","ذكي","ذكاء","ذكرى","ذو الفقار","ذريعة","ذكي","ذكاء","ذكرى","ذو الفقار","ذريعة"],
    "ر": ["ريم","رامي","رغد","رانية","رائد","رباب","رياض","راشد","رنا","رامي","ريم","رامي","رغد","رانية","رائد","رباب","رياض","راشد","رنا","رامي","ريم","رامي","رغد","رانية","رائد","رباب","رياض","راشد","رنا","رامي"],
    "ز": ["زينب","زيد","زكي","زهرة","زكريا","زين","زكية","زاهر","زينة","زينب","زيد","زكي","زهرة","زكريا","زين","زكية","زاهر","زينة","زينب","زيد","زكي","زهرة","زكريا","زين","زكية","زاهر","زينة","زينب","زيد","زكي"],
    "س": ["سارة","سعيد","سلمان","سحر","سعد","سمر","سليمان","سهام","سالم","سجى","سارة","سعيد","سلمان","سحر","سعد","سمر","سليمان","سهام","سالم","سجى","سارة","سعيد","سلمان","سحر","سعد","سمر","سليمان","سهام","سالم","سجى"],
    "ش": ["شهد","شريف","شمس","شادي","شروق","شهاب","شذى","شوق","شيماء","شفيق","شهد","شريف","شمس","شادي","شروق","شهاب","شذى","شوق","شيماء","شفيق","شهد","شريف","شمس","شادي","شروق","شهاب","شذى","شوق","شيماء","شفيق"],
    "ص": ["صالح","صفاء","صدام","صهيب","صباح","صابر","صقر","صديق","صفية","صالح","صفاء","صدام","صهيب","صباح","صابر","صقر","صديق","صفية","صالح","صفاء","صدام","صهيب","صباح","صابر","صقر","صديق","صفية","صالح","صفاء","صدام"],
    "ض": ["ضياء","ضحى","ضرار","ضيف","ضاحي","ضاري","ضوى","ضباب","ضيف الله","ضرار","ضياء","ضحى","ضرار","ضيف","ضاحي","ضاري","ضوى","ضباب","ضيف الله","ضرار","ضياء","ضحى","ضرار","ضيف","ضاحي","ضاري","ضوى","ضباب","ضيف الله","ضرار"],
    "ط": ["طارق","طاهرة","طلال","طيبة","طيف","طالب","طلعت","طروب","طاهر","طيف","طارق","طاهرة","طلال","طيبة","طيف","طالب","طلعت","طروب","طاهر","طيف","طارق","طاهرة","طلال","طيبة","طيف","طالب","طلعت","طروب","طاهر","طيف"],
    "ظ": ["ظافر","ظبية","ظلال","ظريف","ظاهر","ظلال","ظافر","ظبية","ظلال","ظريف","ظاهر","ظلال","ظافر","ظبية","ظلال","ظريف","ظاهر","ظلال","ظافر","ظبية","ظلال","ظريف","ظاهر","ظلال","ظافر","ظبية","ظلال","ظريف","ظاهر","ظلال"],
    "ع": ["علي","عائشة","عمر","عبير","عبد الله","عصام","عزيز","علاء","عفراء","عبد الرحمن","علي","عائشة","عمر","عبير","عبد الله","عصام","عزيز","علاء","عفراء","عبد الرحمن","علي","عائشة","عمر","عبير","عبد الله","عصام","عزيز","علاء","عفراء","عبد الرحمن"],
    "غ": ["غادة","غسان","غزل","غيداء","غريب","غالية","غسان","غادة","غزل","غيداء","غريب","غالية","غسان","غادة","غزل","غيداء","غريب","غالية","غسان","غادة","غزل","غيداء","غريب","غالية","غسان","غادة","غزل","غيداء","غريب","غالية"],
    "ف": ["فاطمة","فارس","فهد","فدوى","فريد","فوزية","فواز","فضيلة","فريال","فاروق","فاطمة","فارس","فهد","فدوى","فريد","فوزية","فواز","فضيلة","فريال","فاروق","فاطمة","فارس","فهد","فدوى","فريد","فوزية","فواز","فضيلة","فريال","فاروق"],
    "ق": ["قيس","قمر","قدري","قاسم","قتيبة","قمر","قيس","قدري","قاسم","قتيبة","قمر","قيس","قدري","قاسم","قتيبة","قمر","قيس","قدري","قاسم","قتيبة","قمر","قيس","قدري","قاسم","قتيبة","قمر","قيس","قدري","قاسم","قتيبة"],
    "ك": ["كريم","كاملة","كاظم","كرم","كلثوم","كامل","كندا","كرم","كريمة","كاظم","كريم","كاملة","كاظم","كرم","كلثوم","كامل","كندا","كرم","كريمة","كاظم","كريم","كاملة","كاظم","كرم","كلثوم","كامل","كندا","كرم","كريمة","كاظم"],
    "ل": ["ليلى","لؤي","لمى","لين","لطيفة","لبيب","لمياء","ليندا","لؤي","ليلى","ليلى","لؤي","لمى","لين","لطيفة","لبيب","لمياء","ليندا","لؤي","ليلى","ليلى","لؤي","لمى","لين","لطيفة","لبيب","لمياء","ليندا","لؤي","ليلى"],
    "م": ["محمد","مريم","مصطفى","منى","ماجد","مها","مازن","مريم","محمد","مصطفى","منى","ماجد","مها","مازن","مريم","محمد","مصطفى","منى","ماجد","مها","مازن","مريم","محمد","مصطفى","منى","ماجد","مها","مازن","مريم","محمد"],
    "ن": ["نور","ناصر","ناهد","ندى","نضال","نوال","نادر","ناهدة","نجوى","نور","نور","ناصر","ناهد","ندى","نضال","نوال","نادر","ناهدة","نجوى","نور","نور","ناصر","ناهد","ندى","نضال","نوال","نادر","ناهدة","نجوى","نور"],
    "ه": ["هاني","هند","هدى","هبة","هشام","هناء","هيثم","هاجر","هاني","هند","هاني","هند","هدى","هبة","هشام","هناء","هيثم","هاجر","هاني","هند","هاني","هند","هدى","هبة","هشام","هناء","هيثم","هاجر","هاني","هند"],
    "و": ["وسام","ولاء","وليد","وجدان","وسن","وفاء","وسيم","وجيه","وسام","ولاء","وسام","ولاء","وليد","وجدان","وسن","وفاء","وسيم","وجيه","وسام","ولاء","وسام","ولاء","وليد","وجدان","وسن","وفاء","وسيم","وجيه","وسام","ولاء"],
    "ي": ["ياسر","ياسمين","يوسف","يمنى","يحيى","يسرى","يوسف","ياسمين","ياسر","يمنى","ياسر","ياسمين","يوسف","يمنى","يحيى","يسرى","يوسف","ياسمين","ياسر","يمنى","ياسر","ياسمين","يوسف","يمنى","يحيى","يسرى","يوسف","ياسمين","ياسر","يمنى"]
}

# ------ بيانات الأبنية ------
BUILDINGS_DATA = {
    "متجر صغير": {"price": 1000, "prerequisite": None},
    "اسواق": {"price": 5000, "prerequisite": {"building": "متجر صغير", "quantity": 5}},
    "محل ملابس": {"price": 10000, "prerequisite": {"building": "اسواق", "quantity": 3}},
    "محل مجوهرات": {"price": 25000, "prerequisite": {"building": "محل ملابس", "quantity": 5}},
    "وكالة": {"price": 100000, "prerequisite": {"building": "محل مجوهرات", "quantity": 5}},
    "فندق": {"price": 250000, "prerequisite": {"building": "وكالة", "quantity": 5}},
    "مجمع سكني": {"price": 1000000, "prerequisite": {"building": "فندق", "quantity": 5}},
    "شركة عالمية": {"price": 100000000, "prerequisite": {"building": "مجمع سكني", "quantity": 10}}
}

# ------ بيانات امونج اس ------
COLORS = ["احمر", "اسود", "اخضر", "بنفسجي", "ازرق", "ابيض", "وردي", "بني", "برتقالي", "رصاصي"]
TASKS = [
    {"type": "timer", "steps": ["تحميل", "تثبيت"], "durations": [15, 10], "reward": 100, "description": "أكمل المهمة في الوقت المحدد"},
    {"type": "sticker", "required": "�", "response": "🔋", "reward": 150, "description": "أرسل الملصق المطلوب"},
    {"type": "math", "problem": "5 + 3*2", "answer": "11", "reward": 200, "description": "حل المسألة الحسابية"},
    {"type": "reverse", "word": "مثال", "answer": "لاثم", "reward": 120, "description": "اكتب الكلمة بالعكس"},
    {"type": "captcha", "code": "AB12C", "reward": 180, "description": "أدخل الرمز الصحيح"},
    {"type": "memory", "sequence": [1,3,2], "reward": 160, "description": "تذكر التسلسل"}
]
KILLER_ABILITIES = {
    "قتل": {"cooldown": 60},
    "تخدير": {"duration": 180, "cooldown": 120},
    "اطفاء": {"duration": 180, "cooldown": 180},
    "تعطيل": {"duration": 180, "cooldown": 180}
}

# ------ دوال النظام ------
def load_data():
    global users_data, among_us_games
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            users_data = json.load(f)
    except FileNotFoundError:
        users_data = {}
    try:
        with open(AMONG_US_DATA_FILE, "r", encoding="utf-8") as f:
            among_us_games = json.load(f)
    except FileNotFoundError:
        among_us_games = {}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users_data, f, ensure_ascii=False, indent=4)
    with open(AMONG_US_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(among_us_games, f, ensure_ascii=False, indent=4)

def auto_save():
    save_data()
    threading.Timer(60, auto_save).start()

def get_user(user_id):
    uid = str(user_id)
    if uid not in users_data:
        users_data[uid] = {
            "money": 1000,
            "buildings": {},
            "last_purchase": None,
            "last_profit": None,
            "riddle_active": False,
            "riddle_answer": None,
            "riddle_start_time": None,
            "names_active": False,
            "names_letter": None,
            "names_valid": None,
            "names_start_time": None,
            "profit_count": 0
        }
    return users_data[uid]

def get_game(chat_id):
    return among_us_games.get(str(chat_id))

def create_game(chat_id):
    among_us_games[str(chat_id)] = {
        "players": {},
        "state": "registration",
        "start_time": datetime.now().isoformat(),
        "tasks": {},
        "killer": None,
        "current_votes": {},
        "dead_players": [],
        "bodies": [],
        "cooldowns": {},
        "meeting": False,
        "lights": True,
        "tasks_disabled": False,
        "round": 1,
        "meeting_cooldown": None
    }
    return among_us_games[str(chat_id)]

def format_time(seconds):
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins:02d}:{secs:02d}"

# ------ دوال البناء ------
async def my_account(update: Update, user: dict):
    buildings = "\n".join([f"{k}: {v}" for k, v in user["buildings"].items() if v > 0])
    await update.message.reply_text(f"💰 الرصيد: {user['money']} 💸\n🏗 الأبنية:\n{buildings or 'لا أبنية'}")

async def shop(update: Update):
    shop_list = "\n".join([f"{i+1}. {name} - السعر: {data['price']}💸" for i, (name, data) in enumerate(BUILDINGS_DATA.items())])
    await update.message.reply_text(f"🏪 المتجر:\n{shop_list}")

async def purchase(update: Update, user: dict):
    text = update.message.text.strip()
    match = re.match(r"شراء (.+) (\d+)", text)

    if not match:
        await update.message.reply_text("❌ استخدم: شراء <اسم البناء> <العدد>")
        return

    building_name = match.group(1)
    quantity = int(match.group(2))

    if building_name not in BUILDINGS_DATA:
        await update.message.reply_text("❌ هذا البناء غير موجود!")
        return

    building = BUILDINGS_DATA[building_name]
    total_cost = building["price"] * quantity

    if user["money"] < total_cost:
        await update.message.reply_text("❌ رصيدك غير كافي!")
        return

    if building["prerequisite"]:
        req_building = building["prerequisite"]["building"]
        req_quantity = building["prerequisite"]["quantity"]
        if user["buildings"].get(req_building, 0) < req_quantity:
            await update.message.reply_text(f"❌ تحتاج {req_quantity} من {req_building}!")
            return

    user["money"] -= total_cost
    user["buildings"][building_name] = user["buildings"].get(building_name, 0) + quantity
    user["last_purchase"] = datetime.now().isoformat()
    save_data()
    await update.message.reply_text(f"✅ تم الشراء! الرصيد المتبقي: {user['money']}💸")

async def sell(update: Update, user: dict):
    text = update.message.text.strip()
    match = re.match(r"بيع (.+) (\d+)", text)

    if not match:
        await update.message.reply_text("❌ استخدم: بيع <اسم البناء> <العدد>")
        return

    building_name = match.group(1)
    quantity = int(match.group(2))

    if building_name not in BUILDINGS_DATA:
        await update.message.reply_text("❌ هذا البناء غير موجود!")
        return

    if user["buildings"].get(building_name, 0) < quantity:
        await update.message.reply_text("❌ لا تملك هذا العدد!")
        return

    refund = int(BUILDINGS_DATA[building_name]["price"] * 0.5 * quantity)
    user["money"] += refund
    user["buildings"][building_name] -= quantity

    if user["buildings"][building_name] == 0:
        del user["buildings"][building_name]

    save_data()
    await update.message.reply_text(f"✅ تم البيع! الرصيد الحالي: {user['money']}💸")

async def collect_profit(update: Update, user: dict):
    now = datetime.now()
    cooldown_map = {
        "متجر صغير": 15 * 60,
        "اسواق": 20 * 60,
        "محل ملابس": 25 * 60,
        "محل مجوهرات": 30 * 60,
        "وكالة": 35 * 60,
        "فندق": 40 * 60,
        "مجمع سكني": 45 * 60,
        "شركة عالمية": 50 * 60
    }

    # تحديد أعلى مبنى
    max_cooldown = 0
    for building in reversed(cooldown_map.keys()):
        if user["buildings"].get(building, 0) > 0:
            max_cooldown = cooldown_map[building]
            break

    if user["last_profit"]:
        last_profit_time = datetime.fromisoformat(user["last_profit"])
        if (now - last_profit_time).total_seconds() < max_cooldown:
            remaining = max_cooldown - (now - last_profit_time).total_seconds()
            await update.message.reply_text(f"⏳ عليك الانتظار {format_time(int(remaining))}!")
            return

    total_profit = 0
    profit_percentage = 15 + (list(cooldown_map.keys()).index(building) * 5) if building else 15
    profit_percentage /= 100

    for building, count in user["buildings"].items():
        if count > 0:
            profit = count * (BUILDINGS_DATA[building]["price"] * profit_percentage)
            total_profit += profit

    user["money"] += int(total_profit)
    user["last_profit"] = now.isoformat()
    save_data()
    await update.message.reply_text(f"✅ تم جمع الأرباح: {int(total_profit)}💸 (نسبة {int(profit_percentage*100)}%)\nالرصيد الحالي: {user['money']}💸")

async def puzzle(update: Update, user: dict):
    if user["riddle_active"]:
        await update.message.reply_text("❌ لديك حزورة نشطة بالفعل!")
        return

    question, answer = random.choice(RIDDLES)
    user["riddle_active"] = True
    user["riddle_answer"] = answer
    user["riddle_start_time"] = datetime.now().isoformat()
    await update.message.reply_text(question)

async def names_game(update: Update, user: dict):
    if user["names_active"]:
        await update.message.reply_text("❌ لديك لعبة أسماء نشطة بالفعل!")
        return

    letter = random.choice(list(NAMES_GAME.keys()))
    user["names_active"] = True
    user["names_letter"] = letter
    user["names_valid"] = NAMES_GAME[letter]
    user["names_start_time"] = datetime.now().isoformat()
    await update.message.reply_text(f"📝 أرسل اسمًا يبدأ بحرف '{letter}'")

# ------ دوال امونج اس ------
async def amoung_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = get_game(chat_id)

    if game and game["state"] != "ended":
        await update.message.reply_text("🚫 هناك لعبة نشطة بالفعل!")
        return

    game = create_game(chat_id)
    threading.Timer(300, lambda: end_registration(context, chat_id)).start()
    await update.message.reply_text("🕹 بدأت فترة التسجيل! اكتب 'انضمام' للانضمام")

async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    game = get_game(chat_id)

    if not game or game["state"] != "registration":
        await update.message.reply_text("🚫 لا يوجد فترة تسجيل نشطة")
        return

    if str(user.id) in game["players"]:
        await update.message.reply_text("✅ أنت مسجل بالفعل!")
        return

    if len(game["players"]) >= 10:
        await update.message.reply_text("🚫 اكتمل العدد الأقصى (10 لاعبين)")
        return

    used_colors = [p["color"] for p in game["players"].values()]
    available_colors = [c for c in COLORS if c not in used_colors]
    color = random.choice(available_colors)
game["players"][str(user.id)] = {
        "id": str(user.id),
        "name": user.full_name,
        "color": color,
        "role": None,
        "alive": True,
        "tasks": [],
        "current_task": None,
        "tasks_completed": 0
    }

    await update.message.reply_text(f"✅ انضممت كلون {color}!")
    await context.bot.send_message(user.id, f"🎮 لونك: {color} - انتظر بدء اللعبة!")

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = get_game(chat_id)

    if not game or game["state"] != "registration":
        await update.message.reply_text("🚫 لا يوجد لعبة قيد التسجيل")
        return

    if len(game["players"]) < 5:
        game["state"] = "ended"
        await update.message.reply_text("❌ لم يكتمل العدد الأدنى (5 لاعبين)")
    else:
        assign_roles(game, context)
        start_game_tasks(context, game, chat_id)
        await update.message.reply_text("🎮 بدأت اللعبة!")
        check_bodies(context, chat_id)

def assign_roles(game, context):
    players = list(game["players"].values())
    killer = random.choice(players)
    killer["role"] = "قاتل"
    game["killer"] = killer["color"]

    for p in players:
        if p["id"] != killer["id"]:
            p["role"] = "مواطن"
            p["tasks"] = random.sample(TASKS, 3)
            context.bot.send_message(p["id"], f"🎮 أنت مواطن!\nمهامك:\n{format_tasks(p['tasks'])}")
        else:
            context.bot.send_message(killer["id"], f"🔪 أنت القاتل!\nقدراتك:\n{format_killer_abilities()}")

def format_tasks(tasks):
    return "\n".join([f"- {task['description']}" for task in tasks])

def format_killer_abilities():
    return "\n".join([f"{k}: كل {v['cooldown']} ثانية" for k, v in KILLER_ABILITIES.items()])

def start_game_tasks(context, game, chat_id):
    game["state"] = "started"
    for player in game["players"].values():
        if player["role"] == "مواطن":
            assign_task(context, player["id"], chat_id)
    # بدء التحقق من شروط الفوز
    threading.Timer(30, lambda: check_win_conditions(context, chat_id)).start()

def assign_task(context, player_id, chat_id):
    game = get_game(chat_id)
    player = game["players"][player_id]

    if player["tasks_completed"] >= len(player["tasks"]):
        return

    task = player["tasks"][player["tasks_completed"]]
    player["current_task"] = task

    if task["type"] == "timer":
        msg = f"⏳ المهمة: {task['steps'][0]} لمدة {task['durations'][0]} ثانية"
    elif task["type"] == "sticker":
        msg = f"📎 أرسل الملصق {task['required']}"
    elif task["type"] == "math":
        msg = f"🧮 حل: {task['problem']}"
    elif task["type"] == "reverse":
        msg = f"🔀 اكتب {task['word']} بالعكس"
    elif task["type"] == "captcha":
        msg = f"🔐 أدخل الرمز: {task['code']}"
    elif task["type"] == "memory":
        msg = f"🧠 تذكر التسلسل: {task['sequence']}"

    context.bot.send_message(int(player["id"]), msg)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    user_id = update.effective_user.id
    user = get_user(user_id)

    if user["riddle_active"]:
        if text == user["riddle_answer"].lower():
            user["money"] += 50
            user["riddle_active"] = False
            await update.message.reply_text(f"✅ إجابة صحيحة! +50💸 الرصيد: {user['money']}💸")
        else:
            await update.message.reply_text("❌ إجابة خاطئة! حاول مجددًا")
        return

    if user["names_active"]:
        if text in [name.lower() for name in user["names_valid"]]:
            user["money"] += 30
            user["names_active"] = False
            await update.message.reply_text(f"✅ إجابة صحيحة! +30💸 الرصيد: {user['money']}💸")
        else:
            await update.message.reply_text("❌ اسم خاطئ! حاول مجددًا")
        return

    if text == "حسابي":
        await my_account(update, user)
    elif text == "متجر":
        await shop(update)
    elif text.startswith("شراء"):
        await purchase(update, user)
    elif text.startswith("بيع"):
        await sell(update, user)
    elif text == "جمع ارباح":
        await collect_profit(update, user)
    elif text == "حزورة":
        await puzzle(update, user)
    elif text == "اسماء":
        await names_game(update, user)
    elif text == "امونج اس":
        await amoung_us(update, context)
    elif text == "انضمام":
        await join_game(update, context)
    elif text == "بدء":
        await start_game(update, context)
    elif text == "خروج":
        await handle_exit(update, context)
    elif text == "الاوامر":
        await show_commands(update)
    else:
        await handle_among_us_commands(update, context, text)

async def handle_among_us_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    game = get_game(chat_id)

    if not game or game["state"] != "started":
        return

    player = game["players"].get(str(user_id))
    if not player or not player["alive"]:
        return

    if player["current_task"]:
        task = player["current_task"]

        if task["type"] == "math" and text == task["answer"]:
            await complete_task(context, game, player, chat_id)
        elif task["type"] == "reverse" and text == task["answer"]:
            await complete_task(context, game, player, chat_id)
        elif task["type"] == "captcha" and text == task["code"]:
            await complete_task(context, game, player, chat_id)
        elif task["type"] == "sticker" and update.message.sticker and update.message.sticker.emoji == task["required"]:
            await complete_task(context, game, player, chat_id)

    if text == "اجتماع":
        await start_meeting(update, context)
    elif text.startswith("تصويت"):
        await handle_vote(update, game, text)
    elif text in KILLER_ABILITIES and player["role"] == "قاتل":
        await use_killer_ability(update, context, game, player, text)

async def complete_task(context, game, player, chat_id):
    player["tasks_completed"] += 1
    get_user(player["id"])["money"] += 100
    player["current_task"] = None

    if player["tasks_completed"] >= len(player["tasks"]):
        await context.bot.send_message(player["id"], "🎉 أكملت جميع المهام!")
    else:
        assign_task(context, player["id"], chat_id)
    await check_win_conditions(context, chat_id)

async def start_meeting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = get_game(chat_id)

    if not game or game["state"] != "started":
        return

    if game["meeting"]:
        await update.message.reply_text("🚫 هناك اجتماع نشط بالفعل!")
        return

    current_round_bodies = [p for p in game["dead_players"] if p["round_died"] == game["round"]]
    if not current_round_bodies:
        await update.message.reply_text("❌ لا توجد جثث للإبلاغ عنها!")
        return

    bodies_list = "\n".join([f"- {p['color']}" for p in current_round_bodies])
    await context.bot.send_message(chat_id, f"🕵️♂️ اجتماع طارئ! الجثث المكتشفة:\n{bodies_list}\nاكتب 'تصويت [اللون]'")

    game["meeting"] = True
    game["current_votes"] = {}
    game["round"] += 1
    threading.Timer(60, lambda: end_voting(context, chat_id)).start()

async def end_voting(context, chat_id):
    game = get_game(chat_id)
    if not game or not game["meeting"]:
        return

    vote_counts = {}
    for color in game["current_votes"].values():
        vote_counts[color] = vote_counts.get(color, 0) + 1

    if vote_counts:
        max_color = max(vote_counts, key=vote_counts.get)
        eliminated = next(p for p in game["players"].values() if p["color"] == max_color)
        eliminated["alive"] = False
        game["dead_players"].append(eliminated)
        redistribute_tasks(eliminated, game)
        await context.bot.send_message(chat_id, f"☠️ تم إقصاء اللاعب {max_color}!")

    game["meeting"] = False
    game["meeting_cooldown"] = datetime.now() + timedelta(minutes=5)
    await check_win_conditions(context, chat_id)

async def handle_vote(update: Update, game: dict, text: str):
    user_id = update.effective_user.id
    match = re.match(r"تصويت (\w+)", text)

    if not match:
        await update.message.reply_text("❌ استخدم: تصويت <اللون>")
        return

    color = match.group(1)
    game["current_votes"][str(user_id)] = color
    await update.message.reply_text(f"✅ تم التصويت على {color}")

async def use_killer_ability(update: Update, context: ContextTypes.DEFAULT_TYPE, game: dict, player: dict, ability: str):
    cooldown = KILLER_ABILITIES[ability]["cooldown"]

    if player["color"] in game["cooldowns"] and datetime.now() < game["cooldowns"][player["color"]]:
        remaining = (game["cooldowns"][player["color"]] - datetime.now()).total_seconds()
        await update.message.reply_text(f"⏳ القدرة غير متاحة حالياً. انتظر {format_time(int(remaining))}")
        return

    if ability == "قتل":
        target_color = update.message.text.split()[-1]
        target = next((p for p in game["players"].values() if p["color"] == target_color and p["alive"]), None)

        if not target:
            await update.message.reply_text("❌ اللاعب غير موجود أو ميت!")
            return

        target["alive"] = False
        target["round_died"] = game["round"]
        game["dead_players"].append(target)
        game["cooldowns"][player["color"]] = datetime.now() + timedelta(seconds=cooldown)
        redistribute_tasks(target, game)

        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"☠️ تم قتل اللاعب {target_color} بواسطة القاتل!")
        await context.bot.send_message(target["id"], "💀 لقد قتلك القاتل!")
        await check_win_conditions(context, chat_id)

async def handle_exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    game = get_game(chat_id)

    if not game:
        await update.message.reply_text("⚠️ لا يوجد لعبة نشطة")
        return

    player = game["players"].get(str(user.id))
    if not player:
        await update.message.reply_text("⚠️ أنت لست جزءًا من اللعبة")
        return

    if game["state"] == "registration":
        del game["players"][str(user.id)]
        await update.message.reply_text("✅ تم إخراجك من اللعبة")
    else:
        player["alive"] = False
        game["dead_players"].append(player)
        await update.message.reply_text("☠️ تم تسجيلك كميت في اللعبة")

async def show_commands(update: Update):
    commands = [
        "📜 الأوامر المتاحة:",
        "حسابي - عرض الحالة المالية",
        "متجر - عرض قائمة الأبنية",
        "شراء <الاسم> <العدد> - شراء أبنية",
        "بيع <الاسم> <العدد> - بيع أبنية",
        "جمع ارباح - جمع أرباح الأبنية",
        "حزورة - بدء لعبة الحزازير",
        "اسماء - بدء لعبة الأسماء",
        "امونج اس - بدء لعبة جديدة",
        "انضمام - الانضمام للعبة الحالية",
        "بدء - بدء اللعبة إذا اكتمل العدد",
        "خروج - الخروج من اللعبة الحالية",
        "الاوامر - عرض هذه القائمة"
    ]
    await update.message.reply_text("\n".join(commands))

async def check_win_conditions(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    game = get_game(chat_id)
    if not game or game["state"] != "started":
        return

    all_citizens = [p for p in game["players"].values() if p["role"] == "مواطن"]
    alive_players = [p for p in game["players"].values() if p["alive"]]
    killer = next((p for p in alive_players if p["role"] == "قاتل"), None)

    # حالة فوز المواطنين (القاتل تم طرده)
    if not killer:
        for citizen in all_citizens:  # يشمل الأموات والأحياء
            user = get_user(int(citizen["id"]))
            user["money"] += 5000
            save_data()
        await context.bot.send_message(chat_id, f"🎉 فوز المواطنين! الجميع يحصل على 5000💸")
        game["state"] = "ended"
        return

    # حالة فوز المواطنين (إكمال المهام)
    all_tasks_completed = all(p["tasks_completed"] >= len(p["tasks"]) for p in all_citizens)
    if all_tasks_completed:
        for citizen in all_citizens:  # يشمل الأموات والأحياء
            user = get_user(int(citizen["id"]))
            user["money"] += 5000
            save_data()
        await context.bot.send_message(chat_id, f"🎉 فوز المواطنين! الجميع يحصل على 5000💸")
        game["state"] = "ended"
        return

       # حالة فوز القاتل (بقي مع مواطن واحد)
    if len(alive_players) == 2 and killer in alive_players:
        user = get_user(int(killer["id"]))
        user["money"] += 45000
        save_data()
        await context.bot.send_message(chat_id, "🎭 فوز القاتل! بقي مع مواطن واحد\nالقاتل يحصل على 45000💸")
        game["state"] = "ended"
        return

    # إذا لم تتحقق أي حالة، نستمر في اللعبة
    threading.Timer(30, lambda: check_win_conditions(context, chat_id)).start()

async def check_bodies(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    game = get_game(chat_id)
    if not game or game["state"] != "started":
        return

    current_round_bodies = [p for p in game["dead_players"] if p["round_died"] == game["round"]]
    if current_round_bodies:
        alive_players = [p for p in game["players"].values() if p["alive"]]
        if alive_players:
            chosen_player = random.choice(alive_players)
            context.bot.send_message(chosen_player["id"], "⚠️ تم العثور على جثة! اكتب 'اجتماع' لبدء التصويت")

    threading.Timer(90, lambda: check_bodies(context, chat_id)).start()

    await check_win_conditions(context, chat_id)

def redistribute_tasks(dead_player, game):
    if dead_player["role"] != "مواطن":
        return

    remaining_tasks = dead_player["tasks"][dead_player["tasks_completed"]:]
    if not remaining_tasks:
        return

    # البحث عن مواطن حي عشوائي
    alive_citizens = [p for p in game["players"].values()
                     if p["alive"] and p["role"] == "مواطن" and p["id"] != dead_player["id"]]

    if not alive_citizens:
        return

    recipient = random.choice(alive_citizens)
    recipient["tasks"].extend(remaining_tasks)

    # إذا كان المتلقي ليس لد مهمة حالية
    if not recipient["current_task"]:
        recipient["current_task"] = recipient["tasks"][recipient["tasks_completed"]]
        context.bot.send_message(recipient["id"], f"📦 وصلتك مهام جديدة من اللاعب الراحل!\n{format_tasks(remaining_tasks)}")

def end_registration(context, chat_id):
    game = get_game(chat_id)
    if not game:
        return

    if len(game["players"]) >= 5:
        assign_roles(game, context)
        start_game_tasks(context, game, chat_id)
        context.bot.send_message(chat_id, "🎮 بدأت اللعبة!")
        check_bodies(context, chat_id)
    else:
        game["state"] = "ended"
        context.bot.send_message(chat_id, "❌ لم يكتمل العدد الأدنى (5 لاعبين)")

def format_tasks(tasks):
    return "\n".join([f"- {task['description']}" for task in tasks])

# ------ التشغيل الرئيسي ------
def main():
    load_data()
    auto_save()
    token = "bot_token"  # استبدل هذا بالتوكن الفعلي
    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
