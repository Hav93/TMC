#!/usr/bin/env node
/**
 * 同步版本号脚本
 * 
 * 从根目录的 VERSION 文件读取版本号，并更新到 package.json
 */

const fs = require('fs');
const path = require('path');

// 读取 VERSION 文件
const versionFile = path.join(__dirname, '..', 'VERSION');
const packageFile = path.join(__dirname, '..', 'app', 'frontend', 'package.json');

try {
  // 读取版本号
  const version = fs.readFileSync(versionFile, 'utf-8').trim();
  
  if (!version) {
    console.error('❌ VERSION 文件为空');
    process.exit(1);
  }
  
  // 读取 package.json
  const packageJson = JSON.parse(fs.readFileSync(packageFile, 'utf-8'));
  
  // 更新版本号
  const oldVersion = packageJson.version;
  packageJson.version = version;
  
  // 写回 package.json (无 BOM)
  const packageContent = JSON.stringify(packageJson, null, 2) + '\n';
  fs.writeFileSync(packageFile, packageContent, { encoding: 'utf-8' });
  
  if (oldVersion === version) {
    console.log(`✅ 版本号已是最新: ${version}`);
  } else {
    console.log(`✅ 版本号已更新: ${oldVersion} → ${version}`);
  }
  
} catch (error) {
  console.error(`❌ 同步版本号失败: ${error.message}`);
  process.exit(1);
}

