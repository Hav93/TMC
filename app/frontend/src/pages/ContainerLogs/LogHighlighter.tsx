import React from 'react';
import { Typography } from 'antd';

const { Text, Link } = Typography;

interface LogHighlighterProps {
  content: string;
  contentTypes?: string[];
  specialContent?: Record<string, any>;  // eslint-disable-line @typescript-eslint/no-unused-vars
}

/**
 * 日志语法高亮组件
 * 支持 JSON、URL、文件路径、关键词等的智能高亮
 */
const LogHighlighter: React.FC<LogHighlighterProps> = ({ 
  content, 
  contentTypes = [],
  specialContent = {}
}) => {
  
  /**
   * 高亮 JSON 内容
   */
  const highlightJSON = (text: string): React.ReactNode => {
    const jsonRegex = /(\{[^{}]*\}|\[[^\[\]]*\])/g;
    const parts = text.split(jsonRegex);
    
    return parts.map((part, index) => {
      if (part.match(jsonRegex)) {
        try {
          const parsed = JSON.parse(part);
          const formatted = JSON.stringify(parsed, null, 2);
          return (
            <code 
              key={index} 
              className="json-block"
              style={{
                display: 'block',
                background: 'rgba(0, 122, 204, 0.1)',
                padding: '8px 12px',
                borderRadius: '4px',
                margin: '4px 0',
                fontSize: '12px',
                fontFamily: 'Monaco, Consolas, monospace',
                whiteSpace: 'pre-wrap',
                border: '1px solid rgba(0, 122, 204, 0.3)'
              }}
            >
              {formatted}
            </code>
          );
        } catch {
          return <span key={index}>{part}</span>;
        }
      }
      return <span key={index}>{part}</span>;
    });
  };

  /**
   * 高亮 URL
   */
  const highlightURL = (text: string): React.ReactNode => {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const parts = text.split(urlRegex);
    
    return parts.map((part, index) => {
      if (part.match(urlRegex)) {
        return (
          <Link 
            key={index} 
            href={part} 
            target="_blank"
            style={{ 
              color: '#1890ff',
              textDecoration: 'underline',
              wordBreak: 'break-all'
            }}
          >
            {part}
          </Link>
        );
      }
      return part;
    });
  };

  /**
   * 高亮关键词（错误、警告、成功等）
   */
  const highlightKeywords = (text: string): React.ReactNode => {
    const patterns = [
      { regex: /(\berror\b|错误|失败|failed|异常|exception)/gi, color: '#ff4d4f', bg: 'rgba(255, 77, 79, 0.1)' },
      { regex: /(\bwarning\b|警告|warn)/gi, color: '#faad14', bg: 'rgba(250, 173, 20, 0.1)' },
      { regex: /(\bsuccess\b|成功|完成|completed|✅)/gi, color: '#52c41a', bg: 'rgba(82, 196, 26, 0.1)' },
      { regex: /(\bdelete\b|删除|移除|removed|🗑️)/gi, color: '#ff7875', bg: 'rgba(255, 120, 117, 0.1)' },
      { regex: /(\bcreate\b|创建|新增|added)/gi, color: '#13c2c2', bg: 'rgba(19, 194, 194, 0.1)' },
    ];

    let result: React.ReactNode = text;

    patterns.forEach(({ regex, color, bg }) => {
      if (typeof result === 'string') {
        const parts = result.split(regex);
        result = parts.map((part, index) => {
          if (part && part.match(regex)) {
            return (
              <span 
                key={`${regex}-${index}`}
                style={{
                  color,
                  background: bg,
                  padding: '2px 4px',
                  borderRadius: '2px',
                  fontWeight: 500
                }}
              >
                {part}
              </span>
            );
          }
          return part;
        });
      }
    });

    return result;
  };

  /**
   * 高亮数字（ID、数量等）
   */
  const highlightNumbers = (nodes: React.ReactNode): React.ReactNode => {
    const processNode = (node: any): any => {
      if (typeof node === 'string') {
        const regex = /\b(\d+)\s*(条|个|次|ms|秒|MB|KB|GB)\b/g;
        const parts = node.split(regex);
        
        return parts.map((part: string, index: number) => {
          if (part.match(/^\d+$/)) {
            return (
              <Text 
                key={index}
                strong
                style={{ 
                  color: '#1890ff',
                  fontSize: '13px'
                }}
              >
                {part}
              </Text>
            );
          }
          return part;
        });
      }
      
      if (Array.isArray(node)) {
        return node.map(processNode);
      }
      
      return node;
    };

    return processNode(nodes);
  };

  /**
   * 高亮文件路径
   */
  const highlightPaths = (text: string): React.ReactNode => {
    const pathRegex = /((?:\/|\\)(?:[\w\-\.]+(?:\/|\\))+[\w\-\.]+)/g;
    const parts = text.split(pathRegex);
    
    return parts.map((part, index) => {
      if (part.match(pathRegex)) {
        return (
          <code 
            key={index}
            style={{
              background: 'rgba(128, 128, 128, 0.1)',
              padding: '2px 6px',
              borderRadius: '3px',
              fontSize: '12px',
              fontFamily: 'Monaco, Consolas, monospace',
              color: '#8c8c8c'
            }}
          >
            {part}
          </code>
        );
      }
      return part;
    });
  };

  /**
   * 应用所有高亮规则
   */
  const applyHighlights = (): React.ReactNode => {
    let processed: React.ReactNode = content;

    // 1. 先处理 JSON（如果有）
    if (contentTypes.includes('json')) {
      processed = highlightJSON(content);
    }

    // 2. 处理 URL
    if (contentTypes.includes('url')) {
      if (typeof processed === 'string') {
        processed = highlightURL(processed);
      }
    }

    // 3. 处理文件路径
    if (contentTypes.includes('path')) {
      if (typeof processed === 'string') {
        processed = highlightPaths(processed);
      }
    }

    // 4. 处理关键词
    if (typeof processed === 'string') {
      processed = highlightKeywords(processed);
    }

    // 5. 最后处理数字
    processed = highlightNumbers(processed);

    return processed;
  };

  return <div className="log-highlighter">{applyHighlights()}</div>;
};

export default LogHighlighter;

