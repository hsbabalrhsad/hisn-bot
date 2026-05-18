#!/usr/bin/env python3
"""🛡️ بوت حصن الموحدين - Zeabur Optimized"""
import os, re, ssl, socket, asyncio, logging, datetime
from urllib.parse import urlparse
import aiohttp
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.request import HTTPXRequest

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8828056179:AAFMkZFRVOH5NTmZbxyD8rqOAfdGObplKtM")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@heesn_almoahdeen")

PLATFORMS = {
    "تيليجرام": r"t\.me|telegram\.me|tg://", "واتساب": r"wa\.me|chat\.whatsapp\.com",
    "إنستغرام": r"instagram\.com", "فيسبوك": r"facebook\.com|fb\.me",
    "تويتر": r"twitter\.com|x\.com", "يوتيوب": r"youtube\.com|youtu\.be",
    "تيك توك": r"tiktok\.com", "ديسكورد": r"discord\.gg|discord\.com",
    "لينكد إن": r"linkedin\.com", "جيت هب": r"github\.com",
    "جوجل": r"google\.[a-z]+", "أمازون": r"amazon\.[a-z]+",
    "باي بال": r"paypal\.com", "باينانس": r"binance\.com",
    "كوين بيس": r"coinbase\.com", "ميتا ماسك": r"metamask\.io",
    "سي إن إن": r"cnn\.com", "بي بي سي": r"bbc\.com",
    "الجزيرة": r"aljazeera\.net", "أبل": r"apple\.com",
    "مايكروسوفت": r"microsoft\.com", "أدوبي": r"adobe\.com"
}

class Analyzer:
    BAD = re.compile(r"\b(login|verify|password|wallet|claim|free|win|urgent|reset|bank|paypal|crypto|signin|alert)\b", re.I)
    def __init__(self): self.sess = None
    async def init(self):
        if not self.sess or self.sess.closed:
            self.sess = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8))
    def plat(self, url):
        d = urlparse(url).netloc.lower()
        for n,p in PLATFORMS.items():
            if re.search(p,d,re.I): return n
        return "موقع عام"
    async def analyze(self, url):
        if not url.startswith("http"): url = "https://"+url
        if not urlparse(url).netloc: return "❌ رابط غير صالح"
        await self.init()
        pt = self.plat(url)
        try:
            async with self.sess.get(url, ssl=False) as r:
                html = await r.text()
                soup = BeautifulSoup(html, "html.parser")
                w = []
                if soup.find("form") and any(i.get("type","").lower() in ["password","email"] for i in soup.find_all("input")): w.append("🔐 نموذج بيانات")
                if re.search(r"eval\(|document\.write\(", html, re.I): w.append(" سكريبت مشبوه")
                if soup.find("iframe"): w.append("🖼️ تضمين خارجي")
                kw = [m.group() for m in self.BAD.finditer(html[:1500])]
                if len(kw)>=3: w.append(f"🚨 {len(kw)} كلمة مشبوهة")
                wl = "\n".join(f"• {x}" for x in w) if w else "• ✅ لا توجد تهديدات"
                return (f"<b>🛡️ تحليل حصن الموحدين</b>\n\n الرابط: <code>{url}</code>\n📱 المنصة: <b>{pt}</b>\n🔐 الأمان:\n{wl}\n{'🔒 HTTPS' if url.startswith('https') else '🌐 HTTP'}\n️ {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')}\n\n<b>🛡️ مؤسسة حصن الموحدين</b>")
        except Exception as e: return f"⚠️ تعذر التحليل. المنصة: <b>{pt}</b>\nالسبب: {str(e)[:80]}"

analyzer = Analyzer()

async def sub_ok(uid, app):
    try:
        m = await app.bot.get_chat_member(CHANNEL_USERNAME, uid)
        return m.status in ["member","administrator","creator"]
    except: return False

async def require_sub(u,c):
    if await sub_ok(u.effective_user.id, c.application): return True
    kb = [[InlineKeyboardButton("✅ تحقق", callback_data="chk")]]
    await u.message.reply_text(f"<b> اشترك أولاً</b>\nالقناة: {CHANNEL_USERNAME}\nثم اضغط الزر.", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))
    return False

async def start(u,c):
    if not await require_sub(u,c): return
    kb = [[InlineKeyboardButton("📊 مساعدة", callback_data="help")]]
    await u.message.reply_text("<b>🛡️ بوت حصن الموحدين</b>\n\nأرسل أي رابط لتحليله:\n✅ كشف التصيد • 🔐 فحص الأذونات • 📱 تحديد المنصة", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

async def on_link(u,c):
    if not await require_sub(u,c): return
    await u.message.reply_chat_action("typing")
    await u.message.reply_text(await analyzer.analyze(u.message.text.strip()), parse_mode="HTML", disable_web_page_preview=True)

async def on_text(u,c):
    if not await require_sub(u,c): return
    await u.message.reply_text("🔍 أرسل رابطاً يبدأ بـ <code>http</code>", parse_mode="HTML")

async def cb(u,c):
    q = u.callback_query; await q.answer()
    if q.data=="chk":
        ok = await sub_ok(q.from_user.id, c.application)
        await q.edit_message_text("✅ مفعل" if ok else "⚠️ اشترك أولاً", parse_mode="HTML")
    elif q.data=="help":
        await q.edit_message_text("<b>📖 الاستخدام</b>\n1. أرسل رابطاً\n2. انتظر التحليل", parse_mode="HTML")

def main():
    app_bot = Application.builder().token(BOT_TOKEN).request(HTTPXRequest(connect_timeout=15, read_timeout=15)).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(cb))
    app_bot.add_handler(MessageHandler(filters.Regex(r"https?://\S+"), on_link))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    logger.info("️ بدء تشغيل بوت حصن الموحدين على Zeabur...")
    app_bot.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()