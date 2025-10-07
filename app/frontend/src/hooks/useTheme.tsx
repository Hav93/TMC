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
    
    // 5. 应用 CSS 变量到根元素（利用 CSS 继承机制）
    requestAnimationFrame(() => {
      // 设置主题类型变量
      rootElement.style.setProperty('--theme-type', themeConfig.type);
      
      // 通过修改根元素的 CSS 变量触发全局样式更新
      Object.entries(colors).forEach(([key, value]) => {
        rootElement.style.setProperty(`--${key}`, value);
      });
      
      // 只需要触发根元素和 body 的重排，CSS 变量会自动继承到所有子元素
      void rootElement.offsetHeight;
      void body.offsetHeight;
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
            duration: 300,
            easing: 'cubic-bezier(0.4, 0.0, 0.2, 1)', // 更自然的缓动
            pseudoElement: '::view-transition-new(root)'
          }
        );
      });

      // 动画完成后只需触发根元素重排
      transition.finished.then(() => {
        requestAnimationFrame(() => {
          void document.documentElement.offsetHeight;
          void document.body.offsetHeight;
        });
      });
    } else {
      // 降级方案：添加过渡类
      document.body.classList.add('theme-transitioning');
      setThemeConfig({ type });
      setTimeout(() => {
        document.body.classList.remove('theme-transitioning');
        // 只触发根元素重排
        requestAnimationFrame(() => {
          void document.documentElement.offsetHeight;
          void document.body.offsetHeight;
        });
      }, 300);
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
