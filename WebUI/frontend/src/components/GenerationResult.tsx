import React, { useState } from 'react';
import styles from '../styles/Home.module.css';

interface GenerationLog {
  summary: {
    generation_time: string;
    duration_seconds: number;
    success: boolean;
    xml_path: string;
    selected_items: any;
    error_count: number;
    warning_count: number;
    total_logs: number;
  };
  json: string;
  text: string;
  download_urls: {
    json: string;
    text: string;
  };
}

interface GenerationResultProps {
  success: boolean;
  message: string;
  xmlContent?: string;
  xmlPath?: string;
  generationId?: string;
  logs?: GenerationLog;
  error?: string;
  traceback?: string;
  onClose: () => void;
  _onDownloadXML?: () => void;
}

const GenerationResult: React.FC<GenerationResultProps> = ({
  success,
  message,
  xmlContent,
  xmlPath,
  generationId,
  logs,
  error,
  traceback,
  onClose,
  _onDownloadXML
}) => {
  const [showDetailedLog, setShowDetailedLog] = useState(false);
  const [selectedLogFormat, setSelectedLogFormat] = useState<'json' | 'text'>('text');
  const [showTraceback, setShowTraceback] = useState(false);

  const handleDownloadLog = async (format: 'json' | 'text') => {
    if (!generationId) return;

    try {
      const response = await fetch(
        `http://192.168.3.92:3050/api/xml/generation-log/${generationId}/download?format=${format}`
      );
      
      if (!response.ok) {
        throw new Error('ログのダウンロードに失敗しました');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `unattend_generation_${generationId}_log.${format === 'json' ? 'json' : 'txt'}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('ログダウンロードエラー:', err);
      alert('ログのダウンロードに失敗しました');
    }
  };

  const handleDownloadXML = () => {
    if (!xmlContent) return;

    const blob = new Blob([xmlContent], { type: 'text/xml' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `unattend_${generationId || 'generated'}.xml`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  return (
    <div className={styles.resultModal}>
      <div className={styles.resultModalContent}>
        <div className={styles.resultHeader}>
          <h2>{success ? '✅ 生成成功' : '❌ 生成失敗'}</h2>
          <button onClick={onClose} className={styles.closeButton}>×</button>
        </div>

        <div className={styles.resultBody}>
          <div className={styles.messageSection}>
            <p className={success ? styles.successMessage : styles.errorMessage}>
              {message}
            </p>
            {xmlPath && (
              <p className={styles.filePath}>
                <strong>保存先:</strong> {xmlPath}
              </p>
            )}
          </div>

          {/* エラー詳細セクション */}
          {!success && error && (
            <div className={styles.errorDetailsSection}>
              <h3>エラー詳細</h3>
              <div className={styles.errorDetails}>
                <pre>{error}</pre>
              </div>
              
              {traceback && (
                <div className={styles.tracebackSection}>
                  <button
                    onClick={() => setShowTraceback(!showTraceback)}
                    className={styles.toggleButton}
                  >
                    {showTraceback ? '▼' : '▶'} スタックトレースを表示
                  </button>
                  {showTraceback && (
                    <div className={styles.traceback}>
                      <pre>{traceback}</pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ログサマリーセクション */}
          {logs && (
            <div className={styles.logSummarySection}>
              <h3>生成ログサマリー</h3>
              <div className={styles.logSummary}>
                <div className={styles.summaryGrid}>
                  <div className={styles.summaryItem}>
                    <span className={styles.summaryLabel}>生成時刻:</span>
                    <span className={styles.summaryValue}>
                      {new Date(logs.summary.generation_time).toLocaleString('ja-JP')}
                    </span>
                  </div>
                  <div className={styles.summaryItem}>
                    <span className={styles.summaryLabel}>処理時間:</span>
                    <span className={styles.summaryValue}>
                      {logs.summary.duration_seconds.toFixed(2)}秒
                    </span>
                  </div>
                  <div className={styles.summaryItem}>
                    <span className={styles.summaryLabel}>総ログ数:</span>
                    <span className={styles.summaryValue}>{logs.summary.total_logs}</span>
                  </div>
                  <div className={styles.summaryItem}>
                    <span className={styles.summaryLabel}>エラー数:</span>
                    <span className={`${styles.summaryValue} ${logs.summary.error_count > 0 ? styles.errorCount : ''}`}>
                      {logs.summary.error_count}
                    </span>
                  </div>
                  <div className={styles.summaryItem}>
                    <span className={styles.summaryLabel}>警告数:</span>
                    <span className={`${styles.summaryValue} ${logs.summary.warning_count > 0 ? styles.warningCount : ''}`}>
                      {logs.summary.warning_count}
                    </span>
                  </div>
                </div>

                {/* 選択された設定項目 */}
                <div className={styles.selectedItemsSection}>
                  <h4>選択された設定項目</h4>
                  <ul className={styles.selectedItemsList}>
                    {Object.entries(logs.summary.selected_items).map(([key, value]) => (
                      <li key={key}>
                        <strong>{key}:</strong> {JSON.stringify(value, null, 2)}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* 詳細ログセクション */}
          {logs && (
            <div className={styles.detailedLogSection}>
              <div className={styles.logControls}>
                <button
                  onClick={() => setShowDetailedLog(!showDetailedLog)}
                  className={styles.toggleButton}
                >
                  {showDetailedLog ? '▼' : '▶'} 詳細ログを表示
                </button>
                
                {showDetailedLog && (
                  <div className={styles.logFormatSelector}>
                    <label>
                      <input
                        type="radio"
                        value="text"
                        checked={selectedLogFormat === 'text'}
                        onChange={(e) => setSelectedLogFormat(e.target.value as 'text')}
                      />
                      テキスト形式
                    </label>
                    <label>
                      <input
                        type="radio"
                        value="json"
                        checked={selectedLogFormat === 'json'}
                        onChange={(e) => setSelectedLogFormat(e.target.value as 'json')}
                      />
                      JSON形式
                    </label>
                  </div>
                )}
              </div>

              {showDetailedLog && (
                <div className={styles.detailedLog}>
                  <pre>
                    {selectedLogFormat === 'json' 
                      ? JSON.stringify(JSON.parse(logs.json), null, 2)
                      : logs.text}
                  </pre>
                </div>
              )}
            </div>
          )}

          {/* アクションボタン */}
          <div className={styles.actionButtons}>
            {success && xmlContent && (
              <button
                onClick={handleDownloadXML}
                className={`${styles.actionButton} ${styles.primaryButton}`}
              >
                📥 XMLファイルをダウンロード
              </button>
            )}
            
            {logs && (
              <>
                <button
                  onClick={() => handleDownloadLog('text')}
                  className={`${styles.actionButton} ${styles.secondaryButton}`}
                >
                  📄 ログをダウンロード (テキスト)
                </button>
                <button
                  onClick={() => handleDownloadLog('json')}
                  className={`${styles.actionButton} ${styles.secondaryButton}`}
                >
                  📊 ログをダウンロード (JSON)
                </button>
              </>
            )}
            
            <button
              onClick={onClose}
              className={`${styles.actionButton} ${styles.tertiaryButton}`}
            >
              閉じる
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GenerationResult;