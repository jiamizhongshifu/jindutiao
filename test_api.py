#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试AI深度分析API"""
import requests
import json

data = {
    'user_id': 'test_user',
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

print('正在调用AI深度分析API...')
try:
    r = requests.post(
        'https://jindutiao.vercel.app/api/analyze-task-completion',
        json=data,
        timeout=60
    )
    print(f'HTTP状态码: {r.status_code}')

    if r.status_code == 200:
        result = r.json()
        print(f'成功! Success: {result.get("success")}')
        print(f'\nAI分析结果:')
        print(result.get('analysis', ''))
    else:
        print(f'错误响应:')
        print(r.text[:500])
except Exception as e:
    print(f'请求失败: {e}')
