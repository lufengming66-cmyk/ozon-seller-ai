# -*- coding: utf-8 -*-
"""
Ozon Seller Pro - 启动代理
解决 PyInstaller 打包后的路径问题 + 自动打开浏览器
"""
import streamlit.web.cli as stcli
import os
import sys
import webbrowser
import time
import threading
import logging
import traceback

def resolve_path(path):
    """解析资源文件路径（兼容打包后的环境）"""
    if getattr(sys, "frozen", False):
        # 打包后的环境
        basedir = sys._MEIPASS
    else:
        # 开发环境
        basedir = os.path.dirname(__file__)
    return os.path.join(basedir, path)

def open_browser():
    """延迟打开浏览器"""
    time.sleep(3)  # 等待 Streamlit 服务器启动
    webbrowser.open('http://localhost:8501')

if __name__ == "__main__":
    # 配置日志记录（将错误信息输出到当前目录下的 app_runtime.log）
    logging.basicConfig(
        filename='app_runtime.log',
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        # 设置 Streamlit 无头模式
        os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
        
        # 解析 app.py 路径
        app_path = resolve_path("app.py")
        
        # 构建 Streamlit 启动参数
        sys.argv = [
            "streamlit",
            "run",
            app_path,
            "--global.developmentMode=false",
            "--server.port=8501",
            "--server.headless=true"
        ]
        
        # 在后台线程中打开浏览器
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # 启动 Streamlit
        sys.exit(stcli.main())
        
    except Exception as e:
        # 记录异常信息到日志文件
        logging.error("运行异常:\n%s", traceback.format_exc())
        sys.exit(1)

