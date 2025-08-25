/** @type {import('next').NextConfig} */
const os = require('os');

// IPアドレスの取得（APIPA除外）
function getLocalIP() {
  const interfaces = os.networkInterfaces();
  
  // 優先順位: Ethernet > Wi-Fi > その他
  const priorityInterfaces = ['Ethernet', 'Wi-Fi', 'WiFi', 'Wireless'];
  
  // 優先インターフェースから検索
  for (const priority of priorityInterfaces) {
    for (const name of Object.keys(interfaces)) {
      if (name.includes(priority)) {
        for (const iface of interfaces[name]) {
          if (iface.family === 'IPv4' && 
              !iface.internal && 
              !iface.address.startsWith('169.254.')) {
            return iface.address;
          }
        }
      }
    }
  }
  
  // 優先インターフェースが見つからない場合、すべてのインターフェースから検索
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      if (iface.family === 'IPv4' && 
          !iface.internal && 
          !iface.address.startsWith('169.254.') &&
          !iface.address.startsWith('127.')) {
        return iface.address;
      }
    }
  }
  
  return '127.0.0.1';
}

const LOCAL_IP = getLocalIP();

const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  
  // 環境変数の設定
  env: {
    NEXT_PUBLIC_API_URL: `http://${LOCAL_IP}:8081/api`,
    NEXT_PUBLIC_WS_URL: `ws://${LOCAL_IP}:8081/ws`,
    NEXT_PUBLIC_LOCAL_IP: LOCAL_IP
  },

  // 開発サーバーのクロスオリジン設定
  // Note: allowedDevOrigins will be supported in future Next.js versions
  // For now, cross-origin warnings can be safely ignored in development

  // Note: Server options are configured via package.json scripts

  // 画像最適化の設定
  images: {
    domains: ['localhost', LOCAL_IP],
  },

  // TypeScript設定
  typescript: {
    ignoreBuildErrors: false,
  },

  // ESLint設定
  eslint: {
    ignoreDuringBuilds: false,
  },
}

module.exports = nextConfig