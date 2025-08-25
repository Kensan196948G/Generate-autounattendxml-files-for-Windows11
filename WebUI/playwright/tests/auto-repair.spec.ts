import { test, expect, Page } from '@playwright/test';

/**
 * 自動エラー検知・修復テスト
 * 最大20回のリトライループを実装
 */

interface TestResult {
  success: boolean;
  error?: string;
  retryCount: number;
  timestamp: Date;
}

class AutoRepairSystem {
  private maxRetries: number = 20;
  private retryDelay: number = 2000;
  private errorHistory: Map<string, number> = new Map();

  async executeWithRetry(
    testName: string,
    testFn: () => Promise<void>,
    repairFn?: (error: Error) => Promise<void>
  ): Promise<TestResult> {
    let retryCount = 0;
    let lastError: Error | null = null;

    while (retryCount < this.maxRetries) {
      try {
        await testFn();
        return {
          success: true,
          retryCount,
          timestamp: new Date(),
        };
      } catch (error) {
        lastError = error as Error;
        retryCount++;
        
        console.log(`[リトライ ${retryCount}/${this.maxRetries}] エラー検知: ${lastError.message}`);
        
        // エラー履歴を記録
        const errorKey = lastError.message;
        this.errorHistory.set(errorKey, (this.errorHistory.get(errorKey) || 0) + 1);
        
        // 修復関数が提供されている場合は実行
        if (repairFn && retryCount < this.maxRetries) {
          console.log('自動修復を試行中...');
          try {
            await repairFn(lastError);
            console.log('修復完了、再試行します');
          } catch (repairError) {
            console.error('修復失敗:', repairError);
          }
        }
        
        // リトライ前に待機
        await new Promise(resolve => setTimeout(resolve, this.retryDelay));
      }
    }

    // 最大リトライ回数に達した場合
    console.error(`最大リトライ回数(${this.maxRetries})に達しました`);
    return {
      success: false,
      error: lastError?.message,
      retryCount,
      timestamp: new Date(),
    };
  }

  getErrorStatistics() {
    return Array.from(this.errorHistory.entries()).map(([error, count]) => ({
      error,
      count,
      percentage: (count / this.maxRetries) * 100,
    }));
  }
}

// テストスイート
test.describe('自動エラー検知・修復システム', () => {
  let autoRepair: AutoRepairSystem;
  
  test.beforeEach(() => {
    autoRepair = new AutoRepairSystem();
  });

  test('フロントエンド接続テスト', async ({ page }) => {
    const result = await autoRepair.executeWithRetry(
      'フロントエンド接続',
      async () => {
        await page.goto('/');
        await expect(page).toHaveTitle(/Windows 11 無人応答ファイル生成システム/);
        
        // ヘッダーの確認
        const header = page.locator('h1');
        await expect(header).toContain Text('Windows 11 無人応答ファイル生成システム');
      },
      async (error) => {
        // 接続エラーの場合、ページをリロード
        if (error.message.includes('net::ERR')) {
          await page.reload();
        }
      }
    );
    
    expect(result.success).toBe(true);
    console.log(`テスト完了: リトライ回数 ${result.retryCount}`);
  });

  test('バックエンドAPI接続テスト', async ({ page }) => {
    const result = await autoRepair.executeWithRetry(
      'API接続',
      async () => {
        const response = await page.request.get('http://192.168.3.92:8080/api/status');
        expect(response.ok()).toBe(true);
        
        const data = await response.json();
        expect(data.status).toBe('operational');
        expect(data.context7).toBe('active');
        expect(data.subagents.total).toBeGreaterThanOrEqual(30);
      },
      async (error) => {
        // APIエラーの場合、少し待機してから再試行
        await new Promise(resolve => setTimeout(resolve, 3000));
      }
    );
    
    expect(result.success).toBe(true);
  });

  test('SubAgent動作確認テスト', async ({ page }) => {
    const result = await autoRepair.executeWithRetry(
      'SubAgent確認',
      async () => {
        const response = await page.request.get('http://192.168.3.92:8080/api/agents');
        expect(response.ok()).toBe(true);
        
        const data = await response.json();
        expect(data.total).toBeGreaterThanOrEqual(30);
        
        // 各カテゴリのエージェントを確認
        const agentsByCategory = {
          user_management: 0,
          network: 0,
          system: 0,
          features: 0,
          applications: 0,
          security: 0,
        };
        
        for (const agent of data.agents) {
          if (agent.role.includes('user')) agentsByCategory.user_management++;
          if (agent.role.includes('network')) agentsByCategory.network++;
          if (agent.role.includes('system')) agentsByCategory.system++;
          if (agent.role.includes('feature')) agentsByCategory.features++;
          if (agent.role.includes('app')) agentsByCategory.applications++;
          if (agent.role.includes('security')) agentsByCategory.security++;
        }
        
        // 各カテゴリに最低5体のエージェントが存在することを確認
        Object.values(agentsByCategory).forEach(count => {
          expect(count).toBeGreaterThanOrEqual(5);
        });
      }
    );
    
    expect(result.success).toBe(true);
  });

  test('XML生成フロー完全テスト', async ({ page }) => {
    const result = await autoRepair.executeWithRetry(
      'XML生成',
      async () => {
        await page.goto('/');
        
        // プリセットボタンをクリック
        await page.click('button:has-text("企業向け")');
        
        // 設定セクションを展開
        await page.click('text=コンピューター情報');
        
        // コンピューター名を入力
        await page.fill('input#computername', 'TEST-PC-001');
        await page.fill('input#organization', 'テスト企業');
        await page.fill('input#owner', 'テストユーザー');
        
        // Windows機能セクションを展開
        await page.click('text=Windows機能');
        
        // 機能を有効化
        await page.check('input[type="checkbox"]:has(+ span:has-text(".NET Framework 3.5"))');
        await page.check('input[type="checkbox"]:has(+ span:has-text("Hyper-V"))');
        
        // XML生成ボタンをクリック
        const downloadPromise = page.waitForEvent('download');
        await page.click('button:has-text("unattend.xml を生成")');
        
        // ダウンロードを待機
        const download = await downloadPromise;
        expect(download.suggestedFilename()).toBe('unattend.xml');
      },
      async (error) => {
        // フォーム要素が見つからない場合、ページをリロード
        if (error.message.includes('selector')) {
          await page.reload();
          await page.waitForTimeout(2000);
        }
      }
    );
    
    expect(result.success).toBe(true);
    
    // エラー統計を出力
    if (!result.success) {
      const stats = autoRepair.getErrorStatistics();
      console.log('エラー統計:');
      stats.forEach(stat => {
        console.log(`  ${stat.error}: ${stat.count}回 (${stat.percentage.toFixed(1)}%)`);
      });
    }
  });

  test('並列処理パフォーマンステスト', async ({ page }) => {
    const result = await autoRepair.executeWithRetry(
      '並列処理',
      async () => {
        // 複数のAPIリクエストを並列で実行
        const requests = [
          page.request.get('http://192.168.3.92:8080/api/status'),
          page.request.get('http://192.168.3.92:8080/api/agents'),
          page.request.get('http://192.168.3.92:8080/api/presets'),
        ];
        
        const startTime = Date.now();
        const responses = await Promise.all(requests);
        const endTime = Date.now();
        
        // すべてのレスポンスが成功していることを確認
        responses.forEach(response => {
          expect(response.ok()).toBe(true);
        });
        
        // 並列処理が3秒以内に完了することを確認
        const duration = endTime - startTime;
        expect(duration).toBeLessThan(3000);
        
        console.log(`並列処理完了時間: ${duration}ms`);
      }
    );
    
    expect(result.success).toBe(true);
  });

  test('Context7機能確認テスト', async ({ page }) => {
    const result = await autoRepair.executeWithRetry(
      'Context7',
      async () => {
        // XML生成をトリガー
        const response = await page.request.post('http://192.168.3.92:8080/api/xml/generate', {
          data: {
            preset: 'enterprise',
            context7_enabled: true,
            parallel_processing: true,
            config: {
              computer: {
                computerName: 'CONTEXT7-TEST',
              },
            },
          },
        });
        
        expect(response.ok()).toBe(true);
        const data = await response.json();
        
        expect(data.session_id).toBeTruthy();
        expect(data.context7).toBe(true);
        expect(data.parallel).toBe(true);
        
        // セッションステータスを確認
        await page.waitForTimeout(2000);
        const statusResponse = await page.request.get(
          `http://192.168.3.92:8080/api/xml/status/${data.session_id}`
        );
        
        expect(statusResponse.ok()).toBe(true);
      }
    );
    
    expect(result.success).toBe(true);
  });

  test.afterAll(async () => {
    console.log('='.repeat(50));
    console.log('自動テスト完了サマリー');
    console.log('='.repeat(50));
  });
});

// エラー修復ヘルパー関数
async function repairConnection(page: Page) {
  try {
    // バックエンドの再起動を試みる
    await page.request.post('http://192.168.3.92:8080/api/restart', {
      failOnStatusCode: false,
    });
    await page.waitForTimeout(5000);
  } catch (error) {
    console.log('接続修復をスキップ');
  }
}

// WebSocketエラー修復
async function repairWebSocket(page: Page) {
  try {
    await page.evaluate(() => {
      // 既存のWebSocket接続をクローズ
      if ((window as any).ws) {
        (window as any).ws.close();
      }
      // 新しい接続を確立
      (window as any).ws = new WebSocket('ws://192.168.3.92:8080/ws/progress');
    });
  } catch (error) {
    console.log('WebSocket修復をスキップ');
  }
}