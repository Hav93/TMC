import { useState, useEffect } from 'react';

export type ThemeType = 'light' | 'dark';

export interface ThemeConfig {
  type: ThemeType;
}

const THEME_STORAGE_KEY = 'telegram-bot-theme';

const themes = {
  light: {
    name: '日间模式',
    colors: {
      background: '#f0f2f5',
      cardBackground: '#ffffff',
      textPrimary: '#000000',
      textSecondary: '#666666',
      border: '#d9d9d9',
      primary: '#1890ff',
      success: '#52c41a',
      warning: '#faad14',
      error: '#ff4d4f',
    }
  },
  dark: {
    name: '夜间模式',
    colors: {
      background: '#0a0e27',
      cardBackground: '#1a1d2e',
      textPrimary: '#e8eaed',
      textSecondary: '#c8cad0',
      border: '#2a2f45',
      primary: '#1890ff',
      success: '#52c41a',
      warning: '#faad14',
      error: '#ff4d4f',
    }
  }
};

export const useTheme = () => {
  const [themeConfig, setThemeConfig] = useState<ThemeConfig>(() => {
    try {
      const saved = localStorage.getItem(THEME_STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        return { type: parsed.type === 'dark' ? 'dark' : 'light' };
      }
      // 默认根据系统时间决定（6:00-18:00为日间模式）
      const hour = new Date().getHours();
      return { type: (hour >= 6 && hour < 18) ? 'light' : 'dark' };
    } catch {
      return { type: 'light' };
    }
  });

  useEffect(() => {
    const theme = themes[themeConfig.type];
    const body = document.body;
    const root = document.getElementById('root');
    const rootElement = document.documentElement;
    
    // 1. 强制触发重排以避免缓存问题
    void body.offsetHeight;
    
    // 2. 移除旧的主题类和data-theme属性
    body.classList.remove('theme-light', 'theme-dark', 'theme-gradient', 'theme-gray', 'theme-custom');
    rootElement.removeAttribute('data-theme');
    
    // 3. 立即添加新的主题类和data-theme属性
    body.classList.add(`theme-${themeConfig.type}`);
    rootElement.setAttribute('data-theme', themeConfig.type);
    
    // 4. 应用背景色（兼容旧样式）
    const colors = theme.colors;
    body.style.background = colors.background;
    body.style.color = colors.textPrimary;
    
    if (root) {
      root.style.background = colors.background;
      root.style.color = colors.textPrimary;
    }
    
    // 5. 强制所有 Ant Design 组件重新计算样式
    requestAnimationFrame(() => {
      // 触发 CSS 变量更新
      rootElement.style.setProperty('--theme-type', themeConfig.type);
      
      // 更全面的选择器列表，包括所有可能的 Ant Design 组件
      const comprehensiveSelectors = [
        // 布局
        '.ant-layout', '.ant-layout-header', '.ant-layout-sider', '.ant-layout-content', '.ant-layout-footer',
        // 卡片和面板
        '.ant-card', '.ant-card-head', '.ant-card-body', '.ant-collapse', '.ant-collapse-item',
        // 表格
        '.ant-table', '.ant-table-thead', '.ant-table-tbody', '.ant-table-cell',
        // 菜单和导航
        '.ant-menu', '.ant-menu-item', '.ant-menu-submenu', '.ant-breadcrumb',
        // 表单
        '.ant-form', '.ant-form-item', '.ant-input', '.ant-input-number', '.ant-select', 
        '.ant-select-selector', '.ant-picker', '.ant-checkbox', '.ant-radio', '.ant-switch',
        // 按钮
        '.ant-btn', '.ant-btn-primary', '.ant-btn-default',
        // 模态框和抽屉
        '.ant-modal', '.ant-modal-content', '.ant-modal-header', '.ant-modal-body', '.ant-modal-footer',
        '.ant-drawer', '.ant-drawer-content',
        // 下拉和弹出
        '.ant-dropdown', '.ant-dropdown-menu', '.ant-popover', '.ant-tooltip',
        // 标签和徽章
        '.ant-tag', '.ant-badge',
        // 分页
        '.ant-pagination', '.ant-pagination-item',
        // 统计和数据展示
        '.ant-statistic', '.ant-descriptions', '.ant-list', '.ant-list-item',
        // 自定义组件
        '.stats-card', '.glass-card', '.sidebar-logo', '.sidebar-footer', 
        '.user-info', '.header-content', '.layout-header'
      ];
      
      // 方法1: 强制重排和重绘
      comprehensiveSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach((el) => {
          if (el instanceof HTMLElement) {
            void el.offsetHeight; // 强制重排
            el.style.transform = 'translateZ(0)'; // 触发GPU加速重绘
          }
        });
      });
      
      // 方法2: 清理transform并添加临时类触发重绘
      requestAnimationFrame(() => {
        comprehensiveSelectors.forEach(selector => {
          const elements = document.querySelectorAll(selector);
          elements.forEach((el) => {
            if (el instanceof HTMLElement) {
              el.style.transform = '';
              // 添加并立即移除一个类来触发样式重新计算
              el.classList.add('theme-force-update');
              void el.offsetHeight;
              el.classList.remove('theme-force-update');
            }
          });
        });
      });
      
      // 方法3: 强制触发所有元素的样式重新计算
      requestAnimationFrame(() => {
        const allElements = document.querySelectorAll('*');
        allElements.forEach((el) => {
          if (el instanceof HTMLElement) {
            const style = window.getComputedStyle(el);
            void style.backgroundColor;
            void style.color;
          }
        });
      });
    });
    
    // 6. 多阶段延迟刷新 - 确保异步组件和延迟加载的元素也更新
    const refreshDelays = [50, 150, 300, 500];
    refreshDelays.forEach(delay => {
      setTimeout(() => {
        requestAnimationFrame(() => {
          // 全局重排
          void body.offsetHeight;
          void rootElement.offsetHeight;
          
          // 关键组件二次刷新
          const criticalElements = document.querySelectorAll(
            '.ant-card, .ant-table, .ant-modal, .ant-drawer, ' +
            '.ant-menu-item, .ant-input, .ant-select, .ant-btn, ' +
            '.sidebar-logo, .user-info, .stats-card'
          );
          
          criticalElements.forEach(el => {
            if (el instanceof HTMLElement) {
              void el.offsetHeight;
              // 触发样式重新计算
              const computedStyle = window.getComputedStyle(el);
              void computedStyle.backgroundColor; // 读取计算样式强制重新计算
            }
          });
        });
      }, delay);
    });
    
    // 7. 保存到 localStorage
    try {
      localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify(themeConfig));
    } catch (error) {
      console.warn('无法保存主题配置:', error);
    }
  }, [themeConfig]);

  const changeTheme = (type: ThemeType, event?: React.MouseEvent) => {
    // 使用 View Transitions API 实现圆形扩散效果
    if (event && 'startViewTransition' in document) {
      const x = event.clientX;
      const y = event.clientY;
      const endRadius = Math.hypot(
        Math.max(x, window.innerWidth - x),
        Math.max(y, window.innerHeight - y)
      );

      // @ts-ignore - View Transitions API 可能不在类型定义中
      const transition = document.startViewTransition(() => {
        setThemeConfig({ type });
      });

      transition.ready.then(() => {
        // 主圆形扩散动画 - 更自然的缓动
        const clipPath = [
          `circle(0px at ${x}px ${y}px)`,
          `circle(${endRadius}px at ${x}px ${y}px)`
        ];
        
        document.documentElement.animate(
          { clipPath },
          {
            duration: 600,
            easing: 'cubic-bezier(0.4, 0.0, 0.2, 1)', // 更自然的缓动
            pseudoElement: '::view-transition-new(root)'
          }
        );
      });

      // 动画完成后强制刷新所有内联样式
      transition.finished.then(() => {
        // 强制重新渲染所有带内联样式的元素
        const inlineStyledElements = document.querySelectorAll('[style*="color"]');
        inlineStyledElements.forEach(el => {
          if (el instanceof HTMLElement) {
            // 强制重新计算样式
            const styleContent = el.getAttribute('style') || '';
            el.setAttribute('style', styleContent);
            void el.offsetHeight;
          }
        });
      });

      // 动画完成后额外刷新
      transition.finished.then(() => {
        requestAnimationFrame(() => {
          // 强制所有元素重新计算样式
          document.querySelectorAll('*').forEach(el => {
            if (el instanceof HTMLElement) {
              void el.offsetHeight;
            }
          });
        });
      });
    } else {
      // 降级方案：添加过渡类
      document.body.classList.add('theme-transitioning');
      setThemeConfig({ type });
      setTimeout(() => {
        document.body.classList.remove('theme-transitioning');
        // 额外刷新
        requestAnimationFrame(() => {
          document.querySelectorAll('*').forEach(el => {
            if (el instanceof HTMLElement) {
              void el.offsetHeight;
            }
          });
        });
      }, 500);
    }
  };

  const toggleTheme = (event?: React.MouseEvent) => {
    const newType = themeConfig.type === 'light' ? 'dark' : 'light';
    changeTheme(newType, event);
  };

  const getThemeName = () => {
    return themes[themeConfig.type].name;
  };

  const getColors = () => {
    return themes[themeConfig.type].colors;
  };

  return {
    themeConfig,
    changeTheme,
    toggleTheme,
    getThemeName,
    getColors,
    themes
  };
};
