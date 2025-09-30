Write-Host "Activating Python virtual environment..." -ForegroundColor Green
& "venv\Scripts\Activate.ps1"
Write-Host "Virtual environment activated!" -ForegroundColor Green
Write-Host "You can now run: python -m pytest_gui" -ForegroundColor Yellow