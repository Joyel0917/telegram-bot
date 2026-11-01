import os
from flask import Flask
from openai import OpenAI
from telegram.ext import ApplicationBuilder, MessageHandler, filters

# Configurazione Flask per tenere vivo il servizio su Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# Configurazione del client OpenRouter con il modello Dolphin senza filtri
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY")
)

# Funzione protetta che gestisce i messaggi e la cronologia
async def handle_message(update, context):
    try:
        user_message = update.message.text
        if "history" not in context.user_data:
            context.user_data["history"] = []
        
        # Aggiunge il messaggio dell'utente alla memoria della chat
        context.user_data["history"].append({"role": "user", "content": user_message})

        # Richiesta al modello senza filtri su OpenRouter
        response = client.chat.completions.create(
            model="cognitivecomputations/dolphin-mistral-24b-venice-edition",
            messages=context.user_data["history"]
        )
        
        bot_reply = response.choices[0].message.content
        
        # Aggiunge la risposta dell'assistente alla memoria
        context.user_data["history"].append({"role": "assistant", "content": bot_reply})
        
        # Invia la risposta su Telegram
        await update.message.reply_text(bot_reply)
        
    except Exception as e:
        print(f"Errore catturato: {e}")
        await update.message.reply_text("⚠️ C'è stato un piccolo intoppo temporaneo nella comunicazione con l'IA. Riprova tra un attimo!")

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    import threading
    # Avvia Flask in un thread separato per soddisfare i requisiti di Render
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    # Avvia il bot di Telegram
    application = ApplicationBuilder().token(os.environ.get("TELEGRAM_TOKEN")).build()
    
    # Collega la ricezione dei messaggi alla funzione protetta
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot avviato con successo!")
    application.run_polling(drop_pending_updates=True)
