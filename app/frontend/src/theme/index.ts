/**
 * 主题系统统一导出
 */

export * from './colors';
export * from './ThemeContext';
export * from './styled';

// 使用指南常量
export const THEME_USAGE_GUIDE = `
主题系统使用指南：

1. 获取主题颜色：
   import { useThemeContext } from '@/theme';
   const { colors } = useThemeContext();
   
2. 使用样式：
   <div style={{ color: colors.textPrimary }}>文本</div>
   
3. 创建组件样式：
   const styles = createStyles((colors) => ({
     container: {
       backgroundColor: colors.bgContainer,
       color: colors.textPrimary,
     }
   }));
   
4. 禁止事项：
   ❌ 不要使用硬编码颜色：color: '#141414'
   ❌ 不要使用 CSS 变量在 JSX 中：color: 'var(--color-text-primary)'
   ✅ 始终从 colors 对象获取：color: colors.textPrimary
`;

