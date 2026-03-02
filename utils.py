# -*- coding: utf-8 -*-
"""
Ozon Seller Pro - 工具函数库
包含数据库操作、配置管理、通用函数等
"""
import sqlite3
import streamlit as st
from contextlib import contextmanager
import os
import requests
import json

# 数据库文件路径（基于当前运行目录，兼容打包后的环境）
current_dir = os.getcwd()
DB_PATH = os.path.join(current_dir, "ozon_config.db")

# 云端配置URL（占位符，请替换为实际的GitHub仓库地址）
REMOTE_CONFIG_URL = "https://raw.githubusercontent.com/你的用户名/OzonPro/main/config.json"


@contextmanager
def get_db_connection():
    """数据库连接上下文管理器"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database():
    """
    初始化数据库表结构（防崩兜底版）
    首次运行时自动创建数据库和默认配置，绝不抛出异常
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 创建 db_meta 表（数据库版本管理）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS db_meta (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    version INTEGER NOT NULL DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 检查并初始化数据库版本
            cursor.execute("SELECT version FROM db_meta WHERE id = 1")
            row = cursor.fetchone()
            
            if row is None:
                # 首次创建，插入版本 1
                cursor.execute("INSERT INTO db_meta (id, version) VALUES (1, 1)")
                current_version = 1
            else:
                current_version = row[0]
            
            # 创建 config 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            
            # 创建 logistics_tiers 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logistics_tiers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    max_weight REAL DEFAULT 0,
                    max_price REAL DEFAULT 0,
                    fixed_fee REAL DEFAULT 0,
                    per_gram_fee REAL DEFAULT 0,
                    priority INTEGER DEFAULT 0
                )
            """)
            
            # 创建 history 表（测款历史记录）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT,
                    cost REAL,
                    weight REAL,
                    charge_weight REAL,
                    channel_name TEXT,
                    shipping_fee REAL,
                    final_price REAL,
                    profit REAL,
                    margin REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 【关键】初始化默认配置（使用 INSERT OR IGNORE 防止重复插入）
            default_configs = [
                ('commission_rate', '15.0'),
                ('exchange_rate', '13.5'),
                ('label_fee', '1.5'),
                ('profit_rate', '1.35')
            ]
            
            for key, value in default_configs:
                cursor.execute("""
                    INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)
                """, (key, value))
            
            # 【关键】初始化默认物流档位（仅在表为空时插入）
            cursor.execute("SELECT COUNT(*) FROM logistics_tiers")
            count = cursor.fetchone()[0]
            
            if count == 0:
                default_tiers = [
                    ("轻小件", 500, 135, 2.6, 0.035, 1),
                    ("标准轻小", 2000, 635, 16.0, 0.033, 2),
                    ("标准大件", 30000, 635, 36.0, 0.025, 3),
                    ("中等件/兜底", 0, 0, 23.0, 0.025, 4)
                ]
                cursor.executemany("""
                    INSERT INTO logistics_tiers (name, max_weight, max_price, fixed_fee, per_gram_fee, priority)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, default_tiers)
            
            conn.commit()
            print("✅ 数据库初始化成功")
            
    except Exception as e:
        # 【防崩兜底】即使出错也不影响程序启动，只打印错误日志
        print(f"⚠️ 数据库初始化警告: {e}")
        import traceback
        traceback.print_exc()


def load_config(key, default_value=None):
    """从数据库加载配置"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM config WHERE key=?", (key,))
            row = cursor.fetchone()
            if row:
                return row['value']
            return default_value
    except Exception as e:
        st.error(f"加载配置失败: {e}")
        return default_value


def save_config(key, value):
    """保存配置到数据库"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO config (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """, (key, str(value)))
            conn.commit()
            return True
    except Exception as e:
        st.error(f"保存配置失败: {e}")
        return False


def get_logistics_tiers():
    """获取所有物流档位"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, max_weight, max_price, fixed_fee, per_gram_fee, priority
                FROM logistics_tiers
                ORDER BY priority ASC
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        st.error(f"加载物流档位失败: {e}")
        return []


def save_logistics_tiers(tiers_data):
    """保存物流档位数据"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # 清空现有数据
            cursor.execute("DELETE FROM logistics_tiers")
            # 插入新数据
            for tier in tiers_data:
                cursor.execute("""
                    INSERT INTO logistics_tiers (name, max_weight, max_price, fixed_fee, per_gram_fee, priority)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    tier.get('name', ''),
                    tier.get('max_weight', 0),
                    tier.get('max_price', 0),
                    tier.get('fixed_fee', 0),
                    tier.get('per_gram_fee', 0),
                    tier.get('priority', 0)
                ))
            conn.commit()
            return True
    except Exception as e:
        st.error(f"保存物流档位失败: {e}")
        return False


def smart_match_logistics(weight_g, cost_cny, profit_rate, commission_rate, label_fee, tiers=None):
    """
    智能物流匹配算法 - 解决抛货漏算和死循环问题
    
    参数:
        weight_g: 计费重量（克）
        cost_cny: 商品成本（人民币）
        profit_rate: 利润率系数
        commission_rate: 平台佣金率（百分比）
        label_fee: 贴单费
        tiers: 物流档位列表
    
    返回:
        dict: {
            'tier': 匹配的档位,
            'shipping_fee': 运费,
            'final_price': 最终售价,
            'matched': 是否成功匹配
        }
    """
    if tiers is None:
        tiers = get_logistics_tiers()
    
    if not tiers:
        return {
            'tier': None,
            'shipping_fee': 0,
            'final_price': 0,
            'matched': False
        }
    
    # 按优先级遍历档位
    for tier in tiers:
        # 计算该档位下的试算运费
        trial_shipping = tier['fixed_fee'] + label_fee + (weight_g * tier['per_gram_fee'])
        
        # 计算该档位下的试算售价
        commission_factor = 1 - (commission_rate / 100)
        product_base = cost_cny * profit_rate
        trial_price = (product_base + trial_shipping) / commission_factor
        
        # 判断是否满足该档位条件
        weight_ok = (tier['max_weight'] == 0) or (weight_g <= tier['max_weight'])
        price_ok = (tier['max_price'] == 0) or (trial_price <= tier['max_price'])
        
        if weight_ok and price_ok:
            return {
                'tier': tier,
                'shipping_fee': trial_shipping,
                'final_price': trial_price,
                'matched': True
            }
    
    # 兜底：使用最后一个档位
    last_tier = tiers[-1]
    fallback_shipping = last_tier['fixed_fee'] + label_fee + (weight_g * last_tier['per_gram_fee'])
    commission_factor = 1 - (commission_rate / 100)
    product_base = cost_cny * profit_rate
    fallback_price = (product_base + fallback_shipping) / commission_factor
    
    return {
        'tier': last_tier,
        'shipping_fee': fallback_shipping,
        'final_price': fallback_price,
        'matched': True
    }


def match_logistics_channel(weight_g, price_cny, tiers=None):
    """
    匹配物流渠道（保留旧接口兼容性）
    按 priority 遍历，找到第一个满足条件的档位
    条件：(weight <= max_weight OR max_weight=0) AND (price <= max_price OR max_price=0)
    """
    if tiers is None:
        tiers = get_logistics_tiers()
    
    if not tiers:
        return None
    
    for tier in tiers:
        weight_ok = (tier['max_weight'] == 0) or (weight_g <= tier['max_weight'])
        price_ok = (tier['max_price'] == 0) or (price_cny <= tier['max_price'])
        
        if weight_ok and price_ok:
            return tier
    
    # 兜底：返回最后一个档位
    return tiers[-1]


def calculate_shipping_fee(weight_g, tier, label_fee=0):
    """计算运费"""
    if tier is None:
        return 0
    return tier['fixed_fee'] + label_fee + (weight_g * tier['per_gram_fee'])


def calculate_final_price(cost_cny, shipping_cny, profit_rate, commission_rate):
    """
    计算最终售价
    commission_rate: 平台佣金率（百分比，如15表示15%）
    """
    commission_factor = 1 - (commission_rate / 100)
    product_base = cost_cny * profit_rate
    return (product_base + shipping_cny) / commission_factor


def calculate_volume_weight(length_cm, width_cm, height_cm):
    """
    计算体积重
    公式: (长 × 宽 × 高) / 6000
    """
    if length_cm <= 0 or width_cm <= 0 or height_cm <= 0:
        return 0
    return (length_cm * width_cm * height_cm) / 6000


def get_charge_weight(actual_weight_g, length_cm, width_cm, height_cm):
    """
    获取计费重量（实重与体积重取大）
    返回: (计费重, 体积重, 是否抛货)
    """
    volume_weight = calculate_volume_weight(length_cm, width_cm, height_cm)
    charge_weight = max(actual_weight_g, volume_weight)
    is_bulky = volume_weight > actual_weight_g
    
    return charge_weight, volume_weight, is_bulky


@st.cache_data(ttl=30)
def get_dashboard_stats():
    """
    获取仪表盘统计数据（带缓存，30秒刷新）
    
    返回:
        tuple: (今日测算数, 高利润产品数, 累计潜在利润)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 今日测算数 (按当地时间计算)
            cursor.execute("SELECT COUNT(*) FROM history WHERE date(created_at, 'localtime') = date('now', 'localtime')")
            today_count = cursor.fetchone()[0] or 0
            
            # 发现的高利润产品数 (margin >= 20.0)
            cursor.execute("SELECT COUNT(*) FROM history WHERE margin >= 20.0")
            high_profit_count = cursor.fetchone()[0] or 0
            
            # 累计潜在利润（使用 COALESCE 处理 NULL）
            cursor.execute("SELECT COALESCE(SUM(profit), 0) FROM history")
            total_profit = cursor.fetchone()[0] or 0
            
            return today_count, high_profit_count, total_profit
    except Exception as e:
        # 出错时返回默认值，避免侧边栏崩溃
        print(f"⚠️ 获取仪表盘统计失败: {e}")
        return 0, 0, 0


def sidebar_footer():
    """侧边栏底部信息"""
    st.sidebar.markdown("---")
    
    # 搞钱仪表盘
    st.sidebar.markdown("### 📊 我的搞钱战绩")
    
    # 获取统计数据
    today_count, high_profit_count, total_profit = get_dashboard_stats()
    
    # 上排：今日测算 & 发现爆款
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        st.metric(
            label="今日测算",
            value=f"{today_count}",
            delta="↑" if today_count > 0 else None,
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            label="发现爆款",
            value=f"{high_profit_count}",
            delta="↑" if high_profit_count > 0 else None,
            delta_color="normal"
        )
    
    # 下排：累计潜在利润
    st.sidebar.metric(
        label="累计潜在利润",
        value=f"¥{total_profit:,.2f}",
        delta=None
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <div style="text-align: center; color: #999; font-size: 0.75rem; padding: 1rem 0;">
        <p><strong>Ozon Seller Pro v4.0</strong></p>
        <p>跨境电商智能助手</p>
        <p>© 2024 All Rights Reserved</p>
    </div>
    """, unsafe_allow_html=True)


def format_currency(value, currency="CNY"):
    """格式化货币显示"""
    if currency == "CNY":
        return f"¥{value:.2f}"
    elif currency == "RUB":
        return f"₽{int(value)}"
    else:
        return f"{value:.2f}"


def get_profit_color(profit_margin):
    """根据利润率返回颜色"""
    if profit_margin >= 20:
        return "#2E7D32"  # 绿色
    elif profit_margin >= 10:
        return "#FF9800"  # 橙色
    else:
        return "#C62828"  # 红色


def get_profit_status(profit_margin):
    """根据利润率返回状态文本"""
    if profit_margin >= 20:
        return "✅ 优秀"
    elif profit_margin >= 10:
        return "⚠️ 一般"
    else:
        return "❌ 偏低"


def save_history_record(data_dict):
    """
    保存测款历史记录
    
    参数:
        data_dict: {
            'product_name': 商品名称,
            'cost': 成本,
            'weight': 实重,
            'charge_weight': 计费重,
            'channel_name': 渠道名称,
            'shipping_fee': 运费,
            'final_price': 最终售价,
            'profit': 利润,
            'margin': 利润率
        }
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO history (
                    product_name, cost, weight, charge_weight, channel_name,
                    shipping_fee, final_price, profit, margin
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data_dict.get('product_name', '未命名商品'),
                data_dict.get('cost', 0),
                data_dict.get('weight', 0),
                data_dict.get('charge_weight', 0),
                data_dict.get('channel_name', ''),
                data_dict.get('shipping_fee', 0),
                data_dict.get('final_price', 0),
                data_dict.get('profit', 0),
                data_dict.get('margin', 0)
            ))
            conn.commit()
            print(f"✅ 历史记录保存成功: {data_dict.get('product_name', '未命名商品')}")
            return True
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ 保存历史记录失败: {e}")
        print(f"详细错误堆栈:\n{error_details}")
        st.error(f"保存历史记录失败: {e}")
        return False


def get_history_records(limit=50):
    """
    获取历史记录
    
    参数:
        limit: 返回记录数量限制
    
    返回:
        list: 历史记录列表
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    id, product_name, cost, weight, charge_weight, channel_name,
                    shipping_fee, final_price, profit, margin,
                    datetime(created_at, 'localtime') as created_at
                FROM history
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        st.error(f"加载历史记录失败: {e}")
        return []


def reverse_calculate_cost(final_price_rub, weight_g, exchange_rate, profit_rate, commission_rate, label_fee, tiers=None):
    """
    竞品反推：根据售价反推成本上限
    
    参数:
        final_price_rub: 竞品售价（卢布）
        weight_g: 预估重量（克）
        exchange_rate: 汇率
        profit_rate: 利润率系数
        commission_rate: 佣金率
        label_fee: 贴单费
        tiers: 物流档位
    
    返回:
        dict: {
            'max_cost': 最大成本,
            'shipping_fee': 运费,
            'tier': 使用的档位
        }
    """
    if tiers is None:
        tiers = get_logistics_tiers()
    
    if not tiers:
        return {'max_cost': 0, 'shipping_fee': 0, 'tier': None}
    
    # 转换为人民币
    final_price_cny = final_price_rub / exchange_rate
    
    # 尝试每个档位，找到最合适的
    for tier in tiers:
        # 计算运费
        shipping_fee = tier['fixed_fee'] + label_fee + (weight_g * tier['per_gram_fee'])
        
        # 反推成本：(售价 * (1 - 佣金率) - 运费) / 利润率系数
        commission_factor = 1 - (commission_rate / 100)
        max_cost = (final_price_cny * commission_factor - shipping_fee) / profit_rate
        
        # 检查是否符合该档位限制
        weight_ok = (tier['max_weight'] == 0) or (weight_g <= tier['max_weight'])
        price_ok = (tier['max_price'] == 0) or (final_price_cny <= tier['max_price'])
        
        if weight_ok and price_ok and max_cost > 0:
            return {
                'max_cost': max_cost,
                'shipping_fee': shipping_fee,
                'tier': tier
            }
    
    # 兜底：使用最后一个档位
    last_tier = tiers[-1]
    shipping_fee = last_tier['fixed_fee'] + label_fee + (weight_g * last_tier['per_gram_fee'])
    commission_factor = 1 - (commission_rate / 100)
    max_cost = (final_price_cny * commission_factor - shipping_fee) / profit_rate
    
    return {
        'max_cost': max(max_cost, 0),
        'shipping_fee': shipping_fee,
        'tier': last_tier
    }


def get_current_product(default=None):
    """
    获取当前商品数据（从session_state）
    优先读取 transfer_data（跨页面传输），然后转存到 current_product
    
    参数:
        default: 默认值，如果session中无数据则返回此值
    
    返回:
        dict: 商品数据字典
    """
    if default is None:
        default = {}
    
    # 优先读取 transfer_data（跨页面传输数据）
    transfer_data = st.session_state.get('transfer_data')
    if transfer_data:
        # 转存到 current_product
        st.session_state['current_product'] = transfer_data
        # 清空 transfer_data（防止重复读取）
        del st.session_state['transfer_data']
        return transfer_data
    
    # 如果没有 transfer_data，则读取 current_product
    return st.session_state.get('current_product', default)


def clear_current_product():
    """
    清除当前商品数据并刷新页面
    """
    if 'current_product' in st.session_state:
        del st.session_state['current_product']
    st.rerun()


def load_local_version():
    """
    加载本地配置版本号
    优先从数据库读取，如果不存在则从 version.txt 读取
    
    返回:
        str: 版本号（如 "1.0.0"），如果不存在返回 "0.0.0"
    """
    try:
        # 优先从数据库读取
        version = load_config('config_version', None)
        if version:
            return version
        
        # 尝试从 version.txt 读取（兼容旧版本）
        version_file = os.path.join(os.path.dirname(__file__), "version.txt")
        if os.path.exists(version_file):
            with open(version_file, 'r', encoding='utf-8') as f:
                version = f.read().strip()
                # 迁移到数据库
                save_config('config_version', version)
                return version
        
        return "0.0.0"
    except Exception:
        return "0.0.0"


def save_local_version(version):
    """
    保存本地配置版本号到数据库
    
    参数:
        version: 版本号字符串（如 "1.0.0"）
    
    返回:
        bool: 是否保存成功
    """
    try:
        return save_config('config_version', version)
    except Exception:
        return False


def update_logistics_tiers(tiers_data):
    """
    更新物流档位数据（用于云端配置更新）
    
    参数:
        tiers_data: 物流档位列表
    
    返回:
        bool: 是否更新成功
    """
    return save_logistics_tiers(tiers_data)


def check_remote_config():
    """
    检查并更新云端配置
    
    逻辑：
    1. 从远程URL获取配置JSON
    2. 比较版本号，如果远程版本更新则更新本地配置
    3. 更新物流档位、佣金率等全局参数
    4. 保存新版本号
    
    返回:
        bool: 是否有更新（True表示已更新，False表示无更新或失败）
    """
    try:
        # 获取本地版本
        local_version = load_local_version()
        
        # 请求远程配置（3秒超时）
        response = requests.get(REMOTE_CONFIG_URL, timeout=3)
        
        # 检查响应状态
        if response.status_code != 200:
            return False
        
        # 解析JSON
        remote_config = response.json()
        
        # 获取远程版本号
        remote_version = remote_config.get('version', '0.0.0')
        
        # 比较版本号（简单字符串比较，假设格式为 "x.y.z"）
        if remote_version <= local_version:
            return False
        
        # 版本更新，开始更新配置
        updated = False
        
        # 更新物流档位
        if 'logistics_tiers' in remote_config:
            if update_logistics_tiers(remote_config['logistics_tiers']):
                updated = True
        
        # 更新佣金率
        if 'commission_rate' in remote_config:
            save_config('commission_rate', str(remote_config['commission_rate']))
            updated = True
        
        # 更新汇率
        if 'exchange_rate' in remote_config:
            save_config('exchange_rate', str(remote_config['exchange_rate']))
            updated = True
        
        # 更新贴单费
        if 'label_fee' in remote_config:
            save_config('label_fee', str(remote_config['label_fee']))
            updated = True
        
        # 更新利润率系数
        if 'profit_rate' in remote_config:
            save_config('profit_rate', str(remote_config['profit_rate']))
            updated = True
        
        # 保存新版本号
        if updated:
            save_local_version(remote_version)
            return True
        
        return False
        
    except requests.exceptions.Timeout:
        # 超时，静默失败
        return False
    except requests.exceptions.ConnectionError:
        # 网络连接错误，静默失败
        return False
    except requests.exceptions.RequestException:
        # 其他请求异常，静默失败
        return False
    except json.JSONDecodeError:
        # JSON解析错误，静默失败
        return False
    except Exception:
        # 其他未知异常，静默失败
        return False


# 初始化数据库
init_database()


def export_analysis_image(data_dict):
    """
    将定价分析数据转化为可视化的 PNG 图像
    
    参数:
        data_dict: {
            'product_name': 商品名称,
            'cost': 商品成本(CNY),
            'shipping_fee': 预估运费(CNY),
            'final_price_rub': 建议卢布售价(RUB),
            'profit': 净利润(CNY),
            'margin': 净利润率(%)
        }
    
    返回:
        io.BytesIO: PNG 图像的字节流对象
    """
    from PIL import Image, ImageDraw, ImageFont
    import io
    import os
    
    # 创建画布：800x1000 白色背景
    img = Image.new('RGB', (800, 1000), color='#FFFFFF')
    draw = ImageDraw.Draw(img)
    
    # 加载中文字体（优先使用 Windows 自带的微软雅黑，备用黑体）
    try:
        title_font = ImageFont.truetype("msyh.ttc", 46)  # 标题字体
        text_font = ImageFont.truetype("msyh.ttc", 28)   # 正文字体
        bold_font = ImageFont.truetype("msyhbd.ttc", 36) # 加粗强调字体
        small_font = ImageFont.truetype("msyh.ttc", 20)  # 小字体
    except IOError:
        try:
            title_font = ImageFont.truetype("simhei.ttf", 46)
            text_font = ImageFont.truetype("simhei.ttf", 28)
            bold_font = ImageFont.truetype("simhei.ttf", 36)
            small_font = ImageFont.truetype("simhei.ttf", 20)
        except IOError:
            # 最终降级使用默认字体
            title_font = text_font = bold_font = small_font = ImageFont.load_default()
    
    # 当前绘制位置
    y_position = 50
    
    # 绘制标题：Ozon 选品利润分析（蓝色，居中）
    title_text = "Ozon 选品利润分析"
    try:
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
    except:
        # 兼容旧版本 Pillow
        title_width = len(title_text) * 30
    
    title_x = (800 - title_width) // 2
    draw.text((title_x, y_position), title_text, fill='#005BFF', font=title_font)
    y_position += 90
    
    # 绘制分隔线
    draw.line([(100, y_position), (700, y_position)], fill='#CCCCCC', width=2)
    y_position += 50
    
    # 绘制商品名称
    product_name = data_dict.get('product_name', '未命名商品')
    draw.text((100, y_position), f"商品名称: {product_name}", fill='#333333', font=text_font)
    y_position += 70
    
    # 绘制商品成本
    cost = data_dict.get('cost', 0)
    draw.text((100, y_position), f"商品成本: ¥{cost:.2f}", fill='#333333', font=text_font)
    y_position += 70
    
    # 绘制预估运费
    shipping_fee = data_dict.get('shipping_fee', 0)
    draw.text((100, y_position), f"预估运费: ¥{shipping_fee:.2f}", fill='#333333', font=text_font)
    y_position += 70
    
    # 绘制建议卢布售价（加粗突出）
    final_price_rub = data_dict.get('final_price_rub', 0)
    draw.text((100, y_position), f"建议售价: RUB {int(final_price_rub)}", fill='#F91155', font=bold_font)
    y_position += 90
    
    # 绘制分隔线
    draw.line([(100, y_position), (700, y_position)], fill='#CCCCCC', width=2)
    y_position += 60
    
    # 绘制净利润率（重点突出，根据利润率判断颜色）
    margin = data_dict.get('margin', 0)
    margin_color = '#2E7D32' if margin >= 20 else '#FF9800'
    
    margin_text = f"净利润率: {margin:.2f}%"
    draw.text((100, y_position), margin_text, fill=margin_color, font=bold_font)
    y_position += 80
    
    # 绘制净利润
    profit = data_dict.get('profit', 0)
    draw.text((100, y_position), f"净利润: ¥{profit:.2f}", fill='#333333', font=text_font)
    y_position += 100
    
    # 尝试加载二维码图片
    qrcode_path = os.path.join(os.getcwd(), 'qrcode.png')
    if os.path.exists(qrcode_path):
        try:
            qrcode_img = Image.open(qrcode_path)
            # 缩放为 150x150
            qrcode_img = qrcode_img.resize((150, 150), Image.Resampling.LANCZOS)
            # 粘贴到右下角
            qr_x = 800 - 150 - 40
            qr_y = 1000 - 150 - 40
            img.paste(qrcode_img, (qr_x, qr_y))
            
            # 在二维码左侧绘制文本
            text_y = qr_y + 60
            draw.text((80, text_y), "数据由 Ozon Seller Pro 测算生成", fill='#999999', font=small_font)
        except Exception:
            pass
    else:
        # 如果没有二维码，只显示文本
        text_y = 1000 - 80
        draw.text((80, text_y), "数据由 Ozon Seller Pro 测算生成", fill='#999999', font=small_font)
    
    # 保存到 BytesIO
    output = io.BytesIO()
    img.save(output, format='PNG')
    output.seek(0)
    
    return output


def get_ai_insight(calc_data, api_key):
    """
    调用 DeepSeek AI 获取利润分析和爆款包装建议（防幻觉优化版）
    
    参数:
        calc_data: 计算数据字典，包含成本、运费、售价、利润等信息
        api_key: DeepSeek API Key
    
    返回:
        str: AI 生成的洞察文本，或错误提示信息
    """
    try:
        from openai import OpenAI
        
        # 初始化 DeepSeek 客户端
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        # 【关键】提取商品名称，用于防止 AI 幻觉
        product_name = calc_data.get('product_name', '未命名商品')
        cost = calc_data.get('cost', 0)
        shipping_fee = calc_data.get('shipping_fee', 0)
        final_price = calc_data.get('final_price', 0)
        final_price_rub = calc_data.get('final_price_rub', 0)
        profit = calc_data.get('profit', 0)
        margin = calc_data.get('margin', 0)
        commission_fee = calc_data.get('commission_fee', 0)
        
        # 【优化】构建用户消息，商品名称放在最前面
        user_message = f"""- 商品名称：{product_name}
- 采购成本：¥{cost:.2f}
- 物流运费：¥{shipping_fee:.2f}
- 平台佣金：¥{commission_fee:.2f}
- 建议售价：¥{final_price:.2f} (₽{int(final_price_rub)})
- 预计净利润：¥{profit:.2f}
- 净利润率：{margin:.1f}%
"""
        
        # 【重写】System Prompt - 增强防幻觉指令
        system_prompt = """你是一个拥有10年经验的跨境电商操盘手兼首席UI/UX体验官。请根据提供的SKU测算数据，用大白话给出不超过150字的犀利点评。

【严格要求】：
1. 评价利润率健康度。
2. 给出支撑该售价的视觉包装或营销建议。
3. 【极其重要的防幻觉指令】：如果商品名称是'未命名商品'，说明用户没有输入具体品类。此时请只给出【通用的高级视觉升级策略】（如光影质感提升、排版留白、高级配色），绝对不允许主观臆断或瞎猜商品的具体材质、品类或用途（严禁出现衣服、金属、机器、电器等具体名词）！只有在商品名称明确时，才能针对该真实品类给精准建议。

语气干练，像行业大佬，多使用emoji。"""
        
        # 调用 API
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        # 提取回复内容
        ai_insight = response.choices[0].message.content.strip()
        
        return ai_insight
        
    except ImportError:
        return "❌ 缺少依赖库：请先安装 openai 库（pip install openai）"
    
    except Exception as e:
        error_msg = str(e)
        
        # 友好的错误提示
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            return "❌ API Key 无效或已过期，请检查后重试。新用户可前往 platform.deepseek.com 免费获取。"
        elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
            return "❌ 网络连接超时，请检查网络后重试。"
        elif "rate_limit" in error_msg.lower():
            return "❌ API 调用频率超限，请稍后再试。"
        else:
            return f"❌ AI 调用失败：{error_msg}"


def chat_with_agent(agent_role: str, user_input: str, api_key: str, has_image: bool = False):
    """通用的多 Agent 调度引擎"""
    from openai import OpenAI
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        # 巧妙的视觉降级处理：防止 DeepSeek-chat 报错
        if has_image:
            user_input = f"【系统提示：用户上传了一张产品参考图。请主要基于以下文字描述，为其提供视觉溢价升级方案】\n\n用户描述：{user_input}"
            
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": agent_role},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7,
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Agent 唤醒失败，请检查 API Key 或网络状态。详细错误: {str(e)}"
