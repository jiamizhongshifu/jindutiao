#!/bin/bash

echo "=== 详细速率限制测试 ==="
echo ""

for i in {1..7}; do
    echo "=========================================="
    echo "第 $i 次请求..."
    echo ""
    
    # 发送请求并显示完整响应
    curl -i -X POST "https://jindutiao.vercel.app/api/auth-signin" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"test@example.com\",\"password\":\"wrongpassword\"}" \
        2>&1 | grep -E "HTTP/|X-RateLimit|Retry-After|error"
    
    echo ""
    sleep 1
done

echo "=========================================="
echo "=== 测试完成 ==="
