#!/bin/bash
# 更新 TMC Docker 镜像脚本

echo "🔄 停止当前容器..."
docker-compose down

echo "📥 拉取最新镜像..."
docker-compose pull

echo "🚀 启动新容器..."
docker-compose up -d

echo "📋 查看日志..."
docker-compose logs -f --tail=50

