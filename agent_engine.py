import json
import uuid
import time
from utils import get_db_connection

def create_task(user_id: str, action: str, source_data: dict, cost_points: int):
    """创建任务并扣减积分"""
    task_id = f"ozon_{uuid.uuid4().hex[:8]}"
    payload = json.dumps({"action": action, "data": source_data}, ensure_ascii=False)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 检查积分
        cursor.execute("SELECT credits FROM user_credits WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        if not row or row['credits'] < cost_points:
            return None, "❌ 积分不足！"
        
        # 扣减积分并写入任务
        cursor.execute("UPDATE user_credits SET credits = credits - ? WHERE user_id=?", (cost_points, user_id))
        cursor.execute("""
            INSERT INTO ai_tasks (task_id, status, user_id, payload, cost)
            VALUES (?, 'pending', ?, ?, ?)
        """, (task_id, user_id, payload, cost_points))
        
        # 合规日志
        cursor.execute("INSERT INTO compliance_log (task_id, action, detail) VALUES (?, 'create', '任务创建成功')", (task_id,))
        
    return task_id, "✅ 发布成功！后台正在处理..."

def process_task(task_id: str):
    """Agent处理引擎（含中国合规风控）"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ai_tasks WHERE task_id=?", (task_id,))
        task = cursor.fetchone()
        
        if not task or task['status'] != 'pending':
            return
            
        cursor.execute("UPDATE ai_tasks SET status='processing', updated_at=CURRENT_TIMESTAMP WHERE task_id=?", (task_id,))
        cursor.execute("INSERT INTO compliance_log (task_id, action, detail) VALUES (?, 'start_processing', 'Agent接单')", (task_id,))

    # 提取数据（防崩处理）
    try:
        payload_dict = json.loads(task['payload'])
        text_data = str(payload_dict.get('data', ''))
    except Exception:
        text_data = ""

    # 合规拦截
    sensitive_words = ["违禁词", "政治敏感", "刷单", "翻墙"]
    if any(kw in text_data for kw in sensitive_words):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE ai_tasks SET status='failed_compliance', result='触发风控，已退回积分', updated_at=CURRENT_TIMESTAMP WHERE task_id=?", (task_id,))
            cursor.execute("UPDATE user_credits SET credits = credits + ? WHERE user_id=?", (task['cost'], task['user_id']))
            cursor.execute("INSERT INTO compliance_log (task_id, action, detail) VALUES (?, 'failed_compliance', '包含敏感词拦截')", (task_id,))
        return

    # 模拟 AI 处理时长
    time.sleep(1.5)
    
    # 模拟成功结果
    result_data = {
        "title_ru": "Беспроводные наушники с шумоподавлением и долгим временем работы",
        "seo_keywords": ["наушники", "bluetooth", "Ozon SEO", "降噪耳机"],
        "confidence": 0.97
    }
    result_json = json.dumps(result_data, ensure_ascii=False)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE ai_tasks SET status='completed', result=?, updated_at=CURRENT_TIMESTAMP WHERE task_id=?", (result_json, task_id))
        cursor.execute("INSERT INTO compliance_log (task_id, action, detail) VALUES (?, 'completed', 'AI生成结果通过审核')", (task_id,))
        
        # 平台抽成 10%
        platform_take = int(task['cost'] * 0.1)
        cursor.execute("UPDATE user_credits SET credits = credits + ? WHERE user_id='platform'", (platform_take,))

def get_user_tasks(user_id: str):
    """获取用户任务列表"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT task_id, status, result, datetime(created_at, 'localtime') as created_at FROM ai_tasks WHERE user_id=? ORDER BY created_at DESC", (user_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

