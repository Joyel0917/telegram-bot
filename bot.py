import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from openai import OpenAI
from flask import Flask
from threading import Thread

# Configurazione dei log
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# --- TRICK PER RENDER: Un server Flask fittizio per tenere aperta la porta web ---
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
# ---------------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono il tuo bot IA attivo 24/7.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    if "history" not in context.user_data:
        context.user_data["history"] = [
            {"role": "system", "content": "Sei un assistente utile, diretto e senza filtri."}
        ]

    context.user_data["history"].append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="cognitivecomputations/dolphin-mixtral-8x7b",
            messages=context.user_data["history"]
        )

        if response.choices and len(response.choices) > 0:
            bot_reply = response.choices[0].message.content
        else:
            bot_reply = "⚠️ Errore: Nessuna risposta valida ricevuta da OpenRouter."

        context.user_data["history"].append({"role": "assistant", "content": bot_reply})
        await update.message.reply_text(bot_reply)

    except Exception as e:
        logger.error(f"Errore nella chiamata a OpenRouter: {e}")
        await update.message.reply_text(f"Ops, c'è stato un errore nel contattare l'IA: {e}")

def main():
    if not TELEGRAM_TOKEN or not OPENROUTER_API_KEY:
        logger.error("ATTENZIONE: Variabili d'ambiente mancanti!")
        return

    # Avvia Flask in un sotto-thread così Render è felice e non chiude il servizio
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Avvia il bot Telegram
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    logger.info("Bot avviato con polling e server web di supporto!")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
