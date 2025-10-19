/**
 * 上传进度Hook
 * 
 * 通过WebSocket实时获取上传进度
 */
import { useEffect, useState, useCallback, useRef } from 'react';

export interface UploadProgress {
  file_name: string;
  file_size: number;
  status: 'pending' | 'hashing' | 'checking' | 'quick_success' | 'uploading' | 'success' | 'failed' | 'cancelled';
  percentage: number;
  uploaded_bytes: number;
  total_bytes: number;
  total_parts: number;
  uploaded_parts: number;
  speed_mbps: number;
  elapsed_seconds: number;
  eta_seconds: number | null;
  error_message: string | null;
  file_id: string | null;
  is_quick_upload: boolean;
}

export interface UploadProgressData {
  uploads: UploadProgress[];
}

export const useUploadProgress = () => {
  const [uploads, setUploads] = useState<UploadProgress[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // 已连接
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    const port = import.meta.env.VITE_API_PORT || '8000';
    const wsUrl = `${protocol}//${host}:${port}/ws/upload/progress`;

    console.log('连接WebSocket:', wsUrl);

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket已连接');
      setConnected(true);

      // 发送心跳
      const heartbeat = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({
            type: 'ping',
            timestamp: Date.now()
          }));
        }
      }, 30000); // 30秒心跳

      ws.addEventListener('close', () => {
        clearInterval(heartbeat);
      });
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        if (message.type === 'upload_progress' && message.data) {
          setUploads(message.data.uploads || []);
        } else if (message.type === 'pong') {
          // 心跳响应
          console.log('WebSocket心跳正常');
        }
      } catch (error) {
        console.error('解析WebSocket消息失败:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket错误:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket已断开');
      setConnected(false);
      wsRef.current = null;

      // 5秒后重连
      reconnectTimerRef.current = window.setTimeout(() => {
        console.log('尝试重新连接WebSocket...');
        connect();
      }, 5000);
    };

    wsRef.current = ws;
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setConnected(false);
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    uploads,
    connected,
    reconnect: connect,
    disconnect,
  };
};

export default useUploadProgress;

