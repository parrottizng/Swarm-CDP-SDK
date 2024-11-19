import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from agents import based_agent, create_token, deploy_nft, transfer_asset, get_balance, request_eth_from_faucet, generate_art

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the bot token from environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Command to create a token
async def create_token_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        name = context.args[0]
        symbol = context.args[1]
        initial_supply = int(context.args[2])
        result = create_token(name, symbol, initial_supply)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# Command to deploy an NFT
async def deploy_nft_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        name = context.args[0]
        symbol = context.args[1]
        base_uri = context.args[2]
        result = deploy_nft(name, symbol, base_uri)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# Command to transfer assets
async def transfer_asset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        amount = float(context.args[0])
        asset_id = context.args[1]
        destination_address = context.args[2]
        result = transfer_asset(amount, asset_id, destination_address)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# Command to check balance
async def get_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        asset_id = context.args[0]
        result = get_balance(asset_id)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# Command to request ETH from faucet
async def request_eth_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        result = request_eth_from_faucet()
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# Command to generate art
async def generate_art_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        prompt = " ".join(context.args)
        result = generate_art(prompt)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# Main function to start the bot
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("create_token", create_token_command))
    application.add_handler(CommandHandler("deploy_nft", deploy_nft_command))
    application.add_handler(CommandHandler("transfer_asset", transfer_asset_command))
    application.add_handler(CommandHandler("get_balance", get_balance_command))
    application.add_handler(CommandHandler("request_eth", request_eth_command))
    application.add_handler(CommandHandler("generate_art", generate_art_command))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()