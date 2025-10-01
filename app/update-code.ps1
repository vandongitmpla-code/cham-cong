# update-code.ps1
Write-Host "=== Đang cập nhật code từ GitHub... ==="

# Di chuyển tới thư mục project
Set-Location "F:\cham-cong"

# Chạy git pull
git pull

Write-Host "=== Cập nhật hoàn tất! ==="
pause
