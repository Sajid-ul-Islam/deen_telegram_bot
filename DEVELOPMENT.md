# DeenCommerce Telegram Bot Development & Strategy Guide

This document aggregates the app code review, strategy recommendations for the Bangladeshi market, and the final implementation walkthrough of priority categories and support command workflows.

---

## 🏛️ Part 1: Code Review & Architecture

The application is structured as a single-file FastAPI server (`main.py`) running with Uvicorn, integrating `FastAPI` and the `python-telegram-bot` libraries.

### Refactored Lifespan Architecture
We migrated from deprecated `@app.on_event` startup/shutdown hooks to a modern, consolidated lifespan context manager:
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    # Startup: Initialize global httpx.AsyncClient and bot
    yield
    # Shutdown: Clean up client connections and stop bot
```
- **Connection Pooling**: By sharing a global `httpx.AsyncClient`, the application avoids socket exhaustion and reduces WooCommerce API latency.
- **DNS Resolution**: A monkey-patch for `socket.getaddrinfo` enforces IPv4, preventing connection timeouts inside environments like Render or Hugging Face.
- **Null Safety**: Accessing product images is guarded (`isinstance(images, list) and len(images) > 0`) to prevent index crashes.

---

## 🔒 Part 2: Security Posture

1. **Order Search Isolation**:
   - Order lookup requires both the **Order ID** and the **Billing Email** (`1234 customer@example.com`).
   - If there is a mismatch or an invalid ID, the bot returns a generic `"❌ No matching order found."` message to prevent order harvesting.
2. **Webhook Authorization**:
   - Compares the `X-Telegram-Bot-Api-Secret-Token` header on incoming updates with `TELEGRAM_WEBHOOK_SECRET` to reject unauthorized requests.
3. **Escaping**:
   - Employs `escape_markdown` on all WooCommerce API parameters and user text inputs before rendering Telegram Markdown.

---

## 🎯 Part 3: Strategy & E-commerce Recommendations

### Active & Priority Categories
The bot queries WooCommerce categories (`products/categories`) and filters them dynamically:
- **Top-Level Only**: Only displays categories where `parent == 0`, filtering out backend sizes, tags, or colors.
- **menu_order Sorting**: Categories are sorted based on WooCommerce's custom drag-and-drop hierarchy (`menu_order`) configured in the WordPress dashboard.

### Bangladeshi Customer Care Workflows
The bot is designed to act as an automated customer care intelligence assistant:
- **MFS Payment Guide**: Details Cash on Delivery (COD) and prepayments via bKash and Nagad.
- **Delivery Rules**: Explains shipping costs and timelines (Dhaka: ৳80 within 48h; Outside Dhaka: ৳150 via Pathao/Steadfast within 3-5 days).
- **Return / Exchange Terms**: Explains size exchange rules (7-day window with tags intact).
- **Live Agent Hand-off**: Provides links to Facebook Messenger (`m.me/deencommerce`), WhatsApp, and support hotlines.

---

## 🛠️ Part 4: Interactive Commands Walkthrough

The bot binds direct Telegram commands to corresponding workflows (supporting both button interactions and typed inputs):

1. **`/start`** or **`/strat`**: Resets context and displays the main greeting and keyboard menu.
2. **`/help`**: Triggers the interactive FAQ and customer support panel.
3. **`/browse`**: Directly displays the top-level categories menu.
4. **`/search <keyword>`** or **`/search`**:
   - Typing `/search panjabi` instantly runs the search query.
   - Typing `/search` prompts the user for a text query.
5. **`/my_order`**: Direct lookup for customer order status.
