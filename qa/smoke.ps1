# smoke.ps1 - 打包后冒烟验收（大厂工序落地，PM 2026-11-27）
# 用途：每次 tauri build 出包后运行，绿灯=允许发版，红灯=拦截，绝不交给人肉排查。
# 用法：powershell -File qa\smoke.ps1 [-Installer <nsis安装包路径>]
# 验收项（对应 2026-11-27 三个真实事故）：
#   1. 引擎从安装目录启动（非临时解包目录）        ← 事故一
#   2. 引擎无控制台窗口、不被控制台事件杀死        ← 事故二（0xC000013A）
#   3. 前端请求到达壳并返回（日志出现 REQ -> RESP）← 事故三（合同裂缝）
param(
    [string]$Installer = "D:\XiangMu\Project\BizSpark\apps\desktop\src-tauri\target\release\bundle\nsis\Buzidea_1.0.0_x64-setup.exe"
)

$ErrorActionPreference = "Stop"
$fail = @()

Write-Host "=== Buzidea 冒烟验收开始 ===" -ForegroundColor Cyan

# ---- 准备：关闭旧实例，静默安装 ----
taskkill /IM bizspark-desktop.exe /F 2>$null
taskkill /IM bizspark-core.exe /F 2>$null
Start-Sleep -Seconds 2

$logPath = "$env:APPDATA\com.buzidea.desktop\logs\engine.log"
$logBefore = if (Test-Path $logPath) { (Get-Content $logPath -Encoding UTF8).Count } else { 0 }

$p = Start-Process $Installer -ArgumentList "/S" -Wait -PassThru
if ($p.ExitCode -ne 0) { $fail += "安装器退出码 $($p.ExitCode)" }

$exeCandidates = @(
    "$env:LOCALAPPDATA\Buzidea\bizspark-desktop.exe",
    "C:\Program Files\Buzidea\bizspark-desktop.exe"
)
$exe = $exeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $exe) { $fail += "安装后找不到 bizspark-desktop.exe"; (Write-Host "=== 红灯：安装失败 ===" -ForegroundColor Red); exit 1 }
Write-Host "[1/5] 静默安装 OK -> $exe"

# ---- 启动 ----
Start-Process $exe
Start-Sleep -Seconds 25

# ---- 验收 1：壳与引擎进程存活 ----
$shell = Get-Process bizspark-desktop -ErrorAction SilentlyContinue
$engine = Get-Process bizspark-core -ErrorAction SilentlyContinue
if (-not $shell) { $fail += "壳进程未存活" }
if (-not $engine) { $fail += "引擎进程未存活" }
Write-Host "[2/5] 进程检查：壳=$([bool]$shell) 引擎=$([bool]$engine)"

# ---- 验收 2：引擎从安装目录启动（非 PyInstaller 临时 _MEI 目录）----
$enginePath = (Get-CimInstance Win32_Process -Filter "name='bizspark-core.exe'" -ErrorAction SilentlyContinue).ExecutablePath
if ($enginePath -and $enginePath -notlike "*$env:TEMP*") {
    Write-Host "[3/5] 引擎路径 OK -> $enginePath"
} else {
    $fail += "引擎从临时目录运行: $enginePath"
    Write-Host "[3/5] 引擎路径异常 -> $enginePath"
}

# ---- 验收 3：日志有 SPAWN OK 且无 EXIT ----
$newLines = if (Test-Path $logPath) { (Get-Content $logPath -Encoding UTF8)[$logBefore..((Get-Content $logPath -Encoding UTF8).Count-1)] } else { @() }
if (-not ($newLines | Where-Object { $_ -match "SPAWN OK" })) { $fail += "日志无 SPAWN OK" }
if ($newLines | Where-Object { $_ -match "EXIT" }) { $fail += "日志出现 EXIT（引擎被杀）" }
Write-Host "[4/5] 日志检查：SPAWN=$([bool]($newLines | Where-Object { $_ -match 'SPAWN OK' })) EXIT出现=$([bool]($newLines | Where-Object { $_ -match 'EXIT' }))"

# ---- 验收 4：链路贯通（REQ -> RESP）----
$reqCount = ($newLines | Where-Object { $_ -match "REQ .* -> RESP" }).Count
if ($reqCount -lt 2) { $fail += "REQ->RESP 不足 2 条（链路未贯通），实际 $reqCount" }
Write-Host "[5/5] 链路检查：REQ->RESP x $reqCount"

# ---- 结论 ----
if ($fail.Count -eq 0) {
    Write-Host "=== 绿灯：冒烟验收全部通过，允许发版 ===" -ForegroundColor Green
    exit 0
} else {
    Write-Host "=== 红灯：冒烟验收未通过 ===" -ForegroundColor Red
    $fail | ForEach-Object { Write-Host "  X $_" -ForegroundColor Red }
    exit 1
}
