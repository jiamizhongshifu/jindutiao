"""
测试 payment_cache 表和 webhook 回调流程
"""
import os
import sys

# 设置环境变量
os.environ['SUPABASE_URL'] = 'https://your-project.supabase.co'
os.environ['SUPABASE_ANON_KEY'] = 'your-anon-key'

sys.path.insert(0, 'api')

from supabase_client import get_supabase_client

def test_payment_cache_table():
    """测试 payment_cache 表是否存在"""
    try:
        supabase = get_supabase_client()
        
        print("[TEST] 测试查询 payment_cache 表...")
        response = supabase.table('payment_cache').select('*').limit(1).execute()
        
        print(f"[TEST] ✅ payment_cache 表存在! 记录数: {len(response.data)}")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ payment_cache 表不存在或查询失败: {e}")
        return False

def test_insert_cache():
    """测试写入缓存"""
    try:
        from datetime import datetime, timezone
        
        supabase = get_supabase_client()
        
        test_data = {
            'out_trade_no': 'TEST_ORDER_12345',
            'trade_no': 'TEST_ZPAY_67890',
            'status': 'paid',
            'money': '0.10',
            'param': 'test-user-id|pro_monthly',
            'name': '测试订单',
            'type': 'wxpay',
            'paid_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        print("[TEST] 插入测试数据...")
        result = supabase.table('payment_cache').upsert(
            test_data,
            on_conflict='out_trade_no'
        ).execute()
        
        print(f"[TEST] ✅ 插入成功! 受影响行数: {len(result.data)}")
        
        # 查询验证
        print("[TEST] 验证数据...")
        response = supabase.table('payment_cache').select('*').eq(
            'out_trade_no', 'TEST_ORDER_12345'
        ).execute()
        
        if response.data:
            record = response.data[0]
            print(f"[TEST] ✅ 查询成功! status={record['status']}, money={record['money']}")
            
            # 清理测试数据
            print("[TEST] 清理测试数据...")
            supabase.table('payment_cache').delete().eq(
                'out_trade_no', 'TEST_ORDER_12345'
            ).execute()
            print("[TEST] ✅ 清理完成!")
            
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Payment Cache 表测试工具")
    print("=" * 60)
    
    # 测试1: 表是否存在
    if not test_payment_cache_table():
        print("\n⚠️ 请先在 Supabase Dashboard 执行 SQL 创建表!")
        print("SQL 位于: api/payment_cache_schema.sql")
        sys.exit(1)
    
    print()
    
    # 测试2: 插入和查询
    if test_insert_cache():
        print("\n✅ 所有测试通过! payment_cache 表工作正常")
    else:
        print("\n❌ 测试失败,请检查表结构和权限")
        sys.exit(1)
