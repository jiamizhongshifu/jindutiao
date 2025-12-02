"""
测试任务回顾窗口修复

手动插入测试数据并触发任务回顾窗口
"""
import sys
from datetime import datetime
from pathlib import Path
from gaiya.data.db_manager import db

def create_test_completions():
    """创建测试任务完成记录（不会被手动推理删除的数据）"""
    date = datetime.now().strftime('%Y-%m-%d')

    # 注意：不要删除所有记录，只删除未确认的
    # 这样可以保留已确认的历史记录

    # 插入测试数据（使用不同的 time_block_id 避免冲突）
    test_tasks = [
        {
            'time_block_id': 'test-00:00-06:00',  # 添加 'test-' 前缀
            'name': '深度睡眠',
            'start_time': '00:00',
            'end_time': '06:00',
            'duration_minutes': 360,
            'completion': 80,
            'confidence': 'high',
            'user_confirmed': True  # 标记为已确认，避免被删除
        },
        {
            'time_block_id': 'test-06:00-07:00',
            'name': '起床准备',
            'start_time': '06:00',
            'end_time': '07:00',
            'duration_minutes': 60,
            'completion': 100,
            'confidence': 'high',
            'user_confirmed': False  # 未确认，会触发回顾窗口
        },
        {
            'time_block_id': 'test-07:00-08:00',
            'name': '早餐时间',
            'start_time': '07:00',
            'end_time': '08:00',
            'duration_minutes': 60,
            'completion': 50,
            'confidence': 'medium',
            'user_confirmed': False  # 未确认，会触发回顾窗口
        },
        {
            'time_block_id': 'test-08:00-09:00',
            'name': '晨间运动',
            'start_time': '08:00',
            'end_time': '09:00',
            'duration_minutes': 60,
            'completion': 75,
            'confidence': 'high',
            'user_confirmed': False  # 未确认，会触发回顾窗口
        },
    ]

    # 先删除之前的测试数据
    conn = db._get_connection()
    try:
        conn.execute("DELETE FROM task_completions WHERE time_block_id LIKE 'test-%' AND date = ?", (date,))
        conn.commit()
        print(f"已清除 {date} 的测试数据")
    finally:
        conn.close()

    for task in test_tasks:
        # 创建任务完成记录
        completion_id = db.create_task_completion(
            date=date,
            time_block_id=task['time_block_id'],
            task_data={
                'name': task['name'],
                'task_type': 'other',
                'start_time': task['start_time'],
                'end_time': task['end_time'],
                'duration_minutes': task['duration_minutes']
            },
            inference_result={
                'completion': task['completion'],
                'confidence': task['confidence'],
                'signal_count': 5,
                'total_weight': 0.8,
                'details': {
                    'focus_duration': 30,
                    'primary_apps': ['测试应用'],
                    'time_match_score': 0.9
                }
            }
        )

        # 如果需要标记为已确认
        if task.get('user_confirmed', False):
            db.update_task_completion_confirmation(
                completion_id=completion_id,
                user_confirmed=True,
                user_corrected=False,
                user_note='测试数据'
            )

    print(f"已插入 {len(test_tasks)} 条测试记录")

    # 验证数据
    unconfirmed = db.get_unconfirmed_task_completions(date)
    print(f"\n未确认任务数: {len(unconfirmed)}")
    for task in unconfirmed:
        print(f"  - {task['task_name']}: {task['completion_percentage']}% ({task['confidence_level']})")

    # 显示已确认的任务
    conn = db._get_connection()
    try:
        cursor = conn.execute(
            "SELECT task_name, completion_percentage FROM task_completions WHERE date = ? AND user_confirmed = 1",
            (date,)
        )
        confirmed = cursor.fetchall()
        if confirmed:
            print(f"\n已确认任务数: {len(confirmed)}")
            for task in confirmed:
                print(f"  - {task[0]}: {task[1]}%")
    finally:
        conn.close()

if __name__ == '__main__':
    create_test_completions()
    print("\n测试数据已准备完成!")
    print("现在可以运行主程序并点击托盘菜单 '今日任务回顾' 来测试窗口显示")
