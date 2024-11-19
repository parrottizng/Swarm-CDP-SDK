import os
import time
import json
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from swarm import Swarm
from agents import based_agent, generate_art, deploy_nft, create_token, transfer_asset, get_balance, request_eth_from_faucet

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the bot token and OpenAI API key from environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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

# Function to pretty print messages (for non-streaming responses)
def pretty_print_messages(messages) -> str:
    formatted_response = ""
    for message in messages:
        if message["role"] != "assistant":
            continue

        # Print agent name in blue
        formatted_response += f"{message['sender']}: "

        # Print response, if any
        if message["content"]:
            formatted_response += message["content"]

        # Print tool calls in purple, if any
        tool_calls = message.get("tool_calls") or []
        if len(tool_calls) > 1:
            formatted_response += "\n"
        for tool_call in tool_calls:
            f = tool_call["function"]
            name, args = f["name"], f["arguments"]
            arg_str = json.dumps(json.loads(args)).replace(":", "=")
            formatted_response += f"\n{name}({arg_str[1:-1]})"
    
    return formatted_response

# Function to handle incoming text messages from Telegram
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

# Function to handle incoming voice messages from Telegram
async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    voice = update.message.voice

    # Get the file ID and download the voice message
    file_id = voice.file_id
    file = await context.bot.get_file(file_id)
    
    # Get the file URL
    file_url = file.file_path

    # Download the file using requests
    file_path = f"voice_{file_id}.ogg"
    response = requests.get(file_url)

    # Save the file locally
    with open(file_path, 'wb') as f:
        f.write(response.content)

    # Convert the voice message to text using OpenAI Whisper API
    transcription = transcribe_audio(file_path)

    if transcription:
        # Log the transcription
        logger.info(f"Transcription: {transcription}")

        # Process the transcription as a regular text message
        messages = [{"role": "user", "content": transcription}]
        response = client.run(
            agent=based_agent,
            messages=messages,
            stream=True
        )

        # Process and format the streaming response
        formatted_response = process_and_format_streaming_response(response)

        # Send the response back to the user
        await update.message.reply_text(formatted_response)
    else:
        await update.message.reply_text("Sorry, I couldn't transcribe the audio.")

# Function to transcribe audio using OpenAI Whisper API
def transcribe_audio(file_path):
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    files = {
        "file": open(file_path, "rb"),
        "model": (None, "whisper-1")  # Указываем модель "whisper-1"
    }

    response = requests.post(url, headers=headers, files=files)

    if response.status_code == 200:
        return response.json().get("text")
    else:
        logger.error(f"Failed to transcribe audio: {response.text}")
        return None

# Main function to start the bot
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add message handler for text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Add message handler for voice messages
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()