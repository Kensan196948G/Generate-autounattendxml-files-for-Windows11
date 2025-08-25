import React, { useState, useCallback } from 'react'
import Head from 'next/head'
import styles from '../styles/Home.module.css'
import WiFiConfigSection from '../components/WiFiConfigSection'
import DesktopConfigSection from '../components/DesktopConfigSection'
import ErrorDisplay from '../components/ErrorDisplay'
import { useApi } from '../services/api'
import { ComprehensiveConfig, defaultComprehensiveConfig } from '../types/comprehensive-config'

// 旧型定義（互換性のため一時的に保持）
interface UnattendConfig {
  // 1. 地域と言語
  regionLanguage: {
    displayLanguage: string
    languagePriority: string[]
    keyboardLayouts: { language: string; layout: string }[]
    country: string
    manualSelection: boolean
  }
  
  // 2. プロセッサー・アーキテクチャ
  architecture: 'x86' | 'amd64' | 'arm64'
  
  // 3. セットアップの挙動
  setupBehavior: {
    bypassWin11Requirements: boolean
    allowOfflineInstall: boolean
    useDistributionShare: boolean
    hidePowerShellWindow: boolean
  }
  
  // 4. エディション/プロダクトキー
  windowsEdition: {
    useGenericKey: boolean
    edition: string
    productKey: string
    manualKeyEntry: boolean
    useBiosKey: boolean
    imageSelection: 'key' | 'index' | 'name'
    imageIndex?: number
    imageName?: string
  }
  
  // 5. Windows PE
  windowsPE: {
    mode: 'default' | 'script' | 'custom'
    disable83Names: boolean
    pauseBeforePartition: boolean
    pauseBeforeRestart: boolean
    customScript?: string
  }
  
  // 6. ディスク構成
  diskConfig: {
    mode: 'manual' | 'auto' | 'custom'
    partitionLayout: 'GPT' | 'MBR'
    efiSize: number
    recoveryMode: 'partition' | 'windows' | 'remove'
    customDiskpart?: string
    targetPartition?: number
    validatePhysicalDisk: boolean
  }
  
  // 7. コンピューター名/CompactOS/タイムゾーン
  computerSettings: {
    computerName: 'random' | 'fixed' | 'powershell'
    fixedName?: string
    compactOS: 'auto' | 'enable' | 'disable'
    timezone: string
  }
  
  // 8. ユーザーアカウント
  userAccounts: {
    accounts: Array<{
      name: string
      displayName: string
      password: string
      group: 'Administrators' | 'Users'
    }>
    firstLogon: 'lastAdmin' | 'administrator' | 'none'
    obfuscatePasswords: boolean
    allowAccountWizard: boolean
    passwordExpiry: 'never' | 'default' | number
    lockoutPolicy: 'default' | 'disabled' | 'custom'
  }
  
  // 9. エクスプローラー
  explorerSettings: {
    showHiddenFiles: 'default' | 'osOnly' | 'all'
    showExtensions: boolean
    classicContextMenu: boolean
    defaultToThisPC: boolean
    showTaskKill: boolean
  }
  
  // 10. スタートメニュー/タスクバー
  startTaskbar: {
    searchBox: 'full' | 'iconLabel' | 'icon' | 'hidden'
    pinnedIcons: 'default' | 'remove' | 'xml'
    disableWidgets: boolean
    alignLeft: boolean
    hideTaskView: boolean
    showAllTrayIcons: boolean
    disableBingSearch: boolean
    startMenuConfig: 'default' | 'remove' | 'custom'
  }
  
  // 11. システム調整
  systemTweaks: {
    disableDefender: boolean
    disableWindowsUpdate: boolean
    disableUAC: boolean
    disableSmartAppControl: boolean
    disableSmartScreen: boolean
    disableFastStartup: boolean
    disableSystemRestore: boolean
    enableLongPaths: boolean
    enableRDP: boolean
    hardenACL: boolean
    allowPowerShellScripts: boolean
    disableLastAccessTime: boolean
    preventUpdateRestart: boolean
    disableSystemSounds: boolean
    disableAppSuggestions: boolean
    preventDeviceEncryption: boolean
    hideEdgeFirstRun: boolean
    disableEdgeStartupBoost: boolean
    makeEdgeUninstallable: boolean
    disableMouseAcceleration: boolean
    removeWindowsOld: boolean
    auditProcessCreation: boolean
    includeCommandLine: boolean
  }
  
  // 12. 視覚効果
  visualEffects: 'default' | 'bestAppearance' | 'bestPerformance' | 'custom'
  
  // 13. デスクトップアイコン/フォルダー
  desktopSettings: {
    desktop_icons: {
      show_this_pc: boolean
      show_user_files: boolean
      show_network: boolean
      show_recycle_bin: boolean
      show_control_panel: boolean
    }
    start_menu: {
      show_documents: boolean
      show_downloads: boolean
      show_music: boolean
      show_pictures: boolean
      show_videos: boolean
      show_network: boolean
      show_personal_folder: boolean
      show_file_explorer: boolean
      show_settings: boolean
      show_recently_added_apps: boolean
      show_most_used_apps: boolean
      show_suggestions: boolean
    }
  }
  
  // 14. 仮想マシンサポート
  vmSupport: {
    virtualBox: boolean
    vmwareTools: boolean
    virtIO: boolean
    parallelsTools: boolean
  }
  
  // 15. Wi-Fi設定
  wifiSettings: {
    setup_mode: 'interactive' | 'skip' | 'configure'
    profiles: Array<{
      ssid: string
      auth_type: 'WPA2PSK' | 'WPA3PSK'
      password: string
      connect_automatically: boolean
      connect_even_if_hidden: boolean
      priority: number
    }>
    enable_wifi_sense: boolean
    connect_to_suggested_hotspots: boolean
  }
  
  // 16. Express Settings
  expressSettings: 'all_disabled' | 'all_enabled' | 'manual'
  
  // 17. ロックキー
  lockKeys: {
    capsLock: { initial: boolean; behavior: 'toggle' | 'ignore' }
    numLock: { initial: boolean; behavior: 'toggle' | 'ignore' }
    scrollLock: { initial: boolean; behavior: 'toggle' | 'ignore' }
  }
  
  // 18. 固定キー
  stickyKeys: {
    disabled: boolean
    options?: {
      triplePress: boolean
      beep: boolean
      showStatus: boolean
    }
  }
  
  // 19. 個人用設定
  personalization: {
    accentColor?: string
    desktopWallpaper?: string
    lockScreenImage?: string
  }
  
  // 20. 不要なアプリの削除
  removeApps: string[]
  
  // 21. カスタムスクリプト
  customScripts: {
    system?: string
    defaultUser?: string
    firstLogon?: string
    userFirstRun?: string
    restartExplorer: boolean
    commandLine?: string
  }
  
  // 22. WDAC
  wdac: {
    enabled: boolean
    mode?: 'audit' | 'enforce'
    scriptRestriction?: 'restricted' | 'unrestricted'
  }
  
  // 23. その他のコンポーネント
  additionalComponents: {
    includeAllComponents: boolean
    replaceGeneratorComponents: boolean
    customXml?: string
  }
  
}

// アプリケーションリスト
const REMOVABLE_APPS = [
  '3D Viewer', 'Bing Search', 'Calculator', 'Camera', 'Clipchamp',
  'Clock', 'Copilot', 'Cortana', 'Dev Home', 'Family',
  'Feedback Hub', 'Game Assist', 'Get Help', 'Handwriting', 'Internet Explorer',
  'Mail and Calendar', 'Maps', 'Math Input Panel', 'Media Features', 'Mixed Reality',
  'Movies & TV', 'News', 'Notepad (modern)', 'Office 365', 'OneDrive',
  'OneNote', 'OneSync', 'OpenSSH Client', 'Outlook for Windows', 'Paint',
  'Paint 3D', 'People', 'Power Automate', 'PowerShell 2.0', 'PowerShell ISE',
  'Quick Assist', 'Recall', 'Remote Desktop Client', 'Skype', 'Snipping Tool',
  'Solitaire Collection', 'Speech', 'Steps Recorder', 'Sticky Notes', 'Teams',
  'Tips', 'To Do', 'Voice Recorder', 'Wallet', 'Weather',
  'Windows Fax and Scan', 'Windows Hello', 'Windows Media Player (classic)',
  'Windows Media Player (modern)', 'Windows Terminal', 'WordPad', 'Xbox Apps',
  'Your Phone (Phone Link)'
]

export default function Home() {
  // 初期設定（ComprehensiveConfig型を使用）
  const [config, setConfig] = useState<ComprehensiveConfig>(defaultComprehensiveConfig)
  
  // 旧設定の初期値（互換性のためのデータマッピング用）
  const [_unusedOldConfig] = useState<UnattendConfig>({
    regionLanguage: {
      displayLanguage: 'ja-JP',
      languagePriority: ['ja-JP'],
      keyboardLayouts: [{ language: 'ja-JP', layout: '0411:00000411' }],
      country: 'Japan',
      manualSelection: false
    },
    architecture: 'amd64',
    setupBehavior: {
      bypassWin11Requirements: true,
      allowOfflineInstall: true,
      useDistributionShare: false,
      hidePowerShellWindow: true
    },
    windowsEdition: {
      useGenericKey: true,
      edition: 'Pro',  // selectのvalueと一致させる
      productKey: 'VK7JG-NPHTM-C97JM-9MPGT-3V66T',
      manualKeyEntry: false,
      useBiosKey: false,
      imageSelection: 'key'
    },
    windowsPE: {
      mode: 'default',
      disable83Names: false,
      pauseBeforePartition: false,
      pauseBeforeRestart: false
    },
    diskConfig: {
      mode: 'auto',
      partitionLayout: 'GPT',
      efiSize: 100,
      recoveryMode: 'partition',
      validatePhysicalDisk: false
    },
    computerSettings: {
      computerName: 'random',
      compactOS: 'auto',
      timezone: 'Tokyo Standard Time'
    },
    userAccounts: {
      accounts: [{
        name: 'mirai-user',
        displayName: 'Mirai User',
        password: 'mirai',
        group: 'Administrators'
      }],
      firstLogon: 'lastAdmin',
      obfuscatePasswords: true,
      allowAccountWizard: false,
      passwordExpiry: 'never',
      lockoutPolicy: 'default'
    },
    explorerSettings: {
      showHiddenFiles: 'default',
      showExtensions: true,
      classicContextMenu: true,
      defaultToThisPC: true,
      showTaskKill: false
    },
    startTaskbar: {
      searchBox: 'icon',
      pinnedIcons: 'default',
      disableWidgets: true,
      alignLeft: false,
      hideTaskView: false,
      showAllTrayIcons: true,
      disableBingSearch: true,
      startMenuConfig: 'default'
    },
    systemTweaks: {
      disableDefender: false,
      disableWindowsUpdate: false,
      disableUAC: false,
      disableSmartAppControl: false,
      disableSmartScreen: false,
      disableFastStartup: true,
      disableSystemRestore: false,
      enableLongPaths: true,
      enableRDP: false,
      hardenACL: false,
      allowPowerShellScripts: true,
      disableLastAccessTime: false,
      preventUpdateRestart: false,
      disableSystemSounds: true,
      disableAppSuggestions: true,
      preventDeviceEncryption: true,
      hideEdgeFirstRun: true,
      disableEdgeStartupBoost: true,
      makeEdgeUninstallable: false,
      disableMouseAcceleration: false,
      removeWindowsOld: true,
      auditProcessCreation: false,
      includeCommandLine: false
    },
    visualEffects: 'default',
    desktopSettings: {
      desktop_icons: {
        show_this_pc: true,
        show_user_files: true,
        show_network: false,
        show_recycle_bin: true,
        show_control_panel: false
      },
      start_menu: {
        show_documents: true,
        show_downloads: true,
        show_music: false,
        show_pictures: true,
        show_videos: false,
        show_network: false,
        show_personal_folder: true,
        show_file_explorer: true,
        show_settings: true,
        show_recently_added_apps: true,
        show_most_used_apps: true,
        show_suggestions: false
      }
    },
    vmSupport: {
      virtualBox: false,
      vmwareTools: false,
      virtIO: false,
      parallelsTools: false
    },
    wifiSettings: {
      setup_mode: 'configure',  // デフォルトでWi-Fi設定を有効化
      profiles: [{
        ssid: '20mirai18',
        auth_type: 'WPA2PSK',
        password: '20m!ra!18',
        connect_automatically: true,
        connect_even_if_hidden: false,
        priority: 1
      }],
      enable_wifi_sense: false,
      connect_to_suggested_hotspots: false
    },
    expressSettings: 'all_disabled',
    lockKeys: {
      capsLock: { initial: false, behavior: 'toggle' },
      numLock: { initial: true, behavior: 'toggle' },
      scrollLock: { initial: false, behavior: 'toggle' }
    },
    stickyKeys: {
      disabled: true
    },
    personalization: {},
    removeApps: REMOVABLE_APPS,
    customScripts: {
      restartExplorer: false
    },
    wdac: {
      enabled: false
    },
    additionalComponents: {
      includeAllComponents: false,
      replaceGeneratorComponents: false
    }
  })

  const [activeSection, setActiveSection] = useState<string | null>('regionLanguage')
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<any>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)

  // API クライアント
  const apiClient = useApi()

  // セクション定義
  const sections = [
    { id: 'regionLanguage', title: '1. 地域と言語の設定', icon: '🌐' },
    { id: 'architecture', title: '2. プロセッサー・アーキテクチャ', icon: '💻' },
    { id: 'setupBehavior', title: '3. セットアップの挙動', icon: '⚙️' },
    { id: 'windowsEdition', title: '4. エディション/プロダクトキー', icon: '🔑' },
    { id: 'windowsPE', title: '5. Windows PE ステージ', icon: '💾' },
    { id: 'diskConfig', title: '6. ディスク構成', icon: '💿' },
    { id: 'computerSettings', title: '7. コンピューター設定', icon: '🖥️' },
    { id: 'userAccounts', title: '8. ユーザーアカウント', icon: '👤' },
    { id: 'explorerSettings', title: '9. エクスプローラー調整', icon: '📁' },
    { id: 'startTaskbar', title: '10. スタート/タスクバー', icon: '📱' },
    { id: 'systemTweaks', title: '11. システム調整', icon: '🔧' },
    { id: 'visualEffects', title: '12. 視覚効果', icon: '🎨' },
    { id: 'desktopSettings', title: '13. デスクトップ設定', icon: '🖼️' },
    { id: 'vmSupport', title: '14. 仮想マシンサポート', icon: '🖲️' },
    { id: 'wifiSettings', title: '15. Wi-Fi設定', icon: '📶' },
    { id: 'expressSettings', title: '16. Express Settings', icon: '⚡' },
    { id: 'lockKeys', title: '17. ロックキー設定', icon: '⌨️' },
    { id: 'stickyKeys', title: '18. 固定キー', icon: '🔒' },
    { id: 'personalization', title: '19. 個人用設定', icon: '🎭' },
    { id: 'removeApps', title: '20. 不要なアプリの削除', icon: '🗑️' },
    { id: 'customScripts', title: '21. カスタムスクリプト', icon: '📝' },
    { id: 'wdac', title: '22. WDAC設定', icon: '🛡️' },
    { id: 'additionalComponents', title: '23. その他のコンポーネント', icon: '🧩' },
  ]

  // XML生成（シンプル版）
  const generateXML = useCallback(async (withLog: boolean = false) => {
    setGenerating(true)
    setError(null)

    try {
      console.log('XML生成開始:', config)
      
      // ログ付きまたはXMLのみを選択してダウンロード
      if (withLog) {
        await apiClient.downloadXmlWithLog(config)
        console.log('✅ XML+ログ生成・ダウンロード完了')
      } else {
        await apiClient.downloadXml(config)
        console.log('✅ XML生成・ダウンロード完了')
      }
      
      // 成功通知（toast等を表示する場合はここで）
      
    } catch (err) {
      console.error('XML生成エラー:', err)
      // 詳細なエラー情報を取得
      const errorDetails = await apiClient.getErrorDetails(err)
      setError(errorDetails)
    } finally {
      setGenerating(false)
    }
  }, [config, apiClient])

  // ユーザーアカウント追加
  const addUserAccount = useCallback(() => {
    setConfig(prev => ({
      ...prev,
      userAccounts: {
        ...prev.userAccounts,
        accounts: [
          ...prev.userAccounts.accounts,
          {
            name: `User${prev.userAccounts.accounts.length + 1}`,
            displayName: '',
            password: '',
            group: 'Users'
          }
        ]
      }
    }))
  }, [])

  // アプリ選択トグル
  const toggleApp = useCallback((app: string) => {
    setConfig(prev => ({
      ...prev,
      removeApps: prev.removeApps.includes(app)
        ? prev.removeApps.filter(a => a !== app)
        : [...prev.removeApps, app]
    }))
  }, [])

  return (
    <div className={styles.container}>
      <Head>
        <title>Windows 11 無人応答ファイル生成システム</title>
        <meta name="description" content="Windows 11 Sysprep用unattend.xml生成" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      {/* ヘッダー */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <h1>🖥️ Windows 11 無人応答ファイル生成システム</h1>
          <div className={styles.headerInfo}>
            <span className={styles.badge}>Version: 2.0.0</span>
            <span className={styles.badge}>エンタープライズ対応</span>
            <span className={styles.badge}>日本語環境最適化</span>
          </div>
        </div>
      </header>

      {/* メインコンテンツ */}
      <main className={styles.main}>
        <div className={styles.configPanel}>
          {/* セクションリスト */}
          <nav className={styles.sectionNav}>
            {sections.map(section => (
              <button
                key={section.id}
                className={`${styles.sectionButton} ${activeSection === section.id ? styles.active : ''}`}
                onClick={() => setActiveSection(activeSection === section.id ? null : section.id)}
              >
                <span className={styles.sectionIcon}>{section.icon}</span>
                <span className={styles.sectionTitle}>{section.title}</span>
                <span className={styles.sectionToggle}>
                  {activeSection === section.id ? '▼' : '▶'}
                </span>
              </button>
            ))}
          </nav>

          {/* 設定フォーム */}
          <div className={styles.configForm}>
            {/* 1. 地域と言語 */}
            {activeSection === 'regionLanguage' && (
              <div className={styles.section}>
                <h3>🌐 地域と言語の設定</h3>
                
                <div className={styles.formGroup}>
                  <label>Windows 表示言語</label>
                  <select 
                    value={config.regionLanguage.displayLanguage}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      regionLanguage: { ...prev.regionLanguage, displayLanguage: e.target.value }
                    }))}
                  >
                    <option value="ja-JP">日本語</option>
                    <option value="en-US">English (United States)</option>
                    <option value="zh-CN">中文 (简体)</option>
                    <option value="ko-KR">한국어</option>
                  </select>
                </div>

                <div className={styles.formGroup}>
                  <label>国/地域</label>
                  <select 
                    value={config.regionLanguage.country}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      regionLanguage: { ...prev.regionLanguage, country: e.target.value }
                    }))}
                  >
                    <option value="Japan">日本</option>
                    <option value="United States">United States</option>
                    <option value="China">China</option>
                    <option value="Korea">Korea</option>
                  </select>
                </div>

                <div className={styles.formGroup}>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.regionLanguage.manualSelection}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        regionLanguage: { ...prev.regionLanguage, manualSelection: e.target.checked }
                      }))}
                    />
                    セットアップ中に言語設定を手動で選択
                  </label>
                </div>
              </div>
            )}

            {/* 2. アーキテクチャ */}
            {activeSection === 'architecture' && (
              <div className={styles.section}>
                <h3>💻 プロセッサー・アーキテクチャ</h3>
                
                <div className={styles.radioGroup}>
                  <label>
                    <input 
                      type="radio"
                      value="x86"
                      checked={config.architecture === 'x86'}
                      onChange={(_) => setConfig(prev => ({ ...prev, architecture: 'x86' }))}
                    />
                    Intel/AMD 32-bit (x86 - 非推奨)
                  </label>
                  <label>
                    <input 
                      type="radio"
                      value="amd64"
                      checked={config.architecture === 'amd64'}
                      onChange={(e) => setConfig(prev => ({ ...prev, architecture: 'amd64' }))}
                    />
                    Intel/AMD 64-bit (x64)
                  </label>
                  <label>
                    <input 
                      type="radio"
                      value="arm64"
                      checked={config.architecture === 'arm64'}
                      onChange={(e) => setConfig(prev => ({ ...prev, architecture: 'arm64' }))}
                    />
                    Windows on ARM64
                  </label>
                </div>
              </div>
            )}

            {/* 3. セットアップの挙動 */}
            {activeSection === 'setupBehavior' && (
              <div className={styles.section}>
                <h3>⚙️ セットアップの挙動</h3>
                
                <div className={styles.checkboxGroup}>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.setupBehavior.bypassWin11Requirements}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        setupBehavior: { ...prev.setupBehavior, bypassWin11Requirements: e.target.checked }
                      }))}
                    />
                    Windows 11 要件チェックを回避（TPM・Secure Boot等）
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.setupBehavior.allowOfflineInstall}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        setupBehavior: { ...prev.setupBehavior, allowOfflineInstall: e.target.checked }
                      }))}
                    />
                    インターネット接続なしでインストールを許可
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.setupBehavior.hidePowerShellWindow}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        setupBehavior: { ...prev.setupBehavior, hidePowerShellWindow: e.target.checked }
                      }))}
                    />
                    セットアップ中のPowerShellウィンドウを非表示
                  </label>
                </div>
              </div>
            )}

            {/* 4. エディション/プロダクトキー */}
            {activeSection === 'windowsEdition' && (
              <div className={styles.section}>
                <h3>🔑 エディション/プロダクトキー</h3>
                
                <div className={styles.formGroup}>
                  <label>Windowsエディション</label>
                  <select 
                    value={config.windowsEdition.edition}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      windowsEdition: { 
                        ...prev.windowsEdition, 
                        edition: e.target.value,
                        productKey: e.target.value === 'Home' ? 'YTMG3-N6DKC-DKB77-7M9GH-8HVX7' :
                                    e.target.value === 'Pro' ? 'VK7JG-NPHTM-C97JM-9MPGT-3V66T' :
                                    e.target.value === 'Pro N' ? '2B87N-8KFHP-DKV6R-Y2C8J-PKCKT' :
                                    e.target.value === 'Education' ? 'YNMGQ-8RYV3-4PGQ3-C8XTP-7CFBY' :
                                    e.target.value === 'Education N' ? '84NGF-MHBT6-FXBX8-QWJK7-DRR8H' :
                                    e.target.value === 'Enterprise' ? 'XGVPP-NMH47-7TTHJ-W3FW7-8HV2C' :
                                    e.target.value === 'Enterprise N' ? 'WGGHN-J84D6-QYCPR-T7PJ7-X766F' :
                                    prev.windowsEdition.productKey
                      }
                    }))}
                  >
                    <option value="Home">Windows 11 Home</option>
                    <option value="Pro">Windows 11 Pro</option>
                    <option value="Pro N">Windows 11 Pro N</option>
                    <option value="Education">Windows 11 Education</option>
                    <option value="Education N">Windows 11 Education N</option>
                    <option value="Enterprise">Windows 11 Enterprise</option>
                    <option value="Enterprise N">Windows 11 Enterprise N</option>
                    <option value="Pro for Workstations">Windows 11 Pro for Workstations</option>
                    <option value="Pro for Workstations N">Windows 11 Pro for Workstations N</option>
                    <option value="SE">Windows 11 SE</option>
                  </select>
                </div>

                <div className={styles.formGroup}>
                  <label>プロダクトキー設定</label>
                  <div className={styles.radioGroup}>
                    <label>
                      <input 
                        type="radio"
                        checked={config.windowsEdition.useGenericKey}
                        onChange={() => setConfig(prev => ({
                          ...prev,
                          windowsEdition: { 
                            ...prev.windowsEdition, 
                            useGenericKey: true,
                            manualKeyEntry: false,
                            useBiosKey: false
                          }
                        }))}
                      />
                      汎用プロダクトキーを使用（後でライセンス認証）
                    </label>
                    <label>
                      <input 
                        type="radio"
                        checked={config.windowsEdition.manualKeyEntry}
                        onChange={() => setConfig(prev => ({
                          ...prev,
                          windowsEdition: { 
                            ...prev.windowsEdition, 
                            useGenericKey: false,
                            manualKeyEntry: true,
                            useBiosKey: false
                          }
                        }))}
                      />
                      カスタムプロダクトキーを入力
                    </label>
                    <label>
                      <input 
                        type="radio"
                        checked={config.windowsEdition.useBiosKey}
                        onChange={() => setConfig(prev => ({
                          ...prev,
                          windowsEdition: { 
                            ...prev.windowsEdition, 
                            useGenericKey: false,
                            manualKeyEntry: false,
                            useBiosKey: true
                          }
                        }))}
                      />
                      BIOS/UEFIに埋め込まれたキーを使用（OEM）
                    </label>
                  </div>
                </div>

                {config.windowsEdition.manualKeyEntry && (
                  <div className={styles.formGroup}>
                    <label>プロダクトキー（5文字×5グループ）</label>
                    <input 
                      type="text"
                      placeholder="XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"
                      value={config.windowsEdition.productKey}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        windowsEdition: { ...prev.windowsEdition, productKey: e.target.value }
                      }))}
                      maxLength={29}
                      style={{ fontFamily: 'monospace', letterSpacing: '1px' }}
                    />
                  </div>
                )}

                {config.windowsEdition.useGenericKey && (
                  <div className={styles.infoBox}>
                    <h4>ℹ️ 現在選択されている汎用キー</h4>
                    <p style={{ fontFamily: 'monospace', fontSize: '0.9rem' }}>
                      {config.windowsEdition.productKey || 'エディションを選択してください'}
                    </p>
                    <p style={{ fontSize: '0.85rem', color: '#666' }}>
                      このキーは評価/インストール用です。後でライセンス認証が必要です。
                    </p>
                  </div>
                )}

                <div className={styles.formGroup}>
                  <label>イメージ選択方法</label>
                  <div className={styles.radioGroup}>
                    <label>
                      <input 
                        type="radio"
                        value="key"
                        checked={config.windowsEdition.imageSelection === 'key'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          windowsEdition: { ...prev.windowsEdition, imageSelection: 'key' as const }
                        }))}
                      />
                      プロダクトキーで自動選択
                    </label>
                    <label>
                      <input 
                        type="radio"
                        value="index"
                        checked={config.windowsEdition.imageSelection === 'index'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          windowsEdition: { ...prev.windowsEdition, imageSelection: 'index' as const }
                        }))}
                      />
                      インデックス番号で指定
                    </label>
                    <label>
                      <input 
                        type="radio"
                        value="name"
                        checked={config.windowsEdition.imageSelection === 'name'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          windowsEdition: { ...prev.windowsEdition, imageSelection: 'name' as const }
                        }))}
                      />
                      イメージ名で指定
                    </label>
                  </div>
                </div>

                {config.windowsEdition.imageSelection === 'index' && (
                  <div className={styles.formGroup}>
                    <label>イメージインデックス番号</label>
                    <input 
                      type="number"
                      min="1"
                      max="10"
                      value={config.windowsEdition.imageIndex || 1}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        windowsEdition: { ...prev.windowsEdition, imageIndex: parseInt(e.target.value) }
                      }))}
                    />
                    <small>通常: 1=Home, 2=Home N, 3=Pro, 4=Pro N, 5=Education, 6=Enterprise</small>
                  </div>
                )}

                {config.windowsEdition.imageSelection === 'name' && (
                  <div className={styles.formGroup}>
                    <label>イメージ名</label>
                    <input 
                      type="text"
                      placeholder="例: Windows 11 Pro"
                      value={config.windowsEdition.imageName || ''}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        windowsEdition: { ...prev.windowsEdition, imageName: e.target.value }
                      }))}
                    />
                    <small>install.wimファイル内の正確なイメージ名を入力してください</small>
                  </div>
                )}

                <div className={styles.infoBox}>
                  <h4>💡 エディションとプロダクトキーについて</h4>
                  <ul>
                    <li>汎用キーは評価版として機能し、180日間使用可能です</li>
                    <li>正規ライセンスは後で「設定」→「システム」→「ライセンス認証」から適用できます</li>
                    <li>Enterprise/Educationエディションはボリュームライセンスが必要です</li>
                    <li>OEMキーはメーカー製PCにプリインストールされている場合に使用します</li>
                  </ul>
                </div>
              </div>
            )}

            {/* 5. Windows PE ステージ */}
            {activeSection === 'windowsPE' && (
              <div className={styles.section}>
                <h3>💾 Windows PE ステージ</h3>
                
                <div className={styles.formGroup}>
                  <label>Windows PE モード</label>
                  <div className={styles.radioGroup}>
                    <label>
                      <input 
                        type="radio"
                        value="default"
                        checked={config.windowsPE.mode === 'default'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          windowsPE: { ...prev.windowsPE, mode: 'default' as const }
                        }))}
                      />
                      標準モード（推奨）
                    </label>
                    <label>
                      <input 
                        type="radio"
                        value="script"
                        checked={config.windowsPE.mode === 'script'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          windowsPE: { ...prev.windowsPE, mode: 'script' as const }
                        }))}
                      />
                      スクリプト実行モード
                    </label>
                    <label>
                      <input 
                        type="radio"
                        value="custom"
                        checked={config.windowsPE.mode === 'custom'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          windowsPE: { ...prev.windowsPE, mode: 'custom' as const }
                        }))}
                      />
                      カスタムモード（上級者向け）
                    </label>
                  </div>
                </div>

                <div className={styles.checkboxGroup}>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.windowsPE.disable83Names}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        windowsPE: { ...prev.windowsPE, disable83Names: e.target.checked }
                      }))}
                    />
                    8.3形式のファイル名を無効化（パフォーマンス向上）
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.windowsPE.pauseBeforePartition}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        windowsPE: { ...prev.windowsPE, pauseBeforePartition: e.target.checked }
                      }))}
                    />
                    パーティション作成前に一時停止（確認用）
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.windowsPE.pauseBeforeRestart}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        windowsPE: { ...prev.windowsPE, pauseBeforeRestart: e.target.checked }
                      }))}
                    />
                    再起動前に一時停止（デバッグ用）
                  </label>
                </div>

                {config.windowsPE.mode === 'script' && (
                  <div className={styles.formGroup}>
                    <label>カスタムスクリプト（PowerShell/バッチ）</label>
                    <textarea 
                      rows={10}
                      placeholder="# Windows PE環境で実行するスクリプトを入力&#10;# 例: ドライバーのインストール、ネットワーク設定など"
                      value={config.windowsPE.customScript || ''}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        windowsPE: { ...prev.windowsPE, customScript: e.target.value }
                      }))}
                      style={{ fontFamily: 'monospace' }}
                    />
                  </div>
                )}

                <div className={styles.infoBox}>
                  <h4>💡 Windows PEステージについて</h4>
                  <ul>
                    <li>Windows PE（Preinstallation Environment）は、Windowsインストール前の環境です</li>
                    <li>ここでディスクのパーティション作成、ドライバーのロード、初期設定が行われます</li>
                    <li>8.3形式のファイル名を無効化すると、NTFSのパフォーマンスが向上します</li>
                    <li>一時停止オプションは、トラブルシューティング時に便利です</li>
                  </ul>
                </div>
              </div>
            )}

            {/* 6. ディスク構成 */}
            {activeSection === 'diskConfig' && (
              <div className={styles.section}>
                <h3>💿 ディスク構成</h3>
                
                <div className={styles.formGroup}>
                  <label>ディスク構成モード</label>
                  <div className={styles.radioGroup}>
                    <label>
                      <input 
                        type="radio"
                        value="auto"
                        checked={config.diskConfig.mode === 'auto'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          diskConfig: { ...prev.diskConfig, mode: 'auto' as const }
                        }))}
                      />
                      自動構成（推奨）
                    </label>
                    <label>
                      <input 
                        type="radio"
                        value="manual"
                        checked={config.diskConfig.mode === 'manual'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          diskConfig: { ...prev.diskConfig, mode: 'manual' as const }
                        }))}
                      />
                      手動構成
                    </label>
                    <label>
                      <input 
                        type="radio"
                        value="custom"
                        checked={config.diskConfig.mode === 'custom'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          diskConfig: { ...prev.diskConfig, mode: 'custom' as const }
                        }))}
                      />
                      カスタムスクリプト
                    </label>
                  </div>
                </div>

                <div className={styles.formGroup}>
                  <label>パーティションレイアウト</label>
                  <div className={styles.radioGroup}>
                    <label>
                      <input 
                        type="radio"
                        value="GPT"
                        checked={config.diskConfig.partitionLayout === 'GPT'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          diskConfig: { ...prev.diskConfig, partitionLayout: 'GPT' as const }
                        }))}
                      />
                      GPT（UEFI）- 推奨
                    </label>
                    <label>
                      <input 
                        type="radio"
                        value="MBR"
                        checked={config.diskConfig.partitionLayout === 'MBR'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          diskConfig: { ...prev.diskConfig, partitionLayout: 'MBR' as const }
                        }))}
                      />
                      MBR（レガシーBIOS）
                    </label>
                  </div>
                </div>

                <div className={styles.formGroup}>
                  <label>EFIシステムパーティションサイズ（MB）</label>
                  <input 
                    type="number"
                    min="100"
                    max="1000"
                    value={config.diskConfig.efiSize}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      diskConfig: { ...prev.diskConfig, efiSize: parseInt(e.target.value) }
                    }))}
                  />
                  <small>通常100-500MB（GPTの場合のみ）</small>
                </div>

                <div className={styles.formGroup}>
                  <label>回復環境の構成</label>
                  <div className={styles.radioGroup}>
                    <label>
                      <input 
                        type="radio"
                        value="partition"
                        checked={config.diskConfig.recoveryMode === 'partition'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          diskConfig: { ...prev.diskConfig, recoveryMode: 'partition' as const }
                        }))}
                      />
                      専用パーティションに配置
                    </label>
                    <label>
                      <input 
                        type="radio"
                        value="windows"
                        checked={config.diskConfig.recoveryMode === 'windows'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          diskConfig: { ...prev.diskConfig, recoveryMode: 'windows' as const }
                        }))}
                      />
                      Windowsパーティションに配置
                    </label>
                    <label>
                      <input 
                        type="radio"
                        value="remove"
                        checked={config.diskConfig.recoveryMode === 'remove'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          diskConfig: { ...prev.diskConfig, recoveryMode: 'remove' as const }
                        }))}
                      />
                      回復環境を削除（容量節約）
                    </label>
                  </div>
                </div>

                {config.diskConfig.mode === 'manual' && (
                  <div className={styles.formGroup}>
                    <label>対象パーティション番号</label>
                    <input 
                      type="number"
                      min="1"
                      max="10"
                      value={config.diskConfig.targetPartition || 1}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        diskConfig: { ...prev.diskConfig, targetPartition: parseInt(e.target.value) }
                      }))}
                    />
                    <small>Windowsをインストールするパーティション番号</small>
                  </div>
                )}

                {config.diskConfig.mode === 'custom' && (
                  <div className={styles.formGroup}>
                    <label>カスタムDiskpartスクリプト</label>
                    <textarea 
                      rows={10}
                      placeholder="select disk 0&#10;clean&#10;convert gpt&#10;create partition efi size=100&#10;..."
                      value={config.diskConfig.customDiskpart || ''}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        diskConfig: { ...prev.diskConfig, customDiskpart: e.target.value }
                      }))}
                      style={{ fontFamily: 'monospace' }}
                    />
                  </div>
                )}

                <div className={styles.checkboxGroup}>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.diskConfig.validatePhysicalDisk}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        diskConfig: { ...prev.diskConfig, validatePhysicalDisk: e.target.checked }
                      }))}
                    />
                    物理ディスクの検証を実行（インストール前にディスクチェック）
                  </label>
                </div>

                <div className={styles.infoBox}>
                  <h4>💡 推奨パーティション構成</h4>
                  <ul>
                    <li>EFIシステムパーティション: 100-500MB（GPTの場合）</li>
                    <li>MSR（予約）パーティション: 16-128MB（GPTの場合、自動作成）</li>
                    <li>Windowsパーティション: 残り全体（最小20GB推奨）</li>
                    <li>回復パーティション: 500MB-1GB（オプション）</li>
                  </ul>
                </div>
              </div>
            )}

            {/* 7. コンピューター設定 */}
            {activeSection === 'computerSettings' && (
              <div className={styles.section}>
                <h3>🖥️ コンピューター設定</h3>
                
                <div className={styles.formGroup}>
                  <label>コンピューター名設定</label>
                  <div className={styles.radioGroup}>
                    <label>
                      <input 
                        type="radio"
                        value="random"
                        checked={config.computerSettings.computerName === 'random'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          computerSettings: { ...prev.computerSettings, computerName: 'random' as const }
                        }))}
                      />
                      ランダム生成（DESKTOP-XXXXXX）
                    </label>
                    <label>
                      <input 
                        type="radio"
                        value="fixed"
                        checked={config.computerSettings.computerName === 'fixed'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          computerSettings: { ...prev.computerSettings, computerName: 'fixed' as const }
                        }))}
                      />
                      固定名を指定
                    </label>
                    <label>
                      <input 
                        type="radio"
                        value="powershell"
                        checked={config.computerSettings.computerName === 'powershell'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          computerSettings: { ...prev.computerSettings, computerName: 'powershell' as const }
                        }))}
                      />
                      PowerShellスクリプトで生成
                    </label>
                  </div>
                </div>

                {config.computerSettings.computerName === 'fixed' && (
                  <div className={styles.formGroup}>
                    <label>コンピューター名</label>
                    <input 
                      type="text"
                      placeholder="例: DESKTOP-001"
                      value={config.computerSettings.fixedName || ''}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        computerSettings: { ...prev.computerSettings, fixedName: e.target.value }
                      }))}
                      maxLength={15}
                    />
                    <small>最大15文字、英数字とハイフンのみ</small>
                  </div>
                )}

                <div className={styles.formGroup}>
                  <label>CompactOS（OSの圧縮）</label>
                  <div className={styles.radioGroup}>
                    <label>
                      <input 
                        type="radio"
                        value="auto"
                        checked={config.computerSettings.compactOS === 'auto'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          computerSettings: { ...prev.computerSettings, compactOS: 'auto' as const }
                        }))}
                      />
                      自動判定（推奨）
                    </label>
                    <label>
                      <input 
                        type="radio"
                        value="enable"
                        checked={config.computerSettings.compactOS === 'enable'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          computerSettings: { ...prev.computerSettings, compactOS: 'enable' as const }
                        }))}
                      />
                      有効（ディスク容量節約）
                    </label>
                    <label>
                      <input 
                        type="radio"
                        value="disable"
                        checked={config.computerSettings.compactOS === 'disable'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          computerSettings: { ...prev.computerSettings, compactOS: 'disable' as const }
                        }))}
                      />
                      無効（パフォーマンス優先）
                    </label>
                  </div>
                </div>

                <div className={styles.formGroup}>
                  <label>タイムゾーン</label>
                  <select 
                    value={config.computerSettings.timezone}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      computerSettings: { ...prev.computerSettings, timezone: e.target.value }
                    }))}
                  >
                    <option value="Tokyo Standard Time">日本標準時 (UTC+9)</option>
                    <option value="China Standard Time">中国標準時 (UTC+8)</option>
                    <option value="Korea Standard Time">韓国標準時 (UTC+9)</option>
                    <option value="Pacific Standard Time">太平洋標準時 (UTC-8)</option>
                    <option value="Eastern Standard Time">東部標準時 (UTC-5)</option>
                    <option value="Central European Standard Time">中央ヨーロッパ標準時 (UTC+1)</option>
                    <option value="GMT Standard Time">グリニッジ標準時 (UTC+0)</option>
                  </select>
                </div>

                <div className={styles.infoBox}>
                  <h4>💡 CompactOSについて</h4>
                  <ul>
                    <li>CompactOSを有効にすると、OSファイルが圧縮されディスク容量を節約できます（約2-3GB）</li>
                    <li>SSDやeMMCなど容量が限られるデバイスに有効です</li>
                    <li>CPUの性能が低い場合は、無効にすることをお勧めします</li>
                    <li>自動判定では、ディスク容量とCPU性能を考慮して最適な設定を選択します</li>
                  </ul>
                </div>
              </div>
            )}

            {/* 8. ユーザーアカウント */}
            {activeSection === 'userAccounts' && (
              <div className={styles.section}>
                <h3>👤 ユーザーアカウント</h3>
                
                <div className={styles.accountList}>
                  {config.userAccounts.accounts.map((account, index) => (
                    <div key={index} className={styles.accountItem}>
                      <input 
                        type="text"
                        placeholder="アカウント名"
                        value={account.name}
                        onChange={(e) => {
                          const newAccounts = [...config.userAccounts.accounts]
                          newAccounts[index].name = e.target.value
                          setConfig(prev => ({
                            ...prev,
                            userAccounts: { ...prev.userAccounts, accounts: newAccounts }
                          }))
                        }}
                      />
                      <input 
                        type="password"
                        placeholder="パスワード"
                        value={account.password}
                        onChange={(e) => {
                          const newAccounts = [...config.userAccounts.accounts]
                          newAccounts[index].password = e.target.value
                          setConfig(prev => ({
                            ...prev,
                            userAccounts: { ...prev.userAccounts, accounts: newAccounts }
                          }))
                        }}
                      />
                      <select 
                        value={account.group}
                        onChange={(e) => {
                          const newAccounts = [...config.userAccounts.accounts]
                          newAccounts[index].group = e.target.value as 'Administrators' | 'Users'
                          setConfig(prev => ({
                            ...prev,
                            userAccounts: { ...prev.userAccounts, accounts: newAccounts }
                          }))
                        }}
                      >
                        <option value="Administrators">管理者</option>
                        <option value="Users">標準ユーザー</option>
                      </select>
                      <button 
                        onClick={() => {
                          const newAccounts = config.userAccounts.accounts.filter((_, i) => i !== index)
                          setConfig(prev => ({
                            ...prev,
                            userAccounts: { ...prev.userAccounts, accounts: newAccounts }
                          }))
                        }}
                        className={styles.removeButton}
                      >
                        削除
                      </button>
                    </div>
                  ))}
                </div>
                
                <button onClick={addUserAccount} className={styles.addButton}>
                  + ユーザー追加
                </button>

                <div className={styles.formGroup}>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.userAccounts.obfuscatePasswords}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        userAccounts: { ...prev.userAccounts, obfuscatePasswords: e.target.checked }
                      }))}
                    />
                    XMLのパスワードをBase64で難読化
                  </label>
                </div>
              </div>
            )}

            {/* 11. システム調整 */}
            {activeSection === 'systemTweaks' && (
              <div className={styles.section}>
                <h3>🔧 システム調整</h3>
                
                <div className={styles.tweakGrid}>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.systemTweaks.disableDefender}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        systemTweaks: { ...prev.systemTweaks, disableDefender: e.target.checked }
                      }))}
                    />
                    Windows Defenderを無効化
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.systemTweaks.disableWindowsUpdate}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        systemTweaks: { ...prev.systemTweaks, disableWindowsUpdate: e.target.checked }
                      }))}
                    />
                    Windows Updateを無効化
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.systemTweaks.disableUAC}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        systemTweaks: { ...prev.systemTweaks, disableUAC: e.target.checked }
                      }))}
                    />
                    UACを無効化
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.systemTweaks.enableLongPaths}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        systemTweaks: { ...prev.systemTweaks, enableLongPaths: e.target.checked }
                      }))}
                    />
                    長いパスを有効化
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.systemTweaks.enableRDP}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        systemTweaks: { ...prev.systemTweaks, enableRDP: e.target.checked }
                      }))}
                    />
                    リモートデスクトップを有効化
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.systemTweaks.disableSystemSounds}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        systemTweaks: { ...prev.systemTweaks, disableSystemSounds: e.target.checked }
                      }))}
                    />
                    システムサウンドをオフ
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.systemTweaks.preventDeviceEncryption}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        systemTweaks: { ...prev.systemTweaks, preventDeviceEncryption: e.target.checked }
                      }))}
                    />
                    デバイスの暗号化を防止
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.systemTweaks.removeWindowsOld}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        systemTweaks: { ...prev.systemTweaks, removeWindowsOld: e.target.checked }
                      }))}
                    />
                    Windows.oldフォルダを削除
                  </label>
                </div>
              </div>
            )}

            {/* 20. 不要なアプリの削除 */}
            {activeSection === 'removeApps' && (
              <div className={styles.section}>
                <h3>🗑️ 不要なアプリの削除</h3>
                
                <div className={styles.appGrid}>
                  {REMOVABLE_APPS.map(app => (
                    <label key={app} className={styles.appItem}>
                      <input 
                        type="checkbox"
                        checked={config.removeApps.includes(app)}
                        onChange={() => toggleApp(app)}
                      />
                      {app}
                    </label>
                  ))}
                </div>
                
                <div className={styles.appActions}>
                  <button 
                    onClick={() => setConfig(prev => ({ ...prev, removeApps: REMOVABLE_APPS }))}
                    className={styles.selectAllButton}
                  >
                    すべて選択
                  </button>
                  <button 
                    onClick={() => setConfig(prev => ({ ...prev, removeApps: [] }))}
                    className={styles.clearButton}
                  >
                    選択解除
                  </button>
                </div>
              </div>
            )}

            {/* 9. エクスプローラー調整 */}
            {activeSection === 'explorerSettings' && (
              <div className={styles.section}>
                <h3>📁 エクスプローラー調整</h3>
                
                <div className={styles.checkboxGroup}>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.explorerSettings.showExtensions}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        explorerSettings: { ...prev.explorerSettings, showExtensions: e.target.checked }
                      }))}
                    />
                    ファイル拡張子を表示
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.explorerSettings.showHiddenFiles === 'all'}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        explorerSettings: { ...prev.explorerSettings, showHiddenFiles: e.target.checked ? 'all' : 'default' }
                      }))}
                    />
                    隠しファイルを表示
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.explorerSettings.classicContextMenu}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        explorerSettings: { ...prev.explorerSettings, classicContextMenu: e.target.checked }
                      }))}
                    />
                    クラシックコンテキストメニュー
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.explorerSettings.defaultToThisPC}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        explorerSettings: { ...prev.explorerSettings, defaultToThisPC: e.target.checked }
                      }))}
                    />
                    クイックアクセスの代わりにPCを開く
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.explorerSettings.showTaskKill}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        explorerSettings: { ...prev.explorerSettings, showTaskKill: e.target.checked }
                      }))}
                    />
                    タスク終了オプションを表示
                  </label>
                </div>
              </div>
            )}

            {/* 10. スタート/タスクバー */}
            {activeSection === 'startTaskbar' && (
              <div className={styles.section}>
                <h3>📱 スタート/タスクバー</h3>
                
                <div className={styles.checkboxGroup}>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.startTaskbar.alignLeft}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        startTaskbar: { ...prev.startTaskbar, alignLeft: e.target.checked }
                      }))}
                    />
                    タスクバーを左寄せ（Windows 10スタイル）
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.startTaskbar.searchBox === 'hidden'}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        startTaskbar: { ...prev.startTaskbar, searchBox: e.target.checked ? 'hidden' : 'icon' }
                      }))}
                    />
                    検索ボックスを非表示
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.startTaskbar.hideTaskView}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        startTaskbar: { ...prev.startTaskbar, hideTaskView: e.target.checked }
                      }))}
                    />
                    タスクビューボタンを非表示
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.startTaskbar.disableWidgets}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        startTaskbar: { ...prev.startTaskbar, disableWidgets: e.target.checked }
                      }))}
                    />
                    ウィジェットボタンを非表示
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.startTaskbar.disableBingSearch}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        startTaskbar: { ...prev.startTaskbar, disableBingSearch: e.target.checked }
                      }))}
                    />
                    Bing検索を無効化
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.startTaskbar.showAllTrayIcons}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        startTaskbar: { ...prev.startTaskbar, showAllTrayIcons: e.target.checked }
                      }))}
                    />
                    すべてのトレイアイコンを表示
                  </label>
                </div>
              </div>
            )}

            {/* 12. 視覚効果 */}
            {activeSection === 'visualEffects' && (
              <div className={styles.section}>
                <h3>🎨 視覚効果</h3>
                
                <div className={styles.formGroup}>
                  <label>視覚効果の設定</label>
                  <div className={styles.radioGroup}>
                    <label>
                      <input 
                        type="radio"
                        value="default"
                        checked={config.visualEffects === 'default'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          visualEffects: 'default' as const
                        }))}
                      />
                      デフォルト
                    </label>
                    <label>
                      <input 
                        type="radio"
                        value="bestAppearance"
                        checked={config.visualEffects === 'bestAppearance'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          visualEffects: 'bestAppearance' as const
                        }))}
                      />
                      最高の外観
                    </label>
                    <label>
                      <input 
                        type="radio"
                        value="bestPerformance"
                        checked={config.visualEffects === 'bestPerformance'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          visualEffects: 'bestPerformance' as const
                        }))}
                      />
                      パフォーマンス優先
                    </label>
                    <label>
                      <input 
                        type="radio"
                        value="custom"
                        checked={config.visualEffects === 'custom'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          visualEffects: 'custom' as const
                        }))}
                      />
                      カスタム
                    </label>
                  </div>
                </div>
              </div>
            )}

            {/* 13. デスクトップ設定 */}
            {activeSection === 'desktopSettings' && (
              <DesktopConfigSection
                config={config.desktopSettings}
                onChange={(newDesktopSettings) => setConfig(prev => ({
                  ...prev,
                  desktopSettings: newDesktopSettings
                }))}
              />
            )}

            {/* 14. 仮想マシンサポート */}
            {activeSection === 'vmSupport' && (
              <div className={styles.section}>
                <h3>🖲️ 仮想マシンサポート</h3>
                
                <div className={styles.checkboxGroup}>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.vmSupport.virtualBox}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        vmSupport: { ...prev.vmSupport, virtualBox: e.target.checked }
                      }))}
                    />
                    VirtualBox Guest Additions
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.vmSupport.vmwareTools}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        vmSupport: { ...prev.vmSupport, vmwareTools: e.target.checked }
                      }))}
                    />
                    VMware Tools
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.vmSupport.virtIO}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        vmSupport: { ...prev.vmSupport, virtIO: e.target.checked }
                      }))}
                    />
                    VirtIO ドライバー（KVM/QEMU）
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.vmSupport.parallelsTools}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        vmSupport: { ...prev.vmSupport, parallelsTools: e.target.checked }
                      }))}
                    />
                    Parallels Tools
                  </label>
                </div>

                <div className={styles.infoBox}>
                  <h4>💡 仮想マシンツールについて</h4>
                  <ul>
                    <li>使用している仮想化ソフトウェアに対応するツールを選択してください</li>
                    <li>これらのツールは仮想マシン内でのパフォーマンスと機能を向上させます</li>
                    <li>物理マシンにインストールする場合は選択不要です</li>
                  </ul>
                </div>
              </div>
            )}

            {/* 15. Wi-Fi設定 */}
            {activeSection === 'wifiSettings' && (
              <WiFiConfigSection
                config={config.wifiSettings}
                onChange={(wifiConfig) => setConfig(prev => ({
                  ...prev,
                  wifiSettings: wifiConfig
                }))}
              />
            )}

            {/* 16. Express Settings */}
            {activeSection === 'expressSettings' && (
              <div className={styles.section}>
                <h3>⚡ Express Settings</h3>
                
                <div className={styles.formGroup}>
                  <label>Express設定の処理</label>
                  <div className={styles.radioGroup}>
                    <label>
                      <input 
                        type="radio"
                        value="all_enabled"
                        checked={config.expressSettings === 'all_enabled'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          expressSettings: 'all_enabled'
                        }))}
                      />
                      すべて有効（推奨）
                    </label>
                    <label>
                      <input 
                        type="radio"
                        value="all_disabled"
                        checked={config.expressSettings === 'all_disabled'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          expressSettings: 'all_disabled'
                        }))}
                      />
                      すべて無効（プライバシー重視）
                    </label>
                    <label>
                      <input 
                        type="radio"
                        value="manual"
                        checked={config.expressSettings === 'manual'}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          expressSettings: 'manual'
                        }))}
                      />
                      手動設定
                    </label>
                  </div>
                </div>

                <div className={styles.infoBox}>
                  <h4>💡 Express Settingsについて</h4>
                  <p>Windows 11のプライバシー設定やテレメトリー、Cortana、OneDriveなどの初期設定をまとめて制御します。</p>
                </div>
              </div>
            )}

            {/* 17. ロックキー設定 */}
            {activeSection === 'lockKeys' && (
              <div className={styles.section}>
                <h3>⌨️ ロックキー設定</h3>
                
                <div className={styles.formGroup}>
                  <h4>NumLock</h4>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.lockKeys.numLock.initial}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        lockKeys: { ...prev.lockKeys, numLock: { ...prev.lockKeys.numLock, initial: e.target.checked } }
                      }))}
                    />
                    起動時にオン
                  </label>
                </div>

                <div className={styles.formGroup}>
                  <h4>CapsLock</h4>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.lockKeys.capsLock.initial}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        lockKeys: { ...prev.lockKeys, capsLock: { ...prev.lockKeys.capsLock, initial: e.target.checked } }
                      }))}
                    />
                    起動時にオン
                  </label>
                </div>

                <div className={styles.formGroup}>
                  <h4>ScrollLock</h4>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.lockKeys.scrollLock.initial}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        lockKeys: { ...prev.lockKeys, scrollLock: { ...prev.lockKeys.scrollLock, initial: e.target.checked } }
                      }))}
                    />
                    起動時にオン
                  </label>
                </div>
              </div>
            )}

            {/* 18. 固定キー */}
            {activeSection === 'stickyKeys' && (
              <div className={styles.section}>
                <h3>🔒 固定キー</h3>
                
                <div className={styles.checkboxGroup}>
                  <label>
                    <input 
                      type="checkbox"
                      checked={!config.stickyKeys.disabled}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        stickyKeys: { 
                          disabled: !e.target.checked,
                          options: !e.target.checked ? undefined : {
                            triplePress: false,
                            beep: false,
                            showStatus: false
                          }
                        }
                      }))}
                    />
                    固定キー機能を有効化
                  </label>
                </div>

                {!config.stickyKeys.disabled && (
                  <div className={styles.checkboxGroup}>
                    <label>
                      <input 
                        type="checkbox"
                        checked={config.stickyKeys.options?.triplePress || false}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          stickyKeys: { 
                            ...prev.stickyKeys,
                            options: {
                              ...prev.stickyKeys.options,
                              triplePress: e.target.checked,
                              beep: prev.stickyKeys.options?.beep || false,
                              showStatus: prev.stickyKeys.options?.showStatus || false
                            }
                          }
                        }))}
                      />
                      Shiftを3回押して有効/無効を切り替え
                    </label>
                    <label>
                      <input 
                        type="checkbox"
                        checked={config.stickyKeys.options?.beep || false}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          stickyKeys: { 
                            ...prev.stickyKeys,
                            options: {
                              ...prev.stickyKeys.options,
                              triplePress: prev.stickyKeys.options?.triplePress || false,
                              beep: e.target.checked,
                              showStatus: prev.stickyKeys.options?.showStatus || false
                            }
                          }
                        }))}
                      />
                      固定キー使用時に音を鳴らす
                    </label>
                    <label>
                      <input 
                        type="checkbox"
                        checked={config.stickyKeys.options?.showStatus || false}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          stickyKeys: { 
                            ...prev.stickyKeys,
                            options: {
                              ...prev.stickyKeys.options,
                              triplePress: prev.stickyKeys.options?.triplePress || false,
                              beep: prev.stickyKeys.options?.beep || false,
                              showStatus: e.target.checked
                            }
                          }
                        }))}
                      />
                      ステータスを表示
                    </label>
                  </div>
                )}

                <div className={styles.infoBox}>
                  <h4>💡 固定キーとは</h4>
                  <p>Shift、Ctrl、Alt、Windowsキーを一度押すと押したままの状態になる機能です。複数キーの同時押しが困難な場合に便利です。</p>
                </div>
              </div>
            )}

            {/* 19. 個人用設定 */}
            {activeSection === 'personalization' && (
              <div className={styles.section}>
                <h3>🎭 個人用設定</h3>
                
                <div className={styles.formGroup}>
                  <label>アクセントカラー</label>
                  <input 
                    type="color"
                    value={config.personalization.accentColor || '#0078D4'}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      personalization: { ...prev.personalization, accentColor: e.target.value }
                    }))}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label>デスクトップ壁紙（パス）</label>
                  <input 
                    type="text"
                    placeholder="C:\\Windows\\Web\\Wallpaper\\Windows\\img0.jpg"
                    value={config.personalization.desktopWallpaper || ''}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      personalization: { ...prev.personalization, desktopWallpaper: e.target.value }
                    }))}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label>ロック画面画像（パス）</label>
                  <input 
                    type="text"
                    placeholder="C:\\Windows\\Web\\Screen\\img100.jpg"
                    value={config.personalization.lockScreenImage || ''}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      personalization: { ...prev.personalization, lockScreenImage: e.target.value }
                    }))}
                  />
                </div>

                <div className={styles.infoBox}>
                  <h4>💡 画像パスについて</h4>
                  <p>空欄の場合はWindows 11のデフォルト画像が使用されます。カスタム画像を使用する場合は、インストール後に存在するパスを指定してください。</p>
                </div>
              </div>
            )}

            {/* 21. カスタムスクリプト */}
            {activeSection === 'customScripts' && (
              <div className={styles.section}>
                <h3>📝 カスタムスクリプト</h3>
                
                <div className={styles.formGroup}>
                  <label>システムコンテキストで実行するスクリプト</label>
                  <textarea 
                    rows={5}
                    placeholder="システム権限で実行するPowerShellスクリプト"
                    value={config.customScripts.system || ''}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      customScripts: { ...prev.customScripts, system: e.target.value }
                    }))}
                    style={{ fontFamily: 'monospace' }}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label>初回ログオン時に実行するスクリプト</label>
                  <textarea 
                    rows={5}
                    placeholder="最初のログオン時に実行するPowerShellスクリプト"
                    value={config.customScripts.firstLogon || ''}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      customScripts: { ...prev.customScripts, firstLogon: e.target.value }
                    }))}
                    style={{ fontFamily: 'monospace' }}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label>ユーザー初回実行時スクリプト</label>
                  <textarea 
                    rows={5}
                    placeholder="各ユーザーの初回実行時に実行するスクリプト"
                    value={config.customScripts.userFirstRun || ''}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      customScripts: { ...prev.customScripts, userFirstRun: e.target.value }
                    }))}
                    style={{ fontFamily: 'monospace' }}
                  />
                </div>

                <div className={styles.formGroup}>
                  <label>コマンドライン</label>
                  <input 
                    type="text"
                    placeholder="実行するコマンドライン"
                    value={config.customScripts.commandLine || ''}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      customScripts: { ...prev.customScripts, commandLine: e.target.value }
                    }))}
                  />
                </div>

                <div className={styles.checkboxGroup}>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.customScripts.restartExplorer}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        customScripts: { ...prev.customScripts, restartExplorer: e.target.checked }
                      }))}
                    />
                    スクリプト実行後にExplorerを再起動
                  </label>
                </div>

                <div className={styles.infoBox}>
                  <h4>💡 スクリプトの実行タイミング</h4>
                  <ul>
                    <li>システム: システム権限で実行（最も高い権限）</li>
                    <li>初回ログオン: 最初のユーザーログオン時に実行</li>
                    <li>ユーザー初回: 各ユーザーの初回実行時</li>
                  </ul>
                </div>
              </div>
            )}

            {/* 22. WDAC設定 */}
            {activeSection === 'wdac' && (
              <div className={styles.section}>
                <h3>🛡️ WDAC設定（Windows Defender Application Control）</h3>
                
                <div className={styles.checkboxGroup}>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.wdac.enabled}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        wdac: { ...prev.wdac, enabled: e.target.checked }
                      }))}
                    />
                    WDACを有効化
                  </label>
                </div>

                {config.wdac.enabled && (
                  <>
                    <div className={styles.formGroup}>
                      <label>実行モード</label>
                      <div className={styles.radioGroup}>
                        <label>
                          <input 
                            type="radio"
                            value="audit"
                            checked={config.wdac.mode === 'audit'}
                            onChange={(e) => setConfig(prev => ({
                              ...prev,
                              wdac: { ...prev.wdac, mode: 'audit' as const }
                            }))}
                          />
                          監査モード（ログのみ）
                        </label>
                        <label>
                          <input 
                            type="radio"
                            value="enforce"
                            checked={config.wdac.mode === 'enforce'}
                            onChange={(e) => setConfig(prev => ({
                              ...prev,
                              wdac: { ...prev.wdac, mode: 'enforce' as const }
                            }))}
                          />
                          強制モード（ブロック）
                        </label>
                      </div>
                    </div>

                    <div className={styles.formGroup}>
                      <label>スクリプト制限</label>
                      <div className={styles.radioGroup}>
                        <label>
                          <input 
                            type="radio"
                            value="restricted"
                            checked={config.wdac.scriptRestriction === 'restricted'}
                            onChange={(e) => setConfig(prev => ({
                              ...prev,
                              wdac: { ...prev.wdac, scriptRestriction: 'restricted' as const }
                            }))}
                          />
                          制限付き
                        </label>
                        <label>
                          <input 
                            type="radio"
                            value="unrestricted"
                            checked={config.wdac.scriptRestriction === 'unrestricted'}
                            onChange={(e) => setConfig(prev => ({
                              ...prev,
                              wdac: { ...prev.wdac, scriptRestriction: 'unrestricted' as const }
                            }))}
                          />
                          制限なし
                        </label>
                      </div>
                    </div>
                  </>
                )}

                <div className={styles.infoBox}>
                  <h4>⚠️ 注意</h4>
                  <p>WDACはエンタープライズセキュリティ機能です。誤った設定により、正規のアプリケーションがブロックされる可能性があります。</p>
                </div>
              </div>
            )}

            {/* 23. その他のコンポーネント */}
            {activeSection === 'additionalComponents' && (
              <div className={styles.section}>
                <h3>🧩 その他のコンポーネント</h3>
                
                <div className={styles.checkboxGroup}>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.additionalComponents.includeAllComponents}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        additionalComponents: { ...prev.additionalComponents, includeAllComponents: e.target.checked }
                      }))}
                    />
                    すべてのコンポーネントを含める
                  </label>
                  <label>
                    <input 
                      type="checkbox"
                      checked={config.additionalComponents.replaceGeneratorComponents}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        additionalComponents: { ...prev.additionalComponents, replaceGeneratorComponents: e.target.checked }
                      }))}
                    />
                    ジェネレーターコンポーネントを置き換える
                  </label>
                </div>

                <div className={styles.formGroup}>
                  <label>カスタムXML設定</label>
                  <textarea 
                    rows={10}
                    placeholder="追加のXML設定を入力（上級者向け）"
                    value={config.additionalComponents.customXml || ''}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      additionalComponents: { ...prev.additionalComponents, customXml: e.target.value }
                    }))}
                    style={{ fontFamily: 'monospace' }}
                  />
                </div>

                <div className={styles.infoBox}>
                  <h4>💡 カスタムXMLについて</h4>
                  <p>高度な設定が必要な場合のみ使用してください。無効なXMLを入力すると、Sysprepが失敗する可能性があります。</p>
                </div>
              </div>
            )}

          </div>
        </div>

        {/* 生成ボタン */}
        <div className={styles.generateSection}>
          {error && (
            <ErrorDisplay 
              error={error} 
              sessionId={sessionId || undefined} 
              onDownloadLogs={sessionId ? async (format) => {
                try {
                  await apiClient.downloadGenerationLogs(sessionId, format)
                } catch (err) {
                  console.error('ログダウンロードエラー:', err)
                  alert('ログのダウンロードに失敗しました')
                }
              } : undefined}
            />
          )}
          
          <div className={styles.generateButtons}>
            <button 
              onClick={() => generateXML(false)}
              disabled={generating}
              className={styles.generateButton}
            >
              {generating ? '⏳ 生成中...' : '📥 XMLのみダウンロード'}
            </button>
            
            <button 
              onClick={() => generateXML(true)}
              disabled={generating}
              className={`${styles.generateButton} ${styles.withLog}`}
            >
              {generating ? '⏳ 生成中...' : '📦 XML + 設定ログをダウンロード'}
            </button>
          </div>

          <div className={styles.generateInfo}>
            <p>✅ Windows 11完全対応</p>
            <p>✅ 日本語環境最適化</p>
            <p>✅ 企業向け大規模展開対応</p>
          </div>
        </div>
      </main>

      {/* フッター */}
      <footer className={styles.footer}>
        <p>Windows 11 無人応答ファイル生成システム v2.0.0</p>
        <p>© 2024 Windows Sysprep Automation Tool</p>
      </footer>
    </div>
  )
}