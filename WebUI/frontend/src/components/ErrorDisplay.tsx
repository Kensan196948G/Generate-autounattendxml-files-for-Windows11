import React, { useState } from 'react'
import styles from '../styles/Home.module.css'

interface ErrorDisplayProps {
  error: any
  sessionId?: string
  onDownloadLogs?: (format: 'json' | 'text') => void
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ error, sessionId, onDownloadLogs }) => {
  const [showDetails, setShowDetails] = useState(false)
  const [showLogs, setShowLogs] = useState(false)

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString('ja-JP')
    } catch {
      return timestamp
    }
  }

  const copyToClipboard = (text: string) => {
    // Clipboard APIが利用可能かチェック
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text)
        .then(() => alert('クリップボードにコピーしました'))
        .catch(() => {
          // フォールバック: テキストエリアを使用
          fallbackCopyToClipboard(text)
        })
    } else {
      // フォールバック: テキストエリアを使用
      fallbackCopyToClipboard(text)
    }
  }

  const fallbackCopyToClipboard = (text: string) => {
    const textArea = document.createElement('textarea')
    textArea.value = text
    textArea.style.position = 'fixed'
    textArea.style.top = '0'
    textArea.style.left = '0'
    textArea.style.width = '2em'
    textArea.style.height = '2em'
    textArea.style.padding = '0'
    textArea.style.border = 'none'
    textArea.style.outline = 'none'
    textArea.style.boxShadow = 'none'
    textArea.style.background = 'transparent'
    document.body.appendChild(textArea)
    textArea.focus()
    textArea.select()
    
    try {
      const successful = document.execCommand('copy')
      if (successful) {
        alert('クリップボードにコピーしました')
      } else {
        alert('コピーに失敗しました')
      }
    } catch (err) {
      console.error('コピーエラー:', err)
      alert('コピーに失敗しました')
    }
    
    document.body.removeChild(textArea)
  }

  const getErrorMessage = () => {
    if (typeof error === 'string') return error
    if (error?.message) return error.message
    if (error?.detail) return error.detail
    return 'XML生成リクエストに失敗しました'
  }

  const getErrorDetails = () => {
    if (error?.response?.data) return error.response.data
    if (error?.data) return error.data
    return error
  }

  const errorDetails = getErrorDetails()

  return (
    <div className={styles.errorContainer} style={{
      backgroundColor: '#fef2f2',
      border: '1px solid #fecaca',
      borderRadius: '8px',
      padding: '16px',
      marginTop: '16px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
        <span style={{ fontSize: '24px' }}>⚠️</span>
        <h3 style={{ margin: 0, color: '#991b1b' }}>XML生成エラー</h3>
      </div>

      <div style={{ marginBottom: '12px' }}>
        <p style={{ margin: '4px 0', color: '#7f1d1d' }}>
          <strong>メッセージ:</strong> {getErrorMessage()}
        </p>
        
        {errorDetails?.status && (
          <p style={{ margin: '4px 0', color: '#7f1d1d' }}>
            <strong>ステータス:</strong> {errorDetails.status}
          </p>
        )}
        
        {errorDetails?.timestamp && (
          <p style={{ margin: '4px 0', color: '#7f1d1d' }}>
            <strong>タイムスタンプ:</strong> {formatTimestamp(errorDetails.timestamp)}
          </p>
        )}
      </div>

      {/* エラー詳細の展開/折り畳み */}
      <button
        onClick={() => setShowDetails(!showDetails)}
        style={{
          background: 'none',
          border: 'none',
          color: '#0070f3',
          cursor: 'pointer',
          padding: '8px 0',
          fontSize: '14px',
          display: 'flex',
          alignItems: 'center',
          gap: '4px'
        }}
      >
        {showDetails ? '▼' : '▶'} エラー詳細を{showDetails ? '隠す' : '表示'}
      </button>

      {showDetails && (
        <div style={{
          backgroundColor: '#fff',
          border: '1px solid #e5e5e5',
          borderRadius: '4px',
          padding: '12px',
          marginTop: '8px',
          fontSize: '13px',
          fontFamily: 'monospace'
        }}>
          {errorDetails?.error && (
            <div style={{ marginBottom: '12px' }}>
              <strong>エラー詳細:</strong>
              <pre style={{ 
                margin: '4px 0', 
                whiteSpace: 'pre-wrap', 
                wordBreak: 'break-word',
                backgroundColor: '#f5f5f5',
                padding: '8px',
                borderRadius: '4px'
              }}>
                {typeof errorDetails.error === 'string' 
                  ? errorDetails.error 
                  : JSON.stringify(errorDetails.error, null, 2)}
              </pre>
            </div>
          )}

          {errorDetails?.stack_trace && (
            <div style={{ marginBottom: '12px' }}>
              <strong>スタックトレース:</strong>
              <pre style={{ 
                margin: '4px 0', 
                whiteSpace: 'pre-wrap', 
                wordBreak: 'break-word',
                backgroundColor: '#f5f5f5',
                padding: '8px',
                borderRadius: '4px',
                maxHeight: '200px',
                overflow: 'auto'
              }}>
                {errorDetails.stack_trace}
              </pre>
            </div>
          )}

          <button
            onClick={() => copyToClipboard(JSON.stringify(errorDetails, null, 2))}
            style={{
              backgroundColor: '#f3f4f6',
              border: '1px solid #d1d5db',
              borderRadius: '4px',
              padding: '6px 12px',
              fontSize: '12px',
              cursor: 'pointer',
              marginTop: '8px'
            }}
          >
            📋 詳細をコピー
          </button>
        </div>
      )}

      {/* ログ情報の展開/折り畳み */}
      {errorDetails?.logs && (
        <>
          <button
            onClick={() => setShowLogs(!showLogs)}
            style={{
              background: 'none',
              border: 'none',
              color: '#0070f3',
              cursor: 'pointer',
              padding: '8px 0',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              marginTop: '12px'
            }}
          >
            {showLogs ? '▼' : '▶'} 処理ログを{showLogs ? '隠す' : '表示'}
          </button>

          {showLogs && (
            <div style={{
              backgroundColor: '#fff',
              border: '1px solid #e5e5e5',
              borderRadius: '4px',
              padding: '12px',
              marginTop: '8px',
              fontSize: '13px',
              fontFamily: 'monospace'
            }}>
              {errorDetails.logs.summary && (
                <div style={{ marginBottom: '12px' }}>
                  <strong>生成サマリー:</strong>
                  <pre style={{ 
                    margin: '4px 0', 
                    whiteSpace: 'pre-wrap', 
                    wordBreak: 'break-word',
                    backgroundColor: '#f5f5f5',
                    padding: '8px',
                    borderRadius: '4px'
                  }}>
                    {JSON.stringify(errorDetails.logs.summary, null, 2)}
                  </pre>
                </div>
              )}

              {errorDetails.logs.errors && errorDetails.logs.errors.length > 0 && (
                <div style={{ marginBottom: '12px' }}>
                  <strong>エラーログ:</strong>
                  <ul style={{ margin: '4px 0', paddingLeft: '20px' }}>
                    {errorDetails.logs.errors.map((err: any, idx: number) => (
                      <li key={idx} style={{ color: '#991b1b' }}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}

              {errorDetails.logs.entries && errorDetails.logs.entries.length > 0 && (
                <div>
                  <strong>処理ログ:</strong>
                  <div style={{ 
                    maxHeight: '150px', 
                    overflow: 'auto',
                    backgroundColor: '#f5f5f5',
                    padding: '8px',
                    borderRadius: '4px',
                    marginTop: '4px'
                  }}>
                    {errorDetails.logs.entries.map((entry: any, idx: number) => (
                      <div key={idx} style={{ fontSize: '12px', marginBottom: '2px' }}>
                        <span style={{ color: '#6b7280' }}>[{entry.timestamp || idx}]</span> {entry.message || entry}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* ログダウンロードボタン */}
      {sessionId && onDownloadLogs && (
        <div style={{ 
          display: 'flex', 
          gap: '8px', 
          marginTop: '16px',
          paddingTop: '16px',
          borderTop: '1px solid #e5e5e5'
        }}>
          <button
            onClick={() => onDownloadLogs('json')}
            className={styles.button}
            style={{
              backgroundColor: '#0070f3',
              color: 'white',
              padding: '8px 16px',
              borderRadius: '4px',
              border: 'none',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            📥 JSONログをダウンロード
          </button>
          <button
            onClick={() => onDownloadLogs('text')}
            className={styles.button}
            style={{
              backgroundColor: '#059669',
              color: 'white',
              padding: '8px 16px',
              borderRadius: '4px',
              border: 'none',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            📄 テキストログをダウンロード
          </button>
        </div>
      )}
    </div>
  )
}

export default ErrorDisplay