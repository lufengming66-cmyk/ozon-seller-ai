# -*- coding: utf-8 -*-
"""
SellerSwarm 蜂群 - AI 卖家精英团队
多 Agent 协同工作台，提供视觉、竞品、定价、买家视角、破局指导
"""
import streamlit as st
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import chat_with_agent, sidebar_footer

# 页面配置
st.set_page_config(
    page_title="SellerSwarm 蜂群",
    page_icon="🤖",
    layout="wide"
)

# 侧边栏
sidebar_footer()

# 头部深色渐变样式
st.markdown("""
<style>
    .swarm-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    .swarm-title {
        font-size: 3rem;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .swarm-subtitle {
        font-size: 1.2rem;
        color: #e0e7ff;
        margin-top: 0.5rem;
        font-weight: 300;
    }
    .agent-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        border-left: 4px solid #667eea;
    }
    .agent-role {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 0.5rem;
    }
    .agent-desc {
        font-size: 0.95rem;
        color: #4a5568;
        line-height: 1.6;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        background-color: #f7fafc;
        border-radius: 8px 8px 0 0;
        padding: 0 24px;
        font-weight: 600;
        font-size: 1rem;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# 渲染头部
st.markdown("""
<div class="swarm-header">
    <h1 class="swarm-title">🤖 SellerSwarm 控制台</h1>
    <p class="swarm-subtitle">你的私人 AI 卖家精英团队 · 每天自动帮你赚更多</p>
</div>
""", unsafe_allow_html=True)

# 病毒传播栏
st.info("🔥 觉得好用？复制当前网址分享给其他卖家！")

# 全局 API Key 输入
api_key = st.text_input(
    "🔑 输入 DeepSeek API Key 唤醒蜂群",
    type="password",
    help="前往 platform.deepseek.com 免费获取 API Key，新用户赠送 500 万 tokens"
)

st.markdown("---")

# 定义 5 个 Agent 的角色 Prompt
AGENT_ROLES = {
    "visual_master": """你是一个拥有 10 年经验的电商视觉总监，专攻主图改造和溢价视觉策略。你的任务是：
1. 分析用户提供的产品图片或描述，指出当前视觉的致命弱点（光影、构图、质感、氛围感）
2. 给出具体的视觉升级方案，让产品从 199 元档次提升到 500 元档次
3. 提供可落地的拍摄建议、后期处理技巧、场景搭配方案
4. 用大白话，多用 emoji，语气犀利专业，不超过 200 字""",
    
    "spy_agent": """你是一个资深的跨境电商卧底探员，专攻竞品弱点拆解和差异化打法。你的任务是：
1. 根据用户提供的竞品信息（链接、描述、价格等），快速识别其核心弱点
2. 给出 3 条可立即执行的差异化策略（价格、卖点、视觉、服务等维度）
3. 预判竞品可能的反击手段，提前布局防御
4. 用大白话，多用 emoji，语气像特工汇报，不超过 200 字""",
    
    "data_guard": """你是一个严谨的电商价格保安，专攻防亏损监控和利润率守护。你的任务是：
1. 根据用户提供的成本、运费、售价等数据，快速计算真实利润率
2. 识别隐藏的亏损风险（汇率波动、退货率、广告成本等）
3. 给出保守的定价建议和利润率红线
4. 用大白话，多用 emoji，语气严肃警惕，不超过 200 字""",
    
    "buyer_defender": """你是一个挑剔的俄罗斯本地买家，专攻毒舌反馈和真实用户视角。你的任务是：
1. 站在俄罗斯买家的角度，毒舌吐槽用户的产品（价格、质量、描述、物流等）
2. 指出买家最可能产生的 3 个疑虑或不满
3. 给出改进建议，让产品更符合俄罗斯市场的真实需求
4. 用大白话，多用 emoji，语气毒舌但中肯，不超过 200 字""",
    
    "agency_coach": """你是一个高 Agency 教练（类似 Dan Koe），教用户无许可迭代，每天只给 1 条极其犀利、可立即执行的行动指令。你的任务是：
1. 根据用户当前的困境或问题，给出 1 条最关键的破局行动
2. 这条行动必须具体、可执行、不需要任何人许可
3. 用激励性的语言，点燃用户的行动力
4. 用大白话，多用 emoji，语气像教练喊话，不超过 150 字"""
}

# 创建 5 个 Tab
tabs = st.tabs([
    "🎨 视觉总监",
    "🕵️ 卧底探员",
    "🛡️ 价格保安",
    "👤 挑剔买家",
    "💡 破局教练"
])

# Tab 1: 视觉总监
with tabs[0]:
    st.markdown("""
    <div class="agent-card">
        <div class="agent-role">🎨 视觉总监 (VisualMaster)</div>
        <div class="agent-desc">
            专攻主图改造和 199 变 500 的溢价视觉建议。上传产品图或描述产品，获取专业的视觉升级方案。
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_image = st.file_uploader(
            "📸 上传产品图片（可选）",
            type=["jpg", "jpeg", "png"],
            help="上传产品主图，AI 将基于图片给出视觉升级建议"
        )
        
        if uploaded_image:
            st.image(uploaded_image, caption="已上传的产品图", use_container_width=True)
    
    with col2:
        visual_input = st.text_area(
            "📝 描述你的产品",
            placeholder="例如：一款白色陶瓷马克杯，简约风格，目前主图是纯白背景...",
            height=200,
            key="visual_input"
        )
    
    if st.button("⚡ 唤醒视觉总监", type="primary", use_container_width=True, key="visual_btn"):
        if not api_key:
            st.error("❌ 请先输入 DeepSeek API Key")
        elif not visual_input:
            st.warning("⚠️ 请先描述你的产品")
        else:
            with st.spinner("🧠 视觉总监正在深度分析..."):
                has_image = uploaded_image is not None
                result = chat_with_agent(
                    agent_role=AGENT_ROLES["visual_master"],
                    user_input=visual_input,
                    api_key=api_key,
                    has_image=has_image
                )
                st.success(result)

# Tab 2: 卧底探员
with tabs[1]:
    st.markdown("""
    <div class="agent-card">
        <div class="agent-role">🕵️ 卧底探员 (SpyAgent)</div>
        <div class="agent-desc">
            专攻竞品弱点拆解和差异化打法。提供竞品信息，获取精准的差异化策略和防御布局。
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    spy_input = st.text_area(
        "🔍 输入竞品信息",
        placeholder="例如：竞品售价 1999 卢布，月销 500+，主图是白底图，评论区有人吐槽物流慢...",
        height=200,
        key="spy_input"
    )
    
    if st.button("⚡ 唤醒卧底探员", type="primary", use_container_width=True, key="spy_btn"):
        if not api_key:
            st.error("❌ 请先输入 DeepSeek API Key")
        elif not spy_input:
            st.warning("⚠️ 请先输入竞品信息")
        else:
            with st.spinner("🧠 卧底探员正在深度分析..."):
                result = chat_with_agent(
                    agent_role=AGENT_ROLES["spy_agent"],
                    user_input=spy_input,
                    api_key=api_key,
                    has_image=False
                )
                st.success(result)

# Tab 3: 价格保安
with tabs[2]:
    st.markdown("""
    <div class="agent-card">
        <div class="agent-role">🛡️ 价格保安 (DataGuard)</div>
        <div class="agent-desc">
            专攻防亏损监控和利润率守护。提供成本、运费、售价等数据，获取严谨的定价建议和风险预警。
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    guard_input = st.text_area(
        "💰 输入定价数据",
        placeholder="例如：成本 50 元，运费 15 元，平台佣金 15%，计划售价 1500 卢布...",
        height=200,
        key="guard_input"
    )
    
    if st.button("⚡ 唤醒价格保安", type="primary", use_container_width=True, key="guard_btn"):
        if not api_key:
            st.error("❌ 请先输入 DeepSeek API Key")
        elif not guard_input:
            st.warning("⚠️ 请先输入定价数据")
        else:
            with st.spinner("🧠 价格保安正在深度分析..."):
                result = chat_with_agent(
                    agent_role=AGENT_ROLES["data_guard"],
                    user_input=guard_input,
                    api_key=api_key,
                    has_image=False
                )
                st.success(result)

# Tab 4: 挑剔买家
with tabs[3]:
    st.markdown("""
    <div class="agent-card">
        <div class="agent-role">👤 挑剔买家 (BuyerDefender)</div>
        <div class="agent-desc">
            模拟俄罗斯本地买家视角的毒舌反馈。描述你的产品，获取真实的买家疑虑和改进建议。
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    buyer_input = st.text_area(
        "🛒 描述你的产品和售价",
        placeholder="例如：一款智能手环，售价 2999 卢布，宣称 7 天续航，支持心率监测...",
        height=200,
        key="buyer_input"
    )
    
    if st.button("⚡ 唤醒挑剔买家", type="primary", use_container_width=True, key="buyer_btn"):
        if not api_key:
            st.error("❌ 请先输入 DeepSeek API Key")
        elif not buyer_input:
            st.warning("⚠️ 请先描述你的产品")
        else:
            with st.spinner("🧠 挑剔买家正在深度吐槽..."):
                result = chat_with_agent(
                    agent_role=AGENT_ROLES["buyer_defender"],
                    user_input=buyer_input,
                    api_key=api_key,
                    has_image=False
                )
                st.success(result)

# Tab 5: 破局教练
with tabs[4]:
    st.markdown("""
    <div class="agent-card">
        <div class="agent-role">💡 破局教练 (AgencyCoach)</div>
        <div class="agent-desc">
            高 Agency 教练，教你无许可迭代。描述你的困境，获取 1 条极其犀利、可立即执行的破局行动。
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    coach_input = st.text_area(
        "💭 描述你当前的困境",
        placeholder="例如：我的产品利润率只有 8%，不知道该降价促销还是提升溢价...",
        height=200,
        key="coach_input"
    )
    
    if st.button("⚡ 唤醒破局教练", type="primary", use_container_width=True, key="coach_btn"):
        if not api_key:
            st.error("❌ 请先输入 DeepSeek API Key")
        elif not coach_input:
            st.warning("⚠️ 请先描述你的困境")
        else:
            with st.spinner("🧠 破局教练正在深度思考..."):
                result = chat_with_agent(
                    agent_role=AGENT_ROLES["agency_coach"],
                    user_input=coach_input,
                    api_key=api_key,
                    has_image=False
                )
                st.success(result)

# 底部提示
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #718096; font-size: 0.9rem; padding: 2rem 0;">
    <p>💡 <strong>使用技巧</strong>：每个 Agent 都有独特的专业视角，建议组合使用以获得全方位的决策支持。</p>
    <p>🔒 <strong>隐私保护</strong>：所有对话数据仅在本地处理，不会被存储或分享。</p>
</div>
""", unsafe_allow_html=True)

