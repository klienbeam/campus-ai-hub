# 设置控制台编码为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 获取脚本所在目录
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $scriptPath

Write-Host "当前目录: $(Get-Location)" -ForegroundColor Green

# 执行第一个命令：创建迁移文件
Write-Host "`n=== 执行: python manage.py makemigrations ===" -ForegroundColor Yellow
python manage.py makemigrations
if ($LASTEXITCODE -ne 0) {
    Write-Host "makemigrations 执行失败，退出码: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

# 执行第二个命令：执行迁移
Write-Host "`n=== 执行: python manage.py migrate ===" -ForegroundColor Yellow
python manage.py migrate
if ($LASTEXITCODE -ne 0) {
    Write-Host "migrate 执行失败，退出码: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

# 执行第三个命令：启动服务器
Write-Host "`n=== 执行: python manage.py runserver ===" -ForegroundColor Yellow
Write-Host "服务器启动中，按 Ctrl+C 停止..." -ForegroundColor Green
python manage.py runserver


