# -*- coding: utf-8 -*-
"""
Ozon Seller Pro v4.0 - 主入口
多页面架构 - 终极商业化版本
"""
import platform
import streamlit as st
from utils import load_config, save_config, sidebar_footer, check_remote_config, init_database
import os

# ==================== Mac 系统物理阻断 ====================
if platform.system() == "Darwin":
    st.error("❌ 抱歉，本软件核心驱动仅支持 Windows 10 / Windows 11 系统，暂不支持 Mac。")
    st.stop()

# ==================== 数据库初始化（首次运行自动创建） ====================
try:
    init_database()
except Exception as e:
    st.error(f"❌ 数据库初始化失败: {e}")
    st.stop()

# ==================== 云端配置热更新 ====================
# 在页面加载初期检查云端配置更新
try:
    config_updated = check_remote_config()
    if config_updated:
        st.toast("🚀 配置已自动更新至最新版本！", icon="🚀")
except Exception:
    # 静默失败，不影响主程序运行
    pass

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="Ozon Seller Pro v4.0",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 主逻辑 ====================
try:
    # ==================== 自定义CSS ====================
    st.markdown("""
    <style>
        /* 强制浅色主题 */
        .stApp {
            background-color: #f8f9fa !important;
        }
        
        .main {
            background-color: #f8f9fa !important;
        }
        
        /* 优化容器 padding */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            border-radius: 16px !important;
        }
        
        /* 主题色 */
        :root {
            --ozon-blue: #005BFF;
            --ozon-pink: #F91155;
            --success-green: #2E7D32;
            --warning-orange: #FF9800;
            --error-red: #C62828;
        }
        
        /* 全局字体优化 */
        html, body, [class*="css"] {
            font-family: 'Inter', 'Roboto', sans-serif !important;
        }
    
        /* 页面加载动画 */
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .main > div {
            animation: fadeIn 0.6s ease-out;
        }
        
        /* 自定义滚动条 - Webkit浏览器 */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.05);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, #005BFF 0%, #F91155 100%);
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(180deg, #0046cc 0%, #d60e47 100%);
            box-shadow: 0 0 10px rgba(0, 91, 255, 0.5);
        }
        
        /* Firefox滚动条 */
        * {
            scrollbar-width: thin;
            scrollbar-color: #005BFF rgba(0, 0, 0, 0.05);
        }
        
        /* 按钮美化 (悬浮动画) */
        .stButton>button {
            border-radius: 12px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
        }
        
        .stButton>button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 20px rgba(0,0,0,0.15) !important;
        }
        
        .stButton>button:active {
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        }
        
        /* 主标题样式 */
        .main-title {
            font-size: 2.8rem;
            font-weight: 800;
            background: linear-gradient(90deg, #005BFF 0%, #F91155 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            padding: 1.5rem 0 0.5rem 0;
            margin: 0;
            animation: fadeIn 0.8s ease-out;
        }
        
        .sub-title {
            text-align: center;
            color: #666;
            font-size: 1.1rem;
            margin-bottom: 2rem;
            animation: fadeIn 1s ease-out;
        }
        
        /* 欢迎卡片 */
        .welcome-card {
            background: linear-gradient(135deg, #005BFF 0%, #0046cc 100%);
            color: white;
            padding: 2rem;
            border-radius: 16px;
            margin: 2rem 0;
            box-shadow: 0 8px 24px rgba(0,91,255,0.2);
            animation: fadeIn 1.2s ease-out;
            transition: all 0.3s ease;
        }
        
        .welcome-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 32px rgba(0,91,255,0.3);
        }
        
        .welcome-card h2 {
            margin: 0 0 1rem 0;
            font-size: 1.8rem;
        }
        
        .welcome-card p {
            margin: 0.5rem 0;
            font-size: 1rem;
            opacity: 0.95;
        }
        
        /* 功能卡片 */
        .feature-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            border-left: 4px solid #005BFF;
            margin-bottom: 1rem;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            animation: fadeIn 1.4s ease-out;
        }
        
        .feature-card:hover {
            transform: translateY(-5px) scale(1.02);
            box-shadow: 0 8px 24px rgba(0,91,255,0.2);
        }
        
        .feature-icon {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        
        .feature-title {
            font-size: 1.3rem;
            font-weight: 600;
            color: #333;
            margin-bottom: 0.5rem;
        }
        
        .feature-desc {
            color: #666;
            font-size: 0.95rem;
            line-height: 1.5;
        }
        
        /* 侧边栏样式 */
        .sidebar-info {
            background: #f0f4ff;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            text-align: center;
        }
        
        .sidebar-info .label {
            color: #666;
            font-size: 0.85rem;
            margin-bottom: 0.25rem;
        }
        
        .sidebar-info .value {
            color: #005BFF;
            font-size: 1.1rem;
            font-weight: 600;
        }
        
        /* 输入框美化 */
        .stTextInput>div>div>input,
        .stNumberInput>div>div>input,
        .stTextArea>div>div>textarea {
            border-radius: 8px !important;
            border: 1px solid #e0e0e0 !important;
            transition: all 0.3s ease !important;
        }
        
        .stTextInput>div>div>input:focus,
        .stNumberInput>div>div>input:focus,
        .stTextArea>div>div>textarea:focus {
            border-color: #005BFF !important;
            box-shadow: 0 0 0 3px rgba(0,91,255,0.1) !important;
            transform: translateY(-2px);
        }
        
        /* 选择框美化 */
        .stSelectbox>div>div>div {
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
        }
        
        .stSelectbox>div>div>div:hover {
            border-color: #005BFF !important;
        }
        
        /* 滑块美化 */
        .stSlider>div>div>div>div {
            background-color: #005BFF !important;
        }
        
        /* 加载动画 - 脉冲效果 */
        @keyframes pulse {
            0%, 100% {
                opacity: 1;
            }
            50% {
                opacity: 0.5;
            }
        }
        
        .stSpinner > div {
            border-color: #005BFF !important;
            animation: pulse 1.5s ease-in-out infinite;
        }
        
        /* Toast通知美化 */
        .stToast {
            border-radius: 12px !important;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15) !important;
            animation: slideInRight 0.4s ease-out;
        }
        
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        /* Expander美化 */
        .streamlit-expanderHeader {
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
        }
        
        .streamlit-expanderHeader:hover {
            background-color: rgba(0,91,255,0.05) !important;
        }
        
        /* 数据表格美化 */
        .stDataFrame {
            border-radius: 12px !important;
            overflow: hidden !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
        }
        
        /* Tabs美化 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0 !important;
            transition: all 0.3s ease !important;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background-color: rgba(0,91,255,0.05) !important;
        }
        
        /* 进度条美化 */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #005BFF 0%, #F91155 100%) !important;
            border-radius: 10px !important;
        }
        
        /* 成功/警告/错误消息美化 */
        .stSuccess, .stWarning, .stError, .stInfo {
            border-radius: 12px !important;
            animation: fadeIn 0.5s ease-out;
        }
        
        /* 侧边栏过渡效果 */
        [data-testid="stSidebar"] {
            transition: all 0.3s ease !important;
        }
        
        /* 图片悬停效果 */
        img {
            transition: all 0.3s ease !important;
            border-radius: 8px !important;
        }
        
        img:hover {
            transform: scale(1.02);
            box-shadow: 0 8px 24px rgba(0,0,0,0.1);
        }
    </style>
    """, unsafe_allow_html=True)

    # ==================== 侧边栏 ====================
    with st.sidebar:
        st.markdown("### 🎯 全局配置")
        
        # 加载配置
        exchange_rate = float(load_config('exchange_rate', '13.5'))
        commission_rate = float(load_config('commission_rate', '15.0'))
        label_fee = float(load_config('label_fee', '1.5'))
        profit_rate = float(load_config('profit_rate', '1.35'))
        
        # 显示当前配置
        st.markdown(f"""
        <div class="sidebar-info">
            <div class="label">当前汇率</div>
            <div class="value">1 CNY = {exchange_rate:.2f} RUB</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="sidebar-info">
            <div class="label">平台佣金率</div>
            <div class="value">{commission_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="sidebar-info">
            <div class="label">贴单费</div>
            <div class="value">¥{label_fee:.1f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="sidebar-info">
            <div class="label">利润率系数</div>
            <div class="value">{profit_rate:.2f}x</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("💡 在「设置与关于」页面可修改这些参数")
        
        # 底部信息
        sidebar_footer()

    # ==================== 主页面 ====================
    st.markdown('<h1 class="main-title">Ozon Seller Pro v4.0</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">🚀 跨境电商智能助手 · 终极商业化版本</p>', unsafe_allow_html=True)

    # ==================== 产品使用引导组件 ====================
    show_guide = load_config('show_welcome_guide', 'yes')
    
    if show_guide == 'yes':
        st.info("""
        ### 👋 欢迎首次使用 Ozon Seller Pro！
        
        **使用建议：**
        1. 📌 **先配置参数**：前往「⚙️ 设置与关于」页面，设置汇率、佣金率、物流档位等全局参数
        2. 💰 **再进行计算**：配置完成后，使用「💰 智能定价台」进行商品定价和利润分析
        3. 📝 **内容生产**：使用「📝 内容生产线」生成商品文案、尺码表等内容
        
        **提示**：所有配置都会自动保存到本地数据库，无需担心数据丢失。
        """)
        
        if st.button("✅ 确认并进入系统", type="primary", use_container_width=True):
            from utils import save_config
            save_config('show_welcome_guide', 'no')
            st.rerun()
        
        st.markdown("---")

    # 欢迎卡片
    st.markdown("""
    <div class="welcome-card">
        <h2>👋 欢迎使用 Ozon Seller Pro</h2>
        <p>📊 智能定价 · 内容生产 · 选品分析 · 一站式解决方案</p>
        <p>🎯 ERP级别的准确性与灵活性，助力跨境电商业务腾飞</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 功能介绍
    st.markdown("## 🎨 核心功能")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">💰</div>
            <div class="feature-title">智能定价台</div>
            <div class="feature-desc">
                • 动态物流匹配算法<br>
                • 利润红绿灯预警<br>
                • 多渠道价格对比<br>
                • 竞品反推成本
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📦</div>
            <div class="feature-title">选品与SKU</div>
            <div class="feature-desc">
                • 智能SKU生成器<br>
                • 自定义编码规则<br>
                • 批量SKU管理<br>
                • 选品数据分析
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📝</div>
            <div class="feature-title">内容生产线</div>
            <div class="feature-desc">
                • AI Prompt All-in-One<br>
                • HTML尺码表生成<br>
                • JSON工具套件<br>
                • 一键复制导出
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">⚙️</div>
            <div class="feature-title">设置与关于</div>
            <div class="feature-desc">
                • 实时汇率获取<br>
                • 物流档位编辑<br>
                • 全局参数配置<br>
                • 系统信息查看
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 快速开始
    st.markdown("## 🚀 快速开始")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("""
        **第一步：配置参数**
        
        前往「⚙️ 设置与关于」页面：
        - 获取最新汇率
        - 设置佣金率
        - 配置物流档位
        """)

    with col2:
        st.success("""
        **第二步：智能定价**
        
        使用「💰 智能定价台」：
        - 输入成本和重量
        - 自动匹配物流
        - 获取建议售价
        """)

    with col3:
        st.warning("""
        **第三步：内容生产**
        
        使用「📝 内容生产线」：
        - 生成商品文案
        - 制作尺码表
        - 导出JSON数据
        """)

    st.markdown("---")

    # 更新日志
    with st.expander("📋 v4.0 更新日志", expanded=False):
        st.markdown("""
        ### 🎉 重大更新
        
        **数据库升级**
        - ✅ 新建 `logistics_tiers` 表，支持自定义物流档位
        - ✅ 新建 `config` 表，统一管理全局配置
        - ✅ 自动初始化默认数据
        
        **智能定价台**
        - ✅ 动态物流匹配算法（按优先级+兜底机制）
        - ✅ 利润红绿灯预警系统
        - ✅ 移除1688以图搜图模块
        - ✅ 加入佣金率计算
        
        **内容生产线**
        - ✅ AI Prompt All-in-One 模式
        - ✅ HTML尺码表生成（替代图片）
        - ✅ 简化JSON工具（移除手机预览）
        - ✅ 黑白简约风格CSS
        
        **设置与关于**
        - ✅ 实时汇率获取按钮（无需API Key）
        - ✅ 物流档位表格编辑器（增删改）
        - ✅ 平台佣金率配置
        - ✅ 一键保存所有配置
        
        **系统优化**
        - ✅ 所有配置读取都有默认值（Fallback）
        - ✅ 所有输入框都有唯一key
        - ✅ 健壮性全面提升
        """)

    st.markdown("---")

    # 底部信息
    st.markdown("""
    <div style="text-align: center; color: #999; font-size: 0.85rem; padding: 2rem 0;">
        <p><strong>Ozon Seller Pro v4.0</strong> - 终极商业化版本</p>
        <p>让跨境电商运营更简单、更高效、更智能</p>
        <p>© 2024 All Rights Reserved</p>
    </div>
    """, unsafe_allow_html=True)

except Exception as e:
    # 防崩兜底 - 友好的错误提示
    st.error("### ⚠️ 系统遇到了一个小问题")
    st.warning(f"**错误信息：** {str(e)}")
    st.info("""
    **建议操作：**
    1. 点击下方按钮重新加载页面
    2. 如果问题持续，请尝试清除浏览器缓存
    3. 联系技术支持获取帮助
    """)
    
    if st.button("🔄 重新加载", type="primary", use_container_width=True):
        st.rerun()
    
    # 显示详细错误信息（可选，用于调试）
    with st.expander("🔍 查看详细错误信息（开发者模式）"):
        import traceback
        st.code(traceback.format_exc(), language="python")