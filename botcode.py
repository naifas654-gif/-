from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

TOKEN = '8737393959:AAGfNXQAKc6SEemkh07KfBASY2SbIVv5Pek'
ADMIN_IDS = [123456789] 
warnings = {} 

async def check_admin(update: Update):
    return update.effective_user.id in ADMIN_IDS

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update) or not update.message.reply_to_message: return
    user_id = update.message.reply_to_message.from_user.id
    warnings[user_id] = warnings.get(user_id, 0) + 1
    if warnings[user_id] >= 3:
        await context.bot.restrict_chat_member(update.effective_chat.id, user_id, permissions=None)
        await update.message.reply_text("تم كتم المستخدم بسبب وصوله لـ 3 إنذارات.")
    else:
        await update.message.reply_text(f"تم إعطاء إنذار ({warnings[user_id]}/3).")

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update) or not update.message.reply_to_message: return
    user_id = update.message.reply_to_message.from_user.id
    warnings[user_id] = 0
    await context.bot.restrict_chat_member(update.effective_chat.id, user_id, permissions=None)
    await update.message.reply_text("تم فك الكتم وتصفير الإنذارات.")

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update) or not update.message.reply_to_message: return
    user_id = update.message.reply_to_message.from_user.id
    minutes = int(context.args[0]) if context.args else 10
    await context.bot.restrict_chat_member(update.effective_chat.id, user_id, permissions=None)
    await update.message.reply_text(f"تم كتم المستخدم لمدة {minutes} دقيقة.")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update) or not update.message.reply_to_message: return
    user_id = update.message.reply_to_message.from_user.id
    await context.bot.ban_chat_member(update.effective_chat.id, user_id)
    await update.message.reply_text("تم طرد المستخدم نهائياً.")

async def delete_with_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update) or not update.message.reply_to_message: return
    reason = " ".join(context.args)
    await context.bot.delete_message(update.effective_chat.id, update.message.reply_to_message.message_id)
    await update.message.reply_text(f"تم حذف الرسالة بسبب: {reason}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("warn", warn))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("delete", delete_with_reason))
    app.run_polling()
