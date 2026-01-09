# Telegram Taxi Service Bots

Two Telegram bots for managing a taxi service: one for passengers to place orders, and one for drivers to receive them.

## 🚀 Features

### Passenger Bot

- Order taxi with simple conversation flow
- Enter name, phone, pickup location, and drop-off address
- Option to share current location or type address manually
- Option to share contact or type phone manually
- Add optional comment to orders
- Order confirmation before sending

### Driver Bot

- Automatically receive all new orders
- Get customer details with Waze navigation link
- Direct Telegram contact with customers
- Support for up to 4 drivers

### Admin Features

- Add/remove drivers dynamically
- Get notifications if order delivery fails
- List all registered drivers

## 📋 Prerequisites

1. Two Telegram bot tokens from [@BotFather](https://t.me/BotFather)
1. Railway account
1. GitHub account

## 🔧 Setup Instructions

### 1. Create Your Bots

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
1. Create passenger bot:
- Send `/newbot`
- Choose name (e.g., “My Taxi Service”)
- Choose username (e.g., “mytaxi_passenger_bot”)
- **Save the token** - you’ll need it later
1. Create driver bot:
- Send `/newbot` again
- Choose name (e.g., “My Taxi Drivers”)
- Choose username (e.g., “mytaxi_driver_bot”)
- **Save this token** too

### 2. Setup GitHub Repository

1. Create a new repository on GitHub
1. Clone this repository to your computer
1. Add these files to your repository:
- `passenger_bot.py`
- `driver_bot.py`
- `requirements.txt`
- `Procfile`
- `runtime.txt`
1. Commit and push to GitHub

### 3. Deploy to Railway

1. Go to [Railway.app](https://railway.app) and sign in
1. Click “New Project” → “Deploy from GitHub repo”
1. Select your repository
1. Add environment variables in Railway dashboard:
- `PASSENGER_BOT_TOKEN` = your passenger bot token
- `DRIVER_BOT_TOKEN` = your driver bot token
- `ADMIN_USERNAME` = itsbarhit (your Telegram username without @)
1. Railway will automatically deploy both bots

### 4. Get Driver Chat IDs

1. Each driver opens the **driver bot** in Telegram
1. Driver sends `/start` to the bot
1. Bot will reply with their Chat ID (e.g., `123456789`)
1. Driver sends this Chat ID to you

### 5. Register Drivers

1. Open the **passenger bot** in Telegram (as admin @itsbarhit)
1. Add each driver with command:
   
   ```
   /add_driver 123456789
   ```
   
   Replace `123456789` with actual driver Chat ID
1. Verify with `/list_drivers`

## 📱 Usage

### For Passengers

1. Open passenger bot
1. Press “🚖 Order Taxi”
1. Follow the prompts:
- Enter name
- Share phone or type manually
- Send location or type pickup address
- Type drop-off address
1. Review order summary
1. Optionally add comment
1. Press “✅ Confirm Order”
1. Wait for driver’s call

### For Drivers

1. Keep driver bot open
1. Receive orders automatically
1. Contact customer via their Telegram username
1. Use Waze link for navigation

### For Admin (@itsbarhit)

**Add driver:**

```
/add_driver CHAT_ID
```

**Remove driver:**

```
/remove_driver CHAT_ID
```

**List all drivers:**

```
/list_drivers
```

## 🔍 How to Find Chat IDs

**For drivers:**

- Open driver bot
- Send `/start`
- Bot displays the Chat ID

**For admin (you):**

- Open passenger bot
- Send `/start`
- Your Chat ID will be used for error notifications

## ⚠️ Important Notes

- Orders are NOT saved permanently (in-memory only)
- If bots restart, all data is lost
- Driver list resets on restart (re-add drivers with `/add_driver`)
- Maximum 4 drivers supported
- Admin must use username @itsbarhit
- Both bots must run simultaneously on Railway

## 🐛 Troubleshooting

**Bot doesn’t respond:**

- Check if Railway deployment is running
- Verify environment variables are set correctly
- Check Railway logs for errors

**Driver not receiving orders:**

- Verify driver Chat ID is added with `/list_drivers`
- Make sure driver has started the driver bot
- Check if driver blocked the bot

**Waze link doesn’t work:**

- Make sure Waze app is installed on driver’s phone
- Try clicking the link from mobile device

## 📞 Support

For issues or questions, contact admin @itsbarhit on Telegram.

## 📄 File Structure

```
taxi-bots/
├── passenger_bot.py      # Main passenger bot code
├── driver_bot.py         # Main driver bot code
├── requirements.txt      # Python dependencies
├── Procfile             # Railway process configuration
├── runtime.txt          # Python version
└── README.md            # This file
```

## 🔄 Updates

To update the bots:

1. Modify code in your GitHub repository
1. Commit and push changes
1. Railway automatically redeploys

-----

Made with ❤️ for taxi service management
