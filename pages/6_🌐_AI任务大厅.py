# -*- coding: utf-8 -*-
import streamlit as st
import time
import json
import os
import sys

# 动态加载底层依赖
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_db_connection, sidebar_footer
from agent_engine import create_task, process_task, get_user_tasks

st.set_page_config(page_title="AI 任务大厅", page_icon="🌐", layout="wide")
sidebar_footer()

# 当前测试环境默认账号
USER_ID = "seller_001"

def get_credits(user_id):
    """安全获取用户积分"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT credits FROM user_credits WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        return row['credits'] if row else 0

# --- 高级黑金/蓝紫视觉 CSS ---
st.markdown("""
<style>
    .hall-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 8px 32px rgba(30, 60, 114, 0.3);
    }
    .hall-title {
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .hall-subtitle {
        font-size: 1.2rem;
        color: #e0e7ff;
        margin-top: 0.5rem;
        font-weight: 300;
    }
</style>
""", unsafe_allow_html=True)

# --- 头部渲染 ---
st.markdown("""
<div class="hall-header">
    <h1 class="hall-title">🌐 Agent 任务发布大厅</h1>
    <p class="hall-subtitle">让人类与 AI 在这里协同工作,自动搞定跨境电商脏活累活。</p>
</div>
""", unsafe_allow_html=True)

# 获取并展示积分
current_credits = get_credits(USER_ID)
col1, col2, col3 = st.columns([1, 1, 1])
with col3:
    st.metric(label="🪙 您的剩余算力积分", value=f"{current_credits:,}")

st.markdown("---")

# --- 核心交互区 ---
tabs = st.tabs(["📝 发包中心", "📋 我的任务队列"])

# Tab 1: 发布任务
with tabs[0]:
    st.markdown("### 🚀 发布新任务")
    task_action = st.selectbox(
        "📌 选择任务类型",
        ["Ozon 俄语 SEO 深度优化", "竞品差评痛点分析", "客服自动回复生成"]
    )
    
    task_data = st.text_area(
        "📄 输入要处理的数据",
        placeholder="请在此粘贴商品描述、竞品链接或买家留言...",
        height=150
    )
    
    cost = 50
    st.info(f"💡 本次任务预估将扣除 {cost} 积分，平台将自动为您匹配最优 Agent 执行。")
    
    if st.button("🚀 提交并让 Agent 执行", type="primary", use_container_width=True):
        if not task_data.strip():
            st.warning("⚠️ 请输入需处理的任务数据！")
        else:
            task_id, msg = create_task(USER_ID, task_action, {"input": task_data}, cost)
            if not task_id:
                st.error(msg)  # 积分不足等报错
            else:
                st.toast("✅ 任务已挂载至底层队列！")
                # 模拟后端 Worker 进程异步处理
                with st.spinner("⚡ AI Agent 正在云端接单并处理中..."):
                    process_task(task_id)
                st.success("🎉 任务执行完毕！")
                time.sleep(1.5)
                st.rerun()

# Tab 2: 任务队列
with tabs[1]:
    st.markdown("### 📋 历史发包记录")
    tasks = get_user_tasks(USER_ID)
    
    if not tasks:
        st.info("暂无任务记录，快去发包中心试试吧！")
    else:
        status_map = {
            'completed': '✅ 已完成',
            'pending': '⏳ 等待接单',
            'processing': '🔄 处理中',
            'failed_compliance': '🔴 违规拦截'
        }
        
        for t in tasks:
            status_emoji = status_map.get(t['status'], '❓ 未知状态')
            with st.expander(f"{status_emoji} | 任务单号: {t['task_id']} | 发布时间: {t['created_at']}"):
                if t['status'] == 'failed_compliance':
                    st.error(f"**拦截原因:** {t['result']}")
                elif t['result']:
                    try:
                        # 尝试美化输出 JSON 结果
                        res_json = json.loads(t['result'])
                        st.json(res_json)
                    except Exception:
                        st.write(t['result'])
                else:
                    st.info("任务正在处理中或暂无返回结果...")

