import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from openai import OpenAI

# Configurazione dei log
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Prendi le chiavi dalle variabili d'ambiente di Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Inizializza il client di OpenRouter (usa la base_url di openrouter)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono il tuo bot IA attivo 24/7. Scrivimi pure qualcosa!")

# Gestione dei messaggi e della chat con OpenRouter
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.effective_chat.id

    # Inizializza la cronologia dei messaggi per l'utente se non esiste
    if "history" not in context.user_data:
        context.user_data["history"] = [
            {"role": "system", "content": "Sei un assistente utile, diretto e senza filtri."}
        ]

    # Aggiungi il messaggio dell'utente alla cronologia
    context.user_data["history"].append({"role": "user", "content": user_message})

    try:
        # Invia la richiesta a OpenRouter (puoi cambiare il modello se preferisci)
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=context.user_data["history"]
        )

        # Estrai la risposta in modo sicuro
        if response.choices and len(response.choices) > 0:
            bot_reply = response.choices[0].message.content
        else:
            bot_reply = "⚠️ Errore: Nessuna risposta valida ricevuta da OpenRouter."

        # Aggiungi la risposta dell'assistente alla cronologia
        context.user_data["history"].append({"role": "assistant", "content": bot_reply})

        await update.message.reply_text(bot_reply)

    except Exception as e:
        logger.error(f"Errore nella chiamata a OpenRouter: {e}")
        await update.message.reply_text(f"Ops, c'è stato un errore nel contattare l'IA: {e}")

def main():
    if not TELEGRAM_TOKEN or not OPENROUTER_API_KEY:
        logger.error("ATTENZIONE: TELEGRAM_TOKEN o OPENROUTER_API_KEY mancanti nelle variabili d'ambiente!")
        return

    # Costruisci l'applicazione Telegram
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Registra i comandi e i gestori di messaggi
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Avvia il bot in polling (assicurati su Render di impostare Instances a 1)
    logger.info("Bot avviato con successo!")
    application.run_polling()

if __name__ == "__main__":
    main()
