from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👆 بدء الضغط (Tap)", callback_data="start_tap")],
        [InlineKeyboardButton("🎁 المكافأة اليومية", callback_data="daily")],
        [InlineKeyboardButton("🎡 العجلة الدوارة", callback_data="wheel")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")],
        [InlineKeyboardButton("👥 دعوة أصدقاء", callback_data="referral")]
    ])

def ad_button(ad_type):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👀 شاهد الإعلان واحصل على 10 RVT", url=config.MONETAG_AD_URL)],
        [InlineKeyboardButton("✅ تم المشاهدة (تأكيد)", callback_data=f"ad_confirm_{ad_type}")]
    ])

def wheel_webapp():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎡 أدر العجلة الآن", web_app= {"url": config.WEBAPP_URL})]
    ])
