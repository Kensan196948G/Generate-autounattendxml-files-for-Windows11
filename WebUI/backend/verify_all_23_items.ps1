[xml]$xml = Get-Content 'E:\Generate-autounattendxml-files-for-Windows11\WebUI\backend\test_comprehensive_all23.xml'
$content = Get-Content 'E:\Generate-autounattendxml-files-for-Windows11\WebUI\backend\test_comprehensive_all23.xml' -Raw

Write-Host "============================================"
Write-Host "Verification of All 23 Configuration Items"
Write-Host "============================================"
Write-Host ""

$checkMark = [char]0x2713
$crossMark = [char]0x2717

# Item 1: Region and Language
$item1 = $content -match 'ja-JP' -and $content -match 'Tokyo Standard Time'
Write-Host "$(if($item1){$checkMark}else{$crossMark}) Item 1: Region and Language Settings"

# Item 2: Architecture
$item2 = $content -match 'processorArchitecture="amd64"'
Write-Host "$(if($item2){$checkMark}else{$crossMark}) Item 2: Processor Architecture"

# Item 3: Setup Behavior
$item3 = $content -match 'SkipMachineOOBE' -or $content -match 'SkipUserOOBE'
Write-Host "$(if($item3){$checkMark}else{$crossMark}) Item 3: Setup Behavior"

# Item 4: Edition/Product Key
$item4 = $content -match 'VK7JG-NPHTM-C97JM-9MPGT-3V66T'
Write-Host "$(if($item4){$checkMark}else{$crossMark}) Item 4: Edition/Product Key"

# Item 5: Windows PE Stage
$item5 = $content -match 'windowsPE'
Write-Host "$(if($item5){$checkMark}else{$crossMark}) Item 5: Windows PE Stage"

# Item 6: Disk Configuration
$item6 = $content -match 'DiskConfiguration'
Write-Host "$(if($item6){$checkMark}else{$crossMark}) Item 6: Disk Configuration"

# Item 7: Computer Settings
$item7 = $content -match 'TEST-PC-001' -or $content -match 'ComputerName'
Write-Host "$(if($item7){$checkMark}else{$crossMark}) Item 7: Computer Settings"

# Item 8: User Accounts
$item8 = $content -match 'testadmin' -and $content -match 'testuser'
Write-Host "$(if($item8){$checkMark}else{$crossMark}) Item 8: User Accounts"

# Item 9: Explorer Settings
$item9 = $content -match 'HideFileExt' -and $content -match 'Hidden'
Write-Host "$(if($item9){$checkMark}else{$crossMark}) Item 9: Explorer Settings"

# Item 10: Start/Taskbar
$item10 = $content -match 'TaskbarAl' -or $content -match 'TaskbarDa'
Write-Host "$(if($item10){$checkMark}else{$crossMark}) Item 10: Start/Taskbar"

# Item 11: System Tweaks
$item11 = $content -match 'AllowTelemetry' -and $content -match 'AllowCortana'
Write-Host "$(if($item11){$checkMark}else{$crossMark}) Item 11: System Tweaks"

# Item 12: Visual Effects (NEW)
$item12 = $content -match 'MinAnimate' -and $content -match 'EnableTransparency'
Write-Host "$(if($item12){$checkMark}else{$crossMark}) Item 12: Visual Effects (NEW)"

# Item 13: Desktop Settings (NEW)
$item13 = $content -match 'HideDesktopIcons'
Write-Host "$(if($item13){$checkMark}else{$crossMark}) Item 13: Desktop Settings (NEW)"

# Item 14: VM Support
$item14 = $content -match 'Microsoft-Hyper-V' -and $content -match 'Microsoft-Windows-Subsystem-Linux'
Write-Host "$(if($item14){$checkMark}else{$crossMark}) Item 14: VM Support"

# Item 15: Wi-Fi Settings
$item15 = $content -match 'TestNetwork2024'
Write-Host "$(if($item15){$checkMark}else{$crossMark}) Item 15: Wi-Fi Settings"

# Item 16: Express Settings (NEW)
$item16 = $content -match 'LocationAndSensors'
Write-Host "$(if($item16){$checkMark}else{$crossMark}) Item 16: Express Settings (NEW)"

# Item 17: Lock Keys
$item17 = $content -match 'InitialKeyboardIndicators'
Write-Host "$(if($item17){$checkMark}else{$crossMark}) Item 17: Lock Keys"

# Item 18: Sticky Keys (NEW)
$item18 = $content -match 'StickyKeys'
Write-Host "$(if($item18){$checkMark}else{$crossMark}) Item 18: Sticky Keys (NEW)"

# Item 19: Personalization (NEW)
$item19 = $content -match 'Themes\\Personalize' -and $content -match 'FF0078D4'
Write-Host "$(if($item19){$checkMark}else{$crossMark}) Item 19: Personalization (NEW)"

# Item 20: Remove Apps
$item20 = $content -match 'Remove-AppxPackage' -and $content -match 'Microsoft.BingNews'
Write-Host "$(if($item20){$checkMark}else{$crossMark}) Item 20: Remove Apps"

# Item 21: Custom Scripts (NEW)
$item21 = $content -match 'Test Script 1 Executed' -and $content -match 'Test Script 2'
Write-Host "$(if($item21){$checkMark}else{$crossMark}) Item 21: Custom Scripts (NEW)"

# Item 22: WDAC (NEW)
$item22 = $content -match 'CiTool' -or $content -match 'DeviceGuard'
Write-Host "$(if($item22){$checkMark}else{$crossMark}) Item 22: WDAC (NEW)"

# Item 23: Additional Components
$item23 = $content -match 'NetFx3' -and $content -match 'IIS-WebServerRole'
Write-Host "$(if($item23){$checkMark}else{$crossMark}) Item 23: Additional Components"

Write-Host ""
Write-Host "============================================"

# Count verified items
$verifiedCount = 0
if($item1) { $verifiedCount++ }
if($item2) { $verifiedCount++ }
if($item3) { $verifiedCount++ }
if($item4) { $verifiedCount++ }
if($item5) { $verifiedCount++ }
if($item6) { $verifiedCount++ }
if($item7) { $verifiedCount++ }
if($item8) { $verifiedCount++ }
if($item9) { $verifiedCount++ }
if($item10) { $verifiedCount++ }
if($item11) { $verifiedCount++ }
if($item12) { $verifiedCount++ }
if($item13) { $verifiedCount++ }
if($item14) { $verifiedCount++ }
if($item15) { $verifiedCount++ }
if($item16) { $verifiedCount++ }
if($item17) { $verifiedCount++ }
if($item18) { $verifiedCount++ }
if($item19) { $verifiedCount++ }
if($item20) { $verifiedCount++ }
if($item21) { $verifiedCount++ }
if($item22) { $verifiedCount++ }
if($item23) { $verifiedCount++ }

Write-Host "Total Verified: $verifiedCount/23"
Write-Host ""

if ($verifiedCount -eq 23) {
    Write-Host "✅ ALL 23 ITEMS ARE SUCCESSFULLY IMPLEMENTED!" -ForegroundColor Green
} else {
    Write-Host "⚠️ Some items need verification or fixing" -ForegroundColor Yellow
}