from supabase import create_client
import os

def get_supabase_client():
    """获取 Supabase 客户端实例"""
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY', '')
    return create_client(SUPABASE_URL, SUPABASE_KEY)

