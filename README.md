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
| 🎛️ 面板设置 | 面板端口/标题/RCON/模式等配置，修改立即生效 |
| 🔑 RCON 自动检测 | 启动时自动从 `server.properties` 检测/生成 RCON 密码 |

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/xingyiqaq/MCpanel.git
cd MCpanel
```

### 2. 配置

编辑 `config.yaml`（首次可跳过，自动检测）：

```yaml
server:
  host: "0.0.0.0"       # 监听地址
  port: 19888            # 面板端口
  name: "我的世界服务器"   # 面板标题

rcon:
  host: "127.0.0.1"
  port: 25575
  # password: "留空则自动检测"  # 不填则自动从 server.properties 读取

mode: "auto"             # auto / rcon / pipe
```

> **RCON 自动检测**：`rcon.password` 留空或注释，面板启动时会自动从 `server.properties` 读取密码；如果两边都没有，自动生成随机密码写入两边。

## 🌐 在线演示

无需安装即可体验面板全部功能，数据均为模拟数据，仅供功能展示：

👉 **[https://xingyiqaq.github.io/MCpanel/](https://xingyiqaq.github.io/MCpanel/)**

演示模式默认已登录（用户名 `admin`），无需认证。

### 3. 一键启动（自动安装依赖）

```bash
bash start.sh                    # 只开面板
bash start.sh --server           # 面板 + MC 服务器
bash start.sh --stop             # 停止面板
```

首次启动会自动完成以下步骤：
1. **检测 Python** — 若未安装，自动通过 apt/yum/dnf/pacman 安装
2. **检测 PyYAML** — 若未安装，优先从 `setup/wheels/` 离线安装（支持 Python 3.8~3.14）
3. **自动写入 server_dir** — 自动检测服务器根目录并写入 config.yaml
4. **扫描 jar 包** — 自动提取物品/实体/附魔中文名称
5. **启动面板** — 浏览器访问 `http://<服务器IP>:<端口>`

默认账号 `admin` / `admin`，首次登录须修改密码。

## 📂 项目结构

```
MCpanel/
├── panel.py              # 主程序：Web 服务器 + RCON/管道通信
├── discover.py           # 物品/实体/附魔中文名称自动扫描
├── start.sh              # 一键启动脚本（含自动安装依赖）
├── config.yaml           # 配置文件（运行时生成，含密码，不提交 Git）
├── login.html            # 登录页面
├── static/
│   └── index.html        # 主界面（单文件，HTML+CSS+JS）
├── setup/                # 离线安装包
│   ├── install_deps.sh   # 依赖检测与安装脚本
│   └── wheels/           # PyYAML wheel（支持 Python 3.8~3.14）
├── wallpapers/           # 壁纸图片目录
├── .gitignore            # Git 忽略规则
└── README.md
```

## 🔄 通信模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **auto**（推荐） | 优先 RCON，失败自动回退管道 | 通用，最省心 |
| **rcon** | 通过 RCON 协议双向通信 | RCON 已开启的服务器 |
| **pipe** | 通过 stdin 写入命令，日志读取输出 | 无 RCON 权限的服务器 |

## 🎛️ 面板设置说明

在 **配置** tab 下可配置面板自身参数（修改后点击保存，重启生效）：

- **面板标题 / 端口 / 监听地址** — 基本显示设置
- **连接模式** — auto / rcon / pipe
- **RCON 地址 / 端口 / 密码** — 实时检测端口占用和密码一致性
- **服务器目录** — 可在线修改（路径检测）

## 📄 License

本项目采用 **非商用许可**。
未经允许，不得用于任何商业用途。如需商用授权，请联系作者。

> 未经书面许可，本软件不得以任何形式用于营利性项目、付费服务或商业分发。

---

[![GitHub stars](https://img.shields.io/github/stars/xingyiqaq/MCpanel)](https://github.com/xingyiqaq/MCpanel)