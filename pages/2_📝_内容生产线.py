# -*- coding: utf-8 -*-
"""
Ozon Seller Pro v4.0 - 内容生产线
AI Prompt工厂 + HTML尺码表 + JSON工具
"""
import streamlit as st
import json
from utils import sidebar_footer, get_current_product, clear_current_product

st.set_page_config(page_title="内容生产线", page_icon="📝", layout="wide")

# ==================== 自定义CSS ====================
st.markdown("""
<style>
    .tool-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
    }
    
    .output-box {
        background: #f5f5f5;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        white-space: pre-wrap;
        word-wrap: break-word;
        max-height: 400px;
        overflow-y: auto;
    }
    
    .size-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        background: white;
    }
    
    .size-table th {
        background: #333;
        color: white;
        padding: 12px;
        text-align: center;
        font-weight: 600;
        border: 1px solid #000;
    }
    
    .size-table td {
        padding: 10px;
        text-align: center;
        border: 1px solid #ddd;
    }
    
    .size-table tr:nth-child(even) {
        background: #f9f9f9;
    }
    
    .success-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 检查定价台数据 ====================
current_product = get_current_product()

if current_product:
    st.markdown(f"""
    <div class="success-banner">
        <h3>✅ 已自动加载定价台数据：{current_product.get('name', '未命名商品')}</h3>
        <p>直接生成文案/SKU，无需重复输入！</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🗑️ 清除缓存数据", key="clear_cache_top"):
        clear_current_product()

# ==================== 侧边栏 ====================
with st.sidebar:
    st.markdown("### 📝 内容工具")
    
    tool_mode = st.radio(
        "选择工具",
        ["AI指令工厂", "JSON工具", "尺码表生成器"],
        key="content_tool_mode"
    )
    
    # 显示缓存数据信息
    if current_product:
        st.markdown("---")
        st.markdown("### 📦 缓存数据")
        st.info(f"""
        **商品**: {current_product.get('name', 'N/A')}
        
        **售价**: ₽{current_product.get('final_price_rub', 0)}
        
        **利润率**: {current_product.get('profit_margin', 0):.1f}%
        """)
        
        if st.button("🗑️ 清除", key="clear_cache_sidebar"):
            clear_current_product()
    
    sidebar_footer()

# ==================== 主页面 ====================
st.title("📝 内容生产线")
st.markdown("一站式内容生产工具，提升运营效率")

st.markdown("---")

# ==================== AI指令工厂 ====================
if tool_mode == "AI指令工厂":
    st.markdown("## 🤖 AI指令工厂 - All-in-One模式")
    st.info("输入商品信息，一键生成包含SEO标题、HTML描述、Tags、弹窗文案的超级Prompt")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 自动填充商品名称
        default_name = current_product.get('name', '') if current_product else ''
        product_name = st.text_input(
            "商品名称",
            value=default_name,
            placeholder="例如：女士羊绒围巾",
            key="ai_product_name"
        )
        
        # 自动填充卖点（如果用户没填）
        default_notes = current_product.get('notes', '') if current_product else ''
        selling_points = st.text_area(
            "商品卖点",
            value=default_notes,
            placeholder="例如：100%羊绒、保暖透气、多色可选",
            height=100,
            key="ai_selling_points"
        )
    
    with col2:
        style = st.selectbox(
            "文案风格",
            ["专业严谨", "温馨亲切", "时尚潮流", "简约大气", "奢华高端"],
            key="ai_style"
        )
        
        category = st.text_input(
            "商品品类",
            placeholder="例如：服饰配件/围巾",
            key="ai_category"
        )
    
    if st.button("🚀 生成AI超级Prompt", type="primary", use_container_width=True):
        if not product_name:
            st.warning("请输入商品名称")
        else:
            prompt = f"""请为以下商品生成完整的Ozon商品页面内容：

【商品信息】
- 商品名称：{product_name}
- 商品卖点：{selling_points if selling_points else '请根据商品特性自行发挥'}
- 文案风格：{style}
- 商品品类：{category if category else '通用商品'}

【生成要求】
请按以下格式输出：

1. SEO标题（俄语）
   - 长度：80-150字符
   - 包含核心关键词
   - 突出卖点和品类

2. HTML商品描述（俄语）
   - 使用HTML标签美化排版
   - 包含<h3>标题、<p>段落、<ul><li>列表
   - 突出商品特点、材质、使用场景
   - 长度：300-500词

3. 搜索标签Tags（俄语）
   - 提供10-15个相关标签
   - 用逗号分隔
   - 包含品类、材质、风格、用途等

4. 弹窗促销文案（俄语）
   - 简短有力，50字以内
   - 突出优惠或卖点
   - 吸引点击

请确保所有内容符合Ozon平台规范，语言地道自然。"""

            st.markdown("---")
            st.success("✅ Prompt已生成！复制下方内容粘贴到ChatGPT、Claude等AI工具中使用")
            
            st.markdown("### 📋 生成的AI Prompt")
            
            st.text_area(
                "复制以下内容：",
                value=prompt,
                height=400,
                key="prompt_output",
                label_visibility="collapsed"
            )

# ==================== JSON工具 ====================
elif tool_mode == "JSON工具":
    st.markdown("## 🔧 JSON工具")
    st.info("生成Ozon商品属性JSON代码")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📝 输入商品属性")
        
        brand = st.text_input("品牌", placeholder="例如：UNIQLO", key="json_brand")
        color = st.text_input("颜色", placeholder="例如：黑色", key="json_color")
        material = st.text_input("材质", placeholder="例如：100%羊绒", key="json_material")
        size = st.text_input("尺码", placeholder="例如：均码", key="json_size")
        
        custom_attrs = st.text_area(
            "自定义属性（每行一个，格式：键=值）",
            placeholder="例如：\n产地=中国\n重量=200g",
            height=100,
            key="json_custom"
        )
    
    with col2:
        st.markdown("### 📦 生成JSON代码")
        
        st.markdown("")  # 空行对齐
        st.markdown("")
        
    if st.button("生成JSON", type="primary", use_container_width=True, key="gen_json_btn"):
        attributes = {}
        
        if brand:
            attributes["brand"] = brand
        if color:
            attributes["color"] = color
        if material:
            attributes["material"] = material
        if size:
            attributes["size"] = size
        
        # 解析自定义属性
        if custom_attrs:
            for line in custom_attrs.strip().split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    attributes[key.strip()] = value.strip()
        
        json_output = json.dumps(attributes, ensure_ascii=False, indent=2)
        
        st.markdown("---")
        st.success("✅ JSON代码已生成")
        
        st.markdown("### 📄 生成的JSON")
        
        st.text_area(
            "JSON代码：",
            value=json_output,
            height=200,
            key="json_output_area",
            label_visibility="collapsed"
        )
        
        # 下载按钮
        st.download_button(
            "📥 下载JSON文件",
            json_output,
            "product_attributes.json",
            "application/json",
            key="download_json"
        )

# ==================== 尺码表生成器 ====================
elif tool_mode == "尺码表生成器":
    st.markdown("## 📏 HTML尺码表生成器")
    st.info("生成美观的HTML尺码表代码，支持俄语显示，可直接复制到Ozon详情页或截图使用")
    
    st.markdown("### 📝 输入尺码数据")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        size_type = st.selectbox(
            "尺码类型",
            ["服装尺码", "鞋码", "帽子尺码", "自定义"],
            key="size_type"
        )
        
        if size_type == "服装尺码":
            default_data = """Размер,Длина(см),Грудь(см),Плечо(см)
S,65,90,38
M,67,94,39
L,69,98,40
XL,71,102,41
XXL,73,106,42"""
        elif size_type == "鞋码":
            default_data = """Размер CN,Размер EU,Длина стопы(см)
36,37,23.0
37,38,23.5
38,39,24.0
39,40,24.5
40,41,25.0"""
        elif size_type == "帽子尺码":
            default_data = """Размер,Обхват головы(см)
S,54-56
M,56-58
L,58-60
XL,60-62"""
        else:
            default_data = """列1,列2,列3
数据1,数据2,数据3
数据4,数据5,数据6"""
        
        size_data = st.text_area(
            "尺码数据（CSV格式，第一行为表头）",
            value=default_data,
            height=200,
            key="size_data"
        )
    
    with col2:
        table_style = st.selectbox(
            "表格风格",
            ["黑白简约", "蓝色商务", "粉色温馨"],
            key="table_style"
        )
        
        show_border = st.checkbox("显示边框", value=True, key="show_border")
        
        font_size = st.slider("字体大小", 12, 20, 14, key="font_size")
    
    if st.button("🎨 生成HTML尺码表", type="primary", use_container_width=True):
        try:
            # 解析CSV数据
            lines = size_data.strip().split('\n')
            headers = lines[0].split(',')
            rows = [line.split(',') for line in lines[1:]]
            
            # 根据风格选择颜色
            if table_style == "黑白简约":
                header_bg = "#333"
                header_color = "#fff"
                border_color = "#000"
                row_even_bg = "#f9f9f9"
            elif table_style == "蓝色商务":
                header_bg = "#005BFF"
                header_color = "#fff"
                border_color = "#005BFF"
                row_even_bg = "#e3f2fd"
            else:  # 粉色温馨
                header_bg = "#F91155"
                header_color = "#fff"
                border_color = "#F91155"
                row_even_bg = "#fce4ec"
            
            border_style = "1px solid " + border_color if show_border else "none"
            
            # 生成HTML
            html_code = f"""<style>
.size-table {{
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    font-size: {font_size}px;
    font-family: Arial, sans-serif;
    background: white;
}}

.size-table th {{
    background: {header_bg};
    color: {header_color};
    padding: 12px;
    text-align: center;
    font-weight: 600;
    border: {border_style};
}}

.size-table td {{
    padding: 10px;
    text-align: center;
    border: {border_style};
}}

.size-table tr:nth-child(even) {{
    background: {row_even_bg};
}}
</style>

<table class="size-table">
    <thead>
        <tr>
"""
            
            # 添加表头
            for header in headers:
                html_code += f"            <th>{header.strip()}</th>\n"
            
            html_code += """        </tr>
    </thead>
    <tbody>
"""
            
            # 添加数据行
            for row in rows:
                html_code += "        <tr>\n"
                for cell in row:
                    html_code += f"            <td>{cell.strip()}</td>\n"
                html_code += "        </tr>\n"
            
            html_code += """    </tbody>
</table>"""
            
            st.markdown("---")
            st.success("✅ HTML尺码表已生成")
            
            # 预览效果
            st.markdown("### 👁️ 预览效果")
            st.markdown(html_code, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # HTML代码
            st.markdown("### 📄 HTML代码")
            st.text_area(
                "复制以下HTML代码：",
                value=html_code,
                height=300,
                key="html_output_area",
                label_visibility="collapsed"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    "📥 下载HTML文件",
                    html_code,
                    "size_table.html",
                    "text/html",
                    key="download_html",
                    use_container_width=True
                )
            
            with col2:
                st.info("""
                **使用方法：**
                1. 复制HTML代码
                2. 粘贴到Ozon商品描述
                3. 或直接截图使用
                """)
        
        except Exception as e:
            st.error(f"❌ 生成失败: {e}")
            st.info("请检查CSV格式是否正确（用逗号分隔）")

st.markdown("---")

# 使用提示
with st.expander("💡 使用提示", expanded=False):
    st.markdown("""
    ### AI指令工厂
    - 填写商品信息后生成完整的AI Prompt
    - 复制Prompt到ChatGPT/Claude等AI工具
    - AI会生成SEO标题、HTML描述、Tags、弹窗文案
    
    ### JSON工具
    - 快速生成商品属性JSON代码
    - 支持自定义属性
    - 可直接下载JSON文件
    
    ### 尺码表生成器
    - 使用CSV格式输入数据（逗号分隔）
    - 第一行为表头，后续行为数据
    - 支持多种风格和自定义样式
    - 生成的HTML可直接用于Ozon详情页
    - 也可以在预览区域截图使用
    """)

