/**
 * Windows 11 Sysprep WebUI - バックエンドAPI通信サービス
 * 
 * FastAPIバックエンドとの通信を管理し、エラーハンドリング、
 * リクエスト/レスポンス変換、認証などを統合的に処理します。
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'

// API基底URL（環境変数またはデフォルト値）
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || `http://${process.env.NEXT_PUBLIC_LOCAL_IP || 'localhost'}:8081/api`

// リクエストタイムアウト（ミリ秒）
const REQUEST_TIMEOUT = 30000

/**
 * API共通レスポンス型定義
 */
interface ApiResponse<T = any> {
  success: boolean
  message: string
  data?: T
  errors?: string[]
  timestamp: string
}

/**
 * XML生成リクエスト型定義
 */
interface XmlGenerationRequest {
  preset_name?: string
  custom_config?: any
  validation_enabled?: boolean
  output_filename?: string
}

/**
 * XML生成結果型定義
 */
interface XmlGenerationResult {
  session_id: string
  status: string
  xml_content?: string
  output_file_path?: string
  validation_result?: any
  processing_time?: number
  agent_results?: any[]
  error_details?: any
}

/**
 * プリセット情報型定義
 */
interface PresetInfo {
  name: string
  preset_type: string
  description: string
  is_builtin: boolean
  file_path?: string
}

/**
 * エージェント状態型定義
 */
interface AgentStatus {
  system_status: string
  total_workers: number
  active_workers: number
  available_agents: number
  queue_size: number
  statistics: {
    total_tasks_completed: number
    total_tasks_failed: number
    total_execution_time: number
    average_execution_time: number
  }
}

/**
 * APIクライアントクラス
 */
class ApiClient {
  private axiosInstance: AxiosInstance
  private isInitialized = false

  constructor() {
    this.axiosInstance = axios.create({
      baseURL: API_BASE_URL,
      timeout: REQUEST_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    })

    this.setupInterceptors()
  }

  /**
   * リクエスト・レスポンスインターセプター設定
   */
  private setupInterceptors(): void {
    // リクエストインターセプター
    this.axiosInstance.interceptors.request.use(
      (config) => {
        // リクエスト送信前の処理
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
        
        // 認証トークンがあれば追加（将来の拡張用）
        const token = this.getAuthToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }

        return config
      },
      (error) => {
        console.error('Request interceptor error:', error)
        return Promise.reject(error)
      }
    )

    // レスポンスインターセプター
    this.axiosInstance.interceptors.response.use(
      (response: AxiosResponse<ApiResponse>) => {
        // 成功レスポンスの処理
        console.log(`API Response: ${response.status} ${response.config.url}`)
        
        // APIレスポンス形式のチェック
        if (response.data && typeof response.data === 'object') {
          if (!response.data.success && response.data.message) {
            // サーバーエラーメッセージを表示
            console.error(`サーバーエラー: ${response.data.message}`)
          }
        }

        return response
      },
      (error: AxiosError<ApiResponse>) => {
        // エラーレスポンスの処理
        console.error('API Error:', error)
        
        this.handleApiError(error)
        return Promise.reject(error)
      }
    )
  }

  /**
   * APIエラーハンドリング
   */
  private handleApiError(error: AxiosError<ApiResponse>): void {
    let errorMessage = 'API通信エラーが発生しました'

    if (error.response) {
      // サーバーからエラーレスポンスが返された場合
      const { status, data } = error.response
      
      switch (status) {
        case 400:
          errorMessage = data?.message || 'リクエストが不正です'
          break
        case 401:
          errorMessage = '認証が必要です'
          break
        case 403:
          errorMessage = 'アクセス権限がありません'
          break
        case 404:
          errorMessage = 'リソースが見つかりません'
          break
        case 500:
          errorMessage = 'サーバー内部エラーが発生しました'
          break
        case 503:
          errorMessage = 'サービスが利用できません'
          break
        default:
          errorMessage = data?.message || `HTTPエラー: ${status}`
      }
      
      // 詳細エラー情報があれば表示
      if (data?.errors && Array.isArray(data.errors)) {
        errorMessage += `: ${data.errors.join(', ')}`
      }
      
    } else if (error.request) {
      // リクエストが送信されたが応答がない場合
      errorMessage = 'サーバーに接続できません。ネットワーク接続とサーバー状態を確認してください。'
    } else {
      // その他のエラー
      errorMessage = error.message || 'リクエスト設定でエラーが発生しました'
    }

    // エラーログ出力
    console.error(errorMessage)
  }

  /**
   * 認証トークン取得（将来の拡張用）
   */
  private getAuthToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token')
    }
    return null
  }

  /**
   * HTTP GET リクエスト
   */
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    return this.axiosInstance.get<ApiResponse<T>>(url, config)
  }

  /**
   * HTTP POST リクエスト
   */
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    return this.axiosInstance.post<ApiResponse<T>>(url, data, config)
  }

  /**
   * HTTP PUT リクエスト
   */
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    return this.axiosInstance.put<ApiResponse<T>>(url, data, config)
  }

  /**
   * HTTP DELETE リクエスト
   */
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    return this.axiosInstance.delete<ApiResponse<T>>(url, config)
  }

  /**
   * ファイルアップロード
   */
  async upload<T = any>(url: string, file: File, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    const formData = new FormData()
    formData.append('file', file)

    return this.axiosInstance.post<ApiResponse<T>>(url, formData, {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...config?.headers
      }
    })
  }

  /**
   * ファイルダウンロード
   */
  async download(url: string, filename?: string): Promise<void> {
    try {
      const response = await this.axiosInstance.get(url, {
        responseType: 'blob'
      })

      // Blobからダウンロードリンクを作成
      const downloadUrl = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename || 'download'
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(downloadUrl)

      console.log('ファイルのダウンロードが開始されました')
    } catch (error) {
      console.error('ファイルのダウンロードに失敗しました')
      throw error
    }
  }

  // === API専用メソッド ===

  /**
   * システム状態取得
   */
  async getSystemStatus() {
    return this.get('/status')
  }

  /**
   * プリセット一覧取得
   */
  async getPresets(): Promise<AxiosResponse<ApiResponse<PresetInfo[]>>> {
    return this.get<PresetInfo[]>('/presets')
  }

  /**
   * プリセット詳細取得
   */
  async getPresetDetail(presetName: string) {
    return this.get(`/presets/${presetName}`)
  }

  /**
   * XML生成開始
   */
  async generateXml(request: XmlGenerationRequest): Promise<AxiosResponse<ApiResponse<{session_id: string}>>> {
    return this.post<{session_id: string}>('/xml/generate', request)
  }

  /**
   * XML生成進捗取得
   */
  async getXmlProgress(sessionId: string) {
    return this.get(`/xml/status/${sessionId}`)
  }

  /**
   * XML生成結果取得
   */
  async getXmlResult(sessionId: string): Promise<AxiosResponse<ApiResponse<XmlGenerationResult>>> {
    return this.get<XmlGenerationResult>(`/xml/status/${sessionId}`)
  }

  /**
   * XMLファイルダウンロード
   * シンプルなunattend.xml生成エンドポイントを使用
   */
  async downloadXml(config?: any, filename?: string): Promise<void> {
    // 直接XMLを生成してダウンロード（設定データを送信）
    try {
      const response = await this.axiosInstance.post('/generate-unattend', config || {}, {
        responseType: 'blob'
      })
      
      // Blobからダウンロードリンクを作成
      const downloadUrl = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename || 'autounattend.xml'
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(downloadUrl)

      console.log('XMLファイルのダウンロードが開始されました')
    } catch (error) {
      console.error('XMLファイルのダウンロードに失敗しました')
      throw error
    }
  }

  /**
   * XMLファイルと設定ログを同時にダウンロード
   * ZIPファイルとして提供
   */
  async downloadXmlWithLog(config?: any, filename?: string): Promise<void> {
    try {
      const response = await this.axiosInstance.post('/generate-with-log', config || {}, {
        responseType: 'blob'
      })
      
      // Blobからダウンロードリンクを作成
      const downloadUrl = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename || 'unattend_package.zip'
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(downloadUrl)

      console.log('XMLと設定ログのダウンロードが開始されました')
    } catch (error) {
      console.error('ダウンロードに失敗しました')
      throw error
    }
  }

  /**
   * XMLバリデーション
   */
  async validateXml(file: File) {
    return this.upload('/xml/validate', file)
  }

  /**
   * エージェント状態取得
   */
  async getAgentStatus(): Promise<AxiosResponse<ApiResponse<AgentStatus>>> {
    return this.get<AgentStatus>('/agents/status')
  }

  /**
   * 特定エージェントのタスク取得
   */
  async getAgentTasks(agentName: string) {
    return this.get(`/agents/${agentName}/tasks`)
  }

  /**
   * システム情報取得
   */
  async getSystemInfo() {
    return this.get('/system/info')
  }

  /**
   * ログ取得
   */
  async getLogs(limit: number = 100, level?: string) {
    const params = new URLSearchParams({ limit: limit.toString() })
    if (level) params.append('level', level)
    
    return this.get(`/logs?${params.toString()}`)
  }

  /**
   * 生成ログダウンロード（現在は対応していません）
   */
  async downloadGenerationLogs(sessionId: string, format: 'json' | 'text' = 'json'): Promise<void> {
    console.warn('ログダウンロード機能は現在対応していません')
    throw new Error('ログダウンロード機能は現在対応していません')
  }

  /**
   * エラー詳細取得（詳細なスタックトレース含む）
   */
  async getErrorDetails(error: any): Promise<any> {
    // APIエラーから詳細情報を抽出
    if (error.response?.data) {
      return {
        message: error.response.data.message || 'APIエラーが発生しました',
        details: error.response.data.data || {},
        status: error.response.status,
        timestamp: new Date().toISOString(),
        logs: error.response.data.data?.logs || null
      }
    }
    
    return {
      message: error.message || 'エラーが発生しました',
      details: { error: error.toString() },
      status: 'unknown',
      timestamp: new Date().toISOString(),
      logs: null
    }
  }
}

// シングルトンインスタンス
const apiClient = new ApiClient()

// デフォルトエクスポート
export default apiClient

// 名前付きエクスポート
export { ApiClient, apiClient as api }

// React Hook用のエクスポート
export const useApi = () => {
  return apiClient
}

// 型エクスポート
export type {
  ApiResponse,
  XmlGenerationRequest,
  XmlGenerationResult,
  PresetInfo,
  AgentStatus
}