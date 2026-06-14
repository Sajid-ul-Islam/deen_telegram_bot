import os
from dotenv import load_dotenv

load_dotenv()

from db import supabase

if not supabase:
    print("Supabase client not initialized. Check SUPABASE_URL and SUPABASE_KEY in .env")
    exit(1)

providers = [
    {
        "name": "openrouter",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": os.getenv("OPENROUTER_API_KEY", ""),
        "default_model": "google/gemini-2.5-flash"
    },
    {
        "name": "groq",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": os.getenv("GROQ_API_KEY", ""),
        "default_model": "llama-3.3-70b-versatile"
    },
    {
        "name": "openai",
        "base_url": "https://api.openai.com/v1",
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "default_model": "gpt-4o-mini"
    },
    {
        "name": "anthropic",
        "base_url": "https://api.anthropic.com/v1",
        "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "default_model": "claude-3-5-sonnet-20241022"
    },
    {
        "name": "xai",
        "base_url": "https://api.x.ai/v1",
        "api_key": os.getenv("GROK_API_KEY", ""),
        "default_model": "grok-2-latest"
    },
    {
        "name": "gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key": os.getenv("GEMINI_API_KEY", ""),
        "default_model": "gemini-2.5-flash"
    }
]

count = 0
for p in providers:
    if p["api_key"] and not p["api_key"].endswith("here") and "placeholder" not in p["api_key"]:
        try:
            supabase.table("ai_providers").upsert(p).execute()
            print(f"Added provider: {p['name']}")
            count += 1
        except Exception as e:
            print(f"Failed to add {p['name']}: {e}")

print(f"Successfully migrated {count} provider keys to Supabase.")
