"""
测试Token加密存储功能
验证keyring集成是否正常工作
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gaiya.core.auth_client import AuthClient


def test_token_encryption():
    """测试Token加密存储和读取"""
    print("=" * 50)
    print("测试Token加密存储功能")
    print("=" * 50)

    # 1. 创建AuthClient实例
    print("\n[1] 创建AuthClient实例...")
    client = AuthClient()
    print(f"   keyring可用: {client.__class__.__module__}")

    # 2. 清除旧数据（如果存在）
    print("\n[2] 清除旧的Token数据...")
    client._clear_tokens()

    # 3. 保存测试Token
    print("\n[3] 保存测试Token...")
    test_access_token = "test_access_token_12345"
    test_refresh_token = "test_refresh_token_67890"
    test_user_info = {
        "id": "test-uuid-1234",
        "email": "test@example.com",
        "username": "test_user"
    }
    client._save_tokens(test_access_token, test_refresh_token, test_user_info)

    # 验证内存中的Token
    assert client.access_token == test_access_token, "[FAIL] access_token不匹配"
    assert client.refresh_token == test_refresh_token, "[FAIL] refresh_token不匹配"
    assert client.user_info == test_user_info, "[FAIL] user_info不匹配"
    print("   [PASS] Token已保存到内存")

    # 4. 创建新实例，验证从加密存储读取
    print("\n[4] 创建新实例，验证从加密存储读取...")
    client2 = AuthClient()

    # 验证读取的Token
    assert client2.access_token == test_access_token, "[FAIL] 读取的access_token不匹配"
    assert client2.refresh_token == test_refresh_token, "[FAIL] 读取的refresh_token不匹配"
    assert client2.user_info == test_user_info, "[FAIL] 读取的user_info不匹配"
    print("   [PASS] Token已从加密存储读取并验证")

    # 5. 测试清除Token
    print("\n[5] 测试清除Token...")
    client2._clear_tokens()
    assert client2.access_token is None, "[FAIL] access_token未清除"
    assert client2.refresh_token is None, "[FAIL] refresh_token未清除"
    assert client2.user_info is None, "[FAIL] user_info未清除"
    print("   [PASS] Token已清除")

    # 6. 验证清除后重新读取为空
    print("\n[6] 验证清除后重新读取为空...")
    client3 = AuthClient()
    assert client3.access_token is None, "[FAIL] 清除后仍能读取到access_token"
    assert client3.refresh_token is None, "[FAIL] 清除后仍能读取到refresh_token"
    print("   [PASS] 清除成功，无法读取到Token")

    print("\n" + "=" * 50)
    print("[SUCCESS] 所有测试通过！Token加密存储功能正常")
    print("=" * 50)


if __name__ == "__main__":
    try:
        test_token_encryption()
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
