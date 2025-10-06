/**
 * 🤖 示例：自动生成的OpenAPI类型文件
 * 
 * 实际文件由 `npm run generate:api-types` 生成
 * 此文件仅供参考，展示生成后的结构
 * 
 * 生成时间: 2025-10-06
 * API版本: 1.0.0
 */

/**
 * 此文件在首次运行 npm run generate:api-types 后会被真实文件替换
 * 
 * 生成步骤：
 * 1. 启动后端服务: docker-compose up -d
 * 2. 运行生成脚本: npm run generate:api-types
 * 3. 查看生成的 api-schema.ts 文件
 */

// 示例类型结构（实际会更详细）
export interface paths {
  '/api/settings': {
    get: {
      responses: {
        200: {
          content: {
            'application/json': {
              success: boolean;
              config: components['schemas']['BotSettings'];
            };
          };
        };
      };
    };
    post: {
      requestBody: {
        content: {
          'application/json': Partial<components['schemas']['BotSettings']>;
        };
      };
      responses: {
        200: {
          content: {
            'application/json': {
              success: boolean;
              message: string;
            };
          };
        };
      };
    };
  };
  // ... 更多路径
}

export interface components {
  schemas: {
    BotSettings: {
      api_id: string;
      api_hash: string;
      bot_token: string;
      phone_number: string;
      admin_user_ids: string;
      enable_proxy: boolean;
      proxy_type: 'socks5' | 'http' | 'https';
      proxy_host: string;
      proxy_port: number;
      // ... 更多字段
    };
    ForwardRule: {
      id: number;
      name: string;
      source_chat_id: string;
      target_chat_id: string;
      enabled: boolean;
      // ... 更多字段
    };
    // ... 更多schemas
  };
}

