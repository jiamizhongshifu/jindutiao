"""
清理测试数据

删除所有 test- 前缀的任务完成记录
"""
from datetime import datetime
from gaiya.data.db_manager import db

def clean_test_data():
    """清理所有测试数据"""
    date = datetime.now().strftime('%Y-%m-%d')

    conn = db._get_connection()
    try:
        # 查询要删除的记录
        cursor = conn.execute(
            "SELECT id, task_name, completion_percentage FROM task_completions WHERE time_block_id LIKE 'test-%'"
        )
        test_records = cursor.fetchall()

        if not test_records:
            print("没有找到测试数据")
            return

        print(f"找到 {len(test_records)} 条测试记录:")
        for record in test_records:
            print(f"  - {record[1]}: {record[2]}%")

        # 删除测试记录
        conn.execute("DELETE FROM task_completions WHERE time_block_id LIKE 'test-%'")
        conn.commit()

        print(f"\n已成功删除 {len(test_records)} 条测试记录")

    finally:
        conn.close()

if __name__ == '__main__':
    clean_test_data()
