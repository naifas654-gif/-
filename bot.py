from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta

TOKEN = "8737393959:AAGfNXQAKc6SEemkh07KfBASY2SbIVv5Pek"
spam_memory = {}
warn_memory = {}
BAD_WORDS = ["سب", "شتيمة", "كلمة_ممنوعة1", "كلمة_ممنوعة2"]

async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    admins = await context.bot.get_chat_administrators(chat_id)
    for admin in admins:
        if admin.user.id == user_id:
            return True
    return False

async def bot_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    message = update.message
    text = message.text
    chat_id = update.effective_chat.id
    user = message.from_user

    for word in BAD_WORDS:
        if word in text.lower():
            await context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
            warn_memory[user.id] = warn_memory.get(user.id, 0) + 1
            await message.reply_text(f"⚠️ {user.mention_html()}، تم حذف رسالتك بسبب ألفاظ مسيئة! الإنذار ({warn_memory[user.id]}/3)", parse_mode='HTML')
            return

    now = datetime.now()
    if user.id in spam_memory:
        mem = spam_memory[user.id]
        if text == mem["text"] and (now - mem["first_time"]).total_seconds() < 600:
            mem["times"] += 1
        else:
            spam_memory[user.id] = {"text": text, "times": 1, "first_time": now}
    else:
        spam_memory[user.id] = {"text": text, "times": 1, "first_time": now}

    if spam_memory[user.id]["times"] >= 3:
        await context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        await message.reply_text(f"تم حذف رسالتك يا {user.first_name} بسبب التكرار! 🚫")
        spam_memory[user.id] = {"text": "", "times": 0, "first_time": now}
        return

    if message.reply_to_message or "@" in text:
        if not await is_user_admin(update, context):
            return

        target = message.reply_to_message.from_user if message.reply_to_message else None
        if not target and "@" in text:
            for entity in message.entities:
                if entity.type == 'mention':
                    username = text[entity.offset:entity.offset + entity.length].replace('@', '')
                    try:
                        member = await context.bot.get_chat_member(chat_id, username)
                        target = member.user
                    except: pass
        
        if not target: return

        command = text.split()[0].lower() if not text.startswith('@') else text.split()[1].lower()

        if command == "حذف":
            await context.bot.delete_message(chat_id=chat_id, message_id=message.reply_to_message.message_id)
            await message.reply_text(f"تم حذف رسالة {target.first_name} 🚫")

        elif command == "طرد":
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=target.id)
            warn_memory[target.id] = 0
            await message.reply_text(f"تم طرد {target.first_name} نهائياً ⛔")

        elif command == "كتم":
            minutes = int(text.split()[-1]) if text.split()[-1].isdigit() else 30
            await context.bot.restrict_chat_member(chat_id=chat_id, user_id=target.id, permissions=ChatPermissions(can_send_messages=False), until_date=datetime.now() + timedelta(minutes=minutes))
            await message.reply_text(f"تم كتم {target.first_name} لمدة {minutes} دقيقة 🔇")

        elif command == "إنذار":
            warn_memory[target.id] = warn_memory.get(target.id, 0) + 1
            if warn_memory[target.id] >= 3:
                await context.bot.restrict_chat_member(chat_id=chat_id, user_id=target.id, permissions=ChatPermissions(can_send_messages=False))
                await message.reply_text(f"⚠️ {target.first_name} لديه 3/3 إنذارات. تم كتمه نهائياً!")
            else:
                await message.reply_text(f"تنبيه {target.mention_html()} ({warn_memory[target.id]}/3) ⚠️", parse_mode='HTML')

        elif command == "إزالة إنذار":
            if warn_memory.get(target.id, 0) > 0:
                warn_memory[target.id] -= 1
                await message.reply_text(f"تمت إزالة إنذار. رصيده الحالي: {warn_memory[target.id]}/3 ✅")

        elif command == "إزالة الكتم":
            await context.bot.restrict_chat_member(chat_id=chat_id, user_id=target.id, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_polls=True, can_send_other_messages=True, can_add_web_page_previews=True))
            warn_memory[target.id] = 0
            await message.reply_text(f"تمت إزالة الكتم عن {target.first_name} بنجاح ✅")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), bot_logic))
    app.run_polling()
