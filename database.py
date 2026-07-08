from supabase import create_client
import config
from datetime import datetime, timedelta

supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def get_user(user_id):
    res = supabase.table("users").select("*").eq("id", user_id).execute()
    return res.data[0] if res.data else None

def create_user(user_id, username, first_name, referrer_id=None):
    data = {
        "id": user_id,
        "username": username,
        "first_name": first_name,
        "referrer_id": referrer_id,
        "created_at": datetime.utcnow().isoformat()
    }
    supabase.table("users").insert(data).execute()
    # تحديث عدد الإحالات للمُحيل
    if referrer_id:
        supabase.table("users").update({"referral_count": supabase.rpc("increment", {"x": 1})}).eq("id", referrer_id).execute()
    return get_user(user_id)

def start_tap_session(user_id):
    data = {"user_id": user_id, "start_time": datetime.utcnow().isoformat()}
    res = supabase.table("tap_sessions").insert(data).execute()
    return res.data[0]["id"]

def increment_tap_count(session_id):
    # تستدعي الدالة التي أنشأناها في Supabase
    res = supabase.rpc("increment_tap", {"session_id": session_id}).execute()
    return res

def finish_tap_session(session_id, user_id):
    # جلب عدد الضغطات وإنهاء الجلسة
    res = supabase.table("tap_sessions").select("tap_count").eq("id", session_id).execute()
    tap_count = res.data[0]["tap_count"]
    tokens = (tap_count // 1000) * 10

    # تخفيض المكافأة إذا كان المستخدمون > 10000
    total_users = get_total_users()
    if total_users >= 10000:
        tokens = tokens * 0.5

    # تحديث الرصيد
    if tokens > 0:
        supabase.rpc("increment_balance", {"uid": user_id, "amount": tokens}).execute()

    # تحديث حالة الجلسة
    supabase.table("tap_sessions").update({
        "end_time": datetime.utcnow().isoformat(),
        "tokens_earned": tokens,
        "completed": True
    }).eq("id", session_id).execute()
    
    return tap_count, tokens

def claim_daily(user_id):
    today = datetime.utcnow().date()
    user = get_user(user_id)
    last = user.get("last_daily_claim")
    
    if last == today.isoformat():
        return None, "لقد حصلت عليها اليوم بالفعل!"
    
    # حساب التسلسل
    if last and datetime.fromisoformat(last).date() == today - timedelta(days=1):
        streak = user.get("daily_streak", 0) + 1
    else:
        streak = 1
    
    reward_rvt = 10 * streak
    reward_usdt = 0
    if streak == 7:
        reward_usdt = 1
    elif streak == 30:
        reward_usdt = 5

    # تخفيض 50% عند 10000 مستخدم
    total_users = get_total_users()
    if total_users >= 10000:
        reward_rvt = reward_rvt * 0.5

    # تحديث قاعدة البيانات
    supabase.table("users").update({
        "daily_streak": streak,
        "last_daily_claim": today.isoformat()
    }).eq("id", user_id).execute()
    
    if reward_rvt > 0:
        supabase.rpc("increment_balance", {"uid": user_id, "amount": reward_rvt}).execute()
    if reward_usdt > 0:
        supabase.rpc("increment_usdt", {"uid": user_id, "amount": reward_usdt}).execute()
    
    # تسجيل في daily_rewards
    supabase.table("daily_rewards").insert({
        "user_id": user_id,
        "claim_date": today.isoformat(),
        "reward_amount": reward_rvt,
        "day_number": streak
    }).execute()
    
    return streak, reward_rvt, reward_usdt

def spin_wheel(user_id):
    import random
    prizes = [
        {"type": "USDT", "value": 1.0},
        {"type": "RVT", "value": 100.0},
        {"type": "USDT", "value": 0.5},
        {"type": "RVT", "value": 50.0},
        {"type": "USDT", "value": 0.0},
        {"type": "USDT", "value": 1.0},
        {"type": "RVT", "value": 10.0}
    ]
    prize = random.choice(prizes)
    
    # تخفيض 50% عند 10000 مستخدم
    total_users = get_total_users()
    if total_users >= 10000:
        prize["value"] = prize["value"] * 0.5
    
    # تحديث الرصيد
    if prize["type"] == "RVT" and prize["value"] > 0:
        supabase.rpc("increment_balance", {"uid": user_id, "amount": prize["value"]}).execute()
    elif prize["type"] == "USDT" and prize["value"] > 0:
        supabase.rpc("increment_usdt", {"uid": user_id, "amount": prize["value"]}).execute()
    
    # تسجيل الدوران
    supabase.table("wheel_spins").insert({
        "user_id": user_id,
        "prize_type": prize["type"],
        "prize_value": prize["value"]
    }).execute()
    
    return prize

def watch_ad(user_id, ad_type):
    today = datetime.utcnow().date()
    # حساب عدد الإعلانات اليوم
    count_res = supabase.table("ad_views").select("id", count="exact") \
        .eq("user_id", user_id) \
        .gte("view_time", today.isoformat()) \
        .execute()
    
    if count_res.count >= 20:
        return False, "لقد وصلت للحد الأقصى اليومي (20 إعلان)."
    
    reward = 10.0
    total_users = get_total_users()
    if total_users >= 10000:
        reward = 5.0  # 50%
    
    supabase.rpc("increment_balance", {"uid": user_id, "amount": reward}).execute()
    supabase.table("ad_views").insert({
        "user_id": user_id,
        "ad_type": ad_type,
        "reward": reward
    }).execute()
    return True, reward

def get_total_users():
    res = supabase.table("users").select("id", count="exact").execute()
    return res.count

def get_user_stats(user_id):
    user = get_user(user_id)
    total = get_total_users()
    return user, total
