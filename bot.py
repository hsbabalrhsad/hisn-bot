# 🔐 التوكن الصحيح الجديد - لا تغير هذا السطر
BOT_TOKEN = "8924079605:AAHfK3yBVb-KthOo1VbXlq1-YK2VCJacUT8"
CHANNEL_USERNAME = "@heesn_almoahdeen"

import os, re, ssl, socket, asyncio, logging, datetime, warnings
from urllib.parse import urlparse
from typing import List, Tuple
import aiohttp
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.error import TelegramError, InvalidToken, TimedOut, NetworkError
from telegram.request import HTTPXRequest
from aiohttp import web

warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO, handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

class LinkAnalyzer:
    SUSPICIOUS_KEYWORDS = re.compile(r"\b(login|verify|account|secure|update|confirm|password|wallet|claim|free|win|limited|urgent|verify now|reset password|bank|paypal|crypto|signin)\b", re.IGNORECASE)
    PLATFORMS = {"تيليجرام": re.compile(r"(t\.me|telegram\.me|tg://)"), "واتساب": re.compile(r"(wa\.me|chat\.whatsapp\.com)"), "ديسكورد": re.compile(r"(discord\.gg|discord\.com)"), "إنستغرام": re.compile(r"(instagram\.com|instagr\.am)"), "تويتر/X": re.compile(r"(twitter\.com|x\.com)"), "يوتيوب": re.compile(r"(youtube\.com|youtu\.be)"), "تيك توك": re.compile(r"(tiktok\.com)"), "فايبر": re.compile(r"(viber\.com|click\.to\.chat)"), "سناب شات": re.compile(r"(snapchat\.com)"),}
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 HisnBot/1.0"}
        self.session = None
        self._timeout = aiohttp.ClientTimeout(total=10)
    async def init(self):
        if self.session is None or self.session.closed: self.session = aiohttp.ClientSession(headers=self.headers, timeout=self._timeout)
    async def close(self):
        if self.session and not self.session.closed: await self.session.close()
    def detect_platform(self, url: str) -> str:
        for name, pat in self.PLATFORMS.items():
            if pat.search(url): return name
        return "موقع ويب عام / غير معروف"
    def check_keywords(self, url: str, html: str = "") -> List[str]:
        found = [m.group().lower() for m in self.SUSPICIOUS_KEYWORDS.finditer(url)]
        if html: found += [m.group().lower() for m in self.SUSPICIOUS_KEYWORDS.finditer(html[:2000]) if m.group().lower() not in found]
        return list(set(found))[:5]
    async def get_chain(self, url: str) -> List[str]:
        try:
            async with self.session.head(url, allow_redirects=True, ssl=False) as r: return [str(u) for u in [h.url for h in r.history]] + [str(r.url)]
        except: return [url]
    async def fetch(self, url: str) -> Tuple[bool, str]:
        try:
            async with self.session.get(url, ssl=False, max_redirects=5) as r:
                if r.status >= 400: return False, f"⚠️ حالة: {r.status}"
                return True, await r.text()
        except Exception as e: return False, f"❌ فشل الجلب: {e}"
    def analyze_perms(self, html: str) -> List[str]:
        perms = []; soup = BeautifulSoup(html, "html.parser")
        if soup.find("form") and any(i.get("type","").lower() in ["password","email","tel"] for i in soup.find_all("input")): perms.append("🔐 يحتوي على نموذج إدخال بيانات حساسة")
        if soup.find("iframe"): perms.append("🖼️ يحتوي على إطارات خارجية (iframes)")
        if re.search(r"document\.location|window\.open|eval\(", html): perms.append("🔗 يحتوي على سكريبت إعادة توجيه/تنفيذ ديناميكي")
        return perms or ["✅ لم يتم رصد أذونات مشبوهة صريحة"]
    async def check_ssl(self, domain: str) -> str:
        try:
            with socket.create_connection((domain, 443), timeout=3) as sock:
                with ssl.create_default_context().wrap_socket(sock, server_hostname=domain) as s: return f"🔒 شهادة SSL سارية (تنتهي: {s.getpeercert().get('notAfter', '?')})"
        except: return "⚠️ شهادة SSL مفقودة أو غير صالحة"
    async def analyze(self, url: str) -> str:
        if not url.startswith(("http://","https://")): url = "https://"+url
        p = urlparse(url)
        if not p.netloc: return "❌ الرابط غير صالح."
        await self.init()
        plat = self.detect_platform(url); chain = await self.get_chain(url)
        red = f"🔁 إعادة توجيه: {len(chain)-1}\n" if len(chain)>1 else ""
        ok, html = await self.fetch(url); kw = self.check_keywords(url, html if ok else "")
        perms = self.analyze_perms(html) if ok else ["❌ تعذر تحليل المحتوى"]
        ssl = await self.check_ssl(p.netloc) if p.scheme=="https" else "🌐 لا يستخدم HTTPS"
        return (f"🔍 *تحليل حصن الموحدين*\n\n🌐 الرابط: `{url}`\n📱 المنصة: {plat}\n{red}🔑 كلمات مشبوهة: {', '.join(kw) or '✅ لا يوجد'}\n🛡️ الأذونات:\n"+"\n".join(f"• {x}" for x in perms)+f"\n{ssl}\n⏱️ {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n🛡️ *تحليل آمن بواسطة مؤسسة حصن الموحدين*")

async def check_sub(uid: int, app: Application) -> bool:
    try:
        member = await app.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=uid)
        return member.status in ["member", "administrator", "creator"]
    except TelegramError as e: logger.warning(f"فحص الاشتراك: {e}"); return False

SUB_MSG = "🔒 *مرحباً بك في بوت حصن الموحدين*\n\nلاستخدام البوت، يُرجى الاشتراك في قناتنا أولاً:\n📢 {channel}\n\nبعد الاشتراك، اضغط على الزر أدناه للتحقق والمتابعة."
analyzer = LinkAnalyzer()

async def start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not await check_sub(u.effective_user.id, c.application):
        await u.message.reply_text(SUB_MSG.format(channel=CHANNEL_USERNAME), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ تحقق", callback_data="check_sub")]])); return
    await u.message.reply_text("🛡️ مرحباً! أرسل أي رابط لتحليله أمنياً فوراً.", parse_mode="Markdown")

async def handle_link(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not await check_sub(u.effective_user.id, c.application):
        await u.message.reply_text(SUB_MSG.format(channel=CHANNEL_USERNAME), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ تحقق", callback_data="check_sub")]])); return
    await u.message.reply_chat_action("typing")
    try: await u.message.reply_text(await analyzer.analyze(u.message.text.strip()), parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e: logger.exception("خطأ تحليل"); await u.message.reply_text("❌ حدث خطأ أثناء التحليل.")

async def handle_text(u: Update, c: ContextTypes.DEFAULT_TYPE): await u.message.reply_text("🔍 يرجى إرسال رابط يبدأ بـ http أو https للتحليل.")
async def check_callback(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query; await q.answer()
    if await check_sub(q.from_user.id, c.application): await q.edit_message_text("✅ تم التحقق من اشتراكك بنجاح.")
    else: await q.edit_message_text("⚠️ لم يتم رصد اشتراكك بعد.")

async def ping_handler(request): return web.Response(text="✅ Hisn Bot is alive")

async def main():
    request = HTTPXRequest(connection_pool_size=8, connect_timeout=30.0, read_timeout=30.0, write_timeout=30.0, pool_timeout=30.0)
    app = Application.builder().token(BOT_TOKEN).request(request).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_callback, pattern="^check_sub$"))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"https?://\S+"), handle_link))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"🔄 محاولة الاتصال (محاولة {attempt+1}/{max_retries})...")
            async with app:
                await app.start(); await app.updater.start_polling()
                logger.info("🛡️ تم تشغيل بوت تليجرام بنجاح (Polling Active)")
                web_app = web.Application(); web_app.router.add_get("/", ping_handler); web_app.router.add_get("/ping", ping_handler)
                runner = web.AppRunner(web_app); await runner.setup(); await web.TCPSite(runner, "0.0.0.0", 7860).start()
                logger.info("🌐 خادم الويب يعمل على المنفذ 7860")
                await asyncio.Event().wait(); break
        except (TimedOut, NetworkError) as e:
            logger.warning(f"⚠️ فشل الاتصال (محاولة {attempt+1}): {e}")
            if attempt < max_retries - 1: await asyncio.sleep(2 ** attempt)
            else: logger.critical("❌ فشل الاتصال بعد جميع المحاولات"); raise
        except InvalidToken as e: logger.critical(f"❌ التوكن غير صالح: {e}"); raise
        except Exception as e: logger.exception(f"❌ خطأ غير متوقع: {e}"); raise
    await analyzer.close()

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: logger.info("🛑 تم إيقاف البوت يدوياً")
    except Exception as e: logger.critical(f"❌ توقف البوت: {e}")
