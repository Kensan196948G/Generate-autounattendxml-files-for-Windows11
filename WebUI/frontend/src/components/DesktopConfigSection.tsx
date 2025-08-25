import React from 'react';
import styles from '../styles/Home.module.css';

interface DesktopIconSettings {
  show_this_pc: boolean;
  show_user_files: boolean;
  show_network: boolean;
  show_recycle_bin: boolean;
  show_control_panel: boolean;
}

interface StartMenuSettings {
  show_documents: boolean;
  show_downloads: boolean;
  show_music: boolean;
  show_pictures: boolean;
  show_videos: boolean;
  show_network: boolean;
  show_personal_folder: boolean;
  show_file_explorer: boolean;
  show_settings: boolean;
  show_recently_added_apps: boolean;
  show_most_used_apps: boolean;
  show_suggestions: boolean;
}

interface DesktopConfig {
  desktop_icons: DesktopIconSettings;
  start_menu: StartMenuSettings;
}

interface DesktopConfigSectionProps {
  config: DesktopConfig;
  onChange: (config: DesktopConfig) => void;
}

const DesktopConfigSection: React.FC<DesktopConfigSectionProps> = ({ config, onChange }) => {
  // デフォルト設定
  if (!config.desktop_icons) {
    config = {
      ...config,
      desktop_icons: {
        show_this_pc: true,
        show_user_files: true,
        show_network: false,
        show_recycle_bin: true,
        show_control_panel: false
      }
    };
  }
  
  if (!config.start_menu) {
    config = {
      ...config,
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
    };
  }

  const handleDesktopIconChange = (field: keyof DesktopIconSettings, checked: boolean) => {
    onChange({
      ...config,
      desktop_icons: {
        ...config.desktop_icons,
        [field]: checked
      }
    });
  };

  const handleStartMenuChange = (field: keyof StartMenuSettings, checked: boolean) => {
    onChange({
      ...config,
      start_menu: {
        ...config.start_menu,
        [field]: checked
      }
    });
  };

  return (
    <div className={styles.configSection}>
      <h3>13. デスクトップ設定</h3>
      
      <div className={styles.settingsGroup}>
        <h4>デフォルトデスクトップアイコンを表示</h4>
        <div className={styles.checkboxGrid}>
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={config.desktop_icons.show_this_pc}
              onChange={(e) => handleDesktopIconChange('show_this_pc', e.target.checked)}
            />
            <span>このPC</span>
          </label>
          
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={config.desktop_icons.show_user_files}
              onChange={(e) => handleDesktopIconChange('show_user_files', e.target.checked)}
            />
            <span>ユーザーファイル</span>
          </label>
          
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={config.desktop_icons.show_network}
              onChange={(e) => handleDesktopIconChange('show_network', e.target.checked)}
            />
            <span>ネットワーク</span>
          </label>
          
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={config.desktop_icons.show_recycle_bin}
              onChange={(e) => handleDesktopIconChange('show_recycle_bin', e.target.checked)}
            />
            <span>ごみ箱</span>
          </label>
          
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={config.desktop_icons.show_control_panel}
              onChange={(e) => handleDesktopIconChange('show_control_panel', e.target.checked)}
            />
            <span>コントロールパネル</span>
          </label>
        </div>
      </div>

      <div className={styles.settingsGroup}>
        <h4>スタートメニューに標準フォルダを表示</h4>
        <div className={styles.checkboxGrid}>
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={config.start_menu.show_documents}
              onChange={(e) => handleStartMenuChange('show_documents', e.target.checked)}
            />
            <span>ドキュメント</span>
          </label>
          
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={config.start_menu.show_downloads}
              onChange={(e) => handleStartMenuChange('show_downloads', e.target.checked)}
            />
            <span>ダウンロード</span>
          </label>
          
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={config.start_menu.show_music}
              onChange={(e) => handleStartMenuChange('show_music', e.target.checked)}
            />
            <span>ミュージック</span>
          </label>
          
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={config.start_menu.show_pictures}
              onChange={(e) => handleStartMenuChange('show_pictures', e.target.checked)}
            />
            <span>ピクチャ</span>
          </label>
          
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={config.start_menu.show_videos}
              onChange={(e) => handleStartMenuChange('show_videos', e.target.checked)}
            />
            <span>ビデオ</span>
          </label>
          
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={config.start_menu.show_network}
              onChange={(e) => handleStartMenuChange('show_network', e.target.checked)}
            />
            <span>ネットワーク</span>
          </label>
          
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={config.start_menu.show_personal_folder}
              onChange={(e) => handleStartMenuChange('show_personal_folder', e.target.checked)}
            />
            <span>個人用フォルダー</span>
          </label>
          
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={config.start_menu.show_file_explorer}
              onChange={(e) => handleStartMenuChange('show_file_explorer', e.target.checked)}
            />
            <span>ファイルエクスプローラー</span>
          </label>
          
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={config.start_menu.show_settings}
              onChange={(e) => handleStartMenuChange('show_settings', e.target.checked)}
            />
            <span>設定</span>
          </label>
        </div>
        
        <div className={styles.additionalSettings}>
          <h5>追加のスタートメニュー設定</h5>
          
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={config.start_menu.show_recently_added_apps}
              onChange={(e) => handleStartMenuChange('show_recently_added_apps', e.target.checked)}
            />
            <span>最近追加したアプリを表示</span>
          </label>
          
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={config.start_menu.show_most_used_apps}
              onChange={(e) => handleStartMenuChange('show_most_used_apps', e.target.checked)}
            />
            <span>よく使うアプリを表示</span>
          </label>
          
          <label className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={!config.start_menu.show_suggestions}
              onChange={(e) => handleStartMenuChange('show_suggestions', !e.target.checked)}
            />
            <span>おすすめを無効にする</span>
          </label>
        </div>
      </div>

      <div className={styles.presetButtons}>
        <button
          type="button"
          className={styles.presetButton}
          onClick={() => onChange({
            desktop_icons: {
              show_this_pc: true,
              show_user_files: false,
              show_network: false,
              show_recycle_bin: true,
              show_control_panel: false
            },
            start_menu: {
              show_documents: false,
              show_downloads: false,
              show_music: false,
              show_pictures: false,
              show_videos: false,
              show_network: false,
              show_personal_folder: false,
              show_file_explorer: true,
              show_settings: true,
              show_recently_added_apps: false,
              show_most_used_apps: false,
              show_suggestions: false
            }
          })}
        >
          最小構成
        </button>
        
        <button
          type="button"
          className={styles.presetButton}
          onClick={() => onChange({
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
          })}
        >
          標準構成
        </button>
        
        <button
          type="button"
          className={styles.presetButton}
          onClick={() => onChange({
            desktop_icons: {
              show_this_pc: true,
              show_user_files: true,
              show_network: true,
              show_recycle_bin: true,
              show_control_panel: true
            },
            start_menu: {
              show_documents: true,
              show_downloads: true,
              show_music: true,
              show_pictures: true,
              show_videos: true,
              show_network: true,
              show_personal_folder: true,
              show_file_explorer: true,
              show_settings: true,
              show_recently_added_apps: true,
              show_most_used_apps: true,
              show_suggestions: false
            }
          })}
        >
          フル構成
        </button>
      </div>
    </div>
  );
};

export default DesktopConfigSection;