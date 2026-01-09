import os
import json
import logging
from typing import List
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
    Bot,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for conversation
NAME, PHONE, PICKUP, DROPOFF, CONFIRM = range(5)

# Environment variables
PASSENGER_BOT_TOKEN = os.getenv("PASSENGER_BOT_TOKEN")
DRIVER_BOT_TOKEN = os.getenv("DRIVER_BOT_TOKEN")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "itsbarhit")

# Driver storage
DRIVER_STORE_FILE = "drivers.json"


def load_driver_ids() -> List[int]:
    try:
        if os.path.exists(DRIVER_STORE_FILE):
            with open(DRIVER_STORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return [int(x) for x in data]
    except Exception as e:
        logger.error(f"Failed to load driver ids from {DRIVER_STORE_FILE}: {e}")
    return []


def save_driver_ids(ids: List[int]) -> None:
    try:
        with open(DRIVER_STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(ids, f)
    except Exception as e:
        logger.error(f"Failed to save driver ids to {DRIVER_STORE_FILE}: {e}")


# Storage for driver chat IDs (persistent)
driver_chat_ids = load_driver_ids()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - show welcome message with order button"""
    keyboard = [[KeyboardButton("🚖 Order Taxi")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "Welcome to our Taxi Service! 🚕\n\n"
        "Press the button below to order a taxi.",
        reply_markup=reply_markup,
    )
    return ConversationHandler.END


async def order_taxi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the order process"""
    await update.message.reply_text(
        "Please enter your name:", reply_markup=ReplyKeyboardRemove()
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store name and ask for phone"""
    context.user_data["name"] = update.message.text

    # Keyboard with share contact button
    keyboard = [[KeyboardButton("📱 Share Contact", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "Please share your phone number:\n"
        "(You can share your contact or type the number manually)",
        reply_markup=reply_markup,
    )
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store phone and ask for pickup location"""
    if update.message.contact:
        context.user_data["phone"] = update.message.contact.phone_number
    else:
        context.user_data["phone"] = update.message.text

    # Keyboard with location button
    keyboard = [[KeyboardButton("📍 Send Current Location", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "Please send your pickup location:\n"
        "(You can send your current location or type the address)",
        reply_markup=reply_markup,
    )
    return PICKUP


async def get_pickup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store pickup location and ask for dropoff"""
    if update.message.location:
        lat = update.message.location.latitude
        lon = update.message.location.longitude
        context.user_data["pickup"] = f"📍 Location: {lat}, {lon}"
        context.user_data["pickup_coords"] = (lat, lon)
        context.user_data["waze_link"] = f"https://waze.com/ul?ll={lat},{lon}&navigate=yes"
    else:
        context.user_data["pickup"] = update.message.text
        context.user_data["pickup_coords"] = None
        # Create Waze link with address
        address = update.message.text.replace(" ", "%20")
        context.user_data["waze_link"] = f"https://waze.com/ul?q={address}&navigate=yes"

    await update.message.reply_text(
        "Please enter the drop-off address:", reply_markup=ReplyKeyboardRemove()
    )
    return DROPOFF


async def get_dropoff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store dropoff and show confirmation"""
    context.user_data["dropoff"] = update.message.text
    context.user_data["comment"] = ""

    # Show summary with confirm and add comment buttons
    summary = (
        f"📋 Order Summary:\n\n"
        f"👤 Name: {context.user_data['name']}\n"
        f"📱 Phone: {context.user_data['phone']}\n"
        f"📍 Pickup: {context.user_data['pickup']}\n"
        f"🏁 Drop-off: {context.user_data['dropoff']}\n"
    )

    keyboard = [
        [InlineKeyboardButton("✅ Confirm Order", callback_data="confirm")],
        [InlineKeyboardButton("💬 Add Comment", callback_data="add_comment")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(summary, reply_markup=reply_markup)
    return CONFIRM


async def add_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for comment"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Please enter your comment:")
    context.user_data["waiting_for_comment"] = True
    return CONFIRM


async def receive_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive comment and show updated summary"""
    if context.user_data.get("waiting_for_comment"):
        context.user_data["comment"] = update.message.text
        context.user_data["waiting_for_comment"] = False

        # Show updated summary
        summary = (
            f"📋 Order Summary:\n\n"
            f"👤 Name: {context.user_data['name']}\n"
            f"📱 Phone: {context.user_data['phone']}\n"
            f"📍 Pickup: {context.user_data['pickup']}\n"
            f"🏁 Drop-off: {context.user_data['dropoff']}\n"
            f"💬 Comment: {context.user_data['comment']}\n"
        )

        keyboard = [[InlineKeyboardButton("✅ Confirm Order", callback_data="confirm")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(summary, reply_markup=reply_markup)
    return CONFIRM


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send order to drivers"""
    query = update.callback_query
    await query.answer()

    # Prepare order message for drivers
    customer_username = update.effective_user.username
    customer_name = context.user_data.get("name", "Unknown")

    order_lines = [
        "🚖 NEW ORDER",
        "",
        f"👤 Name: {context.user_data.get('name','')}",
        f"📱 Phone: {context.user_data.get('phone','')}",
        f"📍 Pickup: {context.user_data.get('pickup','')}",
        f"🏁 Drop-off: {context.user_data.get('dropoff','')}",
    ]
    if context.user_data.get("comment"):
        order_lines.append(f"💬 Comment: {context.user_data['comment']}")

    order_lines.append("")  # spacer
    order_lines.append(f"🔗 Waze Navigation: {context.user_data.get('waze_link','')}")

    # Contact line: prefer username, fall back to phone
    if customer_username:
        order_lines.append(f"💬 Contact customer: @{customer_username}")
    else:
        phone = context.user_data.get("phone", "(no phone)")
        order_lines.append(f"💬 Contact customer by phone: {phone}")

    order_message = "\n".join(order_lines)

    # If no drivers are registered, notify admin and the passenger
    if not driver_chat_ids:
        admin_chat = context.bot_data.get("admin_chat_id")
        if admin_chat:
            await context.bot.send_message(
                chat_id=admin_chat,
                text=(
                    f"⚠️ New order from {customer_name} but no drivers are registered. "
                    "Please add drivers using /add_driver CHAT_ID."
                ),
            )
        await query.edit_message_text("⚠️ No drivers are currently registered. The admin has been notified.")
        context.user_data.clear()
        # Show start button again
        keyboard = [[KeyboardButton("🚖 Order Taxi")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Thank you for using our service!", reply_markup=reply_markup
        )
        return ConversationHandler.END

    # Send to all drivers
    if not DRIVER_BOT_TOKEN:
        logger.error("DRIVER_BOT_TOKEN not set. Cannot forward order to drivers.")
    driver_bot = Bot(token=DRIVER_BOT_TOKEN) if DRIVER_BOT_TOKEN else context.bot

    failed_deliveries = []
    for driver_id in driver_chat_ids:
        try:
            await driver_bot.send_message(chat_id=driver_id, text=order_message)
        except Exception as e:
            logger.error(f"Failed to send to driver {driver_id}: {e}")
            failed_deliveries.append(driver_id)

    # Notify admin if any failures
    if failed_deliveries:
        try:
            admin_message = (
                f"⚠️ ORDER DELIVERY FAILED\n\n"
                f"Customer: @{customer_username or customer_name}\n"
                f"Failed to deliver to {len(failed_deliveries)} driver(s)"
            )
            if "admin_chat_id" in context.bot_data:
                await context.bot.send_message(
                    chat_id=context.bot_data["admin_chat_id"], text=admin_message
                )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")

    # Always confirm to passenger
    await query.edit_message_text("✅ Your order has been accepted, wait for a call from the driver.")

    # Clear user data
    context.user_data.clear()

    # Show start button again
    keyboard = [[KeyboardButton("🚖 Order Taxi")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Thank you for using our service!", reply_markup=reply_markup
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation"""
    context.user_data.clear()

    keyboard = [[KeyboardButton("🚖 Order Taxi")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Order cancelled. Press the button to start a new order.", reply_markup=reply_markup
    )
    return ConversationHandler.END


# Admin commands
async def add_driver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add driver chat ID (admin only)"""
    if update.effective_user.username != ADMIN_USERNAME:
        await update.message.reply_text("⛔ You are not authorized to use this command.")
        return

    # Store admin chat ID for notifications
    context.bot_data["admin_chat_id"] = update.effective_chat.id

    if not context.args or len(context.args) != 1:
        await update.message.reply_text("Usage: /add_driver CHAT_ID")
        return

    try:
        chat_id = int(context.args[0])
        if chat_id not in driver_chat_ids:
            driver_chat_ids.append(chat_id)
            save_driver_ids(driver_chat_ids)
            await update.message.reply_text(
                f"✅ Driver {chat_id} added successfully!\nTotal drivers: {len(driver_chat_ids)}"
            )
        else:
            await update.message.reply_text(f"⚠️ Driver {chat_id} already exists!")
    except ValueError:
        await update.message.reply_text("❌ Invalid chat ID. Please provide a numeric chat ID.")


async def remove_driver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove driver chat ID (admin only)"""
    if update.effective_user.username != ADMIN_USERNAME:
        await update.message.reply_text("⛔ You are not authorized to use this command.")
        return

    if not context.args or len(context.args) != 1:
        await update.message.reply_text("Usage: /remove_driver CHAT_ID")
        return

    try:
        chat_id = int(context.args[0])
        if chat_id in driver_chat_ids:
            driver_chat_ids.remove(chat_id)
            save_driver_ids(driver_chat_ids)
            await update.message.reply_text(
                f"✅ Driver {chat_id} removed successfully!\nTotal drivers: {len(driver_chat_ids)}"
            )
        else:
            await update.message.reply_text(f"⚠️ Driver {chat_id} not found!")
    except ValueError:
        await update.message.reply_text("❌ Invalid chat ID. Please provide a numeric chat ID.")


async def list_drivers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all drivers (admin only)"""
    if update.effective_user.username != ADMIN_USERNAME:
        await update.message.reply_text("⛔ You are not authorized to use this command.")
        return

    if not driver_chat_ids:
        await update.message.reply_text("📋 No drivers registered yet.")
    else:
        drivers_list = "\n".join([f"• {chat_id}" for chat_id in driver_chat_ids])
        await update.message.reply_text(f"📋 Registered Drivers ({len(driver_chat_ids)}):\n\n{drivers_list}")


def main():
    """Start the bot"""
    if not PASSENGER_BOT_TOKEN:
        logger.error("PASSENGER_BOT_TOKEN not set. Exiting.")
        return
    # DRIVER_BOT_TOKEN is optional: if missing we attempt to send via passenger bot API object
    application = Application.builder().token(PASSENGER_BOT_TOKEN).build()

    # Conversation handler for ordering
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^🚖 Order Taxi$"), order_taxi),
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [
                MessageHandler(filters.CONTACT, get_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone),
            ],
            PICKUP: [
                MessageHandler(filters.LOCATION, get_pickup),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_pickup),
            ],
            DROPOFF: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dropoff)],
            CONFIRM: [
                CallbackQueryHandler(add_comment, pattern="^add_comment$"),
                CallbackQueryHandler(confirm_order, pattern="^confirm$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_comment),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Admin commands
    application.add_handler(CommandHandler("add_driver", add_driver))
    application.add_handler(CommandHandler("remove_driver", remove_driver))
    application.add_handler(CommandHandler("list_drivers", list_drivers))

    # Start the bot
    logger.info("Passenger bot started...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
