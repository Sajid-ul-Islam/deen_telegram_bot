# Quick Deployment Guides

## Railway.app (Easiest)

### 1. Create GitHub Repo
```bash
git init
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Deploy on Railway
1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account
5. Select your `deen_telegram_bot` repo
6. Click "Deploy"

### 3. Add Environment Variables
1. In Railway dashboard, go to your project
2. Click "Variables"
3. Add these variables:
   - `TELEGRAM_BOT_TOKEN` = your bot token
   - `WOOCOMMERCE_URL` = your site URL
   - `WOOCOMMERCE_KEY` = your API key
   - `WOOCOMMERCE_SECRET` = your API secret

### 4. Get Your Domain
1. Go to "Settings"
2. Copy your Railway domain (e.g., `https://deen-bot-prod.railway.app`)

### 5. Set Telegram Webhook
```bash
curl -X POST "https://api.telegram.org/botYOUR_TOKEN/setWebhook?url=https://YOUR_RAILWAY_DOMAIN/telegram/webhook"
```

---

## Render.com

### 1. Push to GitHub (same as above)

### 2. Deploy on Render
1. Go to [render.com](https://render.com)
2. Click "New +"
3. Select "Web Service"
4. Connect GitHub
5. Select your repo
6. Fill in:
   - **Name**: `deen-telegram-bot`
   - **Region**: Singapore or Singapore (closest to Bangladesh)
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 8000`

### 3. Add Environment Variables
1. Scroll down to "Environment"
2. Add all 4 variables (same as Railway)

### 4. Create & Deploy
- Click "Create Web Service"
- Wait for deployment to complete
- Copy your domain from the Render dashboard

### 5. Set Telegram Webhook
```bash
curl -X POST "https://api.telegram.org/botYOUR_TOKEN/setWebhook?url=https://YOUR_RENDER_DOMAIN/telegram/webhook"
```

---

## Local Development

### Run Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Copy and edit .env
cp .env.example .env
# Edit .env with your credentials

# Run the bot
python main.py
```

Server will run at `http://localhost:8000`

**Note:** For local testing without webhook:
- Use `python-telegram-bot` polling instead of webhook
- Or use a tunneling tool like ngrok

---

## Verify Bot is Working

After setting webhook, test with:
```bash
# Check webhook status
curl "https://api.telegram.org/botYOUR_TOKEN/getWebhookInfo"

# Should return:
{
  "ok": true,
  "result": {
    "url": "https://your-domain/telegram/webhook",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "ip_address": "..."
  }
}
```

---

## Troubleshooting Deployment

### Bot not responding
1. Check webhook is set correctly
2. Check server logs for errors
3. Verify all environment variables are set

### 502 Bad Gateway
- Server might be starting, wait 30 seconds
- Check logs for Python errors
- Verify all environment variables are present

### "Connection refused"
- Bot server might be down
- Check Railway/Render dashboard
- Redeploy if necessary

---

## Update Bot Code

After making changes:
```bash
git add .
git commit -m "Update bot features"
git push origin main
```

Railway/Render will auto-redeploy within seconds.

---

## Environment Variables Checklist

Before deploying, verify you have:
- ✅ `TELEGRAM_BOT_TOKEN` (from @BotFather)
- ✅ `WOOCOMMERCE_URL` (your store URL)
- ✅ `WOOCOMMERCE_KEY` (REST API key)
- ✅ `WOOCOMMERCE_SECRET` (REST API secret)

All 4 are REQUIRED for the bot to work.
