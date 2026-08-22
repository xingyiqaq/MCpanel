# 🎮 MCpanel — Minecraft 服务器 Web 管理面板

> 一个开源的 Minecraft 服务器 Web 管理面板，支持全量物品/实体中文显示，适用于原版 + 模组服务器。

## ✨ 功能一览

| 功能 | 说明 |
|------|------|
| 🏠 状态概览 | 玩家数、TPS、内存、运行时间 |
| 🖥️ RCON 控制台 | 实时发送命令、查看输出 |
| ⚡ 快捷指令 | 一键保存/白名单/天气等常用操作 |
| 🧩 指令生成器 | 图形化生成 `give`/`summon`/`enchant` 等复杂指令 |
| 📋 实时日志 | 自动刷新服务器日志 |
| 👤 玩家统计 | 在线时长排行 |
| 📦 全量物品选择 | 支持中文分类、搜索，自动加载模组物品 |
| 👾 全量实体选择 | 按命名空间分类，支持搜索 |
| 🎨 壁纸背景 | 随机壁纸 + 动态粒子效果 |
| 🔐 登录认证 | 首次强制修改密码，可自定义用户名/密码 |
| ⚙️ 游戏配置 | 在线编辑 `server.properties` |

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/xingyiqaq/MCpanel.git
cd MCpanel
```

### 2. 配置

编辑 `config.yaml`：

```yaml
server:
  port: 8690              # 面板端口
  name: "我的世界服务器"   # 显示名称

rcon:
  host: "127.0.0.1"
  port: 25575
  password: "你的RCON密码"

mode: "auto"             # rcon / pipe / auto
```

> **注意**：RCON 模式需要在 `server.properties` 中开启 `rcon.enabled=true`。

### 3. 启动

```bash
bash start.sh
```

首次启动会自动扫描所有 jar 包，提取物品/实体/附魔的中文名称。后续 jar 包未变时跳过扫描。

打开浏览器访问 `http://<服务器IP>:8690`，默认账号 `admin` / `admin`，首次登录须修改密码。

## 📂 项目结构

```
MCpanel/
├── panel.py            # 主程序：Web 服务器 + RCON/管道通信
├── discover.py         # 物品/实体/附魔中文名称自动扫描
├── start.sh            # 一键启动脚本（含自动扫描）
├── config.yaml         # 配置文件
├── login.html          # 登录页面
├── static/
│   └── index.html      # 主界面（单文件，HTML+CSS+JS）
├── wallpapers/         # 壁纸图片目录
└── README.md
```

## 🔄 通信模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **auto**（推荐） | 优先 RCON，失败自动回退管道 | 通用，最省心 |
| **rcon** | 通过 RCON 协议双向通信 | RCON 已开启的服务器 |
| **pipe** | 通过 stdin 写入命令，日志读取输出 | 无 RCON 权限的服务器 |

## ⚙️ 配置项

```yaml
server:
  host: "0.0.0.0"       # 监听地址
  port: 8690             # 面板端口
  name: "MC Server"      # 面板标题

server_dir: "."          # 服务器根目录（相对 start.sh）

rcon:
  host: "127.0.0.1"
  port: 25575
  password: "1"

mode: "auto"

java_process_keyword: "unix_args.txt"   # Java 进程识别关键词
log_path: "logs/latest.log"             # 日志路径
wallpaper_dir: "wallpapers"             # 壁纸目录
lang_zh_file: "cache/lang_zh_all.json"  # 中文翻译表
```

## 🛠️ 技术栈

- **后端**：Python 3.8+，标准库 `http.server`（零依赖）
- **前端**：纯 HTML + CSS + JavaScript，单文件无框架
- **依赖**：仅需 `PyYAML`（`pip3 install pyyaml`）

## 📄 License

MIT License

---

[![GitHub](https://img.shields.io/github/license/xingyiqaq/MCpanel)](https://github.com/xingyiqaq/MCpanel)
[![GitHub stars](https://img.shields.io/github/stars/xingyiqaq/MCpanel)](https://github.com/xingyiqaq/MCpanel)