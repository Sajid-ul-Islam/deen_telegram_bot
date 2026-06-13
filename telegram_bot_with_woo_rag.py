# telegram_bot_with_woo_rag.py

from telegram import Update
from telegram.ext import ContextTypes
from rag_agent_with_woocommerce import agent
import asyncio

user_agents = {}

async def ai_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle product search with WooCommerce knowledge base"""
    
    user_id = update.effective_user.id
    user_query = update.message.text
    
    # Show typing
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )
    
    try:
        # Get response using WooCommerce knowledge base
        response = await agent.answer_query(user_query)
        
        # Split if too long
        if len(response) > 4000:
            for i in range(0, len(response), 4000):
                await update.message.reply_text(
                    response[i:i+4000],
                    parse_mode="Markdown"
                )
        else:
            await update.message.reply_text(
                response,
                parse_mode="Markdown"
            )
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await update.message.reply_text(
            "❌ Error processing your request. Please try again."
        )

# Register all messages as potential product searches
application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, ai_search_handler)
)