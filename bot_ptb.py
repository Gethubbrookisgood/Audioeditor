# -*- coding: utf-8 -*-
"""
===========================================================
🎵 بوت تعديل الأغاني عبر مكتبة python-telegram-bot (v20+)
لا يتطلب سوى Bot Token من @BotFather دون الحاجة لـ API ID/HASH!
===========================================================
"""

import os
import shutil
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, APIC
from mutagen.mp3 import MP3

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "@MyMusicChannel")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    text = (
        f"👋 أهلاً بك {user_name}!\n\n"
        "أنا بوت تعديل وسوم ومعلومات الأغاني 🎵.\n"
        "أرسل لي أي ملف MP3 وسأساعدك على تعديل العنوان، الفنان، الألبوم، والغلاف!\n\n"
        f"قناتنا: {CHANNEL_USERNAME}"
    )
    await update.message.reply_text(text)

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    audio = msg.audio or msg.document
    
    if not audio:
        return

    wait_msg = await msg.reply_text("⏳ جاري تنزيل الملف الصوتي...")
    
    user_id = update.effective_user.id
    user_dir = f"temp_{user_id}"
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, "song.mp3")
    
    # تحميل الملف الصوتي
    tg_file = await audio.get_file()
    await tg_file.download_to_drive(custom_path=file_path)
    
    # استخراج العنوان والفنان الحالي
    title = getattr(audio, 'title', None) or "أغنية جديدة"
    performer = getattr(audio, 'performer', None) or "فنان غير معروف"
    
    context.user_data['file_path'] = file_path
    context.user_data['title'] = title
    context.user_data['performer'] = performer
    context.user_data['album'] = "غير محدد"
    context.user_data['year'] = "2024"
    context.user_data['thumb_path'] = None
    
    keyboard = [
        [
            InlineKeyboardButton("✏️ تعديل العنوان", callback_data="set_title"),
            InlineKeyboardButton("🎤 تعديل الفنان", callback_data="set_artist")
        ],
        [
            InlineKeyboardButton("💿 تعديل الألبوم", callback_data="set_album"),
            InlineKeyboardButton("🖼️ تغيير الغلاف", callback_data="set_thumb")
        ],
        [
            InlineKeyboardButton("✅ حفظ وإرسال الأغنية", callback_data="finish_save")
        ]
    ]
    
    await wait_msg.edit_text(
        f"🎵 **تم استقبال الملف بنجاح!**\n\n"
        f"العنوان الحالي: `{title}`\n"
        f"الفنان الحالي: `{performer}`\n\n"
        "اختر ما تريد تعديله:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    
    if action == "set_title":
        context.user_data['next_step'] = 'title'
        await query.message.reply_text("✍️ أرسل الآن العنوان الجديد:")
    elif action == "set_artist":
        context.user_data['next_step'] = 'artist'
        await query.message.reply_text("✍️ أرسل اسم الفنان الجديد:")
    elif action == "set_album":
        context.user_data['next_step'] = 'album'
        await query.message.reply_text("✍️ أرسل اسم الألبوم الجديد:")
    elif action == "set_thumb":
        context.user_data['next_step'] = 'thumb'
        await query.message.reply_text("🖼️ أرسل الآن صورة الغلاف الجديد:")
    elif action == "finish_save":
        await save_and_send(update, context, query.message)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get('next_step')
    if not step:
        return
        
    text = update.message.text.strip()
    if step == 'title':
        context.user_data['title'] = text
    elif step == 'artist':
        context.user_data['performer'] = text
    elif step == 'album':
        context.user_data['album'] = text
        
    context.user_data['next_step'] = None
    await update.message.reply_text(
        f"✅ تم التحديث! اضغط على 'حفظ وإرسال' أو أرسل أمراً آخر.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ حفظ وإرسال", callback_data="finish_save")]])
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('next_step') == 'thumb':
        photo = update.message.photo[-1]
        user_id = update.effective_user.id
        thumb_path = f"temp_{user_id}/cover.jpg"
        tg_file = await photo.get_file()
        await tg_file.download_to_drive(custom_path=thumb_path)
        context.user_data['thumb_path'] = thumb_path
        context.user_data['next_step'] = None
        await update.message.reply_text("✅ تم استلام صورة الغلاف بنجاح!")

async def save_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE, message):
    file_path = context.user_data.get('file_path')
    if not file_path or not os.path.exists(file_path):
        await message.reply_text("⚠️ لم يتم العثور على الملف، يرجى إعادة إرساله.")
        return
        
    status = await message.reply_text("⚙️ جاري تحديث بيانات ID3 ودمج الغلاف...")
    
    try:
        audio = MP3(file_path, ID3=ID3)
        try:
            audio.add_tags()
        except Exception:
            pass
            
        audio.tags["TIT2"] = TIT2(encoding=3, text=context.user_data.get('title', ''))
        audio.tags["TPE1"] = TPE1(encoding=3, text=context.user_data.get('performer', ''))
        audio.tags["TALB"] = TALB(encoding=3, text=context.user_data.get('album', ''))
        
        thumb_path = context.user_data.get('thumb_path')
        if thumb_path and os.path.exists(thumb_path):
            with open(thumb_path, 'rb') as img:
                audio.tags["APIC"] = APIC(
                    encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img.read()
                )
        audio.save(v2_version=3)
    except Exception as e:
        await status.edit_text(f"❌ حدث خطأ في الوسوم: {e}")
        return
        
    await status.edit_text("📤 جاري رفع الملف الصوتي...")
    
    with open(file_path, 'rb') as audio_file:
        thumb_file = open(thumb_path, 'rb') if thumb_path and os.path.exists(thumb_path) else None
        caption = f"🎵 {context.user_data.get('title')}\n👤 {context.user_data.get('performer')}\n\n{CHANNEL_USERNAME}"
        
        await update.effective_chat.send_audio(
            audio=audio_file,
            title=context.user_data.get('title'),
            performer=context.user_data.get('performer'),
            caption=caption,
            thumbnail=thumb_file
        )
        if thumb_file:
            thumb_file.close()
            
    await status.delete()
    # تنظيف
    user_id = update.effective_user.id
    shutil.rmtree(f"temp_{user_id}", ignore_errors=True)
    context.user_data.clear()

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.AUDIO | filters.Document.AUDIO, handle_audio))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("🤖 البوت يعمل الآن بنجاح عبر Polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
