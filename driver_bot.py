import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variable
DRIVER_BOT_TOKEN = os.getenv("DRIVER_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command for drivers"""
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"🚕 Welcome to Driver Bot!\n\n"
        f"Your Chat ID: {chat_id}\n\n"
        f"Send this Chat ID to the administrator to start receiving orders.\n\n"
        f"You will receive new orders automatically in this chat."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    await update.message.reply_text(
        "🚕 Driver Bot Help\n\n"
        "This bot receives taxi orders automatically.\n\n"
        "When a passenger places an order, you will receive:\n"
        "• Customer name and phone\n"
        "• Pickup and drop-off locations\n"
        "• Waze navigation link\n"
        "• Customer’s Telegram username for contact\n\n"
        "Contact customers directly through Telegram to confirm the ride."
    )

def main():
    """Start the driver bot"""
    if not DRIVER_BOT_TOKEN:
        logger.error("DRIVER_BOT_TOKEN not set. Exiting.")
        return

    application = Application.builder().token(DRIVER_BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Start the bot
    logger.info("Driver bot started...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
