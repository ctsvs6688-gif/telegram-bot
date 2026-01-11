from googletrans import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler
)
from googletrans import Translator
from datetime import datetime, timedelta
import os
import logging

# ================= 配置 =================
BOT_TOKEN = "8228263725:AAHlRuQ8uFTVTeTwMTzhdzL7h5wOlZ8Uczg"
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "-7571918976"))

# ================= 日志 =================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================= 状态 =================
LANG, AREA, TIME = range(3)

# ================= 翻译 =================
translator = Translator()

def tr(text, lang):
    if lang == "zh":
        return text
    try:
        return translator.translate(text, dest=lang).text
    except Exception as e:
        logger.error(f"翻译失败: {e}")
        return text

# ================= admin 双语 =================
def admin_bilingual(zh_text, lang):
    if lang == "zh":
        return zh_text
    return f"🇨🇳 中文：\n{zh_text}\n\n🌍 客户语言：\n{tr(zh_text, lang)}"

# ================= 返回 & 取消按钮 =================
def back_button(target):
    return InlineKeyboardButton("🔙 返回", callback_data=f"back_{target}")

def cancel_button():
    return InlineKeyboardButton("❌ 取消", callback_data="cancel")

# ================= 快捷回复 =================
ADMIN_QUICK_REPLY = {
    "ok": "好的，已帮您确认，请稍等 😊",
    "full": "这个时间已满，可以帮您改时间吗？",
    "price": "价格是按时长计算的",
}

def admin_quick_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ 已确认", callback_data=f"qr_ok_{user_id}")],
        [InlineKeyboardButton("❌ 已满", callback_data=f"qr_full_{user_id}")],
        [InlineKeyboardButton("💰 价格", callback_data=f"qr_price_{user_id}")]
    ])

# ================= /start =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    last = context.user_data.get("last_active")

    if last and now - last < timedelta(hours=24):
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ 继续上次预约", callback_data="resume")],
            [InlineKeyboardButton("🔄 重新开始", callback_data="restart")]
        ])
        await update.message.reply_text("欢迎回来 😊\n是否继续上一次预约？", reply_markup=kb)
        return ConversationHandler.END

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("中文", callback_data="lang_zh")],
        [InlineKeyboardButton("English", callback_data="lang_en")],
        [InlineKeyboardButton("Bahasa Melayu", callback_data="lang_ms")],
        [InlineKeyboardButton("বাংলা", callback_data="lang_bn")],
        [InlineKeyboardButton("اردو", callback_data="lang_ur")],
    ])
    await update.message.reply_text("请选择语言：", reply_markup=kb)
    return LANG

# ================= 语言 =================
async def language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data.split("_")[1]
    context.user_data["lang"] = lang
    context.user_data["last_active"] = datetime.now()

    return await area_handler(update, context)

# ================= 区域 =================
async def area_handler(update, context):
    query = update.callback_query
    lang = context.user_data["lang"]

    text = """您好 😊
我们提供【酒店内专业服务】

请选择您所在区域：
"""
    kb = [
        [InlineKeyboardButton("Mount Austin", callback_data="area_austin")],
        [InlineKeyboardButton("JB Town", callback_data="area_jb")],
        [back_button("lang")],
        [cancel_button()]
    ]
    await query.edit_message_text(tr(text, lang), reply_markup=InlineKeyboardMarkup(kb))
    return AREA

# ================= 时长 =================
async def time_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["area"] = query.data
    context.user_data["last_active"] = datetime.now()
    lang = context.user_data["lang"]

    text = "请选择服务时长："
    kb = [
        [InlineKeyboardButton("1 小时", callback_data="time_1")],
        [InlineKeyboardButton("2 小时", callback_data="time_2")],
        [back_button("area")],
        [cancel_button()]
    ]
    await query.edit_message_text(tr(text, lang), reply_markup=InlineKeyboardMarkup(kb))
    return TIME

# ================= 确认 & 通知 admin =================
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["service_time"] = query.data
    lang = context.user_data["lang"]
    user = query.from_user

    zh_text = (
        "📥 新订单\n"
        f"👤 @{user.username or user.id}\n"
        f"📍 区域：{context.user_data['area']}\n"
        f"⏱ 时长：{context.user_data['service_time']}"
    )

    context.bot_data.setdefault("lang_map", {})[user.id] = lang

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=admin_bilingual(zh_text, lang),
        reply_markup=admin_quick_keyboard(user.id)
    )

    await query.edit_message_text(tr("已收到，我们将尽快联系您 😊", lang))
    return ConversationHandler.END

# ================= admin 快捷回复 =================
async def admin_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    action, user_id = data.split("_")[1], int(data.split("_")[2])
    
    lang = context.bot_data.get("lang_map", {}).get(user_id, "zh")
    reply_text = ADMIN_QUICK_REPLY.get(action, "收到")
    
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=tr(reply_text, lang)
        )
        await query.edit_message_text(
            text=f"✅ 已回复用户 {user_id}: {reply_text}",
            reply_markup=None
        )
    except Exception as e:
        logger.error(f"回复用户失败: {e}")
        await query.edit_message_text("❌ 回复失败，用户可能已屏蔽机器人")

# ================= 返回处理 =================
async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    target = query.data.split("_")[1]
    
    if target == "lang":
        return await start(update, context)
    elif target == "area":
        return await area_handler(update, context)
    
    return ConversationHandler.END

# ================= 取消处理 =================
async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get("lang", "zh")
    await query.edit_message_text(tr("预约已取消", lang))
    return ConversationHandler.END

# ================= 主函数 =================
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG: [CallbackQueryHandler(language_handler, pattern="^lang_")],
            AREA: [
                CallbackQueryHandler(time_handler, pattern="^area_"),
                CallbackQueryHandler(back_handler, pattern="^back_lang"),
                CallbackQueryHandler(cancel_handler, pattern="^cancel")
            ],
            TIME: [
                CallbackQueryHandler(confirm, pattern="^time_"),
                CallbackQueryHandler(back_handler, pattern="^back_area"),
                CallbackQueryHandler(cancel_handler, pattern="^cancel")
            ]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(admin_qr, pattern="^qr_"))
    
    application.run_polling()

if __name__ == "__main__":
    main()
