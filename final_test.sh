#!/bin/bash

echo "=== 最终速率限制测试 ==="
echo ""

for i in {1..7}; do
    echo "第 $i 次请求..."
    
    response=$(curl -i -X POST "https://jindutiao.vercel.app/api/auth-signin" \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","password":"wrongpassword"}' 2>&1)
    
    # 提取关键信息（注意是小写的ratelimit）
    status=$(echo "$response" | grep "HTTP/1.1" | tail -1 | awk '{print $2}')
    remaining=$(echo "$response" | grep -i "x-ratelimit-remaining:" | awk '{print $2}' | tr -d '\r')
    
    if [ "$status" = "429" ]; then
        echo "   ⚠️  状态码: $status (速率限制触发！)"
        retry_after=$(echo "$response" | grep -i "retry-after:" | awk '{print $2}' | tr -d '\r')
        echo "   重试等待: $retry_after 秒"
    else
        echo "   状态码: $status"
        echo "   剩余次数: $remaining"
    fi
    
    echo ""
    sleep 1
done

echo "=== 测试完成 ==="
