# -*- coding: utf-8 -*-
"""
Ozon Seller Pro v4.0 - 选品与SKU
智能SKU生成器 + PDF选品报告
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from utils import sidebar_footer, get_current_product
from fpdf import FPDF
import io

st.set_page_config(page_title="选品与SKU", page_icon="📦", layout="wide")

# ==================== 自定义CSS ====================
st.markdown("""
<style>
    .sku-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
    }
    
    .sku-output {
        background: #f0f4ff;
        border: 2px solid #005BFF;
        border-radius: 8px;
        padding: 1.5rem;
        text-align: center;
        margin: 1rem 0;
    }
    
    .sku-code {
        font-size: 2rem;
        font-weight: 700;
        color: #005BFF;
        font-family: 'Courier New', monospace;
        letter-spacing: 2px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 侧边栏 ====================
with st.sidebar:
    st.markdown("### 📦 SKU工具")
    
    sku_mode = st.radio(
        "选择模式",
        ["单个生成", "批量生成", "SKU解析", "📄 导出选品报告"],
        key="sku_mode"
    )
    
    sidebar_footer()

# ==================== 主页面 ====================
st.title("📦 选品与SKU管理")
st.markdown("智能SKU生成器，支持自定义编码规则")

st.markdown("---")

# ==================== 单个生成 ====================
if sku_mode == "单个生成":
    st.markdown("## 🎯 单个SKU生成")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📝 基础信息")
        
        category_code = st.text_input(
            "品类代码",
            placeholder="例如：CLO（服装）",
            max_chars=10,
            key="sku_category"
        ).upper()
        
        brand_code = st.text_input(
            "品牌代码",
            placeholder="例如：NIKE",
            max_chars=10,
            key="sku_brand"
        ).upper()
        
        color_code = st.text_input(
            "颜色代码",
            placeholder="例如：BLK（黑色）",
            max_chars=10,
            key="sku_color"
        ).upper()
    
    with col2:
        st.markdown("### 🔢 编码规则")
        
        use_date = st.checkbox("包含日期", value=True, key="sku_use_date")
        
        if use_date:
            date_format = st.selectbox(
                "日期格式",
                ["YYMMDD", "YYYYMMDD", "YYMM"],
                key="sku_date_format"
            )
        
        use_sequence = st.checkbox("包含序号", value=True, key="sku_use_sequence")
        
        if use_sequence:
            sequence_num = st.number_input(
                "序号",
                min_value=1,
                max_value=9999,
                value=1,
                key="sku_sequence"
            )
        
        separator = st.selectbox(
            "分隔符",
            ["-", "_", "无"],
            key="sku_separator"
        )
    
    if st.button("🚀 生成SKU", type="primary", use_container_width=True):
        if not category_code:
            st.warning("请输入品类代码")
        else:
            # 构建SKU
            sku_parts = []
            
            if category_code:
                sku_parts.append(category_code)
            
            if brand_code:
                sku_parts.append(brand_code)
            
            if color_code:
                sku_parts.append(color_code)
            
            if use_date:
                now = datetime.now()
                if date_format == "YYMMDD":
                    date_str = now.strftime("%y%m%d")
                elif date_format == "YYYYMMDD":
                    date_str = now.strftime("%Y%m%d")
                else:  # YYMM
                    date_str = now.strftime("%y%m")
                sku_parts.append(date_str)
            
            if use_sequence:
                seq_str = str(sequence_num).zfill(4)
                sku_parts.append(seq_str)
            
            # 组合SKU
            if separator == "无":
                sku_code = "".join(sku_parts)
            else:
                sku_code = separator.join(sku_parts)
            
            st.markdown("---")
            st.markdown("### ✅ 生成的SKU")
            
            st.markdown(f"""
            <div class="sku-output">
                <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">SKU编码</div>
                <div class="sku-code">{sku_code}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.code(sku_code, language=None)
            
            # 显示组成部分
            st.markdown("### 📋 编码组成")
            
            parts_info = []
            if category_code:
                parts_info.append(f"品类: {category_code}")
            if brand_code:
                parts_info.append(f"品牌: {brand_code}")
            if color_code:
                parts_info.append(f"颜色: {color_code}")
            if use_date:
                parts_info.append(f"日期: {date_str}")
            if use_sequence:
                parts_info.append(f"序号: {seq_str}")
            
            for info in parts_info:
                st.info(info)

# ==================== 批量生成 ====================
elif sku_mode == "批量生成":
    st.markdown("## 📦 批量SKU生成")
    st.info("上传包含商品信息的Excel，自动生成SKU编码")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "上传Excel文件",
            type=['xlsx', 'xls'],
            key="batch_sku_upload"
        )
    
    with col2:
        st.markdown("**Excel格式要求：**")
        st.markdown("""
        - 品类代码
        - 品牌代码（可选）
        - 颜色代码（可选）
        """)
    
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            st.dataframe(df.head(), use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                use_date_batch = st.checkbox("包含日期", value=True, key="batch_use_date")
                if use_date_batch:
                    date_format_batch = st.selectbox(
                        "日期格式",
                        ["YYMMDD", "YYYYMMDD", "YYMM"],
                        key="batch_date_format"
                    )
            
            with col2:
                separator_batch = st.selectbox(
                    "分隔符",
                    ["-", "_", "无"],
                    key="batch_separator"
                )
            
            if st.button("批量生成SKU", type="primary", use_container_width=True):
                results = []
                now = datetime.now()
                
                for idx, row in df.iterrows():
                    sku_parts = []
                    
                    category = str(row.get('品类代码', '')).upper().strip()
                    brand = str(row.get('品牌代码', '')).upper().strip()
                    color = str(row.get('颜色代码', '')).upper().strip()
                    
                    if category and category != 'nan':
                        sku_parts.append(category)
                    if brand and brand != 'nan':
                        sku_parts.append(brand)
                    if color and color != 'nan':
                        sku_parts.append(color)
                    
                    if use_date_batch:
                        if date_format_batch == "YYMMDD":
                            date_str = now.strftime("%y%m%d")
                        elif date_format_batch == "YYYYMMDD":
                            date_str = now.strftime("%Y%m%d")
                        else:
                            date_str = now.strftime("%y%m")
                        sku_parts.append(date_str)
                    
                    seq_str = str(idx + 1).zfill(4)
                    sku_parts.append(seq_str)
                    
                    if separator_batch == "无":
                        sku_code = "".join(sku_parts)
                    else:
                        sku_code = separator_batch.join(sku_parts)
                    
                    results.append({
                        "序号": idx + 1,
                        "品类": category,
                        "品牌": brand,
                        "颜色": color,
                        "生成的SKU": sku_code
                    })
                
                df_result = pd.DataFrame(results)
                st.success(f"✅ 成功生成 {len(results)} 个SKU")
                st.dataframe(df_result, use_container_width=True, hide_index=True)
                
                csv = df_result.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "📥 下载结果",
                    csv,
                    "批量SKU结果.csv",
                    "text/csv",
                    key="download_batch_sku"
                )
        
        except Exception as e:
            st.error(f"❌ 文件读取失败: {e}")

# ==================== SKU解析 ====================
elif sku_mode == "SKU解析":
    st.markdown("## 🔍 SKU解析")
    st.info("输入SKU编码，解析其组成部分")
    
    sku_input = st.text_input(
        "输入SKU编码",
        placeholder="例如：CLO-NIKE-BLK-241203-0001",
        key="sku_parse_input"
    )
    
    separator_parse = st.selectbox(
        "分隔符",
        ["-", "_", "无"],
        key="parse_separator"
    )
    
    if st.button("🔍 解析SKU", type="primary", use_container_width=True):
        if not sku_input:
            st.warning("请输入SKU编码")
        else:
            st.markdown("---")
            st.markdown("### 📋 解析结果")
            
            if separator_parse == "无":
                st.info("无分隔符模式：需要手动定义各部分长度")
                st.markdown(f"**原始SKU:** `{sku_input}`")
            else:
                parts = sku_input.split(separator_parse)
                
                st.markdown(f"**原始SKU:** `{sku_input}`")
                st.markdown(f"**分隔符:** `{separator_parse}`")
                st.markdown(f"**组成部分数量:** {len(parts)}")
                
                for idx, part in enumerate(parts, 1):
                    st.markdown(f"**部分 {idx}:** `{part}`")
                
                # 智能识别
                st.markdown("---")
                st.markdown("### 🤖 智能识别")
                
                for idx, part in enumerate(parts):
                    if part.isdigit() and len(part) == 6:
                        st.success(f"部分 {idx+1} 可能是日期: {part}")
                    elif part.isdigit() and len(part) == 4:
                        st.info(f"部分 {idx+1} 可能是序号: {part}")
                    elif part.isalpha() and len(part) <= 5:
                        st.warning(f"部分 {idx+1} 可能是代码: {part}")

# ==================== PDF选品报告 ====================
elif sku_mode == "📄 导出选品报告":
    st.markdown("## 📄 导出选品报告")
    st.info("基于定价台数据生成专业的PDF选品分析报告")
    
    # 获取定价台数据
    current_product = get_current_product()
    
    if not current_product:
        st.warning("⚠️ 未找到商品数据，请先前往「💰 智能定价台」完成定价计算")
        st.markdown("---")
        st.markdown("### 💡 使用流程")
        st.markdown("""
        1. 前往「💰 智能定价台」
        2. 输入商品信息并计算定价
        3. 点击「✨ 一键生成上架文案 & SKU」
        4. 返回本页面生成PDF报告
        """)
        
        st.markdown("---")
        st.markdown("### 🛡️ 兜底方案：手动输入数据")
        st.info("如果数据丢失，可以手动输入商品信息生成报告")
        
        with st.form("manual_product_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                manual_name = st.text_input("商品名称", value="手动输入商品", key="manual_name")
                manual_cost = st.number_input("成本 (CNY)", min_value=0.01, value=50.0, key="manual_cost")
                manual_weight = st.number_input("重量 (克)", min_value=1, value=300, key="manual_weight")
            
            with col2:
                manual_price_rub = st.number_input("售价 (RUB)", min_value=1, value=800, key="manual_price_rub")
                manual_margin = st.number_input("利润率 (%)", min_value=0.0, value=15.0, key="manual_margin")
                manual_channel = st.text_input("物流渠道", value="标准渠道", key="manual_channel")
            
            submitted = st.form_submit_button("📄 生成报告", type="primary", use_container_width=True)
            
            if submitted:
                # 构建手动数据
                from utils import load_config
                exchange_rate = float(load_config('exchange_rate', '13.5'))
                manual_price_cny = manual_price_rub / exchange_rate
                
                current_product = {
                    'name': manual_name,
                    'cost': manual_cost,
                    'weight': manual_weight,
                    'charge_weight': manual_weight,
                    'length': 0,
                    'width': 0,
                    'height': 0,
                    'final_price_rub': int(manual_price_rub),
                    'final_price_cny': manual_price_cny,
                    'profit_margin': manual_margin,
                    'channel': manual_channel,
                    'notes': f"手动输入数据 | 售价: ₽{int(manual_price_rub)} | 利润率: {manual_margin:.1f}%"
                }
                
                # 保存到 session_state
                st.session_state['current_product'] = current_product
                st.success("✅ 数据已保存，请向下滚动生成PDF报告")
                st.rerun()
    else:
        # 显示商品信息
        st.success(f"✅ 已加载商品数据：{current_product.get('name', '未命名商品')}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("成本", f"¥{current_product.get('cost', 0):.2f}")
        
        with col2:
            st.metric("售价", f"₽{current_product.get('final_price_rub', 0)}")
        
        with col3:
            profit_margin = current_product.get('profit_margin', 0)
            st.metric("利润率", f"{profit_margin:.1f}%")
        
        st.markdown("---")
        
        # 自定义选项
        col1, col2 = st.columns(2)
        
        with col1:
            wechat_id = st.text_input(
                "微信号（用于页脚推广）",
                value="YourWeChatID",
                key="pdf_wechat"
            )
        
        with col2:
            report_title = st.text_input(
                "报告标题",
                value="Ozon选品盈利分析报告",
                key="pdf_title"
            )
        
        # 生成PDF按钮
        if st.button("📄 生成PDF报告", type="primary", use_container_width=True):
            with st.spinner("正在生成PDF报告..."):
                try:
                    import os
                    import requests
                    import tempfile
                    
                    # 创建PDF报告生成器（简化版，仅使用英文）
                    class ReportGenerator(FPDF):
                        def __init__(self):
                            super().__init__()
                            self.wechat_id = wechat_id
                        
                        def header(self):
                            # 页眉 - 标题（始终使用英文避免编码问题）
                            self.set_font('Arial', 'B', 18)
                            self.set_text_color(46, 125, 50)
                            self.cell(0, 15, 'Ozon Product Analysis Report', 0, 1, 'C')
                            self.ln(5)
                        
                        def footer(self):
                            # 页脚 - 裂变推广
                            self.set_y(-15)
                            self.set_font('Arial', 'I', 8)
                            self.set_text_color(128, 128, 128)
                            footer_text = f'Generated by Ozon Seller Pro | WeChat: {self.wechat_id}'
                            self.cell(0, 10, footer_text, 0, 0, 'C')
                    
                    # 创建PDF实例
                    pdf = ReportGenerator()
                    pdf.add_page()
                    
                    # 商品名称
                    pdf.set_font('Arial', 'B', 16)
                    pdf.set_text_color(0, 0, 0)
                    product_name = current_product.get('name', 'Unnamed Product')
                    
                    # 使用ASCII兼容的名称（避免中文渲染问题）
                    safe_name = product_name.encode('ascii', 'ignore').decode('ascii')
                    if not safe_name:
                        safe_name = f"Product #{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    pdf.cell(0, 10, safe_name, 0, 1, 'L')
                    pdf.ln(5)
                    
                    # 核心指标
                    pdf.set_font('Arial', 'B', 14)
                    pdf.set_text_color(0, 91, 255)
                    pdf.cell(0, 10, 'Core Metrics', 0, 1, 'L')
                    pdf.ln(2)
                    
                    pdf.set_font('Arial', '', 11)
                    pdf.set_text_color(0, 0, 0)
                    
                    cost = current_product.get('cost', 0)
                    final_price_rub = current_product.get('final_price_rub', 0)
                    final_price_cny = current_product.get('final_price_cny', 0)
                    profit_margin = current_product.get('profit_margin', 0)
                    
                    # 计算净利润
                    from utils import load_config
                    commission_rate = float(load_config('commission_rate', '15.0'))
                    shipping_fee = current_product.get('charge_weight', 0) * 0.03
                    commission_fee = final_price_cny * (commission_rate / 100)
                    net_profit = final_price_cny - cost - shipping_fee - commission_fee
                    
                    pdf.cell(0, 8, f'Cost: CNY {cost:.2f}', 0, 1)
                    pdf.cell(0, 8, f'Price: RUB {final_price_rub} (CNY {final_price_cny:.2f})', 0, 1)
                    pdf.cell(0, 8, f'Net Profit: CNY {net_profit:.2f}', 0, 1)
                    pdf.cell(0, 8, f'Profit Margin: {profit_margin:.1f}%', 0, 1)
                    pdf.ln(5)
                    
                    # 亮点推荐
                    if profit_margin > 20:
                        pdf.set_font('Arial', 'B', 11)
                        pdf.set_text_color(46, 125, 50)
                        pdf.cell(0, 10, 'Recommended - High Profit!', 0, 1, 'L')
                        pdf.ln(3)
                    
                    # 成本结构表格
                    pdf.set_font('Arial', 'B', 13)
                    pdf.set_text_color(0, 91, 255)
                    pdf.cell(0, 10, 'Cost Breakdown', 0, 1, 'L')
                    pdf.ln(2)
                    
                    # 获取页面宽度（减去左右边距）
                    page_width = pdf.w - 2 * pdf.l_margin
                    col1_width = page_width * 0.45  # 45% 给项目名称
                    col2_width = page_width * 0.30  # 30% 给金额
                    col3_width = page_width * 0.25  # 25% 给百分比
                    
                    # 表格表头
                    pdf.set_font('Arial', 'B', 10)
                    pdf.set_fill_color(240, 240, 240)
                    pdf.cell(col1_width, 8, 'Item', 1, 0, 'C', True)
                    pdf.cell(col2_width, 8, 'Amount (CNY)', 1, 0, 'C', True)
                    pdf.cell(col3_width, 8, 'Percentage', 1, 1, 'C', True)
                    
                    # 表格数据
                    pdf.set_font('Arial', '', 9)
                    items = [
                        ('Product Cost', cost, cost/final_price_cny*100),
                        ('Shipping Fee', shipping_fee, shipping_fee/final_price_cny*100),
                        ('Commission', commission_fee, commission_fee/final_price_cny*100),
                        ('Net Profit', net_profit, profit_margin),
                    ]
                    
                    for item_name, amount, percentage in items:
                        pdf.cell(col1_width, 8, item_name, 1, 0, 'L')
                        pdf.cell(col2_width, 8, f'{amount:.2f}', 1, 0, 'C')
                        pdf.cell(col3_width, 8, f'{percentage:.1f}%', 1, 1, 'C')
                    
                    # 总计（始终使用英文）
                    pdf.set_font('Arial', 'B', 10)
                    pdf.cell(col1_width, 8, 'Total Price', 1, 0, 'L')
                    pdf.cell(col2_width, 8, f'{final_price_cny:.2f}', 1, 0, 'C')
                    pdf.cell(col3_width, 8, '100.0%', 1, 1, 'C')
                    
                    pdf.ln(10)
                    
                    # 商品详情（始终使用英文）
                    pdf.set_font('Arial', 'B', 14)
                    pdf.set_text_color(0, 91, 255)
                    pdf.cell(0, 10, 'Product Details', 0, 1, 'L')
                    pdf.ln(2)
                    
                    pdf.set_font('Arial', '', 11)
                    pdf.set_text_color(0, 0, 0)
                    
                    weight = current_product.get('weight', 0)
                    charge_weight = current_product.get('charge_weight', 0)
                    channel = current_product.get('channel', 'N/A')
                    
                    # 确保channel是ASCII兼容的
                    safe_channel = channel.encode('ascii', 'ignore').decode('ascii')
                    if not safe_channel:
                        safe_channel = 'Standard'
                    
                    pdf.cell(0, 8, f'Weight: {weight}g (Chargeable: {charge_weight:.0f}g)', 0, 1)
                    pdf.cell(0, 8, f'Logistics Channel: {safe_channel}', 0, 1)
                    
                    length = current_product.get('length', 0)
                    width = current_product.get('width', 0)
                    height = current_product.get('height', 0)
                    
                    if length > 0 and width > 0 and height > 0:
                        pdf.cell(0, 8, f'Dimensions: {length:.0f} x {width:.0f} x {height:.0f} cm', 0, 1)
                    
                    pdf.ln(10)
                    
                    # 建议（始终使用英文）
                    pdf.set_font('Arial', 'B', 14)
                    pdf.set_text_color(0, 91, 255)
                    pdf.cell(0, 10, 'Recommendations', 0, 1, 'L')
                    pdf.ln(2)
                    
                    pdf.set_font('Arial', '', 11)
                    pdf.set_text_color(0, 0, 0)
                    
                    if profit_margin >= 20:
                        pdf.multi_cell(0, 8, '- Excellent profit margin! Strongly recommended for listing.')
                        pdf.multi_cell(0, 8, '- Consider increasing inventory for this high-potential product.')
                    elif profit_margin >= 10:
                        pdf.multi_cell(0, 8, '- Moderate profit margin. Evaluate market competition carefully.')
                        pdf.multi_cell(0, 8, '- Monitor sales performance and adjust pricing if needed.')
                    else:
                        pdf.multi_cell(0, 8, '- Low profit margin. Not recommended unless strategic reasons exist.')
                        pdf.multi_cell(0, 8, '- Consider negotiating better supplier prices or finding alternatives.')
                    
                    # 生成PDF到内存（新版fpdf2返回bytearray，不需要encode）
                    pdf_output = pdf.output()
                    
                    st.success("✅ PDF报告生成成功！")
                    
                    # 下载按钮
                    st.download_button(
                        label="📥 下载PDF报告",
                        data=pdf_output,
                        file_name=f"Ozon_Product_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True
                    )
                    
                    st.markdown("---")
                    st.info("""
                    **报告已生成！**
                    
                    - 📄 包含完整的盈利分析
                    - 📊 成本结构可视化表格
                    - 💡 智能推荐建议
                    - 🔗 页脚包含推广信息（裂变传播）
                    """)
                
                except Exception as e:
                    st.error(f"❌ PDF生成失败: {e}")
                    st.info("""
                    **可能的原因：**
                    - fpdf2库未安装（运行：pip install fpdf2）
                    - 数据格式问题
                    
                    **解决方案：**
                    1. 确保已安装依赖：`pip install -r requirements.txt`
                    2. 检查定价台数据是否完整
                    3. 如果问题持续，请联系技术支持
                    """)

st.markdown("---")

# 常用代码参考
with st.expander("📚 常用代码参考", expanded=False):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **品类代码**
        - CLO: 服装
        - SHO: 鞋类
        - BAG: 箱包
        - ACC: 配饰
        - ELE: 电子
        - HOM: 家居
        """)
    
    with col2:
        st.markdown("""
        **颜色代码**
        - BLK: 黑色
        - WHT: 白色
        - RED: 红色
        - BLU: 蓝色
        - GRN: 绿色
        - YEL: 黄色
        """)
    
    with col3:
        st.markdown("""
        **尺码代码**
        - XS: 加小号
        - S: 小号
        - M: 中号
        - L: 大号
        - XL: 加大号
        - XXL: 特大号
        """)


