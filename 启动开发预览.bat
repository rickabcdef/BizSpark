@echo off
chcp 65001 >nul
title BizSpark 开发预览（改代码即时生效）
cd /d "%~dp0qa"

rem 端口已开 = 服务在跑，直接开浏览器，不再起第二个
powershell -NoProfile -Command "try{$c=New-Object Net.Sockets.TcpClient;$c.Connect('127.0.0.1',5180);$c.Close();exit 0}catch{exit 1}" >nul 2>&1
if %errorlevel%==0 (
  echo 服务已在运行，直接打开 http://127.0.0.1:5180
  start "" http://127.0.0.1:5180
  timeout /t 2 >nul
  exit /b
)

echo.
echo   BizSpark 开发预览启动中（中文版）…
echo   网址：http://127.0.0.1:5180
echo.
echo   改前端 -> 页面热更新；改引擎 -> 自动重启并刷新页面
echo   关闭本窗口 = 停止服务
echo.
start "" http://127.0.0.1:5180
node dev.mjs zh 5180
pause
