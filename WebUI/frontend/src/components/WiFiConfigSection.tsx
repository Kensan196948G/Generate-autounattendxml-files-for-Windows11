import React, { useState } from 'react';
import styles from '../styles/Home.module.css';

interface WiFiProfile {
  ssid: string;
  auth_type: 'WPA2PSK' | 'WPA3PSK';
  password: string;
  connect_automatically: boolean;
  connect_even_if_hidden: boolean;
  priority: number;
}

interface WiFiConfig {
  setup_mode: 'interactive' | 'skip' | 'configure';
  profiles: WiFiProfile[];
  enable_wifi_sense: boolean;
  connect_to_suggested_hotspots: boolean;
}

interface WiFiConfigSectionProps {
  config: WiFiConfig;
  onChange: (config: WiFiConfig) => void;
}

const WiFiConfigSection: React.FC<WiFiConfigSectionProps> = ({ config, onChange }) => {
  const [showPassword, setShowPassword] = useState(false);

  // デフォルト設定
  const defaultProfile: WiFiProfile = {
    ssid: '20mirai18',
    auth_type: 'WPA2PSK',
    password: '20m!ra!18',
    connect_automatically: true,
    connect_even_if_hidden: false,
    priority: 1
  };

  // 初期設定
  if (!config.profiles || config.profiles.length === 0) {
    config = {
      ...config,
      profiles: [defaultProfile]
    };
  }

  const handleSetupModeChange = (mode: 'interactive' | 'skip' | 'configure') => {
    onChange({
      ...config,
      setup_mode: mode
    });
  };

  const handleProfileChange = (index: number, field: keyof WiFiProfile, value: any) => {
    const newProfiles = [...config.profiles];
    newProfiles[index] = {
      ...newProfiles[index],
      [field]: value
    };
    onChange({
      ...config,
      profiles: newProfiles
    });
  };

  const handleAuthTypeChange = (index: number, authType: 'WPA2PSK' | 'WPA3PSK') => {
    handleProfileChange(index, 'auth_type', authType);
  };

  const handleConnectHiddenChange = (index: number, checked: boolean) => {
    handleProfileChange(index, 'connect_even_if_hidden', checked);
  };

  return (
    <div className={styles.configSection}>
      <h3>15. Wi-Fi設定</h3>
      
      <div className={styles.formGroup}>
        <label className={styles.label}>Wi-Fiセットアップモード</label>
        <div className={styles.radioGroup}>
          <label className={styles.radioLabel}>
            <input
              type="radio"
              name="wifi-setup-mode"
              value="interactive"
              checked={config.setup_mode === 'interactive'}
              onChange={() => handleSetupModeChange('interactive')}
            />
            <span>Windows セットアップ中に対話形式で Wi-Fi を構成する</span>
          </label>
          
          <label className={styles.radioLabel}>
            <input
              type="radio"
              name="wifi-setup-mode"
              value="skip"
              checked={config.setup_mode === 'skip'}
              onChange={() => handleSetupModeChange('skip')}
            />
            <span>Wi-Fi 設定をスキップする（有線接続の場合）</span>
            <div className={styles.helperText}>
              インターネットに有線接続している場合は、これを選択します。
            </div>
          </label>
          
          <label className={styles.radioLabel}>
            <input
              type="radio"
              name="wifi-setup-mode"
              value="configure"
              checked={config.setup_mode === 'configure'}
              onChange={() => handleSetupModeChange('configure')}
            />
            <span>次の設定を使用して Wi-Fi を構成します</span>
          </label>
        </div>
      </div>

      {config.setup_mode === 'configure' && (
        <div className={styles.wifiConfigDetails}>
          {config.profiles.map((profile, index) => (
            <div key={index} className={styles.profileSection}>
              <div className={styles.formGroup}>
                <label className={styles.label}>ネットワーク名(SSID)</label>
                <input
                  type="text"
                  className={styles.input}
                  value={profile.ssid}
                  readOnly
                  style={{ backgroundColor: '#f0f0f0' }}
                />
                <div className={styles.helperText}>
                  * 20mirai18は固定値です
                </div>
              </div>

              <div className={styles.formGroup}>
                <label className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={profile.connect_even_if_hidden}
                    onChange={(e) => handleConnectHiddenChange(index, e.target.checked)}
                  />
                  <span>ブロードキャストしていなくても接続します</span>
                </label>
              </div>

              <div className={styles.formGroup}>
                <label className={styles.label}>認証</label>
                <select
                  className={styles.select}
                  value={profile.auth_type}
                  onChange={(e) => handleAuthTypeChange(index, e.target.value as 'WPA2PSK' | 'WPA3PSK')}
                >
                  <option value="WPA2PSK">WPA2</option>
                  <option value="WPA3PSK">WPA3</option>
                </select>
                <div className={styles.helperText}>
                  Wi-Fi ルーターとコンピューターの Wi-Fi アダプターの両方がサポートしている場合は、必ず WPA3 を選択してください。
                </div>
              </div>

              <div className={styles.formGroup}>
                <label className={styles.label}>パスワード</label>
                <div className={styles.passwordInputWrapper}>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    className={styles.input}
                    value={profile.password}
                    onChange={(e) => handleProfileChange(index, 'password', e.target.value)}
                  />
                  <button
                    type="button"
                    className={styles.passwordToggle}
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? '隠す' : '表示'}
                  </button>
                </div>
                <div className={styles.helperText}>
                  デフォルト: 20m!ra!18
                </div>
              </div>

              <div className={styles.formGroup}>
                <label className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    checked={profile.connect_automatically}
                    onChange={(e) => handleProfileChange(index, 'connect_automatically', e.target.checked)}
                  />
                  <span>自動的に接続する</span>
                </label>
              </div>
            </div>
          ))}

          <div className={styles.additionalSettings}>
            <h4>追加設定</h4>
            
            <div className={styles.formGroup}>
              <label className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={config.enable_wifi_sense}
                  onChange={(e) => onChange({
                    ...config,
                    enable_wifi_sense: e.target.checked
                  })}
                />
                <span>Wi-Fiセンスを有効にする</span>
              </label>
              <div className={styles.helperText}>
                連絡先と共有されたネットワークに自動的に接続します
              </div>
            </div>

            <div className={styles.formGroup}>
              <label className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={config.connect_to_suggested_hotspots}
                  onChange={(e) => onChange({
                    ...config,
                    connect_to_suggested_hotspots: e.target.checked
                  })}
                />
                <span>推奨されるオープンホットスポットに接続する</span>
              </label>
              <div className={styles.helperText}>
                Microsoftが推奨する公共Wi-Fiホットスポットに自動接続します
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WiFiConfigSection;