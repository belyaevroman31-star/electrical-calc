# Установка запуска проверки цен каждые 3 дня через Планировщик задач Windows
# Запуск от имени администратора

$scriptPath = "D:\сайт\калькулятор материалов\check_prices.py"
$pythonPath = "python"
$taskName = "ElectroCalc_PriceCheck"

# Удаляем старую задачу если есть
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Создаём действие
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$scriptPath`" --apply" -WorkingDirectory "D:\сайт\калькулятор материалов"

# Триггер: каждые 3 дня
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date -RepetitionInterval (New-TimeSpan -Days 3) -RepetitionDuration (New-TimeSpan -Days 3650)

# Настройки
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Регистрируем задачу
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Проверка цен el.ru для калькулятора электромонтажа (каждые 3 дня)" -Force

Write-Host "Задача '$taskName' создана successfully!"
Write-Host "  - Запуск: каждые 3 дня"
Write-Host "  - Режим: --apply (автообновление)"
Write-Host "  - Лог: D:\сайт\калькулятор материалов\price_check_log.txt"
