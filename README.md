---
title: DeenCommerce Telegram Bot
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8000
pinned: false
---

# DeenCommerce Telegram Bot

A simple Telegram bot for your WooCommerce store that allows customers to:
- ✅ Browse products and check stock
- ✅ Search for products
- ✅ View their existing orders

**Features:**
- No database required
- Direct integration with WooCommerce REST API
- Real-time product and order data
- Support for Bangla text (৳ Taka currency)

---

## Setup Instructions

### Step 1: Create Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/botfather)
2. Type `/newbot` and follow the prompts
3. You'll receive a **Bot Token** (save this)
4. Example: `123456789:ABCDEFGHijklmnopqrstuvwxyz`

### Step 2: Get WooCommerce API Keys

1. Go to your WordPress Admin: `https://deencommerce.com/wp-admin`
2. Navigate to: **WooCommerce** → **Settings** → **Advanced** → **REST API**
3. Click **Create an API key**
4. Set Permissions to **Read** (minimum)
5. Copy **Consumer Key** and **Consumer Secret**

### Step 3: Configure Environment

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
   WOOCOMMERCE_URL=https://deencommerce.com
   WOOCOMMERCE_KEY=your_consumer_key
   WOOCOMMERCE_SECRET=your_consumer_secret
   ```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Run Locally (Testing)

```bash
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 6: Deploy to Production

#### Option A: Railway (Recommended)
1. Push to GitHub
2. Go to [railway.app](https://railway.app)
3. Connect GitHub repo
4. Add environment variables in Railway dashboard
5. Deploy automatically

#### Option B: Render
1. Go to [render.com](https://render.com)
2. Create new Web Service
3. Connect GitHub
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `uvicorn main:app --host 0.0.0.0`
6. Add environment variables

#### Option C: Your Own Server (VPS/Droplet)
```bash
# SSH into your server
ssh user@your_server_ip

# Clone repo
git clone your_repo_url
cd deen_telegram_bot

# Install Python dependencies
pip install -r requirements.txt

# Run with PM2 or systemd
pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name deen-bot
```

### Step 7: Set Telegram Webhook

After deployment, replace `YOUR_DOMAIN` with your actual domain:

```bash
curl -X POST "https://api.telegram.org/bot{YOUR_BOT_TOKEN}/setWebhook?url=https://YOUR_DOMAIN.com/telegram/webhook"
```

Example:
```bash
curl -X POST "https://api.telegram.org/bot123456789:ABCDEFGHijklmnopqrstuvwxyz/setWebhook?url=https://deen-bot.railway.app/telegram/webhook"
```

---

## Testing

1. Find your bot on Telegram (search for username you set with BotFather)
2. Start the bot: `/start`
3. Test features:
   - Click "Browse Products"
   - Click "Search" and type a product name
   - Click "My Orders" and enter your email

---

## Bot Features

### 📦 Browse Products
- Shows latest 5 products from WooCommerce
- Displays price in ৳ (Taka)
- Shows stock count
- Click to view full product details with image

### 🔍 Search
- Search products by keyword
- Enter any product name
- Results show price and stock

### 📦 My Orders
- Enter your customer email (from WooCommerce account)
- Shows all your orders
- Displays order status (Pending, Processing, Completed, etc.)
- Shows items and total price

---

## Troubleshooting

### Bot not responding
- Check Telegram webhook URL is correct
- Verify bot token in `.env`
- Check server logs for errors

### "No products found"
- Verify WooCommerce API key is correct
- Check WooCommerce REST API is enabled
- Ensure products are published

### "No orders found"
- Customer must enter exact email from WooCommerce account
- Email must be lowercase
- Customer must have at least one order

### WooCommerce API errors
1. Go to WooCommerce → Settings → Advanced
2. Regenerate API key
3. Update `.env` file

---

## File Structure

```
deen_telegram_bot/
├── main.py              # Main bot application
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── .env                # Your actual credentials (don't commit)
└── README.md           # This file
```

---

## Future Enhancements

Add later (step by step):
- Database (SQLite/PostgreSQL)
- Shopping cart
- Order placement
- Payment integration (bKash/Nagad)
- Shipping integration (Pathao)
- AI product recommendations

---

## Support

For issues or questions:
1. Check Telegram logs: `/telegram/webhook` responses
2. Verify WooCommerce REST API is working
3. Test API manually: `curl https://deencommerce.com/wp-json/wc/v3/products`

---

## Security Notes

⚠️ **Important:**
- Never commit `.env` file to GitHub
- Use `.gitignore`:
  ```
  .env
  __pycache__/
  *.pyc
  ```
- Keep your bot token and WooCommerce keys secret
- Consider using read-only API keys for bot

---

**Bot Version:** 1.0  
**Last Updated:** 2024
