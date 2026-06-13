import os
import time
import re
import html
import logging
import unicodedata
import httpx
from telegram.helpers import escape_markdown
from dotenv import load_dotenv

load_dotenv()

# Config
WOOCOMMERCE_URL = os.getenv("WOOCOMMERCE_URL", "").rstrip("/")
WOOCOMMERCE_KEY = os.getenv("WOOCOMMERCE_KEY")
WOOCOMMERCE_SECRET = os.getenv("WOOCOMMERCE_SECRET")

logger = logging.getLogger(__name__)

# Global HTTP client to reuse TCP/TLS connections
http_client = None
store_address_cache = None

class SimpleCache:
    def __init__(self, ttl_seconds=3600):
        self.ttl = ttl_seconds
        self.store = {}

    def get(self, key):
        if key in self.store:
            data, timestamp = self.store[key]
            if time.time() - timestamp < self.ttl:
                return data
            else:
                del self.store[key]
        return None

    def set(self, key, value):
        self.store[key] = (value, time.time())

    def clear(self):
        self.store.clear()

categories_cache = SimpleCache(ttl_seconds=3600)  # 1 hour
products_cache = SimpleCache(ttl_seconds=1800)    # 30 minutes
pathao_status_cache = SimpleCache(ttl_seconds=900)  # 15 minutes
pathao_token_cache = SimpleCache(ttl_seconds=7200)   # 2 hours

# ---------------------------------------------------------------------------
# Bengali / Banglish → English synonym map
# ---------------------------------------------------------------------------
# Keys are Unicode-NFC normalised, lowercase Bengali/Banglish tokens.
# Values are the English terms used in WooCommerce product names/descriptions.
# ---------------------------------------------------------------------------
SYNONYMS_MAP = {
    # ── Clothing types (Bengali) ────────────────────────────────────────────
    "জামা": "shirt",
    "শার্ট": "shirt",
    "কামিজ": "shirt",
    "পাঞ্জাবি": "panjabi",
    "পাঞ্জাব": "panjabi",
    "পাঞ্জাবী": "panjabi",
    "প্যান্ট": "pants",
    "প্যান্টস": "pants",
    "জিন্স": "jeans",
    "জিনস": "jeans",
    "ডেনিম": "denim",
    "গেঞ্জি": "t-shirt",
    "টি-শার্ট": "t-shirt",
    "টিশার্ট": "t-shirt",
    "পোলো": "polo",
    "পোলো শার্ট": "polo shirt",
    "হাফ শার্ট": "half sleeve",
    "হাফশার্ট": "half sleeve",
    "ফুল শার্ট": "full sleeve",
    "ফুলশার্ট": "full sleeve",
    "শর্টস": "shorts",
    "শর্ট": "shorts",
    "লুঙ্গি": "lungi",
    "পায়জামা": "pajama",
    "পাইজামা": "pajama",
    "সোয়েটার": "sweater",
    "জ্যাকেট": "jacket",
    "হুডি": "hoodie",
    "কোট": "coat",
    "ব্লেজার": "blazer",
    "ওভারকোট": "overcoat",
    "মানিব্যাগ": "wallet",
    "ব্যাগ": "bag",
    "বেল্ট": "belt",
    "ক্যাপ": "cap",
    "টুপি": "cap",
    "মোজা": "socks",
    "জুতা": "shoes",
    "স্যান্ডেল": "sandal",

    # ── Fabrics / materials (Bengali) ───────────────────────────────────────
    "সুতি": "cotton",
    "সুতির": "cotton",
    "সুতীর": "cotton",
    "সুতীর কাপড়": "cotton",
    "সুতির কাপড়": "cotton",
    "কটন": "cotton",
    "লিনেন": "linen",
    "পলিয়েস্টার": "polyester",
    "পলিস্টার": "polyester",
    "সিল্ক": "silk",
    "রেশম": "silk",
    "ভিসকোস": "viscose",
    "ফ্লিস": "fleece",
    "উল": "wool",
    "নাইলন": "nylon",
    "স্প্যান্ডেক্স": "spandex",
    "ডেনিম কাপড়": "denim",
    "কাপড়": "fabric",
    "কটন কাপড়": "cotton",

    # ── Colors (Bengali) ────────────────────────────────────────────────────
    "লাল": "red",
    "নীল": "blue",
    "সবুজ": "green",
    "হলুদ": "yellow",
    "কমলা": "orange",
    "বেগুনি": "purple",
    "গোলাপি": "pink",
    "গোলাপী": "pink",
    "সাদা": "white",
    "কালো": "black",
    "ধূসর": "gray",
    "ধুসর": "gray",
    "বাদামি": "brown",
    "বাদামী": "brown",
    "খাকি": "khaki",
    "ক্রিম": "cream",
    "মেরুন": "maroon",
    "আকাশি": "sky blue",
    "আকাশী": "sky blue",
    "নেভি": "navy",
    "নেভি ব্লু": "navy blue",
    "অলিভ": "olive",
    "অফ হোয়াইট": "off white",
    "চারকোল": "charcoal",
    "তামা": "copper",
    "সোনালি": "golden",
    "সোনালী": "golden",
    "রুপালি": "silver",
    "রুপালী": "silver",

    # ── Design / pattern (Bengali) ──────────────────────────────────────────
    "চেক": "check",
    "চেকার": "check",
    "স্ট্রাইপ": "stripe",
    "ডোরা": "stripe",
    "ডোরাকাটা": "stripe",
    "প্রিন্ট": "print",
    "ফুলেল": "floral",
    "ফ্লোরাল": "floral",
    "সলিড": "solid",
    "এমব্রয়ডারি": "embroidery",
    "এমব্রোয়ডারি": "embroidery",
    "পকেট": "pocket",
    "স্লিম ফিট": "slim fit",
    "রেগুলার ফিট": "regular fit",
    "ওভারসাইজ": "oversize",
    "ওভারসাইজড": "oversized",

    # ── Common question words to strip ──────────────────────────────────────
    # These words carry no product meaning; mapping to empty string removes them.
    "আছে": "",
    "আছেন": "",
    "আছো": "",
    "কি": "",
    "কী": "",
    "কোনো": "",
    "কোন": "",
    "পাবো": "",
    "পাব": "",
    "দাম": "price",
    "মূল্য": "price",
    "রং": "color",
    "রঙ": "color",
    "রঙের": "color",
    "সাইজ": "size",
    "মাপ": "size",
    "অথবা": "",
    "এবং": "",
    "বা": "",

    # ── Banglish (Latin-script Bengali) ─────────────────────────────────────
    "jama": "shirt",
    "shart": "shirt",
    "shurt": "shirt",
    "pant": "pants",
    "pants": "pants",
    "tshirt": "t-shirt",
    "t-shirt": "t-shirt",
    "teeshirt": "t-shirt",
    "genji": "t-shirt",
    "genja": "t-shirt",
    "panjabi": "panjabi",
    "punjabi": "panjabi",
    "jeans": "jeans",
    "jins": "jeans",
    "denim": "denim",
    "wallet": "wallet",
    "moneybag": "wallet",
    "polo": "polo",
    "half sleeve": "half sleeve",
    "halfshirt": "half sleeve",
    "full sleeve": "full sleeve",
    "fullshirt": "full sleeve",
    "suti": "cotton",
    "sutir": "cotton",
    "cotton": "cotton",
    "linen": "linen",
    "silk": "silk",
    "lal": "red",
    "nil": "blue",
    "neel": "blue",
    "shobuj": "green",
    "holud": "yellow",
    "komola": "orange",
    "beguni": "purple",
    "golapi": "pink",
    "shada": "white",
    "kalo": "black",
    "dhushor": "gray",
    "badami": "brown",
    "khaki": "khaki",
    "maroon": "maroon",
    "navy": "navy",
    "akashi": "sky blue",
    "check": "check",
    "stripe": "stripe",
    "print": "print",
    "floral": "floral",
    "solid": "solid",
    "hoodie": "hoodie",
    "jacket": "jacket",
    "sweater": "sweater",
    "shorts": "shorts",
    "lungi": "lungi",
    "pajama": "pajama",
}


def _normalize_bengali(text: str) -> str:
    """Normalize Bengali Unicode text.

    Applies NFC normalization to collapse visually identical but differently
    encoded sequences (e.g. ি U+09BF vs ী U+09C0 are *different* vowel signs
    and intentionally kept distinct; NFC just ensures each is in its canonical
    composed form so dictionary lookups are consistent).

    Also strips zero-width joiners/non-joiners that can silently break matches.
    """
    # Canonical decomposition then recomposition
    text = unicodedata.normalize("NFC", text)
    # Remove zero-width characters that don't affect visual appearance
    text = re.sub(r"[\u200b-\u200f\u00ad]", "", text)
    return text


def preprocess_search_query(query: str) -> str:
    """Translate / normalise a customer search query to English WooCommerce terms.

    Handles:
    - Plain English queries (pass-through with synonym mapping)
    - Banglish (Bengali written in Latin script)
    - Bengali (Unicode) — normalised first, then token-by-token translation

    Returns a single English search string suitable for the WooCommerce
    ``search`` query parameter.
    """
    if not query:
        return ""

    # 1. Unicode normalise to make dictionary lookups reliable
    query = _normalize_bengali(query)

    # 2. Lowercase for case-insensitive matching
    q_lower = query.strip().lower()

    # 3. Whole-phrase match first (handles multi-word phrases like "সুতির কাপড়")
    if q_lower in SYNONYMS_MAP:
        translated = SYNONYMS_MAP[q_lower]
        return translated if translated else q_lower

    # 4. Tokenise on whitespace + common Bengali punctuation / question marks
    tokens = re.split(r"[\s,।?!৷]+", q_lower)

    translated_tokens = []
    skip_next = False
    for i, token in enumerate(tokens):
        if skip_next:
            skip_next = False
            continue
        if not token:
            continue

        # Try two-word phrase first (e.g. "সুতির কাপড়", "নেভি ব্লু")
        if i + 1 < len(tokens) and tokens[i + 1]:
            two_word = token + " " + tokens[i + 1]
            if two_word in SYNONYMS_MAP:
                mapped = SYNONYMS_MAP[two_word]
                if mapped:  # empty means stop-word
                    translated_tokens.append(mapped)
                skip_next = True
                continue

        # Single token lookup
        mapped = SYNONYMS_MAP.get(token, token)
        if mapped:  # empty string → stop-word, skip
            translated_tokens.append(mapped)

    if not translated_tokens:
        # Fall back to original query if nothing translated
        return query.strip()

    # De-duplicate while preserving order
    seen = set()
    result = []
    for t in translated_tokens:
        if t not in seen:
            seen.add(t)
            result.append(t)

    return " ".join(result)

async def get_store_address():
    return (
        "DEEN Mirpur 12 Outlet\n"
        "📍 ৩য় তলা, রমজান্নেছা সুপার মার্কেট, মিরপুর ১২, ঢাকা।\n"
        "📞 01972 627 981\n"
        "🕐 প্রতিদিন সকাল ১০টা থেকে রাত ১০টা পর্যন্ত। (সাপ্তাহিক বন্ধ রবিবার)\n"
        "গুগল ম্যাপঃ https://g.co/kgs/3pCJkAZ\n\n"
        "DEEN Wari Outlet\n"
        "📍 Ground Floor, 41 A.K Famous Tower, Rankin Street, Wari, Dhaka 1203.\n"
        "📞 01972-627983\n"
        "🕐 প্রতিদিন সকাল ১০টা থেকে রাত ১০টা পর্যন্ত। (সাপ্তাহিক বন্ধ রবিবার)\n"
        "গুগল ম্যাপঃ https://g.co/kgs/Cu71N8U\n\n"
        "DEEN Cumilla Outlet\n"
        "📍 4th floor, QR Tower, F56H+PF5, QR Tower, Badurtola, Cumilla.\n"
        "📞 01972 627984\n"
        "🕐 প্রতিদিন সকাল ১০টা থেকে রাত ১০টা পর্যন্ত। (সাপ্তাহিক বন্ধ শুক্রবার)\n"
        "গুগল ম্যাপঃ https://g.co/kgs/Dav6rNx\n\n"
        "DEEN Sylhet Outlet\n"
        "📍 Block-A, House-54/2, Kumar Para, Sylhet\n"
        "📞 01972-627985\n"
        "🕐 প্রতিদিন সকাল ১০টা থেকে রাত ১০টা পর্যন্ত। (সাপ্তাহিক বন্ধ শুক্রবার)\n"
        "গুগল ম্যাপঃ https://g.co/kgs/QsvRbtH"
    )

async def get_pathao_tracking_status(consignment_id):
    cache_key = f"pathao_{consignment_id}"
    cached_status = pathao_status_cache.get(cache_key)
    if cached_status is not None:
        logger.info("Using cached Pathao tracking status for consignment: %s", consignment_id)
        return cached_status

    try:
        base_url = os.getenv("PATHAO_BASE_URL", "https://api-hermes.pathao.com").rstrip("/")
        client_id = os.getenv("PATHAO_CLIENT_ID")
        client_secret = os.getenv("PATHAO_CLIENT_SECRET")
        username = os.getenv("PATHAO_USERNAME")
        password = os.getenv("PATHAO_PASSWORD")

        if not all([client_id, client_secret, username, password]):
            return None

        async with httpx.AsyncClient(timeout=4.0) as client:
            async def _get_token():
                """Request a fresh Pathao auth token."""
                token_resp = await client.post(f"{base_url}/aladdin/api/v1/issue-token", json={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "username": username,
                    "password": password,
                    "grant_type": "password"
                })
                if token_resp.status_code != 200:
                    return None
                new_token = token_resp.json().get("access_token")
                if new_token:
                    pathao_token_cache.set("auth_token", new_token)
                return new_token

            token = pathao_token_cache.get("auth_token")
            if not token:
                logger.info("Pathao auth token not cached. Requesting a new one.")
                token = await _get_token()

            if not token:
                return None

            async def _do_track(tkn):
                headers = {"Authorization": f"Bearer {tkn}", "Accept": "application/json"}
                return await client.get(
                    f"{base_url}/aladdin/api/v1/packages/{consignment_id}/track",
                    headers=headers
                )

            track_resp = await _do_track(token)

            # On 401, clear stale token and retry once with a fresh one
            if track_resp.status_code == 401:
                logger.warning("Pathao token 401 — refreshing and retrying...")
                pathao_token_cache.store.pop("auth_token", None)
                token = await _get_token()
                if not token:
                    return None
                track_resp = await _do_track(token)

            if track_resp.status_code != 200:
                return None

            data = track_resp.json()
            if data.get("error") and "Unauthorized" in data.get("message", ""):
                logger.warning("Pathao track API returned Unauthorized, clearing cached token.")
                pathao_token_cache.store.pop("auth_token", None)
                return None

            track_data = data.get("data", {})
            status = track_data.get("status", "Unknown")
            history = track_data.get("history", [])

            text = f"📍 *Pathao Courier Status*: {md(status.upper())}\n"
            if history:
                text += "*Tracking History*:\n"
                for h in history[:5]:
                    time_str = h.get("time", "")
                    desc = h.get("description", h.get("status", ""))
                    text += f"  • _{md(time_str)}_: {md(desc)}\n"

            if text:
                pathao_status_cache.set(cache_key, text)
            return text
    except Exception as e:
        logger.error("Error fetching Pathao tracking status: %s", str(e))
        return None

def get_tracking_info(order):
    if not isinstance(order, dict):
        return None, None
    meta_data = order.get("meta_data", [])
    consignment_id = None
    provider = None

    for meta in meta_data:
        key = str(meta.get("key", "")).lower()
        value = str(meta.get("value", "")).strip()
        if not value:
            continue

        if "ptc_consignment_id" in key or "pathao_consignment" in key:
            consignment_id = value
            provider = "Pathao"
            break
        elif "steadfast_consignment" in key or "steadfast_id" in key:
            consignment_id = value
            provider = "Steadfast"
            break
        elif "consignment_id" in key or "tracking_number" in key or "tracking_code" in key:
            consignment_id = value
            if "pathao" in key or value.upper().startswith("DD"):
                provider = "Pathao"
            elif "steadfast" in key:
                provider = "Steadfast"
            else:
                provider = "Courier"
            break

    if consignment_id:
        if provider == "Pathao":
            url = f"https://merchant.pathao.com/tracking?consignment_id={consignment_id}"
        elif provider == "Steadfast":
            url = f"https://steadfast.com.bd/t/{consignment_id}"
        else:
            if consignment_id.upper().startswith("DD"):
                url = f"https://merchant.pathao.com/tracking?consignment_id={consignment_id}"
                provider = "Pathao"
            else:
                url = f"https://steadfast.com.bd/t/{consignment_id}"
                provider = "Steadfast"
        return consignment_id, url
    return None, None

def html_table_to_markdown(table_html):
    """Convert an HTML table to an aligned column-row grid inside a monospace code block."""
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE)
    md_rows = []

    for row in rows:
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL | re.IGNORECASE)
        clean_cells = []
        for cell in cells:
            c = re.sub(r'<[^>]+>', '', cell)
            c = html.unescape(c)
            c = c.replace('\xa0', ' ').replace('\u200b', '')
            c = c.strip()
            clean_cells.append(c)
        if clean_cells:
            md_rows.append(clean_cells)

    if not md_rows:
        return ""

    # Detect a single-cell title row (e.g., "Size Chart" spanning all columns)
    header_title = ""
    start_idx = 0
    if len(md_rows[0]) == 1 and len(md_rows) > 1:
        header_title = md_rows[0][0]
        start_idx = 1
    elif len(md_rows[0]) == 1:
        return f"📏 *{md_rows[0][0]}*"

    rows_to_format = md_rows[start_idx:]
    if not rows_to_format:
        return f"📏 *{header_title}*" if header_title else ""

    # Normalize all rows to the same number of columns
    max_cols = max(len(r) for r in rows_to_format)
    normalized = [r + [""] * (max_cols - len(r)) for r in rows_to_format]

    # Calculate per-column widths (minimum 4 chars for readability)
    col_widths = [
        max(max(len(normalized[ri][ci]) for ri in range(len(normalized))), 4)
        for ci in range(max_cols)
    ]

    def fmt_row(cells):
        return " | ".join(str(cells[i]).ljust(col_widths[i]) for i in range(len(cells)))

    def fmt_sep():
        return "-+-".join("-" * col_widths[i] for i in range(max_cols))

    # Build the grid: header row, separator, then data rows
    grid_lines = []
    grid_lines.append(fmt_row(normalized[0]))   # column headers
    grid_lines.append(fmt_sep())                 # ----+----+----
    for row in normalized[1:]:
        grid_lines.append(fmt_row(row))          # data rows

    grid_text = "\n".join(grid_lines)

    title_line = f"📏 *{header_title}*\n" if header_title else "📏 *Size Chart*\n"
    return f"{title_line}\n```\n{grid_text}\n```"


def extract_and_format_size_chart(product):
    if not isinstance(product, dict):
        return None
    for field in ["short_description", "description"]:
        html_content = product.get(field, "")
        if not html_content:
            continue
        tables = re.findall(r'<table[^>]*>.*?</table>', html_content, re.DOTALL | re.IGNORECASE)
        for table in tables:
            if any(x in table.lower() for x in ["size", "chart", "guide", "dimension", "measure"]):
                return html_table_to_markdown(table)
    return None

def strip_html_excluding_table(html_content):
    if not html_content:
        return ""
    cleaned = re.sub(r'<table[^>]*>.*?</table>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    return strip_html(cleaned)

def md(value):
    """Escape dynamic values before interpolating into Telegram Markdown."""
    return escape_markdown("" if value is None else str(value), version=1)

def strip_html(value):
    text = html.unescape(str(value or ""))
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    return re.sub(r"<[^>]+>", "", text).strip()

def product_button_name(name):
    clean_name = str(name or "Product").strip()
    return clean_name[:32] if clean_name else "Product"

def stock_display(product):
    stock_status = str(product.get("stock_status") or "").lower()
    stock_quantity = product.get("stock_quantity")
    manage_stock = bool(product.get("manage_stock"))

    if stock_status == "instock":
        status = "✅ In Stock"
    elif stock_status == "onbackorder":
        status = "🟡 On Backorder"
    elif stock_status == "outofstock":
        status = "❌ Out of Stock"
    elif product.get("in_stock"):
        status = "✅ In Stock"
    else:
        status = "❌ Out of Stock"

    if manage_stock and stock_quantity is not None:
        return f"📊 Stock: {md(stock_quantity)} {status}"

    return f"📊 Availability: {status}"

async def woo_get(path, params=None):
    """Fetch JSON from WooCommerce and normalize API/HTTP failures."""
    global http_client
    client_to_use = http_client
    own_client = False
    try:
        if client_to_use is None:
            client_to_use = httpx.AsyncClient(
                auth=(WOOCOMMERCE_KEY, WOOCOMMERCE_SECRET),
                timeout=10.0
            )
            own_client = True

        response = await client_to_use.get(
            f"{WOOCOMMERCE_URL}/wp-json/wc/v3/{path.lstrip('/')}",
            params=params,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error("WooCommerce API returned %s for %s", e.response.status_code, path)
        return {"error": f"WooCommerce API returned {e.response.status_code}"}
    except Exception as e:
        logger.error("Error fetching WooCommerce path %s: %s", path, str(e))
        return {"error": str(e)}
    finally:
        if own_client and client_to_use:
            await client_to_use.aclose()
