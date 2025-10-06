# TMC Icons Guide

## 图标文件清单

### SVG 图标
- `tmc-logo.svg` - 主Logo (256x256)，用于应用内显示
- `tmc-favicon.svg` - Favicon SVG版本，优化用于浏览器标签

### Favicon (浏览器标签)
- `favicon.ico` - 传统ICO格式 (需要生成)
- `favicon-16x16.png` - 16x16 PNG
- `favicon-32x32.png` - 32x32 PNG

### 移动设备
- `apple-touch-icon.png` - iOS设备 (180x180)
- `android-chrome-192x192.png` - Android小图标 (192x192)
- `android-chrome-512x512.png` - Android大图标 (512x512)
- `mstile-150x150.png` - Windows Tiles (150x150，需要生成)

### 配置文件
- `site.webmanifest` - PWA配置
- `browserconfig.xml` - Windows浏览器配置

## 如何生成PNG图标

由于当前环境限制，PNG图标需要手动生成。推荐使用以下工具：

### 方法1: 在线工具（推荐）
访问 https://realfavicongenerator.net/
1. 上传 `tmc-logo.svg`
2. 自动生成所有尺寸的图标
3. 下载并替换到 `public/` 目录

### 方法2: 使用命令行工具
```bash
# 安装 ImageMagick 或 sharp
npm install -g sharp-cli

# 从SVG生成不同尺寸的PNG
sharp -i tmc-logo.svg -o favicon-16x16.png resize 16 16
sharp -i tmc-logo.svg -o favicon-32x32.png resize 32 32
sharp -i tmc-logo.svg -o apple-touch-icon.png resize 180 180
sharp -i tmc-logo.svg -o android-chrome-192x192.png resize 192 192
sharp -i tmc-logo.svg -o android-chrome-512x512.png resize 512 512
sharp -i tmc-logo.svg -o mstile-150x150.png resize 150 150
```

### 方法3: 使用Python脚本
```python
from cairosvg import svg2png

sizes = {
    'favicon-16x16.png': 16,
    'favicon-32x32.png': 32,
    'apple-touch-icon.png': 180,
    'android-chrome-192x192.png': 192,
    'android-chrome-512x512.png': 512,
    'mstile-150x150.png': 150
}

for filename, size in sizes.items():
    svg2png(url='tmc-logo.svg', write_to=filename, 
            output_width=size, output_height=size)
```

## 品牌色彩

- **主色**: `#667eea` (紫色)
- **次色**: `#764ba2` (深紫)
- **深色背景**: `#0a0e27`
- **渐变**: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`

## 使用场景

| 文件 | 使用场景 | 尺寸 |
|------|---------|------|
| tmc-favicon.svg | 现代浏览器标签 | 可缩放 |
| favicon.ico | 传统浏览器 | 16x16/32x32 |
| apple-touch-icon.png | iOS添加到主屏幕 | 180x180 |
| android-chrome-*.png | Android添加到主屏幕 | 192x192/512x512 |
| mstile-150x150.png | Windows 10/11磁贴 | 150x150 |

## PWA支持

`site.webmanifest` 已配置支持PWA（Progressive Web App），包括：
- 应用名称和描述
- 主题颜色
- 启动URL
- 显示模式（standalone）
- 图标集合

当用户将TMC添加到手机主屏幕时，会显示完整的应用图标和名称。

