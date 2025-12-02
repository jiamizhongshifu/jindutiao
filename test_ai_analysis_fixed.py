#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试修复后的AI深度分析API"""
import requests
import json

data = {
    'user_id': 'test_cli_fixed',
    'user_tier': 'free',
    'date': '2025-12-02',
    'task_completions': [
        {
            'task_name': '早晨锻炼',
            'planned_start_time': '07:00',
            'planned_end_time': '08:00',
            'completion_percentage': 90,
            'confidence_level': 'high'
        },
        {
            'task_name': '编程学习',
            'planned_start_time': '09:00',
            'planned_end_time': '11:00',
            'completion_percentage': 65,
            'confidence_level': 'medium'
        }
    ]
}

print('正在调用AI深度分析API(修复后)...')
print(f'URL: https://jindutiao.vercel.app/api/analyze-task-completion')
print(f'测试数据: {len(data["task_completions"])} 个任务\n')

try:
    r = requests.post(
        'https://jindutiao.vercel.app/api/analyze-task-completion',
        json=data,
        timeout=180
    )
    print(f'HTTP状态码: {r.status_code}')
    print(f'响应时间: {r.elapsed.total_seconds():.2f}秒\n')

    if r.status_code == 200:
        result = r.json()
        print(f'✅ 成功! Success: {result.get("success")}')

        if result.get('fallback'):
            print('⚠️  降级模式: AI服务不可用,返回基于规则的分析\n')
        else:
            print('🎉 AI深度分析成功!\n')

        print('=' * 60)
        print('AI分析结果:')
        print('=' * 60)
        print(result.get('analysis', ''))
        print('=' * 60)

        if 'quota_info' in result:
            quota = result['quota_info']
            print(f'\n配额信息: 已使用 {quota.get("used", 0)}/{quota.get("quota", 0)}')
    else:
        print(f'❌ 错误响应 ({r.status_code}):')
        try:
            error_data = r.json()
            print(json.dumps(error_data, indent=2, ensure_ascii=False))
        except:
            print(r.text[:500])
except requests.exceptions.Timeout:
    print('⏱️  请求超时(180秒)')
except Exception as e:
    print(f'❌ 请求失败: {type(e).__name__}: {e}')
