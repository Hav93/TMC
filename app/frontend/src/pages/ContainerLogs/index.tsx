import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, Button, Space, Switch, Typography, Tag, Select, Input, Tabs, message, Modal } from 'antd';
import { 
  ReloadOutlined, 
  PauseCircleOutlined, 
  PlayCircleOutlined,
  ClearOutlined,
  DownloadOutlined 
} from '@ant-design/icons';
import { List, useDynamicRowHeight } from 'react-window';
import { useThemeContext } from '../../theme';
import SmartLogItem from './SmartLogItem';
import './styles.css';

const { Title, Text } = Typography;
const { Option } = Select;

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
  const [availableSources, setAvailableSources] = useState<string[]>([]);
  const [selectedSources, setSelectedSources] = useState<string[]>([]); // 空数组表示显示所有源
  const [selectedLevels, setSelectedLevels] = useState<string[]>([]);
  const [keyword, setKeyword] = useState<string>('');
  const [showStructured, setShowStructured] = useState<boolean>(true); // 是否显示结构化信息
  const [contextModalVisible, setContextModalVisible] = useState(false);
  const [contextLogs, setContextLogs] = useState<LogEntry[]>([]);
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const logsContainerRef = useRef<HTMLDivElement>(null);
  const hasLoadedHistoryRef = useRef(getHasLoadedHistory()); // 从sessionStorage恢复状态
  const saveTimerRef = useRef<NodeJS.Timeout | null>(null); // sessionStorage 保存防抖定时器
  
  // 使用动态行高管理
  const dynamicRowHeight = useDynamicRowHeight({ defaultRowHeight: 100 });
  
  const MAX_LOGS_PER_SOURCE = 500; // 每个来源最多保留500条日志
  const MAX_LOGS_TOTAL = 500; // 不分组时总共最多保留500条日志
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

  // 根据当前Tab显示的日志
  const displayLogs = React.useMemo(() => {
    return groupedLogs[activeTab] || [];
  }, [groupedLogs, activeTab]);

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
    
    if (selectedSources.length > 0) params.set('sources', selectedSources.join(','));
    if (selectedLevels.length > 0) params.set('levels', selectedLevels.join(','));
    if (keyword.trim()) params.set('keyword', keyword.trim());
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
          // 初始或新增源通知
          const msg: any = data as any;
          if (Array.isArray(msg.sources)) {
            setAvailableSources(prev => Array.from(new Set([...(prev || []), ...msg.sources])));
          }
          if (msg.source) {
            setAvailableSources(prev => Array.from(new Set([...(prev || []), msg.source])));
          }
          // 不将连接消息添加到日志列表
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

  // 当搜索关键词变化时重新连接（注意：级别过滤和Tab切换不需要重连，因为是前端过滤）
  useEffect(() => {
    // 避免首次还未建立连接时立即重连
    if (eventSourceRef.current && keyword.trim()) {
      disconnect();
      // 不清空日志，保留已有日志
      connect(false); // 过滤条件变化时不加载历史日志
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [keyword]); // 只有搜索关键词变化时才重连，级别过滤在前端完成

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

  // 获取日志行的级别样式和高亮
  const getLogClass = (level?: string, type?: string, message?: string) => {
    if (type === 'error') return 'log-error';
    if (!level) return 'log-default';
    
    const upperLevel = level.toUpperCase();
    if (upperLevel === 'ERROR' || upperLevel === 'CRITICAL') return 'log-error';
    if (upperLevel === 'WARNING' || upperLevel === 'WARN') return 'log-warning';
    if (upperLevel === 'INFO') return 'log-info';
    if (upperLevel === 'DEBUG') return 'log-debug';
    return 'log-default';
  };

  // 检查是否是关键操作（需要高亮）
  const isHighlightLog = (message?: string) => {
    if (!message) return false;
    const msg = message.toLowerCase();
    return msg.includes('删除') || 
           msg.includes('delete') || 
           msg.includes('❌') || 
           msg.includes('✅') || 
           msg.includes('🗑️') ||
           msg.includes('错误') ||
           msg.includes('失败') ||
           msg.includes('成功') ||
           msg.includes('error') ||
           msg.includes('failed') ||
           msg.includes('success');
  };

  // 根据消息内容获取图标
  const getLogIcon = (message?: string) => {
    if (!message) return null;
    const msg = message.toLowerCase();
    if (msg.includes('删除') || msg.includes('delete') || msg.includes('🗑️')) return '🗑️';
    if (msg.includes('成功') || msg.includes('success') || msg.includes('✅')) return '✅';
    if (msg.includes('失败') || msg.includes('failed') || msg.includes('❌')) return '❌';
    if (msg.includes('警告') || msg.includes('warning') || msg.includes('⚠️')) return '⚠️';
    if (msg.includes('错误') || msg.includes('error')) return '❌';
    if (msg.includes('启动') || msg.includes('start')) return '🚀';
    if (msg.includes('停止') || msg.includes('stop')) return '🛑';
    return null;
  };

  // 查看日志上下文
  const handleShowContext = (log: LogEntry) => {
    setSelectedLog(log);
    
    // 查找相关日志（前后5条）
    const logIndex = displayLogs.findIndex(l => l.timestamp === log.timestamp && l.message === log.message);
    if (logIndex !== -1) {
      const start = Math.max(0, logIndex - 5);
      const end = Math.min(displayLogs.length, logIndex + 6);
      setContextLogs(displayLogs.slice(start, end));
      setContextModalVisible(true);
    }
  };

  // 复制日志
  const handleCopyLog = useCallback(() => {
    message.success('日志已复制到剪贴板');
  }, []);

  // 渲染单个日志项（用于虚拟滚动）
  const LogRow = useCallback(({ index, style }: any) => {
    const log = displayLogs[index];
    if (!log) return null;

    return (
      <div style={style}>
        <SmartLogItem
          log={log}
          index={index}
          showSource={activeTab === 'all'}
          isStructured={showStructured}
          onCopyLog={handleCopyLog}
          onShowContext={handleShowContext}
        />
      </div>
    );
  }, [displayLogs, activeTab, showStructured, handleCopyLog]);

  return (
    <div className="container-logs-page">
      <Card
        title={
          <Title level={4} style={{ margin: 0, color: colors.textPrimary }}>
            容器日志
          </Title>
        }
        extra={
          <Space size="middle" wrap>
            <div>
              <Text type="secondary" style={{ marginRight: 8 }}>级别</Text>
              <Select
                mode="multiple"
                allowClear
                placeholder="选择级别"
                style={{ minWidth: 200 }}
                value={selectedLevels}
                onChange={setSelectedLevels}
              >
                {['DEBUG','INFO','WARNING','ERROR','CRITICAL'].map(lv => (
                  <Option key={lv} value={lv}>{lv}</Option>
                ))}
              </Select>
            </div>
            <div>
              <Input.Search
                allowClear
                placeholder="关键字过滤"
                style={{ width: 200 }}
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                onSearch={() => {
                  disconnect();
                  setLogs([]);
                  connect(false); // 搜索过滤不加载历史日志
                }}
              />
            </div>
            <Switch
              checkedChildren="结构化"
              unCheckedChildren="原始"
              checked={showStructured}
              onChange={setShowStructured}
            />
            <Switch
              checkedChildren="自动滚动"
              unCheckedChildren="自动滚动"
              checked={autoScroll}
              onChange={setAutoScroll}
            />
            <Button
              icon={isPaused ? <PlayCircleOutlined /> : <PauseCircleOutlined />}
              onClick={togglePause}
            >
              {isPaused ? '继续' : '暂停'}
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                console.log('[重新连接] 清空日志、缓存，并重新加载历史');
                disconnect();
                setLogs([]);
                sessionStorage.removeItem('containerLogs');
                sessionStorage.removeItem('containerLogsHistoryLoaded');
                hasLoadedHistoryRef.current = false; // 允许重新加载历史
                connect(true); // 重新连接时加载历史日志
              }}
            >
              重新连接
            </Button>
            <Button
              icon={<ClearOutlined />}
              onClick={clearLogs}
            >
              清空
            </Button>
            <Button
              icon={<DownloadOutlined />}
              onClick={exportLogs}
              disabled={logs.length === 0}
            >
              导出
            </Button>
          </Space>
        }
        style={{
          background: colors.bgContainer,
          border: `1px solid ${colors.borderLight}`,
        }}
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: 'all',
              label: (
                <span>
                  全部日志 <Tag color="blue">{groupedLogs.all?.length || 0}</Tag>
                </span>
              ),
            },
            {
              key: 'enhanced_bot.log',
              label: (
                <span>
                  消息转发 <Tag color="green">{groupedLogs['enhanced_bot.log']?.length || 0}</Tag>
                </span>
              ),
            },
            {
              key: 'api.log',
              label: (
                <span>
                  API日志 <Tag color="orange">{groupedLogs['api.log']?.length || 0}</Tag>
                </span>
              ),
            },
            {
              key: 'web_api.log',
              label: (
                <span>
                  Web日志 <Tag color="purple">{groupedLogs['web_api.log']?.length || 0}</Tag>
                </span>
              ),
            },
          ]}
          style={{ marginBottom: '16px' }}
        />

        <div className="logs-stats" style={{ marginBottom: '16px' }}>
          <Space size="large">
            <Tag color="blue">
              当前显示: {displayLogs.length} / {activeTab === 'all' ? MAX_LOGS_PER_SOURCE * 3 : MAX_LOGS_PER_SOURCE}
            </Tag>
            <Tag color="green">状态: {isConnected ? '实时推送' : '已断开'}</Tag>
            {isPaused && <Tag color="orange">已暂停</Tag>}
          </Space>
        </div>

        <div 
          ref={logsContainerRef}
          className="logs-container"
          style={{
            background: colors.bgLayout,
            border: `1px solid ${colors.borderLight}`,
            borderRadius: '8px',
            height: 'calc(100vh - 320px)',
            minHeight: '400px',
            fontFamily: 'Monaco, Consolas, "Courier New", monospace',
            fontSize: '13px',
            lineHeight: '1.5',
          }}
        >
          {displayLogs.length === 0 ? (
            <div style={{ 
              textAlign: 'center', 
              padding: '40px',
              color: colors.textSecondary 
            }}>
              <div style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.3 }}>📋</div>
              <div>暂无日志数据</div>
              <div style={{ fontSize: '12px', marginTop: '8px' }}>
                {isConnected ? '等待容器输出日志...' : '点击"重新连接"按钮连接到容器'}
              </div>
            </div>
          ) : (
            <List
              rowCount={displayLogs.length}
              rowHeight={dynamicRowHeight}
              rowComponent={LogRow}
              rowProps={{}}
              overscanCount={5}
              style={{ padding: '16px' }}
            />
          )}
          <div ref={logsEndRef} />
        </div>
      </Card>

      {/* 日志上下文模态框 */}
      <Modal
        title={
          <Space>
            <span>日志上下文</span>
            {selectedLog && (
              <Tag color="blue">{selectedLog.timestamp}</Tag>
            )}
          </Space>
        }
        open={contextModalVisible}
        onCancel={() => setContextModalVisible(false)}
        footer={null}
        width={1000}
        bodyStyle={{ maxHeight: '600px', overflow: 'auto' }}
      >
        {contextLogs.map((log, index) => {
          const isSelected = selectedLog && 
            log.timestamp === selectedLog.timestamp && 
            log.message === selectedLog.message;
          
          return (
            <div 
              key={index}
              style={{
                background: isSelected ? colors.info + '20' : 'transparent',
                border: isSelected ? `2px solid ${colors.info}` : '1px solid transparent',
                borderRadius: '6px',
                marginBottom: '8px'
              }}
            >
              <SmartLogItem
                log={log}
                index={index}
                showSource={true}
                isStructured={showStructured}
                onCopyLog={handleCopyLog}
              />
            </div>
          );
        })}
      </Modal>
    </div>
  );
};

export default ContainerLogs;

