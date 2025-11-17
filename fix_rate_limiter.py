#!/usr/bin/env python3
"""修复rate_limiter.py的时间解析问题"""

with open("api/rate_limiter.py", "r", encoding="utf-8") as f:
    content = f.read()

# 原始代码
old_code = '''            # 检查是否超过限制
            if current_count >= max_requests:
                # 计算重置时间
                if response.data:
                    oldest_request = min(response.data, key=lambda x: x["created_at"])
                    reset_at = datetime.fromisoformat(oldest_request["created_at"].replace("Z", "+00:00")) + timedelta(seconds=window_seconds)
                else:
                    reset_at = now + timedelta(seconds=window_seconds)

                print(f"[RATE_LIMITER] 🚫 速率限制触发: {endpoint}, key={limit_key}, {current_count}/{max_requests}", file=sys.stderr)'''

# 修复后的代码
new_code = '''            # 检查是否超过限制
            if current_count >= max_requests:
                # 计算重置时间
                if response.data:
                    oldest_request = min(response.data, key=lambda x: x["created_at"])

                    # ✅ 修复: 处理Supabase返回的datetime对象或字符串
                    created_at = oldest_request["created_at"]
                    if isinstance(created_at, str):
                        # 字符串格式，需要解析
                        oldest_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    else:
                        # 已经是datetime对象，直接使用
                        oldest_time = created_at

                    # 确保时区一致（转换为UTC）
                    if oldest_time.tzinfo is not None:
                        oldest_time = oldest_time.replace(tzinfo=None)

                    reset_at = oldest_time + timedelta(seconds=window_seconds)
                else:
                    reset_at = now + timedelta(seconds=window_seconds)

                print(f"[RATE_LIMITER] 🚫 速率限制触发: {endpoint}, key={limit_key}, {current_count}/{max_requests}", file=sys.stderr)'''

# 替换
if old_code in content:
    content = content.replace(old_code, new_code)
    with open("api/rate_limiter.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("[OK] Fixed successfully!")
else:
    print("[ERROR] Pattern not found")
