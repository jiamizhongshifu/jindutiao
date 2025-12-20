from supabase import create_client
import os

def get_supabase_client():
    """
    获取 Supabase 客户端实例

    ⚠️ 服务端使用SERVICE_KEY，可以绕过Row Level Security (RLS)策略
    客户端应使用ANON_KEY，受RLS策略限制
    """
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    # 优先使用SERVICE_KEY（服务端），fallback到ANON_KEY（客户端）
    SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY', '') or os.getenv('SUPABASE_ANON_KEY', '')
    return create_client(SUPABASE_URL, SUPABASE_KEY)

