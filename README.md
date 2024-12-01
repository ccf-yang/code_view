# 执行方式1：开发模式
```
python server.py
访问 http://127.0.0.1:8000
```

# 执行方式2：独立应用模式
提前打包：pip install pyinstaller   
         pyinstaller code_viewer.spec --clean
- 以后简单的前后端项目，比如fastapi+html+js，可以都用这个方式快速打包成应用。

1. 在 `dist` 目录找到 `Code Viewer.exe`
2. 双击运行，应用会自动：
   - 启动后端服务
   - 打开浏览器访问界面
3. 关闭窗口时会自动清理后端进程

# 特点
- 无需安装 Python 或其他依赖
- 一键启动，自动打开浏览器
- 优雅关闭，自动清理进程
- 支持创建桌面快捷方式