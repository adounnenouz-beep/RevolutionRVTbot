import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
MONETAG_AD_URL = os.getenv("MONETAG_AD_URL")
WEBAPP_URL = os.getenv("WEBAPP_URL")  # هذا سيكون رابط Netlify
