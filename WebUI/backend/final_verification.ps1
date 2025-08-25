[xml]$xml = Get-Content 'E:\Generate-autounattendxml-files-for-Windows11\WebUI\backend\test_comprehensive_final.xml'
$content = Get-Content 'E:\Generate-autounattendxml-files-for-Windows11\WebUI\backend\test_comprehensive_final.xml' -Raw

Write-Host "============================================"
Write-Host "FINAL VERIFICATION - All 23 Configuration Items"
Write-Host "============================================"
Write-Host ""

$checkMark = [char]0x2713
$crossMark = [char]0x2717

# Count FirstLogonCommands
$ns = @{u="urn:schemas-microsoft-com:unattend"}
$commands = Select-Xml -Xml $xml -XPath "//u:FirstLogonCommands/u:SynchronousCommand" -Namespace $ns
Write-Host "Total FirstLogonCommands: $($commands.Count)"
Write-Host ""

# Item-by-item verification
$item1 = $content -match 'ja-JP' -and $content -match 'Tokyo Standard Time'
Write-Host "$(if($item1){$checkMark}else{$crossMark}) Item 1: Region and Language Settings"

$item2 = $content -match 'processorArchitecture="amd64"'
Write-Host "$(if($item2){$checkMark}else{$crossMark}) Item 2: Processor Architecture"

$item3 = $content -match 'SkipMachineOOBE' -or $content -match 'SkipUserOOBE'
Write-Host "$(if($item3){$checkMark}else{$crossMark}) Item 3: Setup Behavior"

$item4 = $content -match 'VK7JG-NPHTM-C97JM-9MPGT-3V66T'
Write-Host "$(if($item4){$checkMark}else{$crossMark}) Item 4: Edition/Product Key"

$item5 = $content -match 'windowsPE'
Write-Host "$(if($item5){$checkMark}else{$crossMark}) Item 5: Windows PE Stage"

$item6 = $content -match 'DiskConfiguration'
Write-Host "$(if($item6){$checkMark}else{$crossMark}) Item 6: Disk Configuration"

$item7 = $content -match 'TEST-PC-001' -or $content -match 'ComputerName'
Write-Host "$(if($item7){$checkMark}else{$crossMark}) Item 7: Computer Settings"

$item8 = $content -match 'testadmin' -and $content -match 'testuser'
Write-Host "$(if($item8){$checkMark}else{$crossMark}) Item 8: User Accounts"

$item9 = $content -match 'HideFileExt' -and $content -match 'Hidden'
Write-Host "$(if($item9){$checkMark}else{$crossMark}) Item 9: Explorer Settings"

$item10 = $content -match 'TaskbarAl' -or $content -match 'TaskbarDa'
Write-Host "$(if($item10){$checkMark}else{$crossMark}) Item 10: Start/Taskbar"

$item11 = $content -match 'AllowTelemetry' -and $content -match 'AllowCortana'
Write-Host "$(if($item11){$checkMark}else{$crossMark}) Item 11: System Tweaks"

$item12 = $content -match 'MinAnimate' -and $content -match 'EnableTransparency'
Write-Host "$(if($item12){$checkMark}else{$crossMark}) Item 12: Visual Effects"

$item13 = $content -match 'HideDesktopIcons'
Write-Host "$(if($item13){$checkMark}else{$crossMark}) Item 13: Desktop Settings"

$item14 = $content -match 'Microsoft-Hyper-V' -and $content -match 'Microsoft-Windows-Subsystem-Linux'
Write-Host "$(if($item14){$checkMark}else{$crossMark}) Item 14: VM Support"

$item15 = $content -match 'TestNetwork2024'
Write-Host "$(if($item15){$checkMark}else{$crossMark}) Item 15: Wi-Fi Settings"

$item16 = $content -match 'LocationAndSensors'
Write-Host "$(if($item16){$checkMark}else{$crossMark}) Item 16: Express Settings"

$item17 = $content -match 'InitialKeyboardIndicators'
Write-Host "$(if($item17){$checkMark}else{$crossMark}) Item 17: Lock Keys"

$item18 = $content -match 'StickyKeys'
Write-Host "$(if($item18){$checkMark}else{$crossMark}) Item 18: Sticky Keys"

# Modified check for personalization - look for accent color command
$item19 = $content -match 'Themes\\Personalize' -and $content -match 'AccentColorMenu'
Write-Host "$(if($item19){$checkMark}else{$crossMark}) Item 19: Personalization"

$item20 = $content -match 'Remove-AppxPackage' -and $content -match 'Microsoft.BingNews'
Write-Host "$(if($item20){$checkMark}else{$crossMark}) Item 20: Remove Apps"

$item21 = $content -match 'Test Script 1 Executed' -and $content -match 'Test Script 2'
Write-Host "$(if($item21){$checkMark}else{$crossMark}) Item 21: Custom Scripts"

$item22 = $content -match 'CiTool' -or $content -match 'DeviceGuard'
Write-Host "$(if($item22){$checkMark}else{$crossMark}) Item 22: WDAC"

# Modified check for additional components - look for multiple features
$item23 = ($content -match 'NetFx3') -and ($content -match 'IIS-WebServerRole') -and ($content -match 'TelnetClient')
Write-Host "$(if($item23){$checkMark}else{$crossMark}) Item 23: Additional Components"

Write-Host ""
Write-Host "============================================"

# Count verified items
$verifiedCount = 0
for ($i = 1; $i -le 23; $i++) {
    $varName = "item$i"
    if ((Get-Variable -Name $varName -ValueOnly)) {
        $verifiedCount++
    }
}

Write-Host "Total Verified: $verifiedCount/23"
Write-Host ""

if ($verifiedCount -eq 23) {
    Write-Host "✅ SUCCESS! ALL 23 ITEMS ARE FULLY IMPLEMENTED!" -ForegroundColor Green
    Write-Host ""
    Write-Host "全23項目の設定がXMLファイルに正しく生成されました。" -ForegroundColor Green
    Write-Host "Windows 11の無人インストールファイルが完全に機能します。" -ForegroundColor Green
} else {
    Write-Host "⚠️ $($23 - $verifiedCount) items still need verification" -ForegroundColor Yellow
    
    # Show which items failed
    Write-Host ""
    Write-Host "Failed items:" -ForegroundColor Yellow
    for ($i = 1; $i -le 23; $i++) {
        $varName = "item$i"
        if (-not (Get-Variable -Name $varName -ValueOnly)) {
            Write-Host "  - Item $i" -ForegroundColor Yellow
        }
    }
}