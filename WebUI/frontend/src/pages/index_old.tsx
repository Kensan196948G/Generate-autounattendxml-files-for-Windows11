import React, { useState, useEffect, useCallback } from 'react'
import Head from 'next/head'
import styles from '../styles/Home.module.css'

// 設定カテゴリの定義
interface ConfigSection {
  id: string
  title: string
  icon: string
  description: string
  expanded: boolean
}

// 設定値の型定義
interface UnattendConfig {
  // 地域と言語
  region: {
    inputLocale: string
    systemLocale: string
    userLocale: string
    uiLanguage: string
    timezone: string
  }
  // コンピューター設定
  computer: {
    computerName: string
    organization: string
    owner: string
    processorArchitecture: string
  }
  // ユーザーアカウント
  users: Array<{
    username: string
    password: string
    displayName: string
    description: string
    groups: string[]
    autoLogon: boolean
  }>
  // ネットワーク設定
  network: {
    workgroupOrDomain: 'workgroup' | 'domain'
    workgroupName: string
    domainName: string
    domainUser: string
    domainPassword: string
    disableIPv6: boolean
    disableFirewall: boolean
    disableBluetooth: boolean
  }
  // Windows機能
  features: {
    dotNet35: boolean
    hyperV: boolean
    wsl: boolean
    sandbox: boolean
    iis: boolean
    telnet: boolean
  }
  // プライバシーとセキュリティ
  privacy: {
    disableTelemetry: boolean
    disableCortana: boolean
    disableLocationServices: boolean
    disableAdvertisingId: boolean
    disableWindowsDefender: boolean
    disableUAC: boolean
  }
  // システムカスタマイズ
  customization: {
    skipOOBE: boolean
    skipEula: boolean
    skipMachineOOBE: boolean
    skipUserOOBE: boolean
    hideWirelessSetupInOOBE: boolean
    disableAutomaticUpdates: boolean
    enableRemoteDesktop: boolean
  }
}

export default function Home() {
  const [systemStatus, setSystemStatus] = useState<any>(null)
  const [agents, setAgents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const API_URL = 'http://192.168.3.92:8080/api'

  useEffect(() => {
    fetchSystemStatus()
    fetchAgents()
  }, [])

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/status`)
      const data = await response.json()
      setSystemStatus(data)
      setLoading(false)
    } catch (err) {
      console.error('Status fetch error:', err)
      setError('バックエンドに接続できません')
      setLoading(false)
    }
  }

  const fetchAgents = async () => {
    try {
      const response = await fetch(`${API_URL}/agents`)
      const data = await response.json()
      setAgents(data.agents || [])
    } catch (err) {
      console.error('Agents fetch error:', err)
    }
  }

  const generateXML = async () => {
    try {
      const response = await fetch(`${API_URL}/xml/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          preset: 'enterprise',
          context7_enabled: true,
          parallel_processing: true
        })
      })
      const data = await response.json()
      alert(`XML生成開始: セッションID ${data.session_id}`)
    } catch (err) {
      console.error('Generate error:', err)
      alert('XML生成に失敗しました')
    }
  }

  return (
    <>
      <Head>
        <title>Windows 11 無人応答ファイル生成システム</title>
        <meta name="description" content="Context7 + SubAgent + Claude-flow対応" />
      </Head>

      <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
        <h1 style={{ color: '#0078d4' }}>Windows 11 無人応答ファイル生成システム</h1>
        <p style={{ color: '#666' }}>Context7 + SubAgent（42体） + Claude-flow並列処理対応</p>

        {error && (
          <div style={{ padding: '10px', backgroundColor: '#ffebee', color: '#c62828', borderRadius: '4px', marginBottom: '20px' }}>
            {error}
          </div>
        )}

        {loading && <p>読み込み中...</p>}

        {systemStatus && (
          <div style={{ marginBottom: '30px' }}>
            <h2>システムステータス</h2>
            <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
              <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '8px', minWidth: '200px' }}>
                <h3 style={{ margin: '0 0 10px 0', fontSize: '16px' }}>ステータス</h3>
                <p style={{ margin: 0, fontSize: '24px', fontWeight: 'bold', color: systemStatus.status === 'operational' ? '#4caf50' : '#f44336' }}>
                  {systemStatus.status === 'operational' ? '✅ 稼働中' : '⚠️ 停止中'}
                </p>
                <p style={{ margin: '5px 0 0 0', fontSize: '12px', color: '#666' }}>IP: {systemStatus.ip_address}</p>
              </div>

              <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '8px', minWidth: '200px' }}>
                <h3 style={{ margin: '0 0 10px 0', fontSize: '16px' }}>Context7</h3>
                <p style={{ margin: 0, fontSize: '24px', fontWeight: 'bold', color: '#4caf50' }}>
                  {systemStatus.context7 === 'active' ? '✅ 有効' : '❌ 無効'}
                </p>
                <p style={{ margin: '5px 0 0 0', fontSize: '12px', color: '#666' }}>高度なコンテキスト管理</p>
              </div>

              <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '8px', minWidth: '200px' }}>
                <h3 style={{ margin: '0 0 10px 0', fontSize: '16px' }}>SubAgent</h3>
                <p style={{ margin: 0, fontSize: '24px', fontWeight: 'bold', color: '#2196f3' }}>
                  {systemStatus.subagents?.total || 0}体
                </p>
                <p style={{ margin: '5px 0 0 0', fontSize: '12px', color: '#666' }}>
                  Ready: {systemStatus.subagents?.ready || 0} / Processing: {systemStatus.subagents?.processing || 0}
                </p>
              </div>
            </div>
          </div>
        )}

        {agents.length > 0 && (
          <div style={{ marginBottom: '30px' }}>
            <h2>SubAgent一覧（{agents.length}体）</h2>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
              {agents.slice(0, 20).map((agent) => (
                <span
                  key={agent.name}
                  style={{
                    padding: '4px 8px',
                    backgroundColor: agent.status === 'ready' ? '#e8f5e9' : '#f5f5f5',
                    color: agent.status === 'ready' ? '#2e7d32' : '#666',
                    borderRadius: '4px',
                    fontSize: '12px',
                    border: '1px solid',
                    borderColor: agent.status === 'ready' ? '#4caf50' : '#ddd'
                  }}
                >
                  {agent.name} ({agent.role})
                </span>
              ))}
              {agents.length > 20 && (
                <span style={{ padding: '4px 8px', color: '#666', fontSize: '12px' }}>
                  他{agents.length - 20}体...
                </span>
              )}
            </div>
          </div>
        )}

        <div style={{ marginBottom: '30px' }}>
          <h2>XML生成</h2>
          <button
            onClick={generateXML}
            style={{
              padding: '10px 20px',
              backgroundColor: '#0078d4',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '16px',
              cursor: 'pointer',
              marginRight: '10px'
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#106ebe'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#0078d4'}
          >
            Enterprise設定で生成
          </button>
          <a
            href="http://192.168.3.92:8080/api/docs"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              padding: '10px 20px',
              backgroundColor: '#fff',
              color: '#0078d4',
              border: '2px solid #0078d4',
              borderRadius: '4px',
              fontSize: '16px',
              textDecoration: 'none',
              display: 'inline-block'
            }}
          >
            API仕様書を開く
          </a>
        </div>
      </div>
    </>
  )
}