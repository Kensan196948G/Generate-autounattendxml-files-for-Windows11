[xml]$xml = Get-Content 'E:\Generate-autounattendxml-files-for-Windows11\WebUI\backend\test_comprehensive_all23.xml'
$ns = @{u="urn:schemas-microsoft-com:unattend"}
$commands = Select-Xml -Xml $xml -XPath "//u:FirstLogonCommands/u:SynchronousCommand" -Namespace $ns

Write-Host "============================================"
Write-Host "XML Analysis Results"
Write-Host "============================================"
Write-Host "Total FirstLogonCommands found: $($commands.Count)"
Write-Host ""

$regCount = 0
$dismCount = 0
$powershellCount = 0
$removeAppCount = 0
$otherCount = 0

foreach ($cmd in $commands) {
    $commandLine = $cmd.Node.CommandLine
    if ($commandLine -like "*reg add*") { $regCount++ }
    elseif ($commandLine -like "*dism*") { $dismCount++ }
    elseif ($commandLine -like "*powershell*" -and $commandLine -like "*Remove-AppxPackage*") { $removeAppCount++ }
    elseif ($commandLine -like "*powershell*") { $powershellCount++ }
    else { $otherCount++ }
}

Write-Host "Command breakdown:"
Write-Host "  Registry commands: $regCount"
Write-Host "  DISM commands: $dismCount"
Write-Host "  App removal commands: $removeAppCount"
Write-Host "  Other PowerShell commands: $powershellCount"
Write-Host "  Other commands: $otherCount"
Write-Host ""

# Check for specific new implementations (items 12-22)
Write-Host "Checking for new implementations (items 12-22):"
$visualEffectsFound = $false
$desktopSettingsFound = $false
$expressSettingsFound = $false
$stickyKeysFound = $false
$personalizationFound = $false
$customScriptsFound = $false
$wdacFound = $false

foreach ($cmd in $commands) {
    $commandLine = $cmd.Node.CommandLine
    if ($commandLine -like "*VisualEffects*") { $visualEffectsFound = $true }
    if ($commandLine -like "*Desktop\NewStartPanel*") { $desktopSettingsFound = $true }
    if ($commandLine -like "*AdvertisingInfo*" -or $commandLine -like "*Privacy*") { $expressSettingsFound = $true }
    if ($commandLine -like "*StickyKeys*") { $stickyKeysFound = $true }
    if ($commandLine -like "*Personalization*" -or $commandLine -like "*Themes*") { $personalizationFound = $true }
    if ($commandLine -like "*Test Script*") { $customScriptsFound = $true }
    if ($commandLine -like "*WDAC*" -or $commandLine -like "*DeviceGuard*") { $wdacFound = $true }
}

$checkMark = [char]0x2713
$crossMark = [char]0x2717

Write-Host "  $(if($visualEffectsFound){$checkMark}else{$crossMark}) Visual Effects (Item 12)"
Write-Host "  $(if($desktopSettingsFound){$checkMark}else{$crossMark}) Desktop Settings (Item 13)"
Write-Host "  $(if($expressSettingsFound){$checkMark}else{$crossMark}) Express Settings (Item 16)"
Write-Host "  $(if($stickyKeysFound){$checkMark}else{$crossMark}) Sticky Keys (Item 18)"
Write-Host "  $(if($personalizationFound){$checkMark}else{$crossMark}) Personalization (Item 19)"
Write-Host "  $(if($customScriptsFound){$checkMark}else{$crossMark}) Custom Scripts (Item 21)"
Write-Host "  $(if($wdacFound){$checkMark}else{$crossMark}) WDAC (Item 22)"

Write-Host ""
Write-Host "First 15 commands:"
$count = 0
foreach ($cmd in $commands) {
    $count++
    if ($count -gt 15) { break }
    $commandLine = $cmd.Node.CommandLine
    if ($commandLine.Length -gt 100) {
        $commandLine = $commandLine.Substring(0, 97) + "..."
    }
    Write-Host "${count}. $commandLine"
}