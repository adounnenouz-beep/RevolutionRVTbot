import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
import database as db
import keyboards as kb
import config

# تخزين المهام المؤقتة للضغط
tap_timers = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    referrer_id = None
    if context.args and context.args[0].startswith("ref_"):
        try:
            referrer_id = int(context.args[0].split("_")[1])
        except: pass

    existing = db.get_user(user.id)
    if not existing:
        db.create_user(user.id, user.username, user.first_name, referrer_id)
        await update.message.reply_text(f"مرحباً {user.first_name}! أهلاً بك في ثورة Revolution RVT 🚀")
    else:
        await update.message.reply_text(f"مرحباً بعودتك {user.first_name}!")
    
    await update.message.reply_text("اختر أحد الخيارات:", reply_markup=kb.main_menu())

async def start_tap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if context.user_data.get("tap_session"):
        await query.edit_message_text("⚠️ لديك جلسة مفتوحة بالفعل! انتظر حتى تنتهي.")
        return

    session_id = db.start_tap_session(user_id)
    context.user_data["tap_session"] = session_id
    context.user_data["tap_count"] = 0

    msg = await query.edit_message_text(
        text=f"⏱️ لديك دقيقة واحدة! اضغط على الزر أدناه بأسرع ما يمكن.\nالضغطات: 0",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👆 اضغط هنا!", callback_data=f"tap_click_{session_id}")],
            [InlineKeyboardButton("⏹️ إنهاء مبكر", callback_data="tap_end")]
        ])
    )
    context.user_data["tap_msg_id"] = msg.message_id

    async def end_tap():
        await asyncio.sleep(60)
        if context.user_data.get("tap_session") == session_id:
            await finish_tap_session(update, context, session_id)
    
    task = asyncio.create_task(end_tap())
    tap_timers[session_id] = task

async def tap_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session_id = int(query.data.split("_")[2])
    
    if context.user_data.get("tap_session") != session_id:
        await query.edit_message_text("انتهت الجلسة! ابدأ جلسة جديدة.")
        return
    
    db.increment_tap_count(session_id)
    old_text = query.message.text
    import re
    match = re.search(r'الضغطات: (\d+)', old_text)
    count = int(match.group(1)) + 1 if match else 1
    new_text = old_text.replace(f'الضغطات: {count-1}', f'الضغطات: {count}')
    await query.edit_message_text(text=new_text, reply_markup=query.message.reply_markup)

async def finish_tap_session(update, context, session_id):
    user_id = update.effective_user.id
    tap_count, tokens = db.finish_tap_session(session_id, user_id)
    
    if session_id in tap_timers:
        tap_timers[session_id].cancel()
        del tap_timers[session_id]
    
    context.user_data.pop("tap_session", None)
    msg = f"✅ انتهت الدقيقة!\nالضغطات: {tap_count}\nالأرباح: {tokens} RVT"
    
    await update.effective_message.reply_text(
        f"{msg}\n\n👀 شاهد الإعلان للحصول على مكافأة إضافية!",
        reply_markup=kb.ad_button("tap")
    )
    await update.effective_message.reply_text("اختر خياراً آخر:", reply_markup=kb.main_menu())

async def tap_end_early(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session_id = context.user_data.get("tap_session")
    if session_id:
        await finish_tap_session(update, context, session_id)
    else:
        await query.edit_message_text("لا توجد جلسة نشطة.")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    result = db.claim_daily(user_id)
    if len(result) == 2:
        await query.edit_message_text(f"⚠️ {result[1]}", reply_markup=kb.main_menu())
        return
    
    streak, rvt, usdt = result
    text = f"🎉 اليوم رقم {streak}!\nحصلت على {rvt} RVT"
    if usdt > 0:
        text += f" و {usdt} USDT 🪙"
    text += "\n\n👀 شاهد الإعلان لمضاعفة الحماس!"
    
    await query.edit_message_text(text, reply_markup=kb.ad_button("daily"))

async def wheel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🎡 اضغط على الزر لفتح العجلة الدوارة:\n(الجوائز: 1 USDT, 100 RVT, 0.5 USDT, 50 RVT, 0, 1 USDT, 10 RVT)",
        reply_markup=kb.wheel_webapp()
    )

async def wheel_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.effective_message.web_app_data.data
    import json
    try:
        json_data = json.loads(data)
        prize_text = json_data.get("prize", "0 RVT")
    except:
        prize_text = "0 RVT"
    
    user_id = update.effective_user.id
    prize = db.spin_wheel(user_id)
    
    await update.effective_message.reply_text(
        f"🎡 العجلة تدور...\n🎁 لقد ربحت: {prize['value']} {prize['type']}!",
        reply_markup=kb.ad_button("wheel")
    )
    await update.effective_message.reply_text("اختر خياراً آخر:", reply_markup=kb.main_menu())

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user, total = db.get_user_stats(user_id)
    
    text = f"📊 **إحصائيات البوت**\n"
    text += f"👥 إجمالي المستخدمين: {total}\n"
    text += f"💰 رصيدك RVT: {user['balance']}\n"
    text += f"🪙 رصيدك USDT: {user['usdt_balance']}\n"
    text += f"🔥 التسلسل اليومي: {user['daily_streak']} يوم\n"
    text += f"👫 عدد المدعوين: {user['referral_count']}\n"
    text += f"🖱️ إجمالي ضغطاتك: {user['total_taps']}"
    
    await query.edit_message_text(text, reply_markup=kb.main_menu())

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    link = f"https://t.me/{(await context.bot.get_me()).username}?start=ref_{user_id}"
    await query.edit_message_text(
        f"👥 شارك الرابط مع أصدقائك!\n\n{link}\n\nكلما دعوت شخصاً، تكسب نسبة من أرباحه!",
        reply_markup=kb.main_menu()
    )

async def ad_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    ad_type = query.data.split("_")[2]
    
    success, reward = db.watch_ad(user_id, ad_type)
    if not success:
        await query.edit_message_text(f"⚠️ {reward}", reply_markup=kb.main_menu())
    else:
        await query.edit_message_text(f"✅ شكراً! حصلت على {reward} RVT مقابل مشاهدة الإعلان.", reply_markup=kb.main_menu())

async def roadmap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
📅 **خريطة طريق Revolution (RVT)**

🚀 **المرحلة 1**: إطلاق تجريبي (100 مستخدم)
✅ نظام الضغط والمكافآت اليومية

⚡ **المرحلة 2**: الوصول إلى 10,000 مستخدم
🔻 تخفيض المكافآت إلى 50%
🔄 إطلاق العجلة الدوارة والإحالات

🏦 **المرحلة 3**: الوصول إلى 1,000,000 مستخدم
💰 توزيع أول مكافآت USDT للمستخدمين النشطين

🌍 **المرحلة 4**: الوصول إلى 5,000,000 مستخدم
📈 الإدراج في منصات OKX, Bitget, Gate.io
🎁 توزيع المكافآت في محافظ المستخدمين
"""
    await update.effective_message.reply_text(text, reply_markup=kb.main_menu())
