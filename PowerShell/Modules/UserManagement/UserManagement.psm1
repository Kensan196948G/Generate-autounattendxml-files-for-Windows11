#Requires -Version 5.0

<#
.SYNOPSIS
    Windows 11 UnattendXML ユーザー管理モジュール

.DESCRIPTION
    Sysprep応答ファイルでのユーザーアカウント設定を管理するPowerShellモジュール
    - mirai-user、l-admin アカウントの作成
    - Administrator アカウントの無効化
    - パスワードの暗号化処理
    - ユーザーグループ設定

.VERSION
    1.0.0

.AUTHOR
    Windows 11 Sysprep Automation Team

.COPYRIGHT
    Copyright (c) 2025. All rights reserved.
#>

# .NET Framework アセンブリの読み込み
Add-Type -AssemblyName System.Security
Add-Type -AssemblyName System.Xml

# ユーザーアカウント情報クラス
class UserAccount {
    [string]$Name
    [securestring]$Password
    [string]$DisplayName
    [string]$Description
    [string[]]$Groups
    [bool]$IsEnabled
    [bool]$IsBuiltIn
    [bool]$PasswordNeverExpires
    [bool]$UserMayNotChangePassword
    [string]$PasswordHint
    
    # 標準ユーザー用コンストラクタ
    UserAccount([string]$name, [securestring]$password) {
        $this.Name = $name
        $this.Password = $password
        $this.DisplayName = $name
        $this.Description = ""
        $this.Groups = @("Users")
        $this.IsEnabled = $true
        $this.IsBuiltIn = $false
        $this.PasswordNeverExpires = $false
        $this.UserMayNotChangePassword = $false
        $this.PasswordHint = ""
    }
    
    # 組み込みアカウント用コンストラクタ
    UserAccount([string]$name, [bool]$isEnabled) {
        $this.Name = $name
        $this.IsEnabled = $isEnabled
        $this.IsBuiltIn = $true
        $this.Groups = @()
    }
    
    # パスワードを平文で取得（XML生成用）
    [string] GetPlainTextPassword() {
        if ($this.Password -eq $null) {
            return ""
        }
        
        try {
            $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($this.Password)
            return [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
        }
        catch {
            Write-Warning "パスワードの復号化に失敗しました: $_"
            return ""
        }
        finally {
            if ($BSTR -ne [IntPtr]::Zero) {
                [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
            }
        }
    }
}

# ユーザー管理設定クラス
class UserManagementConfig {
    [UserAccount[]]$Users
    [hashtable]$DomainSettings
    [bool]$EnableAutologon
    [string]$AutologonUser
    [int]$AutologonCount
    
    # コンストラクタ
    UserManagementConfig() {
        $this.Users = @()
        $this.DomainSettings = @{
            JoinDomain = $false
            DomainName = ""
            DomainUser = ""
            DomainPassword = $null
            MachineObjectOU = ""
        }
        $this.EnableAutologon = $false
        $this.AutologonUser = ""
        $this.AutologonCount = 1
    }
    
    # ユーザー追加
    [void] AddUser([UserAccount]$user) {
        $this.Users += $user
    }
    
    # デフォルトユーザー設定
    [void] SetupDefaultUsers() {
        # Administrator を無効化
        $admin = [UserAccount]::new("Administrator", $false)
        $this.AddUser($admin)
        
        # mirai-user を作成
        $miraiPassword = ConvertTo-SecureString "MiraiUser2025!" -AsPlainText -Force
        $miraiUser = [UserAccount]::new("mirai-user", $miraiPassword)
        $miraiUser.DisplayName = "Mirai User"
        $miraiUser.Description = "システム管理用アカウント"
        $miraiUser.Groups = @("Administrators", "Users")
        $miraiUser.PasswordNeverExpires = $true
        $this.AddUser($miraiUser)
        
        # l-admin を作成
        $ladminPassword = ConvertTo-SecureString "LAdmin2025!" -AsPlainText -Force
        $ladminUser = [UserAccount]::new("l-admin", $ladminPassword)
        $ladminUser.DisplayName = "Local Administrator"
        $ladminUser.Description = "ローカル管理者アカウント"
        $ladminUser.Groups = @("Administrators", "Users")
        $ladminUser.PasswordNeverExpires = $true
        $this.AddUser($ladminUser)
    }
}

# XMLユーザー設定生成クラス
class UnattendUserXMLGenerator {
    [System.Xml.XmlDocument]$XmlDocument
    [UserManagementConfig]$Config
    [System.Xml.XmlNamespaceManager]$NamespaceManager
    
    # コンストラクタ
    UnattendUserXMLGenerator([System.Xml.XmlDocument]$xmlDoc, [UserManagementConfig]$config) {
        $this.XmlDocument = $xmlDoc
        $this.Config = $config
        $this.NamespaceManager = New-Object System.Xml.XmlNamespaceManager($xmlDoc.NameTable)
        $this.NamespaceManager.AddNamespace("un", "urn:schemas-microsoft-com:unattend")
    }
    
    # ユーザーアカウント設定のXML生成
    [System.Xml.XmlElement] GenerateUserAccountsXML() {
        Write-Verbose "ユーザーアカウント設定XML生成開始"
        
        # settings要素の取得または作成
        $unattendRoot = $this.XmlDocument.DocumentElement
        $settingsElement = $this.GetOrCreateSettingsElement($unattendRoot, "oobeSystem")
        
        # Microsoft-Windows-Shell-Setup コンポーネント
        $shellSetupComponent = $this.GetOrCreateComponent($settingsElement, "Microsoft-Windows-Shell-Setup")
        
        # UserAccounts要素
        $userAccountsElement = $this.XmlDocument.CreateElement("UserAccounts", $unattendRoot.NamespaceURI)
        $shellSetupComponent.AppendChild($userAccountsElement) | Out-Null
        
        # LocalAccounts要素
        $localAccountsElement = $this.XmlDocument.CreateElement("LocalAccounts", $unattendRoot.NamespaceURI)
        $userAccountsElement.AppendChild($localAccountsElement) | Out-Null
        
        # AdministratorPassword要素
        $adminPasswordElement = $this.XmlDocument.CreateElement("AdministratorPassword", $unattendRoot.NamespaceURI)
        $userAccountsElement.AppendChild($adminPasswordElement) | Out-Null
        
        # 各ユーザーアカウント処理
        foreach ($user in $this.Config.Users) {
            if ($user.IsBuiltIn) {
                $this.AddBuiltInUserConfig($userAccountsElement, $user)
            } else {
                $this.AddLocalUserAccount($localAccountsElement, $user)
            }
        }
        
        Write-Verbose "ユーザーアカウント設定XML生成完了"
        return $settingsElement
    }
    
    # Settings要素の取得または作成
    [System.Xml.XmlElement] GetOrCreateSettingsElement([System.Xml.XmlElement]$parent, [string]$pass) {
        $xpath = "un:settings[@pass='$pass']"
        $settingsElement = $parent.SelectSingleNode($xpath, $this.NamespaceManager)
        
        if ($settingsElement -eq $null) {
            $settingsElement = $this.XmlDocument.CreateElement("settings", $parent.NamespaceURI)
            $settingsElement.SetAttribute("pass", $pass)
            $parent.AppendChild($settingsElement) | Out-Null
        }
        
        return $settingsElement
    }
    
    # Component要素の取得または作成
    [System.Xml.XmlElement] GetOrCreateComponent([System.Xml.XmlElement]$parent, [string]$name) {
        $xpath = "un:component[@name='$name']"
        $componentElement = $parent.SelectSingleNode($xpath, $this.NamespaceManager)
        
        if ($componentElement -eq $null) {
            $componentElement = $this.XmlDocument.CreateElement("component", $parent.NamespaceURI)
            $componentElement.SetAttribute("name", $name)
            $componentElement.SetAttribute("processorArchitecture", "amd64")
            $componentElement.SetAttribute("publicKeyToken", "31bf3856ad364e35")
            $componentElement.SetAttribute("language", "neutral")
            $componentElement.SetAttribute("versionScope", "nonSxS")
            $componentElement.SetAttribute("xmlns:wcm", "http://schemas.microsoft.com/WMIConfig/2002/State")
            $componentElement.SetAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
            $parent.AppendChild($componentElement) | Out-Null
        }
        
        return $componentElement
    }
    
    # ローカルユーザーアカウント追加
    [void] AddLocalUserAccount([System.Xml.XmlElement]$parent, [UserAccount]$user) {
        Write-Verbose "ローカルユーザー追加: $($user.Name)"
        
        # LocalAccount要素
        $localAccountElement = $this.XmlDocument.CreateElement("LocalAccount", $parent.NamespaceURI)
        $localAccountElement.SetAttribute("action", "add", "http://schemas.microsoft.com/WMIConfig/2002/State")
        $parent.AppendChild($localAccountElement) | Out-Null
        
        # Name要素
        $nameElement = $this.XmlDocument.CreateElement("Name", $parent.NamespaceURI)
        $nameElement.InnerText = $user.Name
        $localAccountElement.AppendChild($nameElement) | Out-Null
        
        # DisplayName要素
        if (![string]::IsNullOrWhiteSpace($user.DisplayName)) {
            $displayNameElement = $this.XmlDocument.CreateElement("DisplayName", $parent.NamespaceURI)
            $displayNameElement.InnerText = $user.DisplayName
            $localAccountElement.AppendChild($displayNameElement) | Out-Null
        }
        
        # Description要素
        if (![string]::IsNullOrWhiteSpace($user.Description)) {
            $descriptionElement = $this.XmlDocument.CreateElement("Description", $parent.NamespaceURI)
            $descriptionElement.InnerText = $user.Description
            $localAccountElement.AppendChild($descriptionElement) | Out-Null
        }
        
        # Password要素
        if ($user.Password -ne $null) {
            $passwordElement = $this.XmlDocument.CreateElement("Password", $parent.NamespaceURI)
            
            $valueElement = $this.XmlDocument.CreateElement("Value", $parent.NamespaceURI)
            $valueElement.InnerText = $user.GetPlainTextPassword()
            $passwordElement.AppendChild($valueElement) | Out-Null
            
            $plainTextElement = $this.XmlDocument.CreateElement("PlainText", $parent.NamespaceURI)
            $plainTextElement.InnerText = "true"
            $passwordElement.AppendChild($plainTextElement) | Out-Null
            
            $localAccountElement.AppendChild($passwordElement) | Out-Null
        }
        
        # Group要素
        if ($user.Groups.Count -gt 0) {
            $groupElement = $this.XmlDocument.CreateElement("Group", $parent.NamespaceURI)
            $groupElement.InnerText = $user.Groups -join ";"
            $localAccountElement.AppendChild($groupElement) | Out-Null
        }
        
        Write-Verbose "ローカルユーザー追加完了: $($user.Name)"
    }
    
    # 組み込みユーザーアカウント設定
    [void] AddBuiltInUserConfig([System.Xml.XmlElement]$parent, [UserAccount]$user) {
        Write-Verbose "組み込みユーザー設定: $($user.Name)"
        
        if ($user.Name -eq "Administrator") {
            # AdministratorPassword/Value要素
            $valueElement = $this.XmlDocument.CreateElement("Value", $parent.NamespaceURI)
            $valueElement.InnerText = ""  # 空パスワードでAdministratorを無効化
            $parent.SelectSingleNode("un:AdministratorPassword", $this.NamespaceManager).AppendChild($valueElement) | Out-Null
            
            # AdministratorPassword/PlainText要素
            $plainTextElement = $this.XmlDocument.CreateElement("PlainText", $parent.NamespaceURI)
            $plainTextElement.InnerText = "true"
            $parent.SelectSingleNode("un:AdministratorPassword", $this.NamespaceManager).AppendChild($plainTextElement) | Out-Null
        }
        
        Write-Verbose "組み込みユーザー設定完了: $($user.Name)"
    }
    
    # 自動ログオン設定
    [void] AddAutoLogonConfiguration() {
        if (!$this.Config.EnableAutologon -or [string]::IsNullOrWhiteSpace($this.Config.AutologonUser)) {
            return
        }
        
        Write-Verbose "自動ログオン設定追加"
        
        $unattendRoot = $this.XmlDocument.DocumentElement
        $settingsElement = $this.GetOrCreateSettingsElement($unattendRoot, "specialize")
        $shellSetupComponent = $this.GetOrCreateComponent($settingsElement, "Microsoft-Windows-Shell-Setup")
        
        # AutoLogon要素
        $autoLogonElement = $this.XmlDocument.CreateElement("AutoLogon", $unattendRoot.NamespaceURI)
        $shellSetupComponent.AppendChild($autoLogonElement) | Out-Null
        
        # Username要素
        $usernameElement = $this.XmlDocument.CreateElement("Username", $unattendRoot.NamespaceURI)
        $usernameElement.InnerText = $this.Config.AutologonUser
        $autoLogonElement.AppendChild($usernameElement) | Out-Null
        
        # Enabled要素
        $enabledElement = $this.XmlDocument.CreateElement("Enabled", $unattendRoot.NamespaceURI)
        $enabledElement.InnerText = "true"
        $autoLogonElement.AppendChild($enabledElement) | Out-Null
        
        # LogonCount要素
        $logonCountElement = $this.XmlDocument.CreateElement("LogonCount", $unattendRoot.NamespaceURI)
        $logonCountElement.InnerText = $this.Config.AutologonCount.ToString()
        $autoLogonElement.AppendChild($logonCountElement) | Out-Null
        
        # 対応するユーザーのパスワード取得
        $autoLogonUser = $this.Config.Users | Where-Object { $_.Name -eq $this.Config.AutologonUser -and !$_.IsBuiltIn }
        if ($autoLogonUser -ne $null -and $autoLogonUser.Password -ne $null) {
            # Password要素
            $passwordElement = $this.XmlDocument.CreateElement("Password", $unattendRoot.NamespaceURI)
            
            $valueElement = $this.XmlDocument.CreateElement("Value", $unattendRoot.NamespaceURI)
            $valueElement.InnerText = $autoLogonUser.GetPlainTextPassword()
            $passwordElement.AppendChild($valueElement) | Out-Null
            
            $plainTextElement = $this.XmlDocument.CreateElement("PlainText", $unattendRoot.NamespaceURI)
            $plainTextElement.InnerText = "true"
            $passwordElement.AppendChild($plainTextElement) | Out-Null
            
            $autoLogonElement.AppendChild($passwordElement) | Out-Null
        }
        
        Write-Verbose "自動ログオン設定追加完了"
    }
}

# ユーザー設定検証クラス
class UserConfigValidator {
    [UserManagementConfig]$Config
    [string[]]$ValidationErrors
    [string[]]$ValidationWarnings
    
    # コンストラクタ
    UserConfigValidator([UserManagementConfig]$config) {
        $this.Config = $config
        $this.ValidationErrors = @()
        $this.ValidationWarnings = @()
    }
    
    # 設定検証実行
    [bool] ValidateConfiguration() {
        Write-Verbose "ユーザー設定検証開始"
        
        $this.ValidationErrors = @()
        $this.ValidationWarnings = @()
        
        # 基本検証
        $this.ValidateUserAccounts()
        $this.ValidatePasswordComplexity()
        $this.ValidateUserGroups()
        $this.ValidateAutoLogonSettings()
        
        # 結果出力
        foreach ($warning in $this.ValidationWarnings) {
            Write-Warning $warning
        }
        
        foreach ($error in $this.ValidationErrors) {
            Write-Error $error
        }
        
        $isValid = $this.ValidationErrors.Count -eq 0
        Write-Verbose "ユーザー設定検証完了 (Valid: $isValid)"
        
        return $isValid
    }
    
    # ユーザーアカウント検証
    [void] ValidateUserAccounts() {
        if ($this.Config.Users.Count -eq 0) {
            $this.ValidationWarnings += "ユーザーアカウントが定義されていません"
            return
        }
        
        # 重複チェック
        $userNames = $this.Config.Users | ForEach-Object { $_.Name }
        $duplicates = $userNames | Group-Object | Where-Object { $_.Count -gt 1 } | Select-Object -ExpandProperty Name
        
        if ($duplicates.Count -gt 0) {
            $this.ValidationErrors += "重複するユーザー名があります: $($duplicates -join ', ')"
        }
        
        # 管理者アカウント存在チェック
        $adminUsers = $this.Config.Users | Where-Object { $_.Groups -contains "Administrators" -and !$_.IsBuiltIn }
        if ($adminUsers.Count -eq 0) {
            $this.ValidationWarnings += "管理者グループに属するユーザーが定義されていません"
        }
        
        # Administrator無効化チェック
        $adminAccount = $this.Config.Users | Where-Object { $_.Name -eq "Administrator" -and $_.IsBuiltIn }
        if ($adminAccount -eq $null) {
            $this.ValidationWarnings += "Administratorアカウントの無効化設定がありません"
        } elseif ($adminAccount.IsEnabled) {
            $this.ValidationWarnings += "Administratorアカウントが有効になっています（セキュリティリスク）"
        }
    }
    
    # パスワード複雑性検証
    [void] ValidatePasswordComplexity() {
        foreach ($user in $this.Config.Users) {
            if ($user.IsBuiltIn -or $user.Password -eq $null) {
                continue
            }
            
            $password = $user.GetPlainTextPassword()
            
            # パスワード長チェック
            if ($password.Length -lt 8) {
                $this.ValidationErrors += "ユーザー '$($user.Name)' のパスワードが短すぎます (最小8文字)"
                continue
            }
            
            # 複雑性チェック
            $hasUpper = $password -cmatch '[A-Z]'
            $hasLower = $password -cmatch '[a-z]'
            $hasDigit = $password -cmatch '\d'
            $hasSymbol = $password -cmatch '[^\w\s]'
            
            $complexityCount = @($hasUpper, $hasLower, $hasDigit, $hasSymbol) | Where-Object { $_ } | Measure-Object | Select-Object -ExpandProperty Count
            
            if ($complexityCount -lt 3) {
                $this.ValidationWarnings += "ユーザー '$($user.Name)' のパスワード複雑性が不十分です"
            }
        }
    }
    
    # ユーザーグループ検証
    [void] ValidateUserGroups() {
        $validGroups = @("Users", "Administrators", "Power Users", "Remote Desktop Users", "Guests")
        
        foreach ($user in $this.Config.Users) {
            if ($user.IsBuiltIn) {
                continue
            }
            
            foreach ($group in $user.Groups) {
                if ($group -notin $validGroups) {
                    $this.ValidationWarnings += "ユーザー '$($user.Name)' に無効なグループが指定されています: $group"
                }
            }
            
            if ($user.Groups.Count -eq 0) {
                $this.ValidationWarnings += "ユーザー '$($user.Name)' にグループが指定されていません"
            }
        }
    }
    
    # 自動ログオン設定検証
    [void] ValidateAutoLogonSettings() {
        if (!$this.Config.EnableAutologon) {
            return
        }
        
        if ([string]::IsNullOrWhiteSpace($this.Config.AutologonUser)) {
            $this.ValidationErrors += "自動ログオンが有効ですが、ユーザー名が指定されていません"
            return
        }
        
        $autoLogonUser = $this.Config.Users | Where-Object { $_.Name -eq $this.Config.AutologonUser -and !$_.IsBuiltIn }
        if ($autoLogonUser -eq $null) {
            $this.ValidationErrors += "自動ログオン用ユーザー '$($this.Config.AutologonUser)' が見つかりません"
        }
        
        if ($this.Config.AutologonCount -le 0 -or $this.Config.AutologonCount -gt 999) {
            $this.ValidationWarnings += "自動ログオン回数が範囲外です (1-999): $($this.Config.AutologonCount)"
        }
    }
}

# メイン関数：UnattendXMLユーザー設定生成
function New-UnattendUserConfiguration {
    <#
    .SYNOPSIS
        UnattendXMLファイルのユーザー設定を生成する
    
    .PARAMETER Config
        メイン設定オブジェクト
    
    .PARAMETER XmlDocument
        XML文書オブジェクト
    
    .PARAMETER UserConfig
        ユーザー管理設定（省略時はデフォルト設定）
    
    .EXAMPLE
        New-UnattendUserConfiguration -Config $config -XmlDocument $xmlDoc
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [object]$Config,
        
        [Parameter(Mandatory = $true)]
        [System.Xml.XmlDocument]$XmlDocument,
        
        [Parameter(Mandatory = $false)]
        [UserManagementConfig]$UserConfig
    )
    
    try {
        Write-Verbose "UnattendXML ユーザー設定生成開始"
        
        # ユーザー設定の準備
        if ($UserConfig -eq $null) {
            $UserConfig = [UserManagementConfig]::new()
            $UserConfig.SetupDefaultUsers()
        }
        
        # 設定検証
        $validator = [UserConfigValidator]::new($UserConfig)
        if (!$validator.ValidateConfiguration()) {
            throw "ユーザー設定の検証に失敗しました"
        }
        
        # XML生成
        $xmlGenerator = [UnattendUserXMLGenerator]::new($XmlDocument, $UserConfig)
        $result = $xmlGenerator.GenerateUserAccountsXML()
        
        # 自動ログオン設定追加
        $xmlGenerator.AddAutoLogonConfiguration()
        
        Write-Verbose "UnattendXML ユーザー設定生成完了"
        return @{
            Success = $true
            Message = "ユーザー設定生成完了"
            UserCount = $UserConfig.Users.Count
            AdminCount = ($UserConfig.Users | Where-Object { $_.Groups -contains "Administrators" }).Count
        }
    }
    catch {
        Write-Error "ユーザー設定生成エラー: $_"
        return @{
            Success = $false
            Message = "ユーザー設定生成エラー: $_"
            Error = $_
        }
    }
}

# セキュアパスワード生成関数
function New-SecurePassword {
    <#
    .SYNOPSIS
        セキュアなパスワードを生成する
    
    .PARAMETER Length
        パスワード長（デフォルト: 12文字）
    
    .PARAMETER IncludeSymbols
        記号を含むかどうか
    
    .EXAMPLE
        New-SecurePassword -Length 16 -IncludeSymbols
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $false)]
        [ValidateRange(8, 128)]
        [int]$Length = 12,
        
        [Parameter(Mandatory = $false)]
        [switch]$IncludeSymbols
    )
    
    $upperCase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    $lowerCase = "abcdefghijklmnopqrstuvwxyz"
    $digits = "0123456789"
    $symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    $characterSet = $upperCase + $lowerCase + $digits
    if ($IncludeSymbols) {
        $characterSet += $symbols
    }
    
    $password = ""
    $random = New-Object System.Random
    
    # 最低1文字ずつ必要な文字種を含む
    $password += $upperCase[$random.Next(0, $upperCase.Length)]
    $password += $lowerCase[$random.Next(0, $lowerCase.Length)]
    $password += $digits[$random.Next(0, $digits.Length)]
    
    if ($IncludeSymbols) {
        $password += $symbols[$random.Next(0, $symbols.Length)]
        $remainingLength = $Length - 4
    } else {
        $remainingLength = $Length - 3
    }
    
    # 残りの文字をランダムに選択
    for ($i = 0; $i -lt $remainingLength; $i++) {
        $password += $characterSet[$random.Next(0, $characterSet.Length)]
    }
    
    # パスワードをシャッフル
    $passwordArray = $password.ToCharArray()
    for ($i = $passwordArray.Length - 1; $i -gt 0; $i--) {
        $j = $random.Next(0, $i + 1)
        $temp = $passwordArray[$i]
        $passwordArray[$i] = $passwordArray[$j]
        $passwordArray[$j] = $temp
    }
    
    $finalPassword = -join $passwordArray
    return ConvertTo-SecureString $finalPassword -AsPlainText -Force
}

# パスワード強度テスト関数
function Test-PasswordComplexity {
    <#
    .SYNOPSIS
        パスワードの複雑性をテストする
    
    .PARAMETER SecurePassword
        テストするセキュアパスワード
    
    .EXAMPLE
        Test-PasswordComplexity -SecurePassword $securePassword
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [securestring]$SecurePassword
    )
    
    try {
        $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword)
        $password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
        
        $result = @{
            Length = $password.Length
            HasUpperCase = $password -cmatch '[A-Z]'
            HasLowerCase = $password -cmatch '[a-z]'
            HasDigits = $password -cmatch '\d'
            HasSymbols = $password -cmatch '[^\w\s]'
            IsStrong = $false
        }
        
        # 強度判定
        $complexityCount = @($result.HasUpperCase, $result.HasLowerCase, $result.HasDigits, $result.HasSymbols) | Where-Object { $_ } | Measure-Object | Select-Object -ExpandProperty Count
        $result.IsStrong = ($result.Length -ge 8) -and ($complexityCount -ge 3)
        
        return $result
    }
    catch {
        Write-Error "パスワード複雑性テストエラー: $_"
        return $null
    }
    finally {
        if ($BSTR -ne [IntPtr]::Zero) {
            [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
        }
    }
}

# エクスポートするメンバー
Export-ModuleMember -Function @(
    'New-UnattendUserConfiguration',
    'New-SecurePassword',
    'Test-PasswordComplexity'
) -Class @(
    'UserAccount',
    'UserManagementConfig',
    'UnattendUserXMLGenerator',
    'UserConfigValidator'
)