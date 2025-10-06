# TMC项目清理脚本
# 将开发文档、测试文件、临时文件移动到_archived文件夹

$ErrorActionPreference = "Continue"
$archiveDir = "_archived"

Write-Host "🧹 开始清理项目..." -ForegroundColor Cyan

# 创建归档子文件夹
$folders = @(
    "$archiveDir/docs",
    "$archiveDir/dev-files", 
    "$archiveDir/test-files",
    "$archiveDir/temp-data",
    "$archiveDir/old-scripts"
)

foreach ($folder in $folders) {
    if (-not (Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
    }
}

# 1. 移动文档文件（保留README.md）
Write-Host "📄 移动文档文件..." -ForegroundColor Yellow
$docFiles = @(
    "LOGIN_SYSTEM_README.md",
    "app/backend/README.md",
    "app/backend/REFACTORING_GUIDE.md",
    "app/frontend/README.md",
    "app/frontend/README-API-TYPES.md",
    "app/frontend/MIGRATION_EXAMPLES.md",
    "app/frontend/THEME_MIGRATION.md",
    "app/frontend/THEME_SOLUTION_FINAL.md",
    "app/frontend/THEME_SYSTEM_COMPLETE.md"
)

foreach ($file in $docFiles) {
    if (Test-Path $file) {
        $dest = Join-Path "$archiveDir/docs" (Split-Path $file -Leaf)
        Move-Item -Path $file -Destination $dest -Force
        Write-Host "  ✓ $file -> $dest" -ForegroundColor Green
    }
}

# 移动整个docs文件夹
if (Test-Path "docs") {
    Move-Item -Path "docs" -Destination "$archiveDir/docs/api-docs" -Force
    Write-Host "  ✓ docs/ -> $archiveDir/docs/api-docs/" -ForegroundColor Green
}

# 2. 移动开发配置文件
Write-Host "⚙️  移动开发配置文件..." -ForegroundColor Yellow
$devFiles = @(
    "app/backend/pytest.ini",
    "app/backend/pyproject.toml",
    "app/backend/requirements-dev.txt",
    "app/backend/requirements-test.txt",
    "app/frontend/jest.config.js",
    "app/frontend/vitest.config.ts",
    # "app/frontend/tsconfig.node.json",  # Vite需要，不移动
    "docker-compose.prod.yml"
)

foreach ($file in $devFiles) {
    if (Test-Path $file) {
        $dest = Join-Path "$archiveDir/dev-files" (Split-Path $file -Leaf)
        Move-Item -Path $file -Destination $dest -Force
        Write-Host "  ✓ $file -> $dest" -ForegroundColor Green
    }
}

# 3. 移动测试文件
Write-Host "🧪 移动测试文件..." -ForegroundColor Yellow
if (Test-Path "app/backend/tests") {
    Move-Item -Path "app/backend/tests" -Destination "$archiveDir/test-files/backend-tests" -Force
    Write-Host "  ✓ app/backend/tests/ -> $archiveDir/test-files/backend-tests/" -ForegroundColor Green
}

if (Test-Path "app/frontend/src/test") {
    Move-Item -Path "app/frontend/src/test" -Destination "$archiveDir/test-files/frontend-tests" -Force
    Write-Host "  ✓ app/frontend/src/test/ -> $archiveDir/test-files/frontend-tests/" -ForegroundColor Green
}

# 4. 移动开发脚本
Write-Host "📜 移动开发脚本..." -ForegroundColor Yellow
$scriptFiles = @(
    "app/frontend/migrate-theme.sh",
    "app/frontend/scripts/check-api-sync.js",
    "app/frontend/scripts/generate-api-types.js",
    "app/frontend/scripts/update-all-services.sh",
    "app/backend/migrate_to_v3.py",
    "app/backend/restore_clients.py",
    "check_clients.py"
)

foreach ($file in $scriptFiles) {
    if (Test-Path $file) {
        $dest = Join-Path "$archiveDir/old-scripts" (Split-Path $file -Leaf)
        Move-Item -Path $file -Destination $dest -Force
        Write-Host "  ✓ $file -> $dest" -ForegroundColor Green
    }
}

# 移动scripts文件夹（如果存在）
if (Test-Path "app/frontend/scripts") {
    Move-Item -Path "app/frontend/scripts" -Destination "$archiveDir/old-scripts/frontend-scripts" -Force
    Write-Host "  ✓ app/frontend/scripts/ -> $archiveDir/old-scripts/frontend-scripts/" -ForegroundColor Green
}

if (Test-Path "scripts") {
    Move-Item -Path "scripts" -Destination "$archiveDir/old-scripts/root-scripts" -Force
    Write-Host "  ✓ scripts/ -> $archiveDir/old-scripts/root-scripts/" -ForegroundColor Green
}

# 5. 移动临时数据和日志（保留空文件夹）
Write-Host "🗑️  清理临时数据..." -ForegroundColor Yellow

# 移动开发数据库文件（保留生产数据库）
if (Test-Path "app/backend/data") {
    $backendDataFiles = Get-ChildItem "app/backend/data" -File
    foreach ($file in $backendDataFiles) {
        $dest = Join-Path "$archiveDir/temp-data" $file.Name
        Move-Item -Path $file.FullName -Destination $dest -Force
        Write-Host "  ✓ $file.Name -> $archiveDir/temp-data/" -ForegroundColor Green
    }
}

# 移动backend日志
if (Test-Path "app/backend/logs") {
    $logFiles = Get-ChildItem "app/backend/logs" -File
    foreach ($file in $logFiles) {
        $dest = Join-Path "$archiveDir/temp-data" "backend-$($file.Name)"
        Move-Item -Path $file.FullName -Destination $dest -Force
        Write-Host "  ✓ $file.Name -> $archiveDir/temp-data/" -ForegroundColor Green
    }
}

# 6. 清理备份文件
Write-Host "🔄 清理备份文件..." -ForegroundColor Yellow
if (Test-Path "app/frontend/src/index.css.bak") {
    Move-Item -Path "app/frontend/src/index.css.bak" -Destination "$archiveDir/dev-files/index.css.bak" -Force
    Write-Host "  ✓ index.css.bak -> $archiveDir/dev-files/" -ForegroundColor Green
}

# 7. 移动node_modules（可选，如果需要节省空间）
# Write-Host "📦 移动node_modules（可选）..." -ForegroundColor Yellow
# if (Test-Path "app/frontend/node_modules") {
#     Write-Host "  ⚠️  跳过node_modules（太大，建议手动删除或运行npm ci重新安装）" -ForegroundColor Yellow
# }

Write-Host ""
Write-Host "✅ 清理完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📊 归档文件夹结构：" -ForegroundColor Cyan
Write-Host "  _archived/"
Write-Host "    ├── docs/           # 文档文件"
Write-Host "    ├── dev-files/      # 开发配置文件"
Write-Host "    ├── test-files/     # 测试文件"
Write-Host "    ├── temp-data/      # 临时数据和日志"
Write-Host "    └── old-scripts/    # 旧脚本"
Write-Host ""
Write-Host "🚀 生产环境文件已保留，可以正常运行 docker compose up -d" -ForegroundColor Green

