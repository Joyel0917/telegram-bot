import os
import re
import sqlite3
from datetime import datetime, timedelta
from flask import Flask
from openai import OpenAI
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from apscheduler.schedulers.background import BackgroundScheduler

# --- CONFIGURAZIONE DATABASE PER I PROMEMORIA ---
def init_db():
    conn = sqlite3.connect("reminders.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            reminder_text TEXT,
            run_time TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

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

# Funzione per inviare il promemoria quando scade il tempo
def trigger_reminder(chat_id, reminder_text, bot):
    try:
        # Usiamo asyncio per inviare il messaggio in modo asincrono dal worker di APScheduler
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot.send_message(
            chat_id=chat_id,
            text=f"⏰ **PROMEMORIA SCADUTO!**\n\n{reminder_text}",
            parse_mode="Markdown"
        ))
    except Exception as e:
        print(f"Errore invio promemoria salvato: {e}")

# Funzione comando /remind avanzata con supporto per m, h, d
async def remind_command(update, context):
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "⚠️ **Uso del comando non valido!**\n"
                "Usa il formato: `/remind [tempo] [messaggio]`\n"
                "Esempi:\n"
                "• `/remind 30m Fai una pausa`\n"
                "• `/remind 2h Riunione`\n"
                "• `/remind 10d Scadenza`", 
                parse_mode="Markdown"
            )
            return
        
        time_input = args[0].lower()
        reminder_text = " ".join(args[1:])
        chat_id = update.effective_chat.id
        
        match = re.match(r"^(\d+(?:\.\d+)?)([mhd])$", time_input)
        
        if not match:
            try:
                delta = timedelta(minutes=float(time_input))
                time_desc = f"{time_input} minuti"
            except ValueError:
                await update.message.reply_text("⚠️ Formato del tempo non valido. Usa ad esempio `30m`, `2h` o `10d`.")
                return
        else:
            value, unit = match.groups()
            value = float(value)
            
            if unit == 'm':
                delta = timedelta(minutes=value)
                time_desc = f"{value} minuti"
            elif unit == 'h':
                delta = timedelta(hours=value)
                time_desc = f"{value} ore"
            elif unit == 'd':
                delta = timedelta(days=value)
                time_desc = f"{value} giorni"
        
        run_time = datetime.now() + delta
        
        # Salva il promemoria nel database SQLite
        conn = sqlite3.connect("reminders.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reminders (chat_id, reminder_text, run_time) VALUES (?, ?, ?)", 
                       (chat_id, reminder_text, run_time))
        conn.commit()
        conn.close()
        
        # Programma l'esecuzione con APScheduler
        scheduler.add_job(trigger_reminder, 'date', run_date=run_time, args=[chat_id, reminder_text, context.bot])
        
        await update.message.reply_text(f"⏱️ Promemoria impostato con successo! Ti ricorderò di farlo tra {time_desc}.")
        
    except Exception as e:
        print(f"Errore promemoria: {e}")

# Funzione protetta che gestisce i messaggi e la cronologia dell'IA
async def handle_message(update, context):
    try:
        user_message = update.message.text
        if "history" not in context.user_data:
            context.user_data["history"] = []
        
        context.user_data["history"].append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model="cognitivecomputations/dolphin-mistral-24b-venice-edition",
            messages=context.user_data["history"]
        )
        
        bot_reply = response.choices[0].message.content
        context.user_data["history"].append({"role": "assistant", "content": bot_reply})
        
        await update.message.reply_text(bot_reply)
        
    except Exception as e:
        print(f"Errore catturato: {e}")
        await update.message.reply_text("⚠️ C'è stato un piccolo intoppo temporaneo nella comunicazione con l'IA. Riprova tra un attimo!")

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    import threading
    
    # Inizializza lo scheduler in background
    scheduler = BackgroundScheduler()
    scheduler.start()
    
    # Avvia Flask in un thread separato
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    # Avvia il bot di Telegram
    application = ApplicationBuilder().token(os.environ.get("TELEGRAM_TOKEN")).build()
    
    application.add_handler(CommandHandler("remind", remind_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot avviato con successo!")
    application.run_polling(drop_pending_updates=True)
