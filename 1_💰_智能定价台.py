# -*- coding: utf-8 -*-
"""
Ozon Seller Pro v4.0 - 智能定价台
动态物流匹配 + 抛货计费 + 活动模拟 + 竞品反推
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from utils import (
    load_config, get_logistics_tiers, smart_match_logistics,
    get_charge_weight, get_profit_color, get_profit_status, sidebar_footer,
    save_history_record, get_history_records, reverse_calculate_cost, get_db_connection,
    export_analysis_image, get_ai_insight
)

st.set_page_config(page_title="智能定价台", page_icon="💰", layout="wide")

# ==================== 自定义CSS ====================
st.markdown("""
<style>
    .price-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .price-rub {
        font-size: 2.5rem;
        font-weight: 800;
        color: #F91155;
        margin: 1rem 0;
    }
    
    .profit-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 1rem;
        margin: 0.5rem 0;
    }
    
    .channel-info {
        background: #f0f4ff;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .bulky-warning {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 侧边栏 ====================
with st.sidebar:
    st.markdown("### 💰 定价参数")
    
    exchange_rate = float(load_config('exchange_rate', '13.5'))
    commission_rate = float(load_config('commission_rate', '15.0'))
    label_fee = float(load_config('label_fee', '1.5'))
    profit_rate = float(load_config('profit_rate', '1.35'))
    
    st.metric("汇率 (CNY→RUB)", f"{exchange_rate:.2f}")
    st.metric("佣金率", f"{commission_rate:.1f}%")
    st.metric("贴单费", f"¥{label_fee:.1f}")
    st.metric("利润率系数", f"{profit_rate:.2f}x")
    
    sidebar_footer()

# ==================== 主页面 ====================
st.title("💰 智能定价台")
st.markdown("输入商品成本和重量，自动匹配最优物流渠道，计算建议售价")

st.markdown("---")

# 创建标签页
tab1, tab2, tab3 = st.tabs(["💰 基础定价", "🎉 活动模拟", "📉 竞品反推"])

# ==================== Tab 1: 基础定价 ====================
with tab1:
    st.markdown("### 📝 商品信息")
    
    # 商品名称
    product_name = st.text_input(
        "商品名称（可选，用于记录）",
        placeholder="例如：女士羊绒围巾",
        key="product_name_input"
    )
    
    # 输入区域
    col1, col2 = st.columns(2)

    with col1:
        cost_cny = st.number_input(
            "商品成本 (CNY)",
            min_value=0.01,
            max_value=100000.0,
            value=50.0,
            step=1.0,
            format="%.2f",
            key="pricing_cost"
        )

    with col2:
        weight_g = st.number_input(
            "商品实际重量 (克)",
            min_value=1,
            max_value=50000,
            value=300,
            step=10,
            key="pricing_weight"
        )

    # 体积输入区域
    st.markdown("### 📦 体积信息（用于计算抛货）")
    st.caption("如果不填写体积，则按实际重量计费")

    col1, col2, col3 = st.columns(3)

    with col1:
        length_cm = st.number_input(
            "长度 (cm)",
            min_value=0.0,
            max_value=500.0,
            value=0.0,
            step=1.0,
            format="%.1f",
            key="pricing_length"
        )

    with col2:
        width_cm = st.number_input(
            "宽度 (cm)",
            min_value=0.0,
            max_value=500.0,
            value=0.0,
            step=1.0,
            format="%.1f",
            key="pricing_width"
        )

    with col3:
        height_cm = st.number_input(
            "高度 (cm)",
            min_value=0.0,
            max_value=500.0,
            value=0.0,
            step=1.0,
            format="%.1f",
            key="pricing_height"
        )
    
    # 计算按钮
    if st.button("🚀 开始计算", type="primary", use_container_width=True, key="calc_basic"):
        # 获取物流档位
        tiers = get_logistics_tiers()
        
        if not tiers:
            st.error("❌ 未找到物流档位配置，请前往「设置与关于」页面配置")
            st.stop()
        
        # 计算计费重量（考虑抛货）
        charge_weight, volume_weight, is_bulky = get_charge_weight(weight_g, length_cm, width_cm, height_cm)
        
        # 使用智能匹配算法
        match_result = smart_match_logistics(
            weight_g=charge_weight,
            cost_cny=cost_cny,
            profit_rate=profit_rate,
            commission_rate=commission_rate,
            label_fee=label_fee,
            tiers=tiers
        )
        
        if not match_result['matched']:
            st.error("❌ 未找到匹配的物流渠道")
            st.stop()
        
        matched_tier = match_result['tier']
        shipping_fee = match_result['shipping_fee']
        final_price_cny = match_result['final_price']
        final_price_rub = final_price_cny * exchange_rate
        
        # 计算利润
        commission_fee = final_price_cny * (commission_rate / 100)
        net_profit = final_price_cny - cost_cny - shipping_fee - commission_fee
        profit_margin = (net_profit / final_price_cny * 100) if final_price_cny > 0 else 0
        
        # 【关键】将所有计算结果封装到 session_state，供后续 UI 使用
        # 注意：键名必须与 save_history_record 函数预期的一致
        st.session_state['last_calculation'] = {
            'product_name': product_name if product_name else '未命名商品',
            'cost': cost_cny,
            'weight': weight_g,
            'charge_weight': charge_weight,
            'volume_weight': volume_weight,
            'is_bulky': is_bulky,
            'length': length_cm,
            'width': width_cm,
            'height': height_cm,
            'matched_tier': matched_tier,
            'channel_name': matched_tier['name'],
            'shipping_fee': shipping_fee,
            'final_price': final_price_cny,
            'final_price_rub': final_price_rub,
            'commission_fee': commission_fee,
            'profit': net_profit,  # 修改：使用 'profit' 而非 'net_profit'
            'margin': profit_margin  # 修改：使用 'margin' 而非 'profit_margin'
        }
    
    # ==================== UI 渲染逻辑（状态驱动，解耦按钮嵌套） ====================
    if 'last_calculation' in st.session_state:
        # 从 session_state 提取所有变量
        calc = st.session_state['last_calculation']
        product_name = calc['product_name']
        cost_cny = calc['cost']
        weight_g = calc['weight']
        charge_weight = calc['charge_weight']
        volume_weight = calc['volume_weight']
        is_bulky = calc['is_bulky']
        length_cm = calc['length']
        width_cm = calc['width']
        height_cm = calc['height']
        matched_tier = calc['matched_tier']
        shipping_fee = calc['shipping_fee']
        final_price_cny = calc['final_price']
        final_price_rub = calc['final_price_rub']
        commission_fee = calc['commission_fee']
        net_profit = calc['profit']  # 修改：从 'profit' 键读取
        profit_margin = calc['margin']  # 修改：从 'margin' 键读取
        
        # 显示结果
        st.markdown("---")
        st.markdown("## 📊 定价结果")
        
        # 抛货警告
        if is_bulky:
            st.markdown(f"""
            <div class="bulky-warning">
                <h3>⚠️ 触发抛货计费！</h3>
                <p><strong>实际重量：</strong>{weight_g}g</p>
                <p><strong>体积重量：</strong>{volume_weight:.0f}g (长{length_cm}×宽{width_cm}×高{height_cm} ÷ 6000)</p>
                <p><strong>计费重量：</strong>{charge_weight:.0f}g（取较大值）</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            if length_cm > 0 and width_cm > 0 and height_cm > 0:
                st.info(f"✅ 未触发抛货。实重 {weight_g}g ≥ 体积重 {volume_weight:.0f}g，按实重计费")
        
        # 物流渠道信息
        st.markdown(f"""
        <div class="channel-info">
            <h3>📦 匹配渠道：{matched_tier['name']}</h3>
            <p>固定费：¥{matched_tier['fixed_fee']:.2f} + 克重费：¥{matched_tier['per_gram_fee']:.3f}/g + 贴单费：¥{label_fee:.2f}</p>
            <p>计费重量：<strong>{charge_weight:.0f}g</strong></p>
            <p>总运费：<strong>¥{shipping_fee:.2f}</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        # 价格展示
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="price-card">
                <h4>💵 人民币售价</h4>
                <div style="font-size: 2rem; font-weight: 700; color: #005BFF;">
                    ¥{:.2f}
                </div>
            </div>
            """.format(final_price_cny), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="price-card">
                <h4>💎 卢布定价</h4>
                <div class="price-rub">
                    ₽{}
                </div>
                <div style="background: #f0f4ff; padding: 0.5rem; border-radius: 8px; margin-top: 1rem;">
                    <code style="font-size: 1.2rem; color: #005BFF;">{}</code>
                </div>
                <small style="color: #666;">建议售价</small>
            </div>
            """.format(int(final_price_rub), int(final_price_rub)), unsafe_allow_html=True)
        
        with col3:
            profit_color = get_profit_color(profit_margin)
            profit_status = get_profit_status(profit_margin)
            
            st.markdown(f"""
            <div class="price-card">
                <h4>📈 利润分析</h4>
                <div style="font-size: 1.8rem; font-weight: 700; color: {profit_color};">
                    ¥{net_profit:.2f}
                </div>
                <div class="profit-badge" style="background: {profit_color}; color: white;">
                    {profit_status} {profit_margin:.1f}%
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # 成本明细
        st.markdown("---")
        st.markdown("## 💡 成本明细")
        
        # 使用 4 个 st.metric 组成的精美矩阵
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💰 采购成本",
                value=f"¥{cost_cny:.2f}",
                delta=f"{cost_cny/final_price_cny*100:.1f}%",
                delta_color="normal"
            )
        
        with col2:
            st.metric(
                label="🚚 物流费用",
                value=f"¥{shipping_fee:.2f}",
                delta=f"{shipping_fee/final_price_cny*100:.1f}%",
                delta_color="inverse"
            )
        
        with col3:
            st.metric(
                label="📊 平台佣金",
                value=f"¥{commission_fee:.2f}",
                delta=f"{commission_fee/final_price_cny*100:.1f}%",
                delta_color="inverse"
            )
        
        with col4:
            st.metric(
                label="💎 预计净利润",
                value=f"¥{net_profit:.2f}",
                delta=f"{profit_margin:.1f}%",
                delta_color="normal"
            )
        
        # ==================== AI 智能洞察面板 ====================
        st.markdown("---")
        
        with st.expander("🤖 AI 智能利润拆解与爆款包装建议", expanded=True):
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 8px; color: white; margin-bottom: 1rem;">
                <p style="margin: 0; font-size: 0.9rem;">💡 <strong>DeepSeek AI</strong> 将基于您的测算数据，从利润健康度和视觉营销两个维度给出专业建议</p>
            </div>
            """, unsafe_allow_html=True)
            
            api_key = st.text_input(
                "🔑 输入 DeepSeek API Key 解锁 AI 洞察",
                type="password",
                key="ds_api_key_input",
                help="新用户可前往 platform.deepseek.com 免费获取数百万 Token 额度"
            )
            
            if st.button("🧠 立即生成 AI 深度点评", type="primary", use_container_width=True, key="btn_ai_insight"):
                if not api_key or api_key.strip() == "":
                    st.warning("⚠️ 请先输入 DeepSeek API Key")
                else:
                    with st.spinner("🤖 AI 正在疯狂计算并思考视觉包装策略..."):
                        from utils import get_ai_insight
                        
                        # 调用 AI 洞察函数
                        ai_result = get_ai_insight(calc, api_key.strip())
                        
                        # 渲染结果
                        if ai_result.startswith("❌"):
                            # 错误提示
                            st.error(ai_result)
                        else:
                            # 成功返回，精美展示
                            st.markdown("""
                            <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 1.5rem; border-radius: 12px; border-left: 4px solid #667eea;">
                                <h4 style="margin-top: 0; color: #667eea;">🎯 AI 专家点评</h4>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(ai_result)
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                            st.success("✅ AI 分析完成！建议已生成")
        
        # 三个操作按钮（解耦到外层，避免嵌套陷阱）
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 保存到历史记录", type="secondary", use_container_width=True, key="save_history"):
                try:
                    calc_data = st.session_state.get('last_calculation')
                    if not calc_data:
                        st.error("❌ 没有可保存的数据")
                    else:
                        result = save_history_record(calc_data)
                        if result:
                            st.success("✅ 已保存到历史记录！")
                            
                            # 【关键】清除所有缓存，确保侧边栏仪表盘立即更新
                            from utils import get_dashboard_stats
                            get_dashboard_stats.clear()  # 清除仪表盘统计缓存
                            st.cache_data.clear()  # 全局缓存清除
                            
                            # 清除历史记录缓存
                            if 'history_cache' in st.session_state:
                                del st.session_state['history_cache']
                            
                            # 延迟后刷新，让用户看到成功提示
                            import time
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ 保存失败，请检查数据库连接")
                except Exception as e:
                    st.error(f"❌ 保存失败: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        
        with col2:
            try:
                # 准备导出数据
                export_data = {
                    'product_name': product_name,
                    'cost': cost_cny,
                    'shipping_fee': shipping_fee,
                    'final_price_rub': final_price_rub,
                    'profit': net_profit,
                    'margin': profit_margin
                }
                
                img_data = export_analysis_image(export_data)
                # 兼容 BytesIO 或 plain bytes 格式
                final_data = img_data.getvalue() if hasattr(img_data, 'getvalue') else img_data
                
                st.download_button(
                    label="📸 下载利润分析图",
                    data=final_data,
                    file_name="Ozon_Analysis.png",
                    mime="image/png",
                    type="secondary",
                    use_container_width=True,
                    key="download_image"
                )
            except Exception as e:
                st.error(f"图片生成失败，错误信息: {e}")
        
        with col3:
            if st.button("✨ 一键生成上架文案 & SKU", type="primary", use_container_width=True, key="goto_content"):
                # 构建尺寸信息
                size_info = ""
                if length_cm > 0 and width_cm > 0 and height_cm > 0:
                    size_info = f" | 尺寸: {length_cm:.0f}×{width_cm:.0f}×{height_cm:.0f}cm"
                
                # 打包商品数据到 transfer_data（跨页面传输）
                st.session_state['transfer_data'] = {
                    'name': product_name,
                    'cost': cost_cny,
                    'weight': weight_g,
                    'charge_weight': charge_weight,
                    'length': length_cm,
                    'width': width_cm,
                    'height': height_cm,
                    'final_price_rub': int(final_price_rub),
                    'final_price_cny': final_price_cny,
                    'profit_margin': profit_margin,
                    'channel': matched_tier['name'],
                    'notes': f"建议售价: ₽{int(final_price_rub)} | 利润率: {profit_margin:.1f}%{size_info}"
                }
                
                # 跳转到内容生产线
                try:
                    st.switch_page("pages/2_📝_内容生产线.py")
                except AttributeError:
                    # 兼容旧版Streamlit
                    st.info("✅ 数据已保存！请手动切换到「📝 内容生产线」页面")
                except Exception as e:
                    st.warning(f"跳转失败，请手动切换页面。数据已保存到缓存。")
    
    # 显示最近5条历史记录
    st.markdown("---")
    st.markdown("### 📜 最近计算记录")
    
    # 使用缓存键来强制刷新
    cache_key = st.session_state.get('history_refresh_key', 0)
    
    history = get_history_records(limit=5)
    if history:
        history_display = []
        for record in history:
            history_display.append({
                "商品": record['product_name'],
                "成本": f"¥{record['cost']:.2f}",
                "计费重": f"{record['charge_weight']:.0f}g",
                "渠道": record['channel_name'],
                "售价": f"¥{record['final_price']:.2f}",
                "利润": f"¥{record['profit']:.2f}",
                "利润率": f"{record['margin']:.1f}%",
                "时间": record['created_at']
            })
        df_history = pd.DataFrame(history_display)
        st.dataframe(df_history, use_container_width=True, hide_index=True)
        
        # 显示记录总数
        st.caption(f"共 {len(history)} 条记录（最近5条）")
    else:
        st.info("暂无历史记录，完成定价计算后点击「保存到历史记录」按钮即可保存")

# ==================== Tab 2: 活动模拟 ====================  
with tab2:
    st.markdown("### 🎉 活动定价模拟器")
    st.info("模拟参加促销活动后的利润变化，反推平时应该标多少原价")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 商品成本输入（新增）
        promo_cost = st.number_input(
            "商品成本 (CNY)",
            min_value=0.01,
            max_value=100000.0,
            value=50.0,
            step=1.0,
            format="%.2f",
            key="promo_cost",
            help="输入商品的实际成本"
        )
        
        promo_weight = st.number_input(
            "商品重量 (克)",
            min_value=1,
            max_value=50000,
            value=300,
            step=10,
            key="promo_weight"
        )
    
    with col2:
        discount_pct = st.slider(
            "活动折扣 (%)",
            min_value=5,
            max_value=50,
            value=20,
            step=5,
            key="promo_discount",
            help="例如：20% 表示打8折"
        )
        
        min_margin = st.number_input(
            "保底利润率 (%)",
            min_value=5.0,
            max_value=50.0,
            value=15.0,
            step=1.0,
            key="promo_min_margin",
            help="打折后希望保持的最低利润率"
        )
    
    if st.button("🎯 开始模拟", type="primary", use_container_width=True, key="calc_promo"):
        # 获取物流档位
        tiers = get_logistics_tiers()
        if not tiers:
            st.error("❌ 未找到物流档位配置")
            st.stop()
        
        # 计算运费（基于重量）
        match_result = smart_match_logistics(
            weight_g=promo_weight,
            cost_cny=promo_cost,
            profit_rate=profit_rate,
            commission_rate=commission_rate,
            label_fee=label_fee,
            tiers=tiers
        )
        
        shipping_fee = match_result['shipping_fee']
        
        # ========== 第一步：计算保底目标售价 ==========
        # 公式：目标售价 = (成本 * (1 + 保底利润率) + 运费) / (1 - 佣金率)
        # 简化：目标售价 = (成本 + 运费 + 目标利润) / (1 - 佣金率)
        # 其中：目标利润 = (成本 + 运费) * 保底利润率 / (1 - 保底利润率)
        
        commission_factor = 1 - (commission_rate / 100)
        margin_factor = min_margin / 100
        
        # 计算保底目标售价（打折后的价格）
        target_price_cny = (promo_cost + shipping_fee) / (commission_factor * (1 - margin_factor))
        target_price_rub = target_price_cny * exchange_rate
        
        # ========== 第二步：计算建议原价 ==========
        # 公式：建议原价 = 保底目标售价 / (1 - 折扣率)
        discount_factor = 1 - (discount_pct / 100)
        suggested_original_price_cny = target_price_cny / discount_factor
        suggested_original_price_rub = suggested_original_price_cny * exchange_rate
        
        # ========== 计算打折后的实际数据 ==========
        discounted_price_cny = suggested_original_price_cny * discount_factor
        discounted_price_rub = discounted_price_cny * exchange_rate
        
        # 计算打折后的利润
        commission_fee = discounted_price_cny * (commission_rate / 100)
        net_profit = discounted_price_cny - promo_cost - shipping_fee - commission_fee
        actual_margin = (net_profit / discounted_price_cny * 100) if discounted_price_cny > 0 else 0
        
        # ========== 显示结果 ==========
        st.markdown("---")
        st.markdown("## 📊 模拟结果")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="price-card">
                <h4>💡 建议原价</h4>
                <div style="font-size: 2rem; font-weight: 700; color: #2E7D32;">
                    ₽{int(suggested_original_price_rub)}
                </div>
                <small>¥{suggested_original_price_cny:.2f}</small>
                <p style="margin-top: 0.5rem; color: #666; font-size: 0.85rem;">平时标价</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="price-card">
                <h4>📉 打折后</h4>
                <div style="font-size: 2rem; font-weight: 700; color: #F91155;">
                    ₽{int(discounted_price_rub)}
                </div>
                <small>¥{discounted_price_cny:.2f} (-{discount_pct}%)</small>
                <p style="margin-top: 0.5rem; color: #666; font-size: 0.85rem;">活动价格</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            profit_color = get_profit_color(actual_margin)
            st.markdown(f"""
            <div class="price-card">
                <h4>💰 净利润</h4>
                <div style="font-size: 2rem; font-weight: 700; color: {profit_color};">
                    ¥{net_profit:.2f}
                </div>
                <small>利润率: {actual_margin:.1f}%</small>
                <p style="margin-top: 0.5rem; color: #666; font-size: 0.85rem;">打折后利润</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 💡 成本明细")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            cost_breakdown = {
                "项目": ["商品成本", "物流运费", "平台佣金", "净利润", "打折后售价"],
                "金额 (CNY)": [
                    f"¥{promo_cost:.2f}",
                    f"¥{shipping_fee:.2f}",
                    f"¥{commission_fee:.2f}",
                    f"¥{net_profit:.2f}",
                    f"¥{discounted_price_cny:.2f}"
                ],
                "占比": [
                    f"{promo_cost/discounted_price_cny*100:.1f}%",
                    f"{shipping_fee/discounted_price_cny*100:.1f}%",
                    f"{commission_fee/discounted_price_cny*100:.1f}%",
                    f"{net_profit/discounted_price_cny*100:.1f}%",
                    "100.0%"
                ]
            }
            df_breakdown = pd.DataFrame(cost_breakdown)
            st.dataframe(df_breakdown, use_container_width=True, hide_index=True)
        
        with col2:
            st.info(f"""
            **计算说明**
            
            📦 运费：¥{shipping_fee:.2f}
            
            💰 成本：¥{promo_cost:.2f}
            
            🎯 保底利润率：{min_margin:.1f}%
            
            📉 折扣：{discount_pct}%
            
            ✅ 实际利润率：{actual_margin:.1f}%
            """)
        
        st.markdown("---")
        st.markdown("### 🎯 策略建议")
        
        st.success(f"""
        ✅ **定价策略**：
        
        1. **平时原价**：标价 **₽{int(suggested_original_price_rub)}** (¥{suggested_original_price_cny:.2f})
        
        2. **活动价格**：打 {100-discount_pct}折 后为 **₽{int(discounted_price_rub)}** (¥{discounted_price_cny:.2f})
        
        3. **利润保证**：打折后仍能保持 **{actual_margin:.1f}%** 的利润率（≥ {min_margin}%）
        
        4. **净利润**：每件商品赚 **¥{net_profit:.2f}**
        
        💡 **提示**：建议原价显著高于活动价，营造促销氛围，提高转化率！
        """)
        
        # 对比表格
        st.markdown("### 📊 方案对比")
        
        comparison_data = {
            "对比项": ["平时售价", "活动价格", "折扣力度", "利润率", "单件利润"],
            "建议方案": [
                f"₽{int(suggested_original_price_rub)}",
                f"₽{int(discounted_price_rub)}",
                f"{discount_pct}% OFF",
                f"{actual_margin:.1f}%",
                f"¥{net_profit:.2f}"
            ],
            "说明": [
                "高价定位",
                "保底利润",
                "吸引力强",
                "≥ 保底要求",
                "可持续经营"
            ]
        }
        
        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(df_comparison, use_container_width=True, hide_index=True)

# ==================== Tab 3: 竞品反推 ====================
with tab3:
    st.markdown("### 📉 竞品成本反推")
    st.info("根据竞品售价反推其进货成本上限，帮助你评估市场竞争力")
    
    col1, col2 = st.columns(2)
    
    with col1:
        competitor_price_rub = st.number_input(
            "竞品 Ozon 售价 (RUB)",
            min_value=1.0,
            max_value=100000.0,
            value=800.0,
            step=10.0,
            key="comp_price"
        )
    
    with col2:
        competitor_weight = st.number_input(
            "竞品预估重量 (克)",
            min_value=1,
            max_value=50000,
            value=300,
            step=10,
            key="comp_weight"
        )
    
    if st.button("🔍 开始反推", type="primary", use_container_width=True, key="calc_reverse"):
        # 使用反推函数
        result = reverse_calculate_cost(
            final_price_rub=competitor_price_rub,
            weight_g=competitor_weight,
            exchange_rate=exchange_rate,
            profit_rate=profit_rate,
            commission_rate=commission_rate,
            label_fee=label_fee
        )
        
        max_cost = result['max_cost']
        shipping_fee = result['shipping_fee']
        tier = result['tier']
        
        if max_cost <= 0:
            st.error("❌ 该售价无法覆盖成本，竞品可能亏本销售或使用了更低的物流渠道")
            st.stop()
        
        st.markdown("---")
        st.markdown("## 📊 反推结果")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="price-card">
                <h4>🎯 竞品售价</h4>
                <div style="font-size: 1.8rem; font-weight: 700; color: #005BFF;">
                    ₽{int(competitor_price_rub)}
                </div>
                <small>¥{competitor_price_rub / exchange_rate:.2f}</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="price-card">
                <h4>📦 预估运费</h4>
                <div style="font-size: 1.8rem; font-weight: 700; color: #FF9800;">
                    ¥{shipping_fee:.2f}
                </div>
                <small>{tier['name']}</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="price-card">
                <h4>💰 成本上限</h4>
                <div style="font-size: 1.8rem; font-weight: 700; color: #F91155;">
                    ¥{max_cost:.2f}
                </div>
                <small>不能超过此价格</small>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 💡 分析结论")
        
        st.success(f"""
        **如果你也想卖 ₽{int(competitor_price_rub)}：**
        
        - 📦 使用渠道：{tier['name']}
        - 🚚 运费成本：¥{shipping_fee:.2f}
        - 💵 进货价不能超过：**¥{max_cost:.2f}**
        - 📊 否则利润率会低于预期
        
        **建议**：
        - 如果你的进货价 < ¥{max_cost:.2f}，可以跟进这个价格
        - 如果你的进货价 > ¥{max_cost:.2f}，建议提高售价或寻找更便宜的货源
        """)
        
        # 成本分解
        st.markdown("### 📋 成本分解")
        
        competitor_price_cny = competitor_price_rub / exchange_rate
        commission_fee = competitor_price_cny * (commission_rate / 100)
        net_income = competitor_price_cny - commission_fee
        profit = net_income - shipping_fee - max_cost
        
        breakdown_data = {
            "项目": ["售价", "平台佣金", "物流运费", "推算成本", "推算利润"],
            "金额 (CNY)": [
                f"¥{competitor_price_cny:.2f}",
                f"-¥{commission_fee:.2f}",
                f"-¥{shipping_fee:.2f}",
                f"-¥{max_cost:.2f}",
                f"¥{profit:.2f}"
            ],
            "占比": [
                "100%",
                f"{commission_fee/competitor_price_cny*100:.1f}%",
                f"{shipping_fee/competitor_price_cny*100:.1f}%",
                f"{max_cost/competitor_price_cny*100:.1f}%",
                f"{profit/competitor_price_cny*100:.1f}%"
            ]
        }
        
        df_breakdown = pd.DataFrame(breakdown_data)
        st.dataframe(df_breakdown, use_container_width=True, hide_index=True)

st.markdown("---")

# 历史记录（显示在所有tab外面）
with st.expander("📜 查看完整历史记录", expanded=False):
    history = get_history_records(limit=20)
    if history:
        history_display = []
        for record in history:
            history_display.append({
                "商品": record['product_name'],
                "成本": f"¥{record['cost']:.2f}",
                "计费重": f"{record['charge_weight']:.0f}g",
                "渠道": record['channel_name'],
                "售价": f"¥{record['final_price']:.2f}",
                "利润": f"¥{record['profit']:.2f}",
                "利润率": f"{record['margin']:.1f}%",
                "时间": record['created_at']
            })
        df_history = pd.DataFrame(history_display)
        st.dataframe(df_history, use_container_width=True, hide_index=True)
        
        st.caption(f"共显示最近 {len(history)} 条记录")
        
        # 添加清空历史记录按钮
        if st.button("🗑️ 清空所有历史记录", key="clear_all_history"):
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM history")
                    conn.commit()
                st.success("✅ 历史记录已清空")
                st.rerun()
            except Exception as e:
                st.error(f"❌ 清空失败: {e}")
    else:
        st.info("暂无历史记录，完成定价计算后点击「保存到历史记录」按钮即可保存")

