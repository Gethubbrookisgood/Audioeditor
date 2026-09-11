# -*- coding: utf-8 -*-
"""
===========================================================
🎵 بوت تليغرام لتعديل معلومات وتفاصيل الأغاني (Audio Tag Editor Bot)
الإصدار: 2.5.0
المكتبات المستخدمة: Pyrogram + Mutagen + FFmpeg
القناة: @MyMusicChannel
===========================================================
"""

import os
import time
import shutil
import asyncio
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Message
)
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, USLT, APIC
from mutagen.mp3 import MP3

# إعدادات البوت من متغيرات البيئة أو الإعدادات المباشرة
API_ID = 30826860
API_HASH = "4b78b969a0a63b92127de3c507bd99f0"
BOT_TOKEN = "8936664404:AAE7QpudfqQAze1GBfuMmxgnbQY4Ld_4pAo"
CHANNEL_USERNAME = "@epicshitting"

# مجلد العمل المؤقت
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# تخزين حالة المستخدم المؤقتة (User State)
user_data = {}

# إنشاء كائن العميل للبوت
app = Client(
    "SongEditorBot_V2",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


def get_audio_keyboard(user_id: int):
    """لوحة أزرار التحكم في تعديل معلومات الأغنية"""
    buttons = [
        [
            InlineKeyboardButton("✏️ تعديل العنوان", callback_data=f"edit_title_{user_id}"),
            InlineKeyboardButton("🎤 تعديل الفنان", callback_data=f"edit_artist_{user_id}")
        ],
        [
            InlineKeyboardButton("💿 تعديل الألبوم", callback_data=f"edit_album_{user_id}"),
            InlineKeyboardButton("📅 سنة الإصدار", callback_data=f"edit_year_{user_id}")
        ],
        [
            InlineKeyboardButton("🖼️ تغيير صورة الغلاف", callback_data=f"edit_thumb_{user_id}"),
            InlineKeyboardButton("🏷️ نوع الموسيقى", callback_data=f"edit_genre_{user_id}")
        ],
        [
            InlineKeyboardButton("✨ حفظ وإرسال الأغنية المعدلة", callback_data=f"save_audio_{user_id}")
        ],
        [
            InlineKeyboardButton("❌ إلغاء العملية", callback_data=f"cancel_{user_id}")
        ]
    ]
    return InlineKeyboardMarkup(buttons)


@app.on_message(filters.command(["start", "help"]) & filters.private)
async def start_handler(client: Client, message: Message):
    """رسالة الترحيب والتعليمات"""
    welcome_text = (
        f"👋 أهلاً بك يا {message.from_user.first_name} في بوت **تعديل تفاصيل الأغاني**! 🎧\n\n"
        "✨ **ماذا يمكن لهذا البوت فعله؟**\n"
        "• تغيير اسم الأغنية (Title)\n"
        "• تغيير اسم الفنان / المغني (Artist)\n"
        "• تغيير اسم الألبوم (Album)\n"
        "• وضع صورة غلاف مخصصة (Cover / Thumbnail)\n"
        "• تعديل سنة الإنتاج وتصنيف الموسيقى\n\n"
        "🚀 **كيف أبدأ؟**\n"
        "فقط أرسل لي أي ملف صوتي أو أغنية بصيغة **MP3** وسأقوم بالباقي!\n\n"
        f"📢 تابع قناتنا: {CHANNEL_USERNAME}"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 قناة التحديثات", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")]
    ]) if CHANNEL_USERNAME.startswith('@') else None

    await message.reply_text(welcome_text, reply_markup=keyboard)


@app.on_message((filters.audio | filters.document) & filters.private)
async def handle_audio(client: Client, message: Message):
    """استقبال الملف الصوتي واستخراج البيانات الحالية"""
    # التحقق من أن الملف صوتي
    file = message.audio or message.document
    if message.document and not (file.file_name and file.file_name.lower().endswith(('.mp3', '.m4a', '.wav', '.flac'))):
        await message.reply_text("⚠️ يرجى إرسال ملف صوتي بصيغة MP3 صالحة.")
        return

    user_id = message.from_user.id
    status_msg = await message.reply_text("⏳ جاري تنزيل الملف وقراءة البيانات الوصفية (ID3 Tags)...")

    # مسار الحفظ المحلي
    user_folder = os.path.join(DOWNLOAD_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)
    file_path = os.path.join(user_folder, "original.mp3")

    try:
        await message.download(file_name=file_path)
    except Exception as e:
        await status_msg.edit_text(f"❌ حدث خطأ أثناء تنزيل الملف: {str(e)}")
        return

    # استخراج المعلومات المتاحة
    title = "غير محدد"
    artist = "غير محدد"
    album = "غير محدد"
    year = "غير محدد"
    genre = "غير محدد"
    has_cover = False

    try:
        audio = MP3(file_path, ID3=ID3)
        try:
            audio.add_tags()
        except Exception:
            pass

        tags = audio.tags
        if tags:
            if "TIT2" in tags:
                title = str(tags["TIT2"])
            if "TPE1" in tags:
                artist = str(tags["TPE1"])
            if "TALB" in tags:
                album = str(tags["TALB"])
            if "TDRC" in tags:
                year = str(tags["TDRC"])
            if "TCON" in tags:
                genre = str(tags["TCON"])
            for tag in tags.values():
                if isinstance(tag, APIC):
                    has_cover = True
                    break
    except Exception:
        # استخدام بيانات تليغرام في حال تعذر القراءة من mutagen
        if message.audio:
            title = message.audio.title or "غير محدد"
            artist = message.audio.performer or "غير محدد"

    # حفظ حالة المستخدم في الذاكرة
    user_data[user_id] = {
        "file_path": file_path,
        "title": title if title != "غير محدد" else (file.file_name or "أغنية جديدة"),
        "artist": artist if artist != "غير محدد" else "فنان غير معروف",
        "album": album,
        "year": year,
        "genre": genre,
        "thumb_path": None,
        "has_cover": has_cover,
        "waiting_for": None,
        "duration": getattr(message.audio, "duration", 0) if message.audio else 0,
        "original_message_id": message.id
    }

    preview_text = (
        "🎵 **تم استلام الملف الصوتي بنجاح!**\n\n"
        f"🏷️ **العنوان:** `{user_data[user_id]['title']}`\n"
        f"👤 **الفنان:** `{user_data[user_id]['artist']}`\n"
        f"💿 **الألبوم:** `{user_data[user_id]['album']}`\n"
        f"📅 **السنة:** `{user_data[user_id]['year']}`\n"
        f"🎶 **النوع:** `{user_data[user_id]['genre']}`\n"
        f"🖼️ **الغلاف:** {'موجود ✅' if has_cover else 'غير موجود ❌'}\n\n"
        "👇 اختر ما تريد تعديله من الأزرار التالية:"
    )

    await status_msg.edit_text(preview_text, reply_markup=get_audio_keyboard(user_id))


@app.on_callback_query()
async def handle_callback(client: Client, callback_query: CallbackQuery):
    """التعامل مع ضغطات الأزرار المضمنة"""
    data = callback_query.data
    user_id = callback_query.from_user.id

    if user_id not in user_data:
        await callback_query.answer("⚠️ انتهت صلاحية الجلسة، يرجى إعادة إرسال الملف الصوتي.", show_alert=True)
        return

    if data.startswith("edit_title_"):
        user_data[user_id]["waiting_for"] = "title"
        await callback_query.message.reply_text("✍️ أرسل الآن **العنوان الجديد** للأغنية:")
        await callback_query.answer()

    elif data.startswith("edit_artist_"):
        user_data[user_id]["waiting_for"] = "artist"
        await callback_query.message.reply_text("✍️ أرسل الآن **اسم الفنان أو المغني الجديد**:")
        await callback_query.answer()

    elif data.startswith("edit_album_"):
        user_data[user_id]["waiting_for"] = "album"
        await callback_query.message.reply_text("✍️ أرسل الآن **اسم الألبوم**:")
        await callback_query.answer()

    elif data.startswith("edit_year_"):
        user_data[user_id]["waiting_for"] = "year"
        await callback_query.message.reply_text("✍️ أرسل الآن **سنة الإصدار** (مثال: 2024):")
        await callback_query.answer()

    elif data.startswith("edit_genre_"):
        user_data[user_id]["waiting_for"] = "genre"
        await callback_query.message.reply_text("✍️ أرسل الآن **نوع الموسيقى / التصنيف** (مثال: Pop, Arabic, Classic):")
        await callback_query.answer()

    elif data.startswith("edit_thumb_"):
        user_data[user_id]["waiting_for"] = "thumb"
        await callback_query.message.reply_text("🖼️ أرسل الآن **الصورة** التي تريد تعيينها كغلاف للأغنية:")
        await callback_query.answer()

    elif data.startswith("save_audio_"):
        await callback_query.answer("🚀 جاري تطبيق التعديلات ومعالجة الصوت...")
        await process_and_send_audio(client, callback_query.message, user_id)

    elif data.startswith("cancel_"):
        # تنظيف المجلد وحذف الحالة
        user_folder = os.path.join(DOWNLOAD_DIR, str(user_id))
        if os.path.exists(user_folder):
            shutil.rmtree(user_folder, ignore_errors=True)
        user_data.pop(user_id, None)
        await callback_query.message.edit_text("❌ تم إلغاء العملية وحذف الملفات المؤقتة بنجاح.")
        await callback_query.answer()


@app.on_message(filters.photo & filters.private)
async def handle_photo_input(client: Client, message: Message):
    """استقبال صورة الغلاف الجديد"""
    user_id = message.from_user.id
    if user_id not in user_data or user_data[user_id].get("waiting_for") != "thumb":
        return

    thumb_path = os.path.join(DOWNLOAD_DIR, str(user_id), "cover.jpg")
    await message.download(file_name=thumb_path)
    user_data[user_id]["thumb_path"] = thumb_path
    user_data[user_id]["has_cover"] = True
    user_data[user_id]["waiting_for"] = None

    await message.reply_text("✅ تم استلام صورة الغلاف بنجاح! انقر على 'حفظ وإرسال الأغنية' لإتمام التعديل.")


@app.on_message(filters.text & filters.private)
async def handle_text_input(client: Client, message: Message):
    """استقبال النصوص الجديدة للعناوين والأسماء"""
    user_id = message.from_user.id
    if user_id not in user_data or not user_data[user_id].get("waiting_for"):
        return

    field = user_data[user_id]["waiting_for"]
    user_data[user_id][field] = message.text.strip()
    user_data[user_id]["waiting_for"] = None

    labels = {
        "title": "العنوان",
        "artist": "اسم الفنان",
        "album": "الألبوم",
        "year": "سنة الإصدار",
        "genre": "نوع الموسيقى"
    }

    reply_text = (
        f"✅ تم تحديث **{labels.get(field, field)}** إلى: `{message.text.strip()}`\n\n"
        "يمكنك تعديل حقول أخرى أو الضغط على زر الحفظ أدناه:"
    )
    await message.reply_text(reply_text, reply_markup=get_audio_keyboard(user_id))


async def process_and_send_audio(client: Client, message: Message, user_id: int):
    """كتابة الوسوم ID3 داخل ملف MP3 وإعادة إرساله للمستخدم"""
    info = user_data[user_id]
    progress_msg = await message.reply_text("⚙️ جاري كتابة معلومات ID3 Tags ودمج الغلاف في ملف MP3...")

    file_path = info["file_path"]
    thumb_path = info["thumb_path"]

    try:
        # فتح ملف الصوت عبر mutagen
        audio = MP3(file_path, ID3=ID3)
        try:
            audio.add_tags()
        except Exception:
            pass

        # تعيين الوسوم
        if info["title"]:
            audio.tags["TIT2"] = TIT2(encoding=3, text=info["title"])
        if info["artist"]:
            audio.tags["TPE1"] = TPE1(encoding=3, text=info["artist"])
        if info["album"]:
            audio.tags["TALB"] = TALB(encoding=3, text=info["album"])
        if info["year"] and info["year"] != "غير محدد":
            audio.tags["TDRC"] = TDRC(encoding=3, text=str(info["year"]))
        if info["genre"] and info["genre"] != "غير محدد":
            audio.tags["TCON"] = TCON(encoding=3, text=info["genre"])

        # دمج صورة الغلاف إذا وُجدت
        if thumb_path and os.path.exists(thumb_path):
            with open(thumb_path, 'rb') as img_file:
                audio.tags["APIC"] = APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3, # 3 = Cover (front)
                    desc='Cover',
                    data=img_file.read()
                )

        # حفظ التغييرات على الملف الصوتي
        audio.save(v2_version=3)

    except Exception as e:
        await progress_msg.edit_text(f"❌ حدث خطأ أثناء تعديل وسوم الأغنية: {str(e)}")
        return

    await progress_msg.edit_text("📤 جاري رفع الأغنية المعدلة إلى تليغرام...")

    caption = (
        f"🎧 **{info['title']}**\n"
        f"👤 الفنان: **{info['artist']}**\n"
        f"💿 الألبوم: {info['album']}\n"
        f"📅 السنة: {info['year']}\n\n"
        f"✨ تم التعديل بواسطة: {CHANNEL_USERNAME}"
    )

    try:
        await client.send_audio(
            chat_id=message.chat.id,
            audio=file_path,
            caption=caption,
            title=info["title"],
            performer=info["artist"],
            duration=info.get("duration", 0),
            thumb=thumb_path if (thumb_path and os.path.exists(thumb_path)) else None
        )
        await progress_msg.delete()
        await message.reply_text("🎉 **تم تعديل معلومات الأغنية وإرسالها بنجاح!**\nشكراً لاستخدامك البوت.")
    except Exception as e:
        await progress_msg.edit_text(f"❌ فشل رفع الملف: {str(e)}")
    finally:
        # تنظيف المجلدات المؤقتة
        user_folder = os.path.join(DOWNLOAD_DIR, str(user_id))
        shutil.rmtree(user_folder, ignore_errors=True)
        user_data.pop(user_id, None)


if __name__ == "__main__":
    print("=" * 50)
    print("🚀 جاري تشغيل بوت تعديل الأغاني بنجاح...")
    print(f"🤖 معرف القناة: {CHANNEL_USERNAME}")
    print("=" * 50)
    app.run()
