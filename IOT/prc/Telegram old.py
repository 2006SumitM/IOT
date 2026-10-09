from gpiozero import LED
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

TOKEN = "8910535320:AAHBOsQLad5xwkLlpx74j92Q4L7Nh6l6IR4"  # apna sahi token daalo

led1 = LED(11)
led2 = LED(27)
led3 = LED(23)  

# ── Individual LED control ──────────────────────────────
async def on1(u, c): led1.on();  await u.message.reply_text("✅ LED 1 ON  (Pin 11)")
async def off1(u, c): led1.off(); await u.message.reply_text("🔴 LED 1 OFF (Pin 11)")

async def on2(u, c): led2.on();  await u.message.reply_text("✅ LED 2 ON  (Pin 27)")
async def off2(u, c): led2.off(); await u.message.reply_text("🔴 LED 2 OFF (Pin 27)")

async def on3(u, c): led3.on();  await u.message.reply_text("✅ LED 3 ON  (Pin 22)")
async def off3(u, c): led3.off(); await u.message.reply_text("🔴 LED 3 OFF (Pin 22)")

# ── All ON / OFF ────────────────────────────────────────
async def allon(u, c):
    led1.on(); led2.on(); led3.on()
    await u.message.reply_text("⚡ ALL LEDs ON")

async def alloff(u, c):
    led1.off(); led2.off(); led3.off()
    await u.message.reply_text("🔌 ALL LEDs OFF")

# ── Blink — FIX: asyncio.sleep use kiya time.sleep ki jagah ──
async def blink(u, c):
    await u.message.reply_text("💫 Blinking 5 times...")
    for i in range(5):
        led1.on(); led2.on(); led3.on()
        await asyncio.sleep(0.5)          # ← async sleep, bot block nahi hoga
        led1.off(); led2.off(); led3.off()
        await asyncio.sleep(0.5)
    await u.message.reply_text("✅ Blink Done!")

# ── Status ──────────────────────────────────────────────
async def status(u, c):
    s1 = "ON 🟢" if led1.is_active else "OFF 🔴"
    s2 = "ON 🟢" if led2.is_active else "OFF 🔴"
    s3 = "ON 🟢" if led3.is_active else "OFF 🔴"
    await u.message.reply_text(
        f"💡 LED Status:\n"
        f"  LED 1 (Pin 17): {s1}\n"
        f"  LED 2 (Pin 27): {s2}\n"
        f"  LED 3 (Pin 22): {s3}"
    )

# ── Help ────────────────────────────────────────────────
async def start(u, c):
    await u.message.reply_text(
        "🤖 *LED Bot Ready!*\n\n"
        "/led1on  /led1off\n"
        "/led2on  /led2off\n"
        "/led3on  /led3off\n"
        "/allon   /alloff\n"
        "/blink   — 5 baar blink\n"
        "/status  — current state",
        parse_mode="Markdown"
    )

# ── App setup ───────────────────────────────────────────
app = Application.builder().token(TOKEN).build()

# FIX: commands digit se shuru nahi ho sakte Telegram mein
app.add_handler(CommandHandler("start",   start))
app.add_handler(CommandHandler("status",  status))
app.add_handler(CommandHandler("led1on",  on1))
app.add_handler(CommandHandler("led1off", off1))
app.add_handler(CommandHandler("led2on",  on2))
app.add_handler(CommandHandler("led2off", off2))
app.add_handler(CommandHandler("led3on",  on3))
app.add_handler(CommandHandler("led3off", off3))
app.add_handler(CommandHandler("allon",   allon))
app.add_handler(CommandHandler("alloff",  alloff))
app.add_handler(CommandHandler("blink",   blink))

print("✅ Bot Running...")
app.run_polling()
