import React, { useState, useEffect, useRef } from 'react';
import { Button, Space, Typography, Tag, Tabs, message, Input, Grid } from 'antd';
import { 
  ReloadOutlined, 
  PauseCircleOutlined, 
  PlayCircleOutlined,
  ClearOutlined,
  DownloadOutlined,
  SearchOutlined
} from '@ant-design/icons';
import { useThemeContext } from '../../theme';

const { Text } = Typography;
const { useBreakpoint } = Grid;

interface LogEntry {
  type: 'log' | 'connected' | 'error';
  message: string;
  timestamp?: string;
  source?: string;
  level?: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL' | string;
  // 结构化字段（新增）
  module?: string;
  function?: string;
  line_number?: number;
  emoji?: string;
  action_type?: string;
  entities?: Record<string, any>;
  severity_score?: number;
  raw?: string;
}

const ContainerLogs: React.FC = () => {
  const { colors } = useThemeContext();
  const screens = useBreakpoint();
  const isMobile = Boolean(screens.xs && !screens.md);
  
  // 添加自定义滚动条样式
  useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      .terminal-logs-container::-webkit-scrollbar {
        width: 12px;
        height: 12px;
      }
      
      .terminal-logs-container::-webkit-scrollbar-track {
        background: #161b22;
        border-radius: 0 0 8px 0;
      }
      
      .terminal-logs-container::-webkit-scrollbar-thumb {
        background: #30363d;
        border-radius: 6px;
        border: 2px solid #161b22;
      }
      
      .terminal-logs-container::-webkit-scrollbar-thumb:hover {
        background: #484f58;
      }
      
      .terminal-logs-container::-webkit-scrollbar-corner {
        background: #161b22;
      }
    `;
    document.head.appendChild(style);
    
    return () => {
      document.head.removeChild(style);
    };
  }, []);
  
  // 从 sessionStorage 恢复日志和历史加载状态
  const loadLogsFromStorage = (): LogEntry[] => {
    try {
      const stored = sessionStorage.getItem('containerLogs');
      if (stored) {
        const parsed = JSON.parse(stored);
        console.log('[加载缓存] 从 sessionStorage 恢复了', parsed.length, '条日志');
        return parsed;
      }
    } catch (error) {
      console.error('从 sessionStorage 加载日志失败:', error);
    }
    return [];
  };

  const getHasLoadedHistory = (): boolean => {
    try {
      const stored = sessionStorage.getItem('containerLogsHistoryLoaded');
      return stored === 'true';
    } catch (error) {
      return false;
    }
  };

  const [logs, setLogs] = useState<LogEntry[]>(loadLogsFromStorage);
  const [isConnected, setIsConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [searchKeyword, setSearchKeyword] = useState<string>('');
  const eventSourceRef = useRef<EventSource | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const logsContainerRef = useRef<HTMLDivElement>(null);
  const hasLoadedHistoryRef = useRef(getHasLoadedHistory()); // 从sessionStorage恢复状态
  const saveTimerRef = useRef<NodeJS.Timeout | null>(null); // sessionStorage 保存防抖定时器
  const MAX_LOGS_PER_SOURCE = 500; // 每个来源最多保留500条日志
  const [activeTab, setActiveTab] = useState<string>('all'); // 当前激活的Tab（all/enhanced_bot/api/web_api）

  // 自动保存日志到 sessionStorage（防抖优化，500ms后保存）
  useEffect(() => {
    // 清除之前的定时器
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current);
    }
    
    // 设置新的定时器
    saveTimerRef.current = setTimeout(() => {
      try {
        sessionStorage.setItem('containerLogs', JSON.stringify(logs));
        console.log('[保存缓存] 保存了', logs.length, '条日志到 sessionStorage');
      } catch (error) {
        console.error('保存日志到 sessionStorage 失败:', error);
      }
    }, 500);
    
    // 清理函数
    return () => {
      if (saveTimerRef.current) {
        clearTimeout(saveTimerRef.current);
      }
    };
  }, [logs]);

  // 按来源分组的日志，每个来源保留最多500条
  const groupedLogs = React.useMemo(() => {
    const groups: Record<string, LogEntry[]> = { all: [] };
    
    logs.forEach(log => {
      const source = log.source || 'unknown';
      if (!groups[source]) {
        groups[source] = [];
      }
      groups[source].push(log);
      groups.all.push(log);
    });
    
    // 对每个分组按时间排序并限制数量
    Object.keys(groups).forEach(source => {
      groups[source] = groups[source]
        .sort((a, b) => {
          const timeA = a.timestamp || '';
          const timeB = b.timestamp || '';
          return timeB.localeCompare(timeA);
        })
        .slice(0, source === 'all' ? MAX_LOGS_PER_SOURCE * 3 : MAX_LOGS_PER_SOURCE);
    });
    
    return groups;
  }, [logs]);

  // 根据当前Tab和搜索关键字显示的日志
  const displayLogs = React.useMemo(() => {
    let logs = groupedLogs[activeTab] || [];
    
    // 如果有搜索关键字，进行过滤
    if (searchKeyword.trim()) {
      const keyword = searchKeyword.toLowerCase();
      logs = logs.filter(log => 
        log.message?.toLowerCase().includes(keyword) ||
        log.level?.toLowerCase().includes(keyword) ||
        log.source?.toLowerCase().includes(keyword)
      );
    }
    
    return logs;
  }, [groupedLogs, activeTab, searchKeyword]);

  // 自动滚动到顶部（因为新日志在顶部）
  useEffect(() => {
    if (autoScroll && logsContainerRef.current) {
      logsContainerRef.current.scrollTop = 0;
    }
  }, [logs, autoScroll]);

  // 连接到SSE
  const connect = (loadHistory: boolean = false) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const params = new URLSearchParams();
    
    // 添加认证token（EventSource不支持自定义请求头）
    const token = localStorage.getItem('access_token');
    console.log('[ContainerLogs] Token从localStorage读取:', token ? `存在(长度${token.length})` : '不存在');
    if (token) {
      params.set('token', token);
    } else {
      console.error('[ContainerLogs] 警告：未找到认证token，连接可能失败');
    }
    
    // 只有显式请求时才加载历史日志（每个文件加载500条）
    if (loadHistory) {
      params.set('tail', '500');
    } else {
      params.set('tail', '0');
    }

    const url = `/api/system/container-logs/stream?${params.toString()}`;
    console.log('[ContainerLogs] 连接SSE:', url.replace(/token=[^&]+/, 'token=***'));
    const eventSource = new EventSource(url);
    
    eventSource.onopen = () => {
      setIsConnected(true);
      console.log('SSE连接已建立');
    };

    eventSource.onmessage = (event) => {
      if (isPaused) return;
      
      try {
        const data: LogEntry = JSON.parse(event.data);
        
        // 调试：记录所有接收到的消息
        if (data.source === 'api.log') {
          console.log('[DEBUG] 收到 api.log 消息:', data);
        }
        
        if (data.type === 'connected') {
          // 初始或新增源通知（不需要处理）
          return;
        }
        // 只添加实际的日志条目（添加到顶部，因为最新日志显示在最上面）
        console.log('[DEBUG] 添加日志到列表:', {
          source: data.source,
          timestamp: data.timestamp,
          level: data.level,
          message: data.message?.substring(0, 80)
        });
        setLogs(prev => {
          const newLogs = [data, ...prev];
          // 限制日志数量，避免内存溢出
          const limit = MAX_LOGS_PER_SOURCE * 10;
          if (newLogs.length > limit * 1.2) {
            return newLogs.slice(0, limit);
          }
          return newLogs;
        });
      } catch (error) {
        console.error('解析日志数据失败:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE连接错误:', error);
      setIsConnected(false);
      eventSource.close();
      
      // 添加错误日志到顶部
      setLogs(prev => [{
        type: 'error',
        message: '连接已断开，尝试重新连接...',
        timestamp: new Date().toISOString(),
        source: 'system',
        level: 'ERROR'
      }, ...prev]);

      // 5秒后自动重连（不加载历史日志）
      setTimeout(() => {
        if (!isPaused) {
          connect(false);
        }
      }, 5000);
    };

    eventSourceRef.current = eventSource;
  };

  // 断开连接
  const disconnect = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    }
  };

  // 组件挂载时自动连接
  useEffect(() => {
    const hasCachedLogs = logs.length > 0;
    // 只有首次打开且没有缓存日志时才加载历史
    const shouldLoadHistory = !hasLoadedHistoryRef.current && !hasCachedLogs;
    
    console.log('[ContainerLogs] 组件挂载:', { 
      hasLoadedHistory: hasLoadedHistoryRef.current,
      hasCachedLogs,
      logsCount: logs.length,
      shouldLoadHistory 
    });
    
    if (shouldLoadHistory) {
      hasLoadedHistoryRef.current = true;
      sessionStorage.setItem('containerLogsHistoryLoaded', 'true');
    }
    
    connect(shouldLoadHistory);
    
    return () => {
      console.log('[ContainerLogs] 组件卸载，断开SSE连接（日志保存在sessionStorage）');
      disconnect();
    };
  }, []);


  // 暂停/恢复
  const togglePause = () => {
    setIsPaused(!isPaused);
  };

  // 清空日志
  const clearLogs = () => {
    console.log('[清空日志] 清空显示和缓存');
    setLogs([]);
    sessionStorage.removeItem('containerLogs');
    // 不重置历史加载标记，这样清空后只接收新日志
  };

  // 导出日志
  const exportLogs = () => {
    const logText = logs.map(log => {
      const time = log.timestamp ? new Date(log.timestamp).toLocaleString() : '';
      return `[${time}] [${log.type.toUpperCase()}] ${log.message}`;
    }).join('\n');

    const blob = new Blob([logText], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `container-logs-${new Date().toISOString()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };


  return (
    <div className="container-logs-page" style={{ 
      height: 'calc(100vh - 112px)', // 固定高度：视口高度 - Header(64px) - padding(48px)
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden' // 防止页面级别滚动，使用内部滚动
    }}>
        {/* 顶部工具栏区域（根据主题切换） */}
        <div style={{
          background: colors.bgContainer,
          borderRadius: '8px 8px 0 0',
          border: `1px solid ${colors.border}`,
          borderBottom: 'none',
          padding: '12px 16px',
          flexShrink: 0
        }}>
        {/* 第一行：标题 + 状态 + 工具按钮 */}
        <div style={{ 
          display: 'flex', 
          flexDirection: isMobile ? 'column' : 'row',
          alignItems: isMobile ? 'stretch' : 'center', 
          justifyContent: 'space-between',
          marginBottom: 12,
          gap: isMobile ? 12 : 0
        }}>
          {/* 左侧：标题 + 状态 */}
          <Space size={isMobile ? 8 : 16} wrap>
            <Text strong style={{ fontSize: isMobile ? 14 : 16, color: colors.textPrimary }}>🐳 容器日志</Text>
            <Space size={12} style={{ fontSize: isMobile ? 11 : 12, color: colors.textSecondary }} wrap>
              <span style={{ 
                display: 'inline-flex', 
                alignItems: 'center',
                gap: 4
              }}>
                <span style={{ 
                  display: 'inline-block',
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: isConnected ? colors.success : colors.error
                }} />
                {isConnected ? '已连接' : '已断开'}
              </span>
              <span>{displayLogs.length} 条日志</span>
              {isPaused && <Tag color="orange" style={{ fontSize: isMobile ? 10 : 11 }}>已暂停</Tag>}
            </Space>
          </Space>

          {/* 右侧：工具按钮 */}
          <Space size={8} wrap style={{ justifyContent: isMobile ? 'flex-start' : 'flex-end' }}>
            <label style={{ 
              fontSize: 12, 
              color: colors.textSecondary, 
              cursor: 'pointer', 
              display: 'flex', 
              alignItems: 'center', 
              gap: 6 
            }}>
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
              />
              自动滚动
            </label>
            <Button
              type="text"
              size="small"
              icon={isPaused ? <PlayCircleOutlined /> : <PauseCircleOutlined />}
              onClick={togglePause}
              style={{ color: isPaused ? colors.success : undefined }}
              title={isPaused ? '继续' : '暂停'}
            />
            <Button
              type="text"
              size="small"
              icon={<ReloadOutlined />}
              onClick={() => {
                console.log('[重新连接] 清空日志、缓存，并重新加载历史');
                disconnect();
                setLogs([]);
                sessionStorage.removeItem('containerLogs');
                sessionStorage.removeItem('containerLogsHistoryLoaded');
                hasLoadedHistoryRef.current = false;
                connect(true);
              }}
              title="重新连接"
            />
            <Button
              type="text"
              size="small"
              icon={<ClearOutlined />}
              onClick={clearLogs}
              title="清空日志"
            />
            <Button
              type="text"
              size="small"
              icon={<DownloadOutlined />}
              onClick={exportLogs}
              disabled={logs.length === 0}
              title="导出日志"
            />
          </Space>
        </div>

        {/* Tab区域和搜索框 */}
        <div style={{ 
          display: 'flex', 
          flexDirection: isMobile ? 'column' : 'row',
          alignItems: isMobile ? 'stretch' : 'center', 
          gap: isMobile ? 8 : 12,
          marginTop: 8,
          marginBottom: -12
        }}>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            size="small"
            items={[
              { 
                key: 'all', 
                label: (
                  <span style={{ fontSize: isMobile ? 11 : 13 }}>
                    全部 <Tag color="blue" style={{ marginLeft: 4, fontSize: isMobile ? 10 : 11 }}>{groupedLogs.all?.length || 0}</Tag>
                  </span>
                )
              },
              { 
                key: 'enhanced_bot.log', 
                label: (
                  <span style={{ fontSize: isMobile ? 11 : 13 }}>
                    消息 <Tag color="green" style={{ marginLeft: 4, fontSize: isMobile ? 10 : 11 }}>{groupedLogs['enhanced_bot.log']?.length || 0}</Tag>
                  </span>
                )
              },
              { 
                key: 'api.log', 
                label: (
                  <span style={{ fontSize: isMobile ? 11 : 13 }}>
                    API <Tag color="orange" style={{ marginLeft: 4, fontSize: isMobile ? 10 : 11 }}>{groupedLogs['api.log']?.length || 0}</Tag>
                  </span>
                )
              },
              { 
                key: 'web_api.log', 
                label: (
                  <span style={{ fontSize: isMobile ? 11 : 13 }}>
                    Web <Tag color="purple" style={{ marginLeft: 4, fontSize: isMobile ? 10 : 11 }}>{groupedLogs['web_api.log']?.length || 0}</Tag>
                  </span>
                )
              },
            ]}
            style={{ flex: 1, marginBottom: 0 }}
          />
          
          {/* 搜索框和结果 */}
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 8,
            width: isMobile ? '100%' : 'auto'
          }}>
            <Input
              placeholder="搜索日志..."
              prefix={<SearchOutlined style={{ color: colors.textSecondary }} />}
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              allowClear
              size="small"
              style={{ 
                width: isMobile ? '100%' : 200,
                fontSize: isMobile ? 11 : 12
              }}
            />
            
            {/* 搜索结果提示 */}
            {searchKeyword && (
              <Text type="secondary" style={{ fontSize: 11, whiteSpace: 'nowrap' }}>
                {displayLogs.length} 条
              </Text>
            )}
          </div>
        </div>
      </div>

      {/* 日志显示区域（黑色终端 - 始终保持深色） */}
      <div 
        ref={logsContainerRef}
        className="terminal-logs-container"
        style={{
          background: '#0d1117',
          border: `1px solid ${colors.border}`,
          borderTop: 'none',
          borderRadius: '0 0 8px 8px',
          flex: 1, // 自动填充剩余空间
          minHeight: 0, // 允许flex子元素缩小
          overflowY: 'scroll', // 强制显示垂直滚动条
          overflowX: 'auto', // 水平滚动按需显示
          fontFamily: 'Monaco, Consolas, "Courier New", monospace',
          fontSize: isMobile ? '10px' : '12px',
          lineHeight: isMobile ? '18px' : '20px',
          position: 'relative' // 确保边框可见
        }}
      >
        {displayLogs.length === 0 ? (
          <div style={{ 
            textAlign: 'center', 
            padding: '80px 20px',
            color: '#6e7681'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.3 }}>📋</div>
            <div style={{ fontSize: 14 }}>暂无日志数据</div>
            <div style={{ fontSize: 11, marginTop: '8px', opacity: 0.7 }}>
              {isConnected ? '等待容器输出日志...' : '点击"重新连接"按钮连接到容器'}
            </div>
          </div>
        ) : (
          displayLogs.map((log, index) => {
            const time = log.timestamp ? new Date(log.timestamp).toLocaleTimeString('zh-CN', { hour12: false }) : '--:--:--';
            const level = log.emoji || log.level || 'INFO';
            
            // 获取级别颜色
            const getLevelColor = () => {
              if (log.emoji) return '#c9d1d9';
              const upperLevel = (log.level || '').toUpperCase();
              if (upperLevel === 'ERROR' || upperLevel === 'CRITICAL') return '#f85149';
              if (upperLevel === 'WARNING' || upperLevel === 'WARN') return '#d29922';
              if (upperLevel === 'INFO') return '#58a6ff';
              if (upperLevel === 'DEBUG') return '#8b949e';
              return '#c9d1d9';
            };

            return (
              <div
                key={`${log.timestamp}-${index}`}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '50px 80px 60px 1fr',
                  gap: '12px',
                  padding: '4px 16px',
                  borderBottom: '1px solid #21262d',
                  cursor: 'pointer',
                  transition: 'background 0.15s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = '#161b22';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'transparent';
                }}
                onClick={() => {
                  // 复制整行日志
                  const logText = `[${time}] [${level}] ${log.message}`;
                  navigator.clipboard.writeText(logText);
                  message.success('日志已复制');
                }}
                title="点击复制"
              >
                {/* 行号 */}
                <div style={{ 
                  color: '#6e7681', 
                  textAlign: 'right',
                  fontSize: 11,
                  userSelect: 'none'
                }}>
                  {index + 1}
                </div>
                
                {/* 时间戳 */}
                <div style={{ color: '#8b949e' }}>
                  {time}
                </div>
                
                {/* 级别/Emoji */}
                <div style={{ 
                  color: getLevelColor(),
                  fontWeight: log.emoji ? 'normal' : '500'
                }}>
                  {level}
                </div>
                
                {/* 消息内容 */}
                <div style={{ 
                  color: '#c9d1d9',
                  wordBreak: 'break-word',
                  whiteSpace: 'pre-wrap'
                }}>
                  {log.message}
                </div>
              </div>
            );
          })
        )}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
};

export default ContainerLogs;

