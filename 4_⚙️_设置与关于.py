# -*- coding: utf-8 -*-
"""
Ozon Seller Pro v4.0 - 设置与关于
全局配置管理 + 物流档位编辑 + 实时汇率获取
"""
import streamlit as st
import pandas as pd
import requests
from utils import (
    load_config, save_config, get_logistics_tiers, 
    save_logistics_tiers, sidebar_footer
)

st.set_page_config(page_title="设置与关于", page_icon="⚙️", layout="wide")

# ==================== 自定义CSS ====================
st.markdown("""
<style>
    .config-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
    }
    
    .success-box {
        background: #E8F5E9;
        border-left: 4px solid #2E7D32;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: #FFF3E0;
        border-left: 4px solid #FF9800;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 侧边栏 ====================
with st.sidebar:
    st.markdown("### ⚙️ 设置导航")
    
    setting_section = st.radio(
        "选择设置项",
        ["汇率设置", "佣金设置", "物流配置", "数据管理", "关于系统"],
        key="setting_section"
    )
    
    sidebar_footer()

# ==================== 主页面 ====================
st.title("⚙️ 设置与关于")
st.markdown("全局参数配置与系统信息")

# 飞书更新中心按钮（极其醒目）
st.link_button(
    "🔄 查看最新版 & 官方教程中心 (强烈建议收藏)", 
    "https://www.feishu.cn/", 
    type="primary", 
    use_container_width=True
)

st.markdown("---")

# ==================== 汇率设置 ====================
if setting_section == "汇率设置":
    st.markdown("## 💱 汇率设置")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        current_rate = float(load_config('exchange_rate', '13.5'))
        
        st.info(f"当前汇率：1 CNY = {current_rate:.2f} RUB")
        
        new_rate = st.number_input(
            "设置新汇率 (CNY → RUB)",
            min_value=1.0,
            max_value=50.0,
            value=current_rate,
            step=0.01,
            format="%.2f",
            key="new_exchange_rate"
        )
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("💾 保存汇率", type="primary", use_container_width=True):
                if save_config('exchange_rate', new_rate):
                    st.success(f"✅ 汇率已更新为 {new_rate:.2f}")
                    st.rerun()
                else:
                    st.error("❌ 保存失败")
        
        with col_b:
            if st.button("🔄 获取实时汇率", use_container_width=True):
                with st.spinner("正在获取实时汇率..."):
                    success = False
                    error_messages = []
                    
                    # API列表（按优先级）
                    apis = [
                        {
                            "name": "ExchangeRate-API",
                            "url": "https://open.er-api.com/v6/latest/CNY",
                            "parser": lambda d: d['rates']['RUB'] if 'rates' in d and 'RUB' in d['rates'] else None
                        },
                        {
                            "name": "Frankfurter",
                            "url": "https://api.frankfurter.app/latest?from=CNY&to=RUB",
                            "parser": lambda d: d['rates']['RUB'] if 'rates' in d and 'RUB' in d['rates'] else None
                        },
                        {
                            "name": "ExchangeRate.host",
                            "url": "https://api.exchangerate.host/latest?base=CNY&symbols=RUB",
                            "parser": lambda d: d['rates']['RUB'] if 'rates' in d and 'RUB' in d['rates'] else None
                        },
                        {
                            "name": "Currency-API",
                            "url": "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/cny.json",
                            "parser": lambda d: d['cny']['rub'] if 'cny' in d and 'rub' in d['cny'] else None
                        }
                    ]
                    
                    # 尝试所有API
                    for api in apis:
                        try:
                            st.caption(f"尝试 {api['name']}...")
                            response = requests.get(api['url'], timeout=8)
                            
                            if response.status_code == 200:
                                data = response.json()
                                real_rate = api['parser'](data)
                                
                                if real_rate and real_rate > 0:
                                    st.success(f"✅ 获取成功！来源：{api['name']}")
                                    st.info(f"实时汇率：1 CNY = {real_rate:.4f} RUB")
                                    
                                    if save_config('exchange_rate', real_rate):
                                        st.success("✅ 已自动保存")
                                        success = True
                                        st.rerun()
                                        break
                                else:
                                    error_messages.append(f"{api['name']}: 数据格式错误")
                            else:
                                error_messages.append(f"{api['name']}: HTTP {response.status_code}")
                        
                        except requests.Timeout:
                            error_messages.append(f"{api['name']}: 请求超时")
                        except requests.ConnectionError:
                            error_messages.append(f"{api['name']}: 网络连接失败")
                        except Exception as e:
                            error_messages.append(f"{api['name']}: {str(e)}")
                    
                    # 如果所有API都失败
                    if not success:
                        st.error("❌ 所有汇率API均获取失败，请手动输入汇率")
                        
                        with st.expander("查看详细错误信息"):
                            for msg in error_messages:
                                st.caption(f"• {msg}")
                        
                        st.warning("""
                        **可能的原因：**
                        - 网络连接问题
                        - 防火墙拦截
                        - API服务暂时不可用
                        
                        **解决方案：**
                        1. 检查网络连接
                        2. 手动输入汇率（可从百度/谷歌搜索"人民币卢布汇率"）
                        3. 稍后重试
                        """)
    
    with col2:
        st.markdown("""
        <div class="warning-box">
            <h4>💡 使用提示</h4>
            <p>• 点击「获取实时汇率」自动更新</p>
            <p>• 获取失败时可手动输入</p>
            <p>• 汇率影响所有定价计算</p>
            <p>• 建议每日更新一次</p>
        </div>
        """, unsafe_allow_html=True)

# ==================== 佣金设置 ====================
elif setting_section == "佣金设置":
    st.markdown("## 💰 佣金与费用设置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 平台佣金率")
        
        current_commission = float(load_config('commission_rate', '15.0'))
        
        new_commission = st.number_input(
            "平台佣金率 (%)",
            min_value=0.0,
            max_value=50.0,
            value=current_commission,
            step=0.5,
            format="%.1f",
            key="new_commission_rate",
            help="Ozon平台收取的佣金百分比"
        )
        
        st.info(f"当前佣金率：{current_commission:.1f}%")
        
        if st.button("💾 保存佣金率", type="primary", use_container_width=True):
            if save_config('commission_rate', new_commission):
                st.success(f"✅ 佣金率已更新为 {new_commission:.1f}%")
                st.rerun()
            else:
                st.error("❌ 保存失败")
    
    with col2:
        st.markdown("### 其他费用")
        
        current_label_fee = float(load_config('label_fee', '1.5'))
        
        new_label_fee = st.number_input(
            "贴单费 (CNY)",
            min_value=0.0,
            max_value=20.0,
            value=current_label_fee,
            step=0.1,
            format="%.1f",
            key="new_label_fee",
            help="每单的贴单费用"
        )
        
        st.info(f"当前贴单费：¥{current_label_fee:.1f}")
        
        if st.button("💾 保存贴单费", type="primary", use_container_width=True):
            if save_config('label_fee', new_label_fee):
                st.success(f"✅ 贴单费已更新为 ¥{new_label_fee:.1f}")
                st.rerun()
            else:
                st.error("❌ 保存失败")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 利润率系数")
        
        current_profit_rate = float(load_config('profit_rate', '1.35'))
        
        new_profit_rate = st.number_input(
            "利润率系数",
            min_value=1.0,
            max_value=5.0,
            value=current_profit_rate,
            step=0.05,
            format="%.2f",
            key="new_profit_rate",
            help="成本乘以此系数得到基础售价"
        )
        
        st.info(f"当前系数：{current_profit_rate:.2f}x")
        
        if st.button("💾 保存利润率系数", type="primary", use_container_width=True):
            if save_config('profit_rate', new_profit_rate):
                st.success(f"✅ 利润率系数已更新为 {new_profit_rate:.2f}x")
                st.rerun()
            else:
                st.error("❌ 保存失败")
    
    with col2:
        st.markdown("""
        <div class="success-box">
            <h4>📊 计算公式</h4>
            <p><strong>售价 = (成本 × 利润率系数 + 运费) / (1 - 佣金率%)</strong></p>
            <p>• 利润率系数：控制基础利润</p>
            <p>• 佣金率：平台抽成比例</p>
            <p>• 贴单费：计入运费成本</p>
        </div>
        """, unsafe_allow_html=True)

# ==================== 物流配置 ====================
elif setting_section == "物流配置":
    st.markdown("## 📦 物流档位配置")
    st.info("支持增删改物流档位，系统将按优先级自动匹配最优渠道")
    
    # 加载当前物流档位
    tiers = get_logistics_tiers()
    
    if tiers:
        # 转换为DataFrame
        df_tiers = pd.DataFrame(tiers)
        
        st.markdown("### 📋 当前物流档位")
        
        # 使用data_editor进行编辑
        edited_df = st.data_editor(
            df_tiers,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "name": st.column_config.TextColumn("渠道名称", required=True),
                "max_weight": st.column_config.NumberColumn(
                    "最大重量(g)",
                    help="0表示无限制",
                    min_value=0,
                    format="%.0f"
                ),
                "max_price": st.column_config.NumberColumn(
                    "最大价格(CNY)",
                    help="0表示无限制",
                    min_value=0,
                    format="%.2f"
                ),
                "fixed_fee": st.column_config.NumberColumn(
                    "固定费(CNY)",
                    min_value=0,
                    format="%.2f"
                ),
                "per_gram_fee": st.column_config.NumberColumn(
                    "克重费(CNY/g)",
                    min_value=0,
                    format="%.4f"
                ),
                "priority": st.column_config.NumberColumn(
                    "优先级",
                    help="数字越小优先级越高",
                    min_value=1,
                    format="%.0f"
                )
            },
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="logistics_editor"
        )
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button("💾 保存物流配置", type="primary", use_container_width=True):
                # 转换回字典列表
                new_tiers = edited_df.to_dict('records')
                
                if save_logistics_tiers(new_tiers):
                    st.success("✅ 物流配置已保存")
                    st.rerun()
                else:
                    st.error("❌ 保存失败")
        
        with col2:
            if st.button("🔄 重置为默认", use_container_width=True):
                default_tiers = [
                    {"name": "轻小件", "max_weight": 500, "max_price": 135, 
                     "fixed_fee": 2.6, "per_gram_fee": 0.035, "priority": 1},
                    {"name": "标准轻小", "max_weight": 2000, "max_price": 635, 
                     "fixed_fee": 16.0, "per_gram_fee": 0.033, "priority": 2},
                    {"name": "标准大件", "max_weight": 30000, "max_price": 635, 
                     "fixed_fee": 36.0, "per_gram_fee": 0.025, "priority": 3},
                    {"name": "中等件/兜底", "max_weight": 0, "max_price": 0, 
                     "fixed_fee": 23.0, "per_gram_fee": 0.025, "priority": 4}
                ]
                
                if save_logistics_tiers(default_tiers):
                    st.success("✅ 已重置为默认配置")
                    st.rerun()
        
        with col3:
            # 导出配置
            csv = edited_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "📥 导出配置",
                csv,
                "物流配置.csv",
                "text/csv",
                use_container_width=True
            )
    
    else:
        st.warning("⚠️ 未找到物流档位配置")
        
        if st.button("初始化默认配置", type="primary"):
            default_tiers = [
                {"name": "轻小件", "max_weight": 500, "max_price": 135, 
                 "fixed_fee": 2.6, "per_gram_fee": 0.035, "priority": 1},
                {"name": "标准轻小", "max_weight": 2000, "max_price": 635, 
                 "fixed_fee": 16.0, "per_gram_fee": 0.033, "priority": 2},
                {"name": "标准大件", "max_weight": 30000, "max_price": 635, 
                 "fixed_fee": 36.0, "per_gram_fee": 0.025, "priority": 3},
                {"name": "中等件/兜底", "max_weight": 0, "max_price": 0, 
                 "fixed_fee": 23.0, "per_gram_fee": 0.025, "priority": 4}
            ]
            
            if save_logistics_tiers(default_tiers):
                st.success("✅ 默认配置已初始化")
                st.rerun()
    
    st.markdown("---")
    
    with st.expander("💡 配置说明", expanded=False):
        st.markdown("""
        ### 字段说明
        
        - **渠道名称**: 物流渠道的名称（如"轻小件"）
        - **最大重量**: 该渠道支持的最大重量（克），0表示无限制
        - **最大价格**: 该渠道支持的最大商品价格（元），0表示无限制
        - **固定费**: 该渠道的固定运费（元）
        - **克重费**: 每克的运费（元/克）
        - **优先级**: 匹配顺序，数字越小优先级越高
        
        ### 匹配逻辑
        
        系统按优先级从小到大遍历所有档位：
        1. 检查重量是否满足：`重量 <= 最大重量` 或 `最大重量 = 0`
        2. 检查价格是否满足：`价格 <= 最大价格` 或 `最大价格 = 0`
        3. 找到第一个同时满足的档位即为匹配结果
        4. 如果都不匹配，使用最后一个档位作为兜底
        
        ### 使用建议
        
        - 最后一个档位建议设置为兜底档位（max_weight=0, max_price=0）
        - 优先级数字要连续且唯一
        - 可以添加自定义档位（如"超轻小件"）
        - 修改后记得点击「保存物流配置」
        """)

# ==================== 数据管理 ====================
elif setting_section == "数据管理":
    st.markdown("## 💾 数据管理")
    
    st.warning("⚠️ 强烈建议每次升级新版本前，先导出备份数据防丢失！")
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📥 一键导出备份数据")
        
        st.info("""
        **备份说明：**
        - 备份文件包含所有配置、物流档位、历史记录
        - 建议定期备份，防止数据丢失
        - 升级新版本前务必备份
        - 备份文件可用于数据恢复或迁移
        """)
        
        # 读取数据库文件
        import os
        db_path = os.path.join(os.getcwd(), "ozon_config.db")
        
        if os.path.exists(db_path):
            try:
                with open(db_path, 'rb') as f:
                    db_data = f.read()
                
                # 生成备份文件名（带时间戳）
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"OzonSellerPro_Backup_{timestamp}.db"
                
                st.download_button(
                    label="📥 下载数据库备份",
                    data=db_data,
                    file_name=backup_filename,
                    mime="application/octet-stream",
                    type="primary",
                    use_container_width=True,
                    help="点击下载完整数据库备份文件"
                )
                
                st.success(f"✅ 数据库文件大小: {len(db_data) / 1024:.2f} KB")
                
            except Exception as e:
                st.error(f"❌ 读取数据库失败: {str(e)}")
        else:
            st.error("❌ 未找到数据库文件")
    
    with col2:
        st.markdown("""
        <div class="warning-box">
            <h4>⚠️ 重要提示</h4>
            <p>• 备份文件请妥善保管</p>
            <p>• 不要随意修改备份文件</p>
            <p>• 升级前必须备份</p>
            <p>• 建议每周备份一次</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="success-box">
            <h4>📊 数据库信息</h4>
            <p><strong>文件名:</strong> ozon_config.db</p>
            <p><strong>类型:</strong> SQLite3</p>
            <p><strong>位置:</strong> 程序根目录</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 📋 数据库版本信息")
    
    # 显示数据库版本
    try:
        from utils import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 检查是否有 db_meta 表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='db_meta'")
            if cursor.fetchone():
                cursor.execute("SELECT version FROM db_meta LIMIT 1")
                row = cursor.fetchone()
                if row:
                    db_version = row[0]
                    st.success(f"✅ 当前数据库版本: v{db_version}")
                else:
                    st.warning("⚠️ 数据库版本信息缺失")
            else:
                st.info("ℹ️ 数据库版本表尚未创建（将在下次启动时自动创建）")
    except Exception as e:
        st.error(f"❌ 读取版本信息失败: {str(e)}")
    
    st.markdown("---")
    
    with st.expander("💡 数据恢复说明", expanded=False):
        st.markdown("""
        ### 如何恢复备份数据
        
        1. **关闭程序**：确保 Ozon Seller Pro 已完全关闭
        2. **找到数据库文件**：在程序根目录找到 `ozon_config.db`
        3. **替换文件**：用备份文件替换现有的 `ozon_config.db`
        4. **重启程序**：重新启动 Ozon Seller Pro
        
        ### 注意事项
        
        - 恢复前请确保程序已关闭
        - 建议先备份当前数据库再恢复
        - 不同版本的数据库可能不兼容
        - 如遇问题请联系技术支持
        """)

# ==================== 关于系统 ====================
elif setting_section == "关于系统":
    st.markdown("## ℹ️ 关于系统")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="config-card">
            <h2>🚀 Ozon Seller Pro v4.0</h2>
            <p style="font-size: 1.1rem; color: #666; margin: 1rem 0;">
                跨境电商智能助手 · 终极商业化版本
            </p>
            <hr>
            <h3>✨ 核心功能</h3>
            <ul style="line-height: 2;">
                <li>💰 <strong>智能定价台</strong> - 动态物流匹配 + 利润红绿灯</li>
                <li>📝 <strong>内容生产线</strong> - AI Prompt + HTML尺码表 + JSON工具</li>
                <li>📦 <strong>选品与SKU</strong> - 智能SKU生成器</li>
                <li>⚙️ <strong>设置与关于</strong> - 全局配置管理</li>
            </ul>
            <hr>
            <h3>🎯 v4.0 重大更新</h3>
            <ul style="line-height: 2;">
                <li>✅ 数据库架构升级（logistics_tiers + config表）</li>
                <li>✅ 动态物流匹配算法（优先级+兜底机制）</li>
                <li>✅ 实时汇率获取（无需API Key）</li>
                <li>✅ 物流档位可视化编辑</li>
                <li>✅ 利润红绿灯预警系统</li>
                <li>✅ AI Prompt All-in-One模式</li>
                <li>✅ HTML尺码表生成器</li>
                <li>✅ 全面健壮性优化</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="success-box">
            <h4>📊 系统信息</h4>
            <p><strong>版本号:</strong> v4.0</p>
            <p><strong>发布日期:</strong> 2024-12</p>
            <p><strong>架构:</strong> Streamlit多页面</p>
            <p><strong>数据库:</strong> SQLite3</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="warning-box">
            <h4>💡 使用建议</h4>
            <p>• 首次使用请先配置汇率</p>
            <p>• 定期更新物流档位</p>
            <p>• 根据实际调整佣金率</p>
            <p>• 建议每日更新汇率</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="config-card" style="text-align: center;">
            <h4>📞 技术支持</h4>
            <p>如有问题请联系开发团队</p>
            <p style="color: #999; font-size: 0.9rem; margin-top: 1rem;">
                © 2024 Ozon Seller Pro<br>
                All Rights Reserved
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 系统状态检查
    st.markdown("### 🔍 系统状态检查")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        exchange_rate = load_config('exchange_rate', None)
        if exchange_rate:
            st.success("✅ 汇率已配置")
        else:
            st.error("❌ 汇率未配置")
    
    with col2:
        commission_rate = load_config('commission_rate', None)
        if commission_rate:
            st.success("✅ 佣金率已配置")
        else:
            st.error("❌ 佣金率未配置")
    
    with col3:
        tiers = get_logistics_tiers()
        if tiers:
            st.success(f"✅ {len(tiers)}个物流档位")
        else:
            st.error("❌ 物流档位未配置")
    
    with col4:
        label_fee = load_config('label_fee', None)
        if label_fee:
            st.success("✅ 贴单费已配置")
        else:
            st.error("❌ 贴单费未配置")

st.markdown("---")

# 底部信息
st.markdown("""
<div style="text-align: center; color: #999; font-size: 0.85rem; padding: 2rem 0;">
    <p><strong>Ozon Seller Pro v4.0</strong> - 让跨境电商运营更简单</p>
    <p>© 2024 All Rights Reserved</p>
</div>
""", unsafe_allow_html=True)


