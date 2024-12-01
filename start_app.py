import os
import sys
import webbrowser
import uvicorn
import threading
import time
from server import app
import logging
import socket
import ctypes

def is_port_available(port):
    """检查端口是否可用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return True
        except:
            return False

def wait_for_server(port):
    """等待服务器启动"""
    for _ in range(30):  # 最多等待30次
        if not is_port_available(port):  # 如果端口被占用，说明服务器启动了
            return True
        time.sleep(0.5)
    return False

def open_browser(port):
    """打开浏览器"""
    if wait_for_server(port):
        url = f'http://127.0.0.1:{port}'
        webbrowser.open(url)
        print(f"\n 服务已启动! 浏览器已自动打开 {url}")
    else:
        print("\n 服务启动失败或超时")

def setup_console():
    """设置控制台窗口"""
    if sys.platform == 'win32':
        # 设置控制台标题
        ctypes.windll.kernel32.SetConsoleTitleW("Code Viewer Server")
        
        # 如果是打包后的exe，确保显示控制台
        if getattr(sys, 'frozen', False):
            ctypes.windll.user32.ShowWindow(
                ctypes.windll.kernel32.GetConsoleWindow(), 1)

def main():
    # 设置控制台
    setup_console()
    
    print("\n--- 正在初始化程序...")
    
    # 获取资源路径
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        print("--- 正在加载资源文件...")
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # 切换到正确的工作目录
    os.chdir(base_path)
    
    # 配置基本的日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    port = 8000
    
    print("\n--- 正在启动 Code Viewer 服务...")
    print("\n--- 提示: 关闭此窗口将停止服务\n")
    
    # 启动浏览器线程
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    
    try:
        # 使用自定义的日志配置启动服务器
        config = uvicorn.Config(
            app=app,
            host="127.0.0.1",
            port=port,
            log_config=None,  # 禁用默认的日志配置
            access_log=False,  # 禁用访问日志
            log_level="error",  # 只显示错误日志
            workers=1  # 限制worker数量
        )
        server = uvicorn.Server(config)
        server.run()
    except KeyboardInterrupt:
        print("\n--- 服务已停止")
    except Exception as e:
        print(f"\n--- 发生错误: {str(e)}")
        input("\n按回车键退出...")

if __name__ == "__main__":
    main()
