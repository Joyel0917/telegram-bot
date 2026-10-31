import os
import asyncio
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") # La chiave di OpenRouter
PORT = int(os.environ.get("PORT", "8080"))
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

app_flask = Flask(__name__)
telegram_app = ApplicationBuilder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono attivo sul Cloud 24/7 con un'IA completamente libera.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    testo_utente = update.message.text
    await update.message.chat.send_action(action="typing")

    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            # Opzionali ma consigliati da OpenRouter per le classifiche
            "HTTP-Referer": "https://github.com", 
            "X-Title": "TelegramBot"
        }
        payload = {
            # Qui usiamo un modello open source eccellente e senza filtri su OpenRouter
            "model": "mistralai/mistral-7b-instruct:free",  # Oppure un altro modello a tua scelta
            "messages": [
                {"role": "system", "content": "Sei un assistente utile e diretto."},
                {"role": "user", "content": testo_utente}
            ]
        }
        
        # Endpoint ufficiale di OpenRouter
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        risposta_json = response.json()
        
        risposta_ia = risposta_json["choices"][0]["message"]["content"]
        await update.message.reply_text(risposta_ia)
        
    except Exception as e:
        await update.message.reply_text(f"Ops, c'è stato un errore nel contattare l'IA: {str(e)}")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

@app_flask.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    asyncio.run(telegram_app.process_update(update))
    return "ok", 200

@app_flask.route("/", methods=["GET"])
def index():
    return "Il bot di Telegram con OpenRouter è attivo!", 200

async def main():
    await telegram_app.initialize()
    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/{TOKEN}"
        await telegram_app.bot.set_webhook(webhook_url)
        print(f"Webhook impostato con successo su: {webhook_url}")
    
    app_flask.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    asyncio.run(main())
