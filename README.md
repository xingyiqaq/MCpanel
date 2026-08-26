# MC 管理面板 — Docker 镜像

[![Docker](https://img.shields.io/badge/Docker-19888-green)](https://hub.docker.com/)

基于 [mc-web-generic](https://github.com/MC-Web-Team/mc-web-generic) 的 MC 服务器 Web 管理面板。

## 🚀 快速开始

```bash
# 1. 构建镜像
docker build -t mc-panel .

# 2. 运行面板
docker run -d \
  --name mc-panel \
  --restart unless-stopped \
  -p 19888:19888 \
  -v /path/to/mc/data:/mc-data \
  -v /path/to/panel/config:/panel-data \
  mc-panel:latest

# 3. 访问面板
# 浏览器打开: http://<IP>:19888
# 默认账号: xingyi / (首次启动需修改密码)
```

## ⚙️ 配置

### 挂载目录

| 路径 | 说明 |
|------|------|
| `/mc-data` | MC 服务器数据目录（需与 mc-server 的 `/data` 挂载到同一路径） |
| `/panel-data` | 面板配置和缓存（首次启动会自动从镜像复制默认配置） |

### 环境变量

面板通过 RCON 协议连接 MC 服务器（默认 `127.0.0.1:25575`），需确保面板容器与 MC 容器在同一 Docker network 中。

## 🔐 安全

首次启动后请立即修改默认密码（`config.yaml` 中的 `auth.password_hash`）。

## License

MIT
