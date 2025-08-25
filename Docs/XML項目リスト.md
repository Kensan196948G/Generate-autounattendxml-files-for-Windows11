# Windows 11 Unattend.xml 項目リスト

## 概要
このドキュメントは、Windows 11のSysprep応答ファイル（unattend.xml）で使用可能なすべての設定項目を体系的に整理したリファレンスです。

## 1. 設定パス（Configuration Pass）

### 1.1 windowsPE
初期のWindows PEフェーズで実行される設定

### 1.2 offlineServicing
Windowsイメージのオフラインサービシング時に適用

### 1.3 generalize
sysprep /generalizeコマンド実行時に処理

### 1.4 specialize
ハードウェア固有の設定を行うフェーズ

### 1.5 auditSystem
監査モードのシステムコンテキストで実行

### 1.6 auditUser
監査モードのユーザーコンテキストで実行

### 1.7 oobeSystem
Out-Of-Box Experience中に処理される設定

## 2. コンポーネント別設定項目

### 2.1 Microsoft-Windows-Setup

#### ディスク構成
```xml
<DiskConfiguration>
    <Disk wcm:action="add">
        <DiskID>0</DiskID>
        <WillWipeDisk>true</WillWipeDisk>
        <CreatePartitions>
            <CreatePartition wcm:action="add">
                <Order>1</Order>
                <Type>Primary</Type>
                <Size>500</Size>
            </CreatePartition>
            <CreatePartition wcm:action="add">
                <Order>2</Order>
                <Type>Primary</Type>
                <Extend>true</Extend>
            </CreatePartition>
        </CreatePartitions>
        <ModifyPartitions>
            <ModifyPartition wcm:action="add">
                <Order>1</Order>
                <PartitionID>1</PartitionID>
                <Label>System</Label>
                <Format>NTFS</Format>
                <Active>true</Active>
            </ModifyPartition>
            <ModifyPartition wcm:action="add">
                <Order>2</Order>
                <PartitionID>2</PartitionID>
                <Label>Windows</Label>
                <Format>NTFS</Format>
                <Letter>C</Letter>
            </ModifyPartition>
        </ModifyPartitions>
    </Disk>
</DiskConfiguration>
```

#### インストール設定
```xml
<ImageInstall>
    <OSImage>
        <InstallFrom>
            <MetaData wcm:action="add">
                <Key>/IMAGE/NAME</Key>
                <Value>Windows 11 Pro</Value>
            </MetaData>
        </InstallFrom>
        <InstallTo>
            <DiskID>0</DiskID>
            <PartitionID>2</PartitionID>
        </InstallTo>
        <WillShowUI>OnError</WillShowUI>
    </OSImage>
</ImageInstall>
```

### 2.2 Microsoft-Windows-Shell-Setup

#### コンピューター名
```xml
<ComputerName>WIN11-PC001</ComputerName>
```

#### タイムゾーン
```xml
<TimeZone>Tokyo Standard Time</TimeZone>
```

#### ユーザーアカウント
```xml
<UserAccounts>
    <LocalAccounts>
        <LocalAccount wcm:action="add">
            <Password>
                <Value>EncryptedPassword</Value>
                <PlainText>false</PlainText>
            </Password>
            <Description>Mirai User Account</Description>
            <DisplayName>mirai-user</DisplayName>
            <Group>Administrators</Group>
            <Name>mirai-user</Name>
        </LocalAccount>
        <LocalAccount wcm:action="add">
            <Password>
                <Value>EncryptedPassword</Value>
                <PlainText>false</PlainText>
            </Password>
            <Description>Local Admin Account</Description>
            <DisplayName>l-admin</DisplayName>
            <Group>Administrators</Group>
            <Name>l-admin</Name>
        </LocalAccount>
    </LocalAccounts>
    <AdministratorPassword>
        <Value></Value>
        <PlainText>true</PlainText>
    </AdministratorPassword>
</UserAccounts>
```

#### OOBE設定
```xml
<OOBE>
    <HideEULAPage>true</HideEULAPage>
    <HideLocalAccountScreen>true</HideLocalAccountScreen>
    <HideOEMRegistrationScreen>true</HideOEMRegistrationScreen>
    <HideOnlineAccountScreens>true</HideOnlineAccountScreens>
    <HideWirelessSetupInOOBE>true</HideWirelessSetupInOOBE>
    <NetworkLocation>Work</NetworkLocation>
    <ProtectYourPC>3</ProtectYourPC>
    <SkipMachineOOBE>true</SkipMachineOOBE>
    <SkipUserOOBE>true</SkipUserOOBE>
</OOBE>
```

#### 自動ログオン
```xml
<AutoLogon>
    <Password>
        <Value>Password</Value>
        <PlainText>true</PlainText>
    </Password>
    <Enabled>true</Enabled>
    <LogonCount>1</LogonCount>
    <Username>mirai-user</Username>
</AutoLogon>
```

#### 初回ログオンコマンド
```xml
<FirstLogonCommands>
    <SynchronousCommand wcm:action="add">
        <Order>1</Order>
        <CommandLine>cmd /c C:\kitting\SetUp20211012.bat</CommandLine>
        <Description>Run Setup Script</Description>
        <RequiresUserInput>false</RequiresUserInput>
    </SynchronousCommand>
    <SynchronousCommand wcm:action="add">
        <Order>2</Order>
        <CommandLine>cmd /c C:\kitting\DomainUserAdd.bat</CommandLine>
        <Description>Add Domain User</Description>
        <RequiresUserInput>false</RequiresUserInput>
    </SynchronousCommand>
</FirstLogonCommands>
```

### 2.3 Microsoft-Windows-International-Core

#### 言語設定
```xml
<InputLocale>0411:00000411</InputLocale>
<SystemLocale>ja-JP</SystemLocale>
<UILanguage>ja-JP</UILanguage>
<UILanguageFallback>en-US</UILanguageFallback>
<UserLocale>ja-JP</UserLocale>
```

### 2.4 Microsoft-Windows-Deployment

#### 実行コマンド
```xml
<RunSynchronous>
    <RunSynchronousCommand wcm:action="add">
        <Order>1</Order>
        <Path>cmd /c reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\System" /v DisableBkGndGroupPolicy /t REG_DWORD /d 0 /f</Path>
        <Description>Enable Group Policy</Description>
        <WillReboot>Never</WillReboot>
    </RunSynchronousCommand>
</RunSynchronous>
```

### 2.5 Microsoft-Windows-TCPIP

#### IPv6無効化
```xml
<Interfaces>
    <Interface wcm:action="add">
        <Identifier>Ethernet</Identifier>
        <DisableIPv6>true</DisableIPv6>
    </Interface>
</Interfaces>
```

### 2.6 Microsoft-Windows-NetBT

#### NetBIOS設定
```xml
<Interfaces>
    <Interface wcm:action="add">
        <NetbiosOptions>2</NetbiosOptions>
        <Identifier>Ethernet</Identifier>
    </Interface>
</Interfaces>
```

### 2.7 Microsoft-Windows-DNS-Client

#### DNS設定
```xml
<Interfaces>
    <Interface wcm:action="add">
        <Identifier>Ethernet</Identifier>
        <DNSServerSearchOrder>
            <IpAddress wcm:action="add" wcm:keyValue="1">8.8.8.8</IpAddress>
            <IpAddress wcm:action="add" wcm:keyValue="2">8.8.4.4</IpAddress>
        </DNSServerSearchOrder>
    </Interface>
</Interfaces>
```

### 2.8 Microsoft-Windows-Firewall

#### ファイアウォール無効化
```xml
<DomainProfile>
    <EnableFirewall>false</EnableFirewall>
</DomainProfile>
<PrivateProfile>
    <EnableFirewall>false</EnableFirewall>
</PrivateProfile>
<PublicProfile>
    <EnableFirewall>false</EnableFirewall>
</PublicProfile>
```

### 2.9 Microsoft-Windows-ServerManager-SvrMgrNc

#### サーバーマネージャー自動起動
```xml
<DoNotOpenServerManagerAtLogon>true</DoNotOpenServerManagerAtLogon>
```

### 2.10 Microsoft-Windows-IE-InternetExplorer

#### Internet Explorer設定
```xml
<HomePage>http://www.google.co.jp</HomePage>
<DisableFirstRunWizard>true</DisableFirstRunWizard>
<DisableDevTools>false</DisableDevTools>
<DisableAutoComplete>false</DisableAutoComplete>
```

## 3. レジストリ設定項目

### 3.1 グループポリシー
```xml
<RunSynchronousCommand wcm:action="add">
    <Order>1</Order>
    <Path>reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" /v AllowInsecureGuestAuth /t REG_DWORD /d 1 /f</Path>
    <Description>Allow Insecure Guest Authentication</Description>
</RunSynchronousCommand>
```

### 3.2 Bluetooth無効化
```xml
<RunSynchronousCommand wcm:action="add">
    <Order>2</Order>
    <Path>reg add "HKLM\SYSTEM\CurrentControlSet\Services\BTHPORT" /v Start /t REG_DWORD /d 4 /f</Path>
    <Description>Disable Bluetooth Service</Description>
</RunSynchronousCommand>
```

### 3.3 音声ミュート
```xml
<RunSynchronousCommand wcm:action="add">
    <Order>3</Order>
    <Path>reg add "HKCU\Software\Microsoft\Multimedia\Audio" /v UserDuckingPreference /t REG_DWORD /d 3 /f</Path>
    <Description>Mute System Sounds</Description>
</RunSynchronousCommand>
```

### 3.4 Windows Update設定
```xml
<RunSynchronousCommand wcm:action="add">
    <Order>4</Order>
    <Path>reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update" /v AUOptions /t REG_DWORD /d 2 /f</Path>
    <Description>Configure Windows Update</Description>
</RunSynchronousCommand>
```

## 4. Windows機能の有効化/無効化

### 4.1 .NET Framework 3.5
```xml
<RunSynchronousCommand wcm:action="add">
    <Order>5</Order>
    <Path>dism /online /enable-feature /featurename:NetFx3 /all /norestart</Path>
    <Description>Enable .NET Framework 3.5</Description>
</RunSynchronousCommand>
```

### 4.2 Windows Defender無効化
```xml
<RunSynchronousCommand wcm:action="add">
    <Order>6</Order>
    <Path>reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 1 /f</Path>
    <Description>Disable Windows Defender</Description>
</RunSynchronousCommand>
```

## 5. アプリケーション関連設定

### 5.1 既定のアプリケーション
```xml
<RunSynchronousCommand wcm:action="add">
    <Order>7</Order>
    <Path>cmd /c dism /online /Import-DefaultAppAssociations:C:\kitting\DefaultApps.xml</Path>
    <Description>Set Default Applications</Description>
</RunSynchronousCommand>
```

### 5.2 タスクバーのピン留め
```xml
<RunSynchronousCommand wcm:action="add">
    <Order>8</Order>
    <Path>powershell -Command "Import-StartLayout -LayoutPath C:\kitting\StartLayout.xml -MountPath C:\"</Path>
    <Description>Configure Start Menu and Taskbar</Description>
</RunSynchronousCommand>
```

## 6. ドメイン参加設定

### 6.1 ドメイン参加
```xml
<Identification>
    <Credentials>
        <Domain>CONTOSO</Domain>
        <Password>DomainPassword</Password>
        <Username>DomainAdmin</Username>
    </Credentials>
    <JoinDomain>contoso.com</JoinDomain>
    <MachineObjectOU>OU=Computers,DC=contoso,DC=com</MachineObjectOU>
</Identification>
```

## 7. 電源管理設定

### 7.1 電源プラン
```xml
<RunSynchronousCommand wcm:action="add">
    <Order>9</Order>
    <Path>powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c</Path>
    <Description>Set High Performance Power Plan</Description>
</RunSynchronousCommand>
```

## 8. セキュリティポリシー

### 8.1 パスワードポリシー
```xml
<RunSynchronousCommand wcm:action="add">
    <Order>10</Order>
    <Path>net accounts /maxpwage:unlimited</Path>
    <Description>Set Password Never Expires</Description>
</RunSynchronousCommand>
```

### 8.2 UAC設定
```xml
<RunSynchronousCommand wcm:action="add">
    <Order>11</Order>
    <Path>reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v EnableLUA /t REG_DWORD /d 1 /f</Path>
    <Description>Enable UAC</Description>
</RunSynchronousCommand>
```

## 9. ネットワーク設定

### 9.1 ネットワーク探索
```xml
<RunSynchronousCommand wcm:action="add">
    <Order>12</Order>
    <Path>netsh advfirewall firewall set rule group="Network Discovery" new enable=Yes</Path>
    <Description>Enable Network Discovery</Description>
</RunSynchronousCommand>
```

### 9.2 ファイル共有
```xml
<RunSynchronousCommand wcm:action="add">
    <Order>13</Order>
    <Path>netsh advfirewall firewall set rule group="File and Printer Sharing" new enable=Yes</Path>
    <Description>Enable File and Printer Sharing</Description>
</RunSynchronousCommand>
```

## 10. カスタムスクリプト実行

### 10.1 PowerShellスクリプト
```xml
<RunSynchronousCommand wcm:action="add">
    <Order>14</Order>
    <Path>powershell -ExecutionPolicy Bypass -File C:\kitting\CustomSetup.ps1</Path>
    <Description>Run Custom PowerShell Script</Description>
</RunSynchronousCommand>
```

### 10.2 バッチファイル
```xml
<RunSynchronousCommand wcm:action="add">
    <Order>15</Order>
    <Path>cmd /c C:\kitting\PostInstall.bat</Path>
    <Description>Run Post Installation Script</Description>
</RunSynchronousCommand>
```

## 注意事項

1. **パス（Pass）の実行順序**
   - windowsPE → offlineServicing → generalize → specialize → auditSystem → auditUser → oobeSystem

2. **wcm:action属性**
   - "add": 新規追加
   - "modify": 既存の変更
   - "remove": 削除

3. **パスワード管理**
   - PlainText="false"の場合は、暗号化されたパスワードを使用
   - セキュリティ上、平文パスワードの使用は推奨されない

4. **実行順序**
   - Order属性で実行順序を制御
   - 依存関係がある場合は適切な順序設定が必要

5. **再起動制御**
   - WillReboot属性で再起動のタイミングを制御
   - "Never", "Always", "OnRequest"から選択

---

*このリストは、Windows 11 22H2に基づいています。Windowsのバージョンによって利用可能な設定項目が異なる場合があります。*