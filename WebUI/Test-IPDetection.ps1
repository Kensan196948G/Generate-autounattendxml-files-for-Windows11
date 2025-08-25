# IP検出テストスクリプト
# 使用方法: .\Test-IPDetection.ps1

Write-Host "IPアドレス検出テスト" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
Write-Host ""

# IPアドレスの取得関数（Start-WebUI.ps1と同じロジック）
function Get-LocalIPAddress {
    # 日本語Windows環境対応 - 有効なネットワークアダプターのIPアドレスを取得
    
    # 方法1: InterfaceAliasで「イーサネット」を優先的に検索
    $ethernetIP = Get-NetIPAddress -AddressFamily IPv4 | 
        Where-Object { 
            ($_.InterfaceAlias -eq 'イーサネット' -or 
             $_.InterfaceAlias -eq 'Ethernet' -or
             $_.InterfaceAlias -like 'イーサネット*' -or
             $_.InterfaceAlias -like 'Ethernet*') -and
            $_.IPAddress -ne '127.0.0.1' -and 
            -not ($_.IPAddress -like '169.254.*') -and
            $_.PrefixOrigin -eq 'Dhcp'
        } |
        Select-Object -First 1
    
    if ($ethernetIP) {
        Write-Host "✓ イーサネット接続を検出" -ForegroundColor Green
        return $ethernetIP.IPAddress
    }
    
    # 方法2: Wi-Fi接続を検索
    $wifiIP = Get-NetIPAddress -AddressFamily IPv4 | 
        Where-Object { 
            ($_.InterfaceAlias -like '*Wi-Fi*' -or 
             $_.InterfaceAlias -like '*WiFi*' -or
             $_.InterfaceAlias -like '*無線*') -and
            $_.IPAddress -ne '127.0.0.1' -and 
            -not ($_.IPAddress -like '169.254.*')
        } |
        Select-Object -First 1
    
    if ($wifiIP) {
        Write-Host "✓ Wi-Fi接続を検出" -ForegroundColor Green
        return $wifiIP.IPAddress
    }
    
    # 方法3: 192.168.x.x のプライベートアドレスを探す
    $privateIP = Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { 
            $_.IPAddress -like '192.168.*' -or
            $_.IPAddress -like '10.*' -or
            $_.IPAddress -like '172.16.*'
        } |
        Select-Object -First 1
    
    if ($privateIP) {
        Write-Host "✓ プライベートIPアドレスを検出" -ForegroundColor Green
        return $privateIP.IPAddress
    }
    
    Write-Host "× 有効なIPアドレスが見つかりません" -ForegroundColor Red
    return "127.0.0.1"
}

# すべてのネットワークアダプター情報を表示
Write-Host "検出されたネットワークアダプター:" -ForegroundColor Yellow
Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | ForEach-Object {
    Write-Host "  - $($_.Name): $($_.InterfaceDescription)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "IPv4アドレス一覧:" -ForegroundColor Yellow
Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -ne '127.0.0.1' } | ForEach-Object {
    $prefix = if ($_.PrefixOrigin -eq 'Dhcp') { "[DHCP]" } else { "[$($_.PrefixOrigin)]" }
    $apipa = if ($_.IPAddress -like '169.254.*') { " (APIPA - 無効)" } else { "" }
    Write-Host "  - $($_.InterfaceAlias): $($_.IPAddress) $prefix$apipa" -ForegroundColor Gray
}

Write-Host ""
Write-Host "検出結果:" -ForegroundColor Yellow
$detectedIP = Get-LocalIPAddress
Write-Host ""
Write-Host "検出されたIPアドレス: " -NoNewline
Write-Host $detectedIP -ForegroundColor Cyan -BackgroundColor DarkBlue
Write-Host ""

Write-Host "アクセスURL:" -ForegroundColor Yellow
Write-Host "  フロントエンド: http://${detectedIP}:3050" -ForegroundColor White
Write-Host "  バックエンド:   http://${detectedIP}:8080" -ForegroundColor White
Write-Host "  API仕様書:     http://${detectedIP}:8080/api/docs" -ForegroundColor White
Write-Host ""

# 期待値の確認
if ($detectedIP -eq "192.168.3.92") {
    Write-Host "✓ 正しいIPアドレスが検出されました！" -ForegroundColor Green
} elseif ($detectedIP -like "192.168.*") {
    Write-Host "○ プライベートIPアドレスが検出されました" -ForegroundColor Yellow
} else {
    Write-Host "× 期待されるIPアドレス (192.168.3.92) とは異なります" -ForegroundColor Red
    Write-Host "  検出されたIP: $detectedIP" -ForegroundColor Red
}