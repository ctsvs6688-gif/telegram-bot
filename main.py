import os
import logging
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext
)
from googletrans import Translator

# ========= 基本配置 =========
BOT_TOKEN = os.getenv("8228263725:AAGrxh6GqkT3cD74o_oprPvvxfpABFOWaLY")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "7571918976"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set")

# ========= 日志 =========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

translator = Translator()

# ========= handlers =========
def start(update: Update, context: CallbackContext):
    update.message.reply_text("🤖 Bot 已上线，可以使用了")

def echo(update: Update, context: CallbackContext):
    text = update.message.text
    result = translator.translate(text, dest="en")
    update.message.reply_text(result.text)

# ========= 主入口 =========
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
