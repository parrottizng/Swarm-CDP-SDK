import os
import time
import json
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from swarm import Swarm
from agents import based_agent, generate_art, deploy_nft, create_token, transfer_asset, get_balance, request_eth_from_faucet

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the bot token from environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize Swarm client
client = Swarm()

# Function to process and print streaming response
def process_and_format_streaming_response(response):
    content = ""
    last_sender = ""
    formatted_response = ""

    for chunk in response:
        if "sender" in chunk:
            last_sender = chunk["sender"]

        if "content" in chunk and chunk["content"] is not None:
            if not content and last_sender:
                formatted_response += f"{last_sender}: "
                last_sender = ""
            formatted_response += chunk["content"]
            content += chunk["content"]

        if "tool_calls" in chunk and chunk["tool_calls"] is not None:
            for tool_call in chunk["tool_calls"]:
                f = tool_call["function"]
                name = f["name"]
                if not name:
                    continue
                formatted_response += f"\n{name}()"

        if "delim" in chunk and chunk["delim"] == "end" and content:
            formatted_response += "\n"  # End of response message
            content = ""

        if "response" in chunk:
            return formatted_response

# Function to handle incoming messages from Telegram
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    messages = [{"role": "user", "content": user_message}]

    # Log the user's message
    logger.info(f"User message: {user_message}")

    # Run the agent with the user's message
    response = client.run(
        agent=based_agent,
        messages=messages,
        stream=True
    )

    # Process and format the streaming response
    formatted_response = process_and_format_streaming_response(response)

    # Send the response back to the user
    await update.message.reply_text(formatted_response)

# Main function to start the bot
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add message handler for natural language
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()