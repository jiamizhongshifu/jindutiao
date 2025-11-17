#!/bin/bash

echo "=== 开始测试速率限制功能 ==="
echo "目标端点: /api/auth-signin"
echo "速率限制: 5次/60秒 (基于IP)"
echo ""

for i in {1..7}; do
    echo "----------------------------------------"
    echo "第 $i 次请求..."

    # 发送请求并捕获响应
    response=$(curl -s -i -X POST "https://jindutiao.vercel.app/api/auth-signin" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"test@example.com\",\"password\":\"wrongpassword\"}")

    # 提取HTTP状态码
    http_code=$(echo "$response" | grep -oP "HTTP/\d\.\d \K\d+" | head -1)

    # 显示状态
    if [ "$http_code" = "429" ]; then
        echo "⚠️  响应状态: $http_code (速率限制触发)"
    elif [ "$http_code" = "401" ]; then
        echo "✅ 响应状态: $http_code (认证失败，速率检查通过)"
    else
        echo "📊 响应状态: $http_code"
    fi

    # 提取并显示速率限制响应头
    rate_limit=$(echo "$response" | grep -i "x-ratelimit-limit:" | cut -d':' -f2 | tr -d ' \r')
    remaining=$(echo "$response" | grep -i "x-ratelimit-remaining:" | cut -d':' -f2 | tr -d ' \r')
    reset=$(echo "$response" | grep -i "x-ratelimit-reset:" | cut -d':' -f2 | tr -d ' \r')
    retry=$(echo "$response" | grep -i "retry-after:" | cut -d':' -f2 | tr -d ' \r')

    if [ ! -z "$rate_limit" ]; then
        echo "   速率限制: $rate_limit 次/时间窗口"
    fi
    if [ ! -z "$remaining" ]; then
        echo "   剩余次数: $remaining"
    fi
    if [ ! -z "$reset" ]; then
        echo "   重置时间: $reset"
    fi
    if [ ! -z "$retry" ]; then
        echo "   重试等待: $retry 秒"
    fi

    sleep 1
done

echo ""
echo "=== 测试完成 ==="
echo "✅ 如果看到第6-7次返回429状态码，说明速率限制正常工作！"
