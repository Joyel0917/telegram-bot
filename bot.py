import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import requests

# 1. Inserisci qui il token che ti ha dato BotFather su Telegram
TELEGRAM_TOKEN = "7104877587:AAF_x6M0f30WLl6HJsM1WfSUdW4Di0MMMcI"

# Configurazione per vedere i log nel terminale del PC
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 2. Questa funzione riceve il tuo messaggio da Telegram e decide cosa rispondere
async def gestisci_messaggio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    testo_utente = update.message.text
    
    print(f"Messaggio ricevuto: {testo_utente}")
    
    # Per ora, per testare, facciamo finta che risponda così:
    risposta_ia = f"Ho ricevuto il tuo messaggio: '{testo_utente}'. Presto qui collegheremo l'IA libera!"
    
    # Manda la risposta indietro su Telegram
    await update.message.reply_text(risposta_ia)

# 3. Qui il programma si avvia e si mette in "ascolto"
if __name__ == '__main__':
    # Crea l'applicazione del bot usando il tuo token
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Dice al bot di mettersi in ascolto per ogni messaggio di testo che mandi
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gestisci_messaggio))
    
    print("🤖 Bot avviato e pronto sul tuo telefono!")
    # Mantiene il bot attivo in ascolto
    app.run_polling()