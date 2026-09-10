# 🎵 بوت تليغرام لتعديل معلومات وتفاصيل الأغاني (Song Tag Editor Bot)

سورس كود احترافي لبوت تليغرام يقوم بتعديل وسوم ملفات MP3 الصوتية (العنوان، اسم الفنان، الألبوم، سنة الإصدار، النوع، صورة الغلاف) بدقة عالية مع حفظ حقوق قناتك.

---

## 🚀 المميزات
- 🎧 دعم كامل لملفات الصوت بصيغة **MP3**.
- ✏️ تعديل اسم الأغنية (Title)، الفنان (Artist)، الألبوم (Album).
- 🖼️ تغيير وتضمين صورة الغلاف (Cover Artwork) داخل الملف الصوتي مباشرة.
- ⚡ واجهة تفاعلية بأزرار تليغرام الشفافة (Inline Keyboard).
- 📦 دعم رفع وتنزيل الملفات حتى 2GB بفضل مكتبة **Pyrogram**.
- 🧹 تنظيف تلقائي للملفات المؤقتة لمنع استهلاك مساحة السيرفر.

---

## 🛠️ متطلبات التشغيل
1. حساب تليغرام وتوكن بوت من [@BotFather](https://t.me/BotFather).
2. `API_ID` و `API_HASH` من [my.telegram.org](https://my.telegram.org).
3. تثبيت **Python 3.9+** و **FFmpeg**.

---

## 💻 طريقة التشغيل محلياً (Local Setup)

```bash
# 1. استنساخ أو فك ضغط المشروع
cd song-editor-bot

# 2. إنشاء بيئة عمل افتراضية (اختياري لكن مفضل)
python -m venv venv
source venv/bin/activate  # في لينكس/ماك
# أو venv\Scripts\activate في ويندوز

# 3. تثبيت المتطلبات
pip install -r requirements.txt

# 4. نسخ ملف الإعدادات وملء البيانات
cp .env.example .env
# قم بفتح .env واكتب التوكن والـ API_ID والـ API_HASH

# 5. تشغيل البوت
python main.py
```

---

## 🌐 الاستضافة المجانية على Render أو Koyeb

1. ارفع الكود إلى مستودع **GitHub**.
2. أنشئ حساباً مجانياً على [Render.com](https://render.com).
3. أنشئ **Background Worker** واختر مستودعك.
4. اضبط **Environment Variables**:
   - `BOT_TOKEN` = توكن البوت
   - `API_ID` = معرف التطبيق
   - `API_HASH` = كود الهاش
   - `CHANNEL_USERNAME` = @MyMusicChannel
5. اضغط على **Deploy** وسيعمل البوت 24/7 دون توقف!

---
حقوق القناة: @MyMusicChannel
