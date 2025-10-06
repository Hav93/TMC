# 使用Node.js 18官方镜像
FROM node:18-alpine

# 设置构建时的代理参数（用于下载依赖）
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY

# 设置工作目录
WORKDIR /app

# 如果提供了代理，配置npm使用代理
RUN if [ -n "$HTTP_PROXY" ]; then \
        npm config set proxy $HTTP_PROXY && \
        npm config set https-proxy $HTTPS_PROXY; \
    fi

# 可选：使用国内npm镜像（如果代理不稳定）
# RUN npm config set registry https://registry.npmmirror.com

# 复制package文件
COPY package*.json ./

# 安装依赖（使用构建时代理）
RUN npm ci

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 3000

# 启动开发服务器
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
