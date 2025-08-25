/**
 * 包括的な設定型定義
 * 全23項目の設定を網羅
 */

export interface ComprehensiveConfig {
  // 1. 地域と言語の設定
  regionLanguage: {
    displayLanguage: string
    inputLocale: string
    systemLocale: string
    userLocale: string
    uiLanguage: string
    uiLanguageFallback: string
    timezone: string
    geoLocation: string
  }

  // 2. プロセッサー・アーキテクチャ
  architecture: 'amd64' | 'x86' | 'arm64'

  // 3. セットアップの挙動
  setupBehavior: {
    skipMachineOOBE: boolean
    skipUserOOBE: boolean
    hideEULAPage: boolean
    hideOEMRegistration: boolean
    hideOnlineAccountScreens: boolean
    hideWirelessSetup: boolean
    protectYourPC: number
    networkLocation: string
    skipDomainJoin: boolean
  }

  // 4. エディション/プロダクトキー
  windowsEdition: {
    edition: string
    productKey: string
    acceptEula: boolean
    installToAvailable: boolean
    willShowUI: string
  }

  // 5. Windows PE ステージ
  windowsPE: {
    disableCommandPrompt: boolean
    disableFirewall: boolean
    enableNetwork: boolean
    enableRemoteAssistance: boolean
    pageFile: string
    scratchSpace: number
  }

  // 6. ディスク構成
  diskConfig: {
    wipeDisk: boolean
    diskId: number
    partitionStyle: 'GPT' | 'MBR'
    partitions: Array<{
      type: string
      size: number | 'remaining'
      letter?: string
    }>
  }

  // 7. コンピューター設定
  computerSettings: {
    computerName: string
    organization: string
    owner: string
    joinDomain: boolean
    domain: string
    domainOU: string
    workgroup: string
  }

  // 8. ユーザーアカウント
  userAccounts: {
    accounts: Array<{
      name: string
      password: string
      displayName: string
      description: string
      group: string
      autoLogon: boolean
      passwordNeverExpires: boolean
    }>
    autoLogonCount: number
    disableAdminAccount: boolean
    enableGuestAccount: boolean
  }

  // 9. エクスプローラー調整
  explorerSettings: {
    showHiddenFiles: boolean
    showFileExtensions: boolean
    showProtectedOSFiles: boolean
    disableThumbnailCache: boolean
    disableThumbsDB: boolean
    launchTo: string
    navPaneExpand: boolean
    navPaneShowAll: boolean
  }

  // 10. スタート/タスクバー
  startTaskbar: {
    taskbarAlignment: string
    taskbarSearch: string
    taskbarWidgets: boolean
    taskbarChat: boolean
    taskbarTaskView: boolean
    startMenuLayout: string
    showRecentlyAdded: boolean
    showMostUsed: boolean
    showSuggestions: boolean
  }

  // 11. システム調整
  systemTweaks: {
    disableUAC: boolean
    disableSmartScreen: boolean
    disableDefender: boolean
    disableFirewall: boolean
    disableUpdates: boolean
    disableTelemetry: boolean
    disableCortana: boolean
    disableSearchWeb: boolean
    disableGameBar: boolean
    fastStartup: boolean
    hibernation: boolean
  }

  // 12. 視覚効果
  visualEffects: {
    performanceMode: string
    transparency: boolean
    animations: boolean
    shadows: boolean
    smoothEdges: boolean
    fontSmoothing: string
    wallpaperQuality: string
  }

  // 13. デスクトップ設定
  desktopSettings: {
    showComputer: boolean
    showUserFiles: boolean
    showNetwork: boolean
    showRecycleBin: boolean
    showControlPanel: boolean
    iconSize: string
    iconSpacing: string
    autoArrange: boolean
    alignToGrid: boolean
    wallpaper: string
    solidColor: string
  }

  // 14. 仮想マシンサポート
  vmSupport: {
    enableHyperV: boolean
    enableWSL: boolean
    enableWSL2: boolean
    enableSandbox: boolean
    enableContainers: boolean
    enableVirtualization: boolean
    nestedVirtualization: boolean
  }

  // 15. Wi-Fi設定
  wifiSettings: {
    setup_mode: 'skip' | 'configure' | 'manual'
    ssid?: string
    password?: string
    authType?: string
    encryption?: string
    connectAutomatically?: boolean
    connectEvenNotBroadcasting?: boolean
  }

  // 16. Express Settings
  expressSettings: {
    mode: 'default' | 'all_enabled' | 'all_disabled' | 'custom'
    sendDiagnosticData?: boolean
    improveInking?: boolean
    tailoredExperiences?: boolean
    advertisingId?: boolean
    locationServices?: boolean
    findMyDevice?: boolean
  }

  // 17. ロックキー設定
  lockKeys: {
    numLock: boolean
    capsLock: boolean
    scrollLock: boolean
  }

  // 18. 固定キー
  stickyKeys: {
    enabled: boolean
    lockModifier: boolean
    turnOffOnTwoKeys: boolean
    feedback: boolean
    beep: boolean
  }

  // 19. 個人用設定
  personalization: {
    theme: string
    accentColor: string
    startColor: boolean
    taskbarColor: boolean
    titleBarColor: boolean
    lockScreenImage: string
    userPicture: string
    soundsScheme: string
    mouseCursorScheme: string
  }

  // 20. 不要なアプリの削除
  removeApps: {
    apps: string[]
  }

  // 21. カスタムスクリプト
  customScripts: {
    firstLogon: Array<{
      order: number
      command: string
      description: string
      requiresRestart: boolean
    }>
    setupScripts: Array<{
      order: number
      path: string
      description: string
    }>
  }

  // 22. WDAC設定
  wdac: {
    enabled: boolean
    policyMode: string
    allowMicrosoftApps: boolean
    allowStoreApps: boolean
    allowReputableApps: boolean
    customRules: string[]
  }

  // 23. その他のコンポーネント
  additionalComponents: {
    dotnet35: boolean
    dotnet48: boolean
    iis: boolean
    telnetClient: boolean
    tftpClient: boolean
    smb1: boolean
    powershell2: boolean
    directPlay: boolean
    printToPDF: boolean
    xpsViewer: boolean
    mediaFeatures: boolean
    workFolders: boolean
  }
}

// デフォルト設定
export const defaultComprehensiveConfig: ComprehensiveConfig = {
  regionLanguage: {
    displayLanguage: 'ja-JP',
    inputLocale: '0411:00000411',
    systemLocale: 'ja-JP',
    userLocale: 'ja-JP',
    uiLanguage: 'ja-JP',
    uiLanguageFallback: 'en-US',
    timezone: 'Tokyo Standard Time',
    geoLocation: '122'
  },
  architecture: 'amd64',
  setupBehavior: {
    skipMachineOOBE: true,
    skipUserOOBE: false,
    hideEULAPage: true,
    hideOEMRegistration: true,
    hideOnlineAccountScreens: true,
    hideWirelessSetup: false,
    protectYourPC: 3,
    networkLocation: 'Work',
    skipDomainJoin: true
  },
  windowsEdition: {
    edition: 'Pro',
    productKey: 'VK7JG-NPHTM-C97JM-9MPGT-3V66T',
    acceptEula: true,
    installToAvailable: true,
    willShowUI: 'OnError'
  },
  windowsPE: {
    disableCommandPrompt: false,
    disableFirewall: true,
    enableNetwork: true,
    enableRemoteAssistance: false,
    pageFile: 'Auto',
    scratchSpace: 512
  },
  diskConfig: {
    wipeDisk: true,
    diskId: 0,
    partitionStyle: 'GPT',
    partitions: [
      { type: 'EFI', size: 100 },
      { type: 'MSR', size: 16 },
      { type: 'Primary', size: 'remaining', letter: 'C' },
      { type: 'Recovery', size: 500 }
    ]
  },
  computerSettings: {
    computerName: '*',
    organization: '',
    owner: '',
    joinDomain: false,
    domain: '',
    domainOU: '',
    workgroup: 'WORKGROUP'
  },
  userAccounts: {
    accounts: [{
      name: 'admin',
      password: 'P@ssw0rd123!',
      displayName: '管理者',
      description: '管理者アカウント',
      group: 'Administrators',
      autoLogon: false,
      passwordNeverExpires: true
    }],
    autoLogonCount: 0,
    disableAdminAccount: true,
    enableGuestAccount: false
  },
  explorerSettings: {
    showHiddenFiles: false,
    showFileExtensions: true,
    showProtectedOSFiles: false,
    disableThumbnailCache: false,
    disableThumbsDB: false,
    launchTo: 'ThisPC',
    navPaneExpand: true,
    navPaneShowAll: false
  },
  startTaskbar: {
    taskbarAlignment: 'Center',
    taskbarSearch: 'Icon',
    taskbarWidgets: false,
    taskbarChat: false,
    taskbarTaskView: true,
    startMenuLayout: 'Default',
    showRecentlyAdded: true,
    showMostUsed: true,
    showSuggestions: false
  },
  systemTweaks: {
    disableUAC: false,
    disableSmartScreen: false,
    disableDefender: false,
    disableFirewall: false,
    disableUpdates: false,
    disableTelemetry: true,
    disableCortana: true,
    disableSearchWeb: true,
    disableGameBar: true,
    fastStartup: false,
    hibernation: false
  },
  visualEffects: {
    performanceMode: 'Balanced',
    transparency: true,
    animations: true,
    shadows: true,
    smoothEdges: true,
    fontSmoothing: 'ClearType',
    wallpaperQuality: 'Fill'
  },
  desktopSettings: {
    showComputer: true,
    showUserFiles: true,
    showNetwork: false,
    showRecycleBin: true,
    showControlPanel: false,
    iconSize: 'Medium',
    iconSpacing: 'Default',
    autoArrange: false,
    alignToGrid: true,
    wallpaper: '',
    solidColor: ''
  },
  vmSupport: {
    enableHyperV: false,
    enableWSL: false,
    enableWSL2: false,
    enableSandbox: false,
    enableContainers: false,
    enableVirtualization: true,
    nestedVirtualization: false
  },
  wifiSettings: {
    setup_mode: 'configure',
    ssid: '20mirai18',
    password: '20m!ra!18',
    authType: 'WPA2PSK',
    encryption: 'AES',
    connectAutomatically: true,
    connectEvenNotBroadcasting: true
  },
  expressSettings: {
    mode: 'all_disabled',
    sendDiagnosticData: false,
    improveInking: false,
    tailoredExperiences: false,
    advertisingId: false,
    locationServices: false,
    findMyDevice: false
  },
  lockKeys: {
    numLock: true,
    capsLock: false,
    scrollLock: false
  },
  stickyKeys: {
    enabled: false,
    lockModifier: false,
    turnOffOnTwoKeys: true,
    feedback: false,
    beep: false
  },
  personalization: {
    theme: 'Light',
    accentColor: '0078D4',
    startColor: true,
    taskbarColor: true,
    titleBarColor: true,
    lockScreenImage: '',
    userPicture: '',
    soundsScheme: 'Windows Default',
    mouseCursorScheme: 'Windows Default'
  },
  removeApps: {
    apps: [
      'Microsoft.BingNews',
      'Microsoft.BingWeather',
      'Microsoft.GetHelp',
      'Microsoft.Getstarted',
      'Microsoft.MicrosoftSolitaireCollection',
      'Microsoft.People',
      'Microsoft.WindowsFeedbackHub',
      'Microsoft.YourPhone',
      'Microsoft.ZuneMusic',
      'Microsoft.ZuneVideo'
    ]
  },
  customScripts: {
    firstLogon: [],
    setupScripts: []
  },
  wdac: {
    enabled: false,
    policyMode: 'Audit',
    allowMicrosoftApps: true,
    allowStoreApps: true,
    allowReputableApps: false,
    customRules: []
  },
  additionalComponents: {
    dotnet35: false,
    dotnet48: true,
    iis: false,
    telnetClient: false,
    tftpClient: false,
    smb1: false,
    powershell2: false,
    directPlay: false,
    printToPDF: true,
    xpsViewer: false,
    mediaFeatures: true,
    workFolders: false
  }
}