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

# Language buttons
LANG_UK = "🇺🇦 Українська"
LANG_EN = "🇬🇧 English"

# Environment variables
PASSENGER_BOT_TOKEN = os.getenv("PASSENGER_BOT_TOKEN")
DRIVER_BOT_TOKEN = os.getenv("DRIVER_BOT_TOKEN")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "itsbarhit")

# Driver storage
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DRIVER_STORE_FILE = os.path.join(BASE_DIR, "drivers.json")


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

# Simple translation dictionary for passenger-facing messages
TRANSLATIONS = {
    "en": {
        # Short welcome (no "select language" text)
        "welcome": "Welcome to AllNight Taxi! 🚕",
        "order_button": "🚖 Order Taxi",
        "ask_name": "Please enter your name:",
        "share_phone_prompt": "Please share your phone number:\n(You can share your contact or type the number manually)",
        "send_pickup_prompt": "Please send your pickup location:\n(You can send your current location or type the address)",
        "ask_dropoff": "Please enter the drop-off address:",
        "order_summary_title": "📋 Order Summary:\n\n",
        "name_label": "👤 Name",
        "phone_label": "📱 Phone",
        "pickup_label": "📍 Pickup",
        "dropoff_label": "🏁 Drop-off",
        "comment_label": "💬 Comment",
        "waze_label": "🔗 Waze Navigation",
        # final confirmation (user requested replacement)
        "order_accepted": "✅Your order has been accepted, the driver will contact you soon",
        # short label shown with start button after order (avoid duplicating the confirmation text)
        "start_again": "Press the button to order again.",
        # button texts
        "share_contact_button": "📱 Share Contact",
        "send_location_button": "📍 Send Current Location",
        "confirm_button": "✅ Confirm Order",
        "add_comment_button": "💬 Add Comment",
        "contact_username": "💬 Contact customer: @{username}",
        "contact_phone": "💬 Contact customer by phone: {phone}",
        "no_drivers_admin": "⚠️ New order from {customer} but no drivers are registered. Please add drivers using /add_driver CHAT_ID.",
        "no_drivers_passenger": "⚠️ No drivers are currently registered. The admin has been notified.",
        "add_comment_prompt": "Please enter your comment:",
        "order_delivery_failed": "⚠️ ORDER DELIVERY FAILED\n\nCustomer: {customer}\nFailed to deliver to {count} driver(s)",
        "cancelled": "Order cancelled. Press the button to start a new order.",
        "not_authorized": "⛔ You are not authorized to use this command.",
        "add_driver_usage": "Usage: /add_driver CHAT_ID",
        "remove_driver_usage": "Usage: /remove_driver CHAT_ID",
        "invalid_chat_id": "❌ Invalid chat ID. Please provide a numeric chat ID.",
        "driver_added": "✅ Driver {chat_id} added successfully!\nTotal drivers: {count}",
        "driver_exists": "⚠️ Driver {chat_id} already exists!",
        "driver_removed": "✅ Driver {chat_id} removed successfully!\nTotal drivers: {count}",
        "driver_not_found": "⚠️ Driver {chat_id} not found!",
        "no_drivers_registered": "📋 No drivers registered yet.",
        "drivers_list": "📋 Registered Drivers ({count}):\n\n{list}",
    },
    "uk": {
        # Short welcome (matches the /start used text)
        "welcome": "Ласкаво просимо до сервісу AllNight Taxi! 🚕",
        "order_button": "🚖 Замовити таксі",
        "ask_name": "Введіть ваше ім'я:",
        "share_phone_prompt": "Будь ласка, надішліть номер телефону:\n(Ви можете поділитися контактом або ввести номер вручну)",
        "send_pickup_prompt": "Будь ласка, надішліть місце посадки:\n(Ви можете надіслати поточне місцезнаходження або ввести адресу)",
        "ask_dropoff": "Введіть адресу призначення:",
        "order_summary_title": "📋 Підсумок замовлення:\n\n",
        "name_label": "👤 Ім'я",
        "phone_label": "📱 Телефон",
        "pickup_label": "📍 Місце посадки",
        "dropoff_label": "🏁 Місце призначення",
        "comment_label": "💬 Коментар",
        "waze_label": "🔗 Waze Навігація",
        "order_accepted": "✅ Ваше замовлення прийнято, очікуйте дзвінка від водія.",
        "start_again": "Натисніть кнопку, щоб замовити знову.",
        # button texts (localized)
        "share_contact_button": "📱 Надіслати контакт",
        "send_location_button": "📍 Надіслати місцезнаходження",
        "confirm_button": "✅ Підтвердити замовлення",
        "add_comment_button": "💬 Додати коментар",
        "contact_username": "💬 Контактувати з клієнтом: @{username}",
        "contact_phone": "💬 Контактувати з клієнтом по телефону: {phone}",
        "no_drivers_admin": "⚠️ Нове замовлення від {customer}, але водії не зареєстровані. Додайте водіїв за допомогою /add_driver CHAT_ID.",
        "no_drivers_passenger": "⚠️ Наразі немає зареєстрованих водіїв. Адміністратор повідомлений.",
        "add_comment_prompt": "Будь ласка, введіть ваш коментар:",
        "order_delivery_failed": "⚠️ ДОСТАВКА ЗАМОВЛЕННЯ НЕ УДАЛАСЯ\n\nКлієнт: {customer}\nНе вдалося доставити {count} водію(ям)",
        "cancelled": "Замовлення скасовано. Натисніть кнопку щоб почати нове замовлення.",
        "not_authorized": "⛔ У вас немає доступу до цієї команди.",
        "add_driver_usage": "Використання: /add_driver CHAT_ID",
        "remove_driver_usage": "Використання: /remove_driver CHAT_ID",
        "invalid_chat_id": "❌ Невірний chat ID. Будь ласка, вкажіть числовий chat ID.",
        "driver_added": "✅ Водій {chat_id} успішно доданий!\nЗагалом водіїв: {count}",
        "driver_exists": "⚠️ Водій {chat_id} вже існує!",
        "driver_removed": "✅ Водій {chat_id} успішно видалений!\nЗагалом водіїв: {count}",
        "driver_not_found": "⚠��� Водій {chat_id} не знайдений!",
        "no_drivers_registered": "📋 Немає зареєстрованих водіїв.",
        "drivers_list": "📋 Зареєстровані водії ({count}):\n\n{list}",
    },
}


def tr(context: ContextTypes.DEFAULT_TYPE, key: str, **kwargs) -> str:
    """Translate by user's selected language, fallback to English."""
    lang = context.user_data.get("lang", "en")
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, TRANSLATIONS["en"].get(key, ""))
    try:
        return text.format(**kwargs)
    except Exception:
        return text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - ask for language selection first"""
    keyboard = [[KeyboardButton(LANG_UK), KeyboardButton(LANG_EN)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    # Show the requested Ukrainian-only initial message (no "select language" text)
    await update.message.reply_text("Ласкаво просимо до сервісу AllNight Taxi! 🚕", reply_markup=reply_markup)
    return ConversationHandler.END


async def language_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection.

    - If user selects Ukrainian, immediately start the ordering flow (ask for name).
      This avoids the duplicated greeting (we already showed Ukrainian on /start).
    - If user selects English, show the short localized welcome and the localized Order button.
    """
    text = update.message.text
    if text == LANG_UK:
        # User selected Ukrainian: set language and immediately start ordering
        context.user_data["lang"] = "uk"
        # Proceed directly to the order flow (ask for name)
        return await order_taxi(update, context)
    elif text == LANG_EN:
        # User selected English: set language and show localized welcome + order button
        context.user_data["lang"] = "en"
        order_btn = tr(context, "order_button")
        keyboard = [[KeyboardButton(order_btn)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(tr(context, "welcome"), reply_markup=reply_markup)
        return ConversationHandler.END
    else:
        # unknown input: treat as english and show order button
        context.user_data["lang"] = "en"
        order_btn = tr(context, "order_button")
        keyboard = [[KeyboardButton(order_btn)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(tr(context, "welcome"), reply_markup=reply_markup)
        return ConversationHandler.END


async def order_taxi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the order process"""
    # ensure language is set; if not, default to english
    if "lang" not in context.user_data:
        context.user_data["lang"] = "en"

    await update.message.reply_text(tr(context, "ask_name"), reply_markup=ReplyKeyboardRemove())
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store name and ask for phone"""
    context.user_data["name"] = update.message.text

    # Keyboard with share contact button (localized label)
    contact_label = tr(context, "share_contact_button")
    keyboard = [[KeyboardButton(contact_label, request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(tr(context, "share_phone_prompt"), reply_markup=reply_markup)
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store phone and ask for pickup location"""
    if update.message.contact:
        context.user_data["phone"] = update.message.contact.phone_number
    else:
        context.user_data["phone"] = update.message.text

    # Keyboard with location button (localized label)
    location_label = tr(context, "send_location_button")
    keyboard = [[KeyboardButton(location_label, request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(tr(context, "send_pickup_prompt"), reply_markup=reply_markup)
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

    await update.message.reply_text(tr(context, "ask_dropoff"), reply_markup=ReplyKeyboardRemove())
    return DROPOFF


async def get_dropoff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store dropoff and show confirmation"""
    context.user_data["dropoff"] = update.message.text
    context.user_data["comment"] = ""

    # Show summary with confirm and add comment buttons (localized labels)
    summary = (
        f"{tr(context, 'order_summary_title')}"
        f"{tr(context, 'name_label')}: {context.user_data['name']}\n"
        f"{tr(context, 'phone_label')}: {context.user_data['phone']}\n"
        f"{tr(context, 'pickup_label')}: {context.user_data['pickup']}\n"
        f"{tr(context, 'dropoff_label')}: {context.user_data['dropoff']}\n"
    )

    keyboard = [
        [InlineKeyboardButton(tr(context, "confirm_button"), callback_data="confirm")],
        [InlineKeyboardButton(tr(context, "add_comment_button"), callback_data="add_comment")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(summary, reply_markup=reply_markup)
    return CONFIRM


async def add_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for comment"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(tr(context, "add_comment_prompt"))
    context.user_data["waiting_for_comment"] = True
    return CONFIRM


async def receive_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive comment and show updated summary"""
    if context.user_data.get("waiting_for_comment"):
        context.user_data["comment"] = update.message.text
        context.user_data["waiting_for_comment"] = False

        # Show updated summary
        summary = (
            f"{tr(context, 'order_summary_title')}"
            f"{tr(context, 'name_label')}: {context.user_data['name']}\n"
            f"{tr(context, 'phone_label')}: {context.user_data['phone']}\n"
            f"{tr(context, 'pickup_label')}: {context.user_data['pickup']}\n"
            f"{tr(context, 'dropoff_label')}: {context.user_data['dropoff']}\n"
            f"{tr(context, 'comment_label')}: {context.user_data['comment']}\n"
        )

        keyboard = [[InlineKeyboardButton(tr(context, "confirm_button"), callback_data="confirm")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(summary, reply_markup=reply_markup)
    return CONFIRM


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send order to drivers"""
    query = update.callback_query
    await query.answer()

    # Prepare order message for drivers (use customer's selected language where possible)
    customer_username = update.effective_user.username
    customer_name = context.user_data.get("name", "Unknown")

    order_lines = [
        "🚖 NEW ORDER",
        "",
        f"{tr(context, 'name_label')}: {context.user_data.get('name','')}",
        f"{tr(context, 'phone_label')}: {context.user_data.get('phone','')}",
        f"{tr(context, 'pickup_label')}: {context.user_data.get('pickup','')}",
        f"{tr(context, 'dropoff_label')}: {context.user_data.get('dropoff','')}",
    ]
    if context.user_data.get("comment"):
        order_lines.append(f"{tr(context, 'comment_label')}: {context.user_data['comment']}")

    order_lines.append("")  # spacer
    order_lines.append(f"{tr(context, 'waze_label')}: {context.user_data.get('waze_link','')}")

    # Contact line: prefer username, fall back to phone
    if customer_username:
        order_lines.append(f"{tr(context, 'contact_username', username=customer_username)}")
    else:
        phone = context.user_data.get("phone", "(no phone)")
        order_lines.append(tr(context, "contact_phone", phone=phone))

    order_message = "\n".join(order_lines)

    # If no drivers are registered, notify admin and the passenger
    if not driver_chat_ids:
        admin_chat = context.bot_data.get("admin_chat_id")
        if admin_chat:
            try:
                await context.bot.send_message(
                    chat_id=admin_chat,
                    text=tr(context, "no_drivers_admin", customer=customer_name),
                )
            except Exception as e:
                logger.error(f"Failed to notify admin about missing drivers: {e}")
        # preserve language, clear other user data, and show short prompt + start button
        lang = context.user_data.get("lang", "en")
        context.user_data.clear()
        context.user_data["lang"] = lang

        order_btn = tr(context, "order_button")
        keyboard = [[KeyboardButton(order_btn)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await query.edit_message_text(tr(context, "no_drivers_passenger"))
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=tr(context, "start_again"), reply_markup=reply_markup
        )
        return ConversationHandler.END

    # Send to all drivers
    if not DRIVER_BOT_TOKEN:
        logger.error("DRIVER_BOT_TOKEN not set. Cannot forward order to drivers.")
    driver_bot = Bot(token=DRIVER_BOT_TOKEN) if DRIVER_BOT_TOKEN else context.bot

    failed_deliveries = []
    logger.info(f"Attempting to deliver order to drivers: {driver_chat_ids}")
    for driver_id in driver_chat_ids:
        try:
            await driver_bot.send_message(chat_id=driver_id, text=order_message)
            logger.info(f"Order sent to driver {driver_id}")
        except Exception as e:
            logger.error(f"Failed to send to driver {driver_id}: {e}")
            failed_deliveries.append(driver_id)

    # Notify admin if any failures
    if failed_deliveries:
        try:
            admin_message = tr(
                context, "order_delivery_failed", customer=(customer_username or customer_name), count=len(failed_deliveries)
            )
            if "admin_chat_id" in context.bot_data:
                await context.bot.send_message(chat_id=context.bot_data["admin_chat_id"], text=admin_message)
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")

    # preserve language so start_again is shown in the same language
    lang = context.user_data.get("lang", "en")
    # Send only one final confirmation text (edited inline message) to avoid duplication
    await query.edit_message_text(TRANSLATIONS.get(lang, TRANSLATIONS["en"])["order_accepted"])

    # Clear user data but keep language
    context.user_data.clear()
    context.user_data["lang"] = lang

    # Show start button again with a short prompt (no duplicate confirmation) in user's language
    order_btn = tr(context, "order_button")
    keyboard = [[KeyboardButton(order_btn)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=tr(context, "start_again"), reply_markup=reply_markup)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation"""
    # preserve language when cancelling
    lang = context.user_data.get("lang", "en")
    context.user_data.clear()
    context.user_data["lang"] = lang

    order_btn = tr(context, "order_button")
    keyboard = [[KeyboardButton(order_btn)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(tr(context, "cancelled"), reply_markup=reply_markup)
    return ConversationHandler.END


# Admin commands (kept in default/english messages handled via tr where appropriate)
async def add_driver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add driver chat ID (admin only)"""
    if update.effective_user.username != ADMIN_USERNAME:
        await update.message.reply_text(TRANSLATIONS["en"]["not_authorized"])
        return

    # Store admin chat ID for notifications
    context.bot_data["admin_chat_id"] = update.effective_chat.id

    if not context.args or len(context.args) != 1:
        await update.message.reply_text(TRANSLATIONS["en"]["add_driver_usage"])
        return

    try:
        chat_id = int(context.args[0])
        if chat_id not in driver_chat_ids:
            driver_chat_ids.append(chat_id)
            save_driver_ids(driver_chat_ids)
            await update.message.reply_text(
                TRANSLATIONS["en"]["driver_added"].format(chat_id=chat_id, count=len(driver_chat_ids))
            )
        else:
            await update.message.reply_text(TRANSLATIONS["en"]["driver_exists"].format(chat_id=chat_id))
    except ValueError:
        await update.message.reply_text(TRANSLATIONS["en"]["invalid_chat_id"])


async def remove_driver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove driver chat ID (admin only)"""
    if update.effective_user.username != ADMIN_USERNAME:
        await update.message.reply_text(TRANSLATIONS["en"]["not_authorized"])
        return

    if not context.args or len(context.args) != 1:
        await update.message.reply_text(TRANSLATIONS["en"]["remove_driver_usage"])
        return

    try:
        chat_id = int(context.args[0])
        if chat_id in driver_chat_ids:
            driver_chat_ids.remove(chat_id)
            save_driver_ids(driver_chat_ids)
            await update.message.reply_text(
                TRANSLATIONS["en"]["driver_removed"].format(chat_id=chat_id, count=len(driver_chat_ids))
            )
        else:
            await update.message.reply_text(TRANSLATIONS["en"]["driver_not_found"].format(chat_id=chat_id))
    except ValueError:
        await update.message.reply_text(TRANSLATIONS["en"]["invalid_chat_id"])


async def list_drivers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all drivers (admin only)"""
    if update.effective_user.username != ADMIN_USERNAME:
        await update.message.reply_text(TRANSLATIONS["en"]["not_authorized"])
        return

    if not driver_chat_ids:
        await update.message.reply_text(TRANSLATIONS["en"]["no_drivers_registered"])
    else:
        drivers_list = "\n".join([f"• {chat_id}" for chat_id in driver_chat_ids])
        await update.message.reply_text(TRANSLATIONS["en"]["drivers_list"].format(count=len(driver_chat_ids), list=drivers_list))


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
            # language selection (flag buttons)
            MessageHandler(filters.Regex(f"^{LANG_UK}$") | filters.Regex(f"^{LANG_EN}$"), language_select),
            # order buttons (both languages)
            MessageHandler(filters.Regex(r"^🚖 Order Taxi$") | filters.Regex(r"^🚖 Замовити таксі$"), order_taxi),
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
