/**
 * 🎵 بوت تليغرام لتعديل معلومات الأغاني عبر Node.js + Telegraf + node-id3
 */

const { Telegraf, Markup } = require('telegraf');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const NodeID3 = require('node-id3');

const BOT_TOKEN = process.env.BOT_TOKEN || 'YOUR_BOT_TOKEN_HERE';
const CHANNEL_USERNAME = process.env.CHANNEL_USERNAME || '@MyMusicChannel';

const bot = new Telegraf(BOT_TOKEN);
const sessions = new Map();

bot.start((ctx) => {
  ctx.reply(
    `👋 أهلاً بك يا ${ctx.from.first_name}!\n\nأنا بوت تعديل وسوم وتفاصيل الأغاني 🎧.\nأرسل لي أي ملف MP3 للبدء.\n\n📢 ${CHANNEL_USERNAME}`
  );
});

bot.on(['audio', 'document'], async (ctx) => {
  const fileObj = ctx.message.audio || ctx.message.document;
  if (!fileObj) return;

  const status = await ctx.reply('⏳ جاري تحميل الملف الصوتي...');
  const fileLink = await ctx.telegram.getFileLink(fileObj.file_id);
  
  const userId = ctx.from.id;
  const userDir = path.join(__dirname, 'temp', String(userId));
  fs.mkdirSync(userDir, { recursive: true });
  const localAudioPath = path.join(userDir, 'song.mp3');

  // تنزيل الملف
  const writer = fs.createWriteStream(localAudioPath);
  const response = await axios({ url: fileLink.href, method: 'GET', responseType: 'stream' });
  response.data.pipe(writer);

  writer.on('finish', async () => {
    // قراءة الوسوم الحالية
    const tags = NodeID3.read(localAudioPath) || {};
    sessions.set(userId, {
      audioPath: localAudioPath,
      title: tags.title || fileObj.title || 'أغنية جديدة',
      artist: tags.artist || fileObj.performer || 'فنان غير معروف',
      album: tags.album || 'غير محدد',
      year: tags.year || '2024',
      thumbPath: null,
      waitingFor: null
    });

    const session = sessions.get(userId);
    await ctx.telegram.editMessageText(
      ctx.chat.id,
      status.message_id,
      undefined,
      `🎵 تم استلام الملف بنجاح!\n\nالعنوان: ${session.title}\nالفنان: ${session.artist}\nالألبوم: ${session.album}\n\nاختر التعديل المطلوب:`,
      Markup.inlineKeyboard([
        [Markup.button.callback('✏️ تعديل العنوان', 'edit_title'), Markup.button.callback('🎤 تعديل الفنان', 'edit_artist')],
        [Markup.button.callback('💿 تعديل الألبوم', 'edit_album'), Markup.button.callback('🖼️ تغيير الغلاف', 'edit_thumb')],
        [Markup.button.callback('✨ حفظ وإرسال الأغنية', 'save_audio')]
      ])
    );
  });
});

bot.action('edit_title', (ctx) => {
  const session = sessions.get(ctx.from.id);
  if (!session) return ctx.answerCbQuery('⚠️ الجلسة منتهية');
  session.waitingFor = 'title';
  ctx.reply('✍️ أرسل العنوان الجديد للأغنية:');
  ctx.answerCbQuery();
});

bot.action('edit_artist', (ctx) => {
  const session = sessions.get(ctx.from.id);
  if (!session) return ctx.answerCbQuery('⚠️ الجلسة منتهية');
  session.waitingFor = 'artist';
  ctx.reply('✍️ أرسل اسم الفنان الجديد:');
  ctx.answerCbQuery();
});

bot.action('edit_album', (ctx) => {
  const session = sessions.get(ctx.from.id);
  if (!session) return ctx.answerCbQuery('⚠️ الجلسة منتهية');
  session.waitingFor = 'album';
  ctx.reply('✍️ أرسل اسم الألبوم الجديد:');
  ctx.answerCbQuery();
});

bot.action('edit_thumb', (ctx) => {
  const session = sessions.get(ctx.from.id);
  if (!session) return ctx.answerCbQuery('⚠️ الجلسة منتهية');
  session.waitingFor = 'thumb';
  ctx.reply('🖼️ أرسل صورة الغلاف الجديد الآن:');
  ctx.answerCbQuery();
});

bot.action('save_audio', async (ctx) => {
  const session = sessions.get(ctx.from.id);
  if (!session) return ctx.answerCbQuery('⚠️ الجلسة منتهية');

  await ctx.answerCbQuery('جاري الحفظ...');
  const progress = await ctx.reply('⚙️ جاري تحديث بيانات الأغنية ورفعها...');

  const newTags = {
    title: session.title,
    artist: session.artist,
    album: session.album,
    year: session.year
  };

  if (session.thumbPath && fs.existsSync(session.thumbPath)) {
    newTags.image = session.thumbPath;
  }

  // كتابة الوسوم
  NodeID3.write(newTags, session.audioPath);

  // إرسال الملف المعدل
  await ctx.replyWithAudio(
    { source: session.audioPath },
    {
      title: session.title,
      performer: session.artist,
      caption: `🎧 ${session.title}\n👤 ${session.artist}\n\nتم التعديل بواسطة ${CHANNEL_USERNAME}`
    }
  );

  await ctx.telegram.deleteMessage(ctx.chat.id, progress.message_id);
  fs.rmSync(path.dirname(session.audioPath), { recursive: true, force: true });
  sessions.delete(ctx.from.id);
});

bot.on('photo', async (ctx) => {
  const session = sessions.get(ctx.from.id);
  if (!session || session.waitingFor !== 'thumb') return;

  const photo = ctx.message.photo[ctx.message.photo.length - 1];
  const link = await ctx.telegram.getFileLink(photo.file_id);
  const userDir = path.dirname(session.audioPath);
  const thumbPath = path.join(userDir, 'cover.jpg');

  const writer = fs.createWriteStream(thumbPath);
  const resp = await axios({ url: link.href, method: 'GET', responseType: 'stream' });
  resp.data.pipe(writer);

  writer.on('finish', () => {
    session.thumbPath = thumbPath;
    session.waitingFor = null;
    ctx.reply('✅ تم استلام صورة الغلاف بنجاح! اضغط على زر حفظ الأغنية لإكمال العملية.');
  });
});

bot.on('text', (ctx) => {
  const session = sessions.get(ctx.from.id);
  if (!session || !session.waitingFor) return;

  const val = ctx.message.text.trim();
  session[session.waitingFor] = val;
  session.waitingFor = null;

  ctx.reply(`✅ تم التحديث!\nاضغط على 'حفظ وإرسال الأغنية' لتطبيق التغييرات.`);
});

bot.launch().then(() => {
  console.log('🤖 بوت Node.js يعمل الآن بنجاح...');
});

process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
