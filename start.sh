#!/bin/bash
# ============================================================================
# MC Web 通用启动脚本
# ============================================================================
# 用法:
#   bash mc-web/start.sh           # 只开面板
#   bash mc-web/start.sh --server  # 面板 + 服务器
#   bash mc-web/start.sh --stop    # 关闭面板
#
# 功能:
#   - 扫描 jar 包 → 启动面板（必做）
#   - 可选启动 MC 服务器
#   - 退出时自动清理
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# 如果 start.sh 就在服务器目录，取消下面注释并注释上面那行：
# SERVER_DIR="$SCRIPT_DIR"

cd "$SERVER_DIR" || exit 1

LOG_DIR="$SERVER_DIR/logs"
PANEL_DIR="$SCRIPT_DIR"
PANEL_LOG="/tmp/mc-web-panel.log"
PID_FILE="$SERVER_DIR/mc-server.pid"
PANEL_PID_FILE="$SERVER_DIR/mc-panel.pid"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'

# ===== 自动检测并安装依赖 =====
INSTALL_SCRIPT="$SCRIPT_DIR/setup/install_deps.sh"
if [ -f "$INSTALL_SCRIPT" ]; then
    bash "$INSTALL_SCRIPT" || { echo -e "${RED}❌ 依赖安装失败${NC}"; exit 1; }
else
    if ! command -v python3 &>/dev/null; then
        echo -e "${RED}❌ 未找到 python3，请安装 Python 3.8+${NC}"
        exit 1
    fi
    python3 -c "import yaml" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  安装 PyYAML...${NC}"
        pip3 install pyyaml -q 2>/dev/null || { echo -e "${RED}❌ 请安装 PyYAML: pip3 install pyyaml${NC}"; exit 1; }
    }
fi

# ===== 读取配置 =====
[ ! -f "$PANEL_DIR/config.yaml" ] && { echo -e "${RED}❌ 未找到: $PANEL_DIR/config.yaml${NC}"; exit 1; }
eval $(python3 -c "
import yaml
with open('$PANEL_DIR/config.yaml') as f:
    c = yaml.safe_load(f)
port = c.get('server', {}).get('port', 8690)
name = c.get('server', {}).get('name', 'MC Server')
print(f'PANEL_PORT={port}')
print(f'SERVER_NAME={name}')
")

# ===== --stop 模式：只关闭面板 =====
if [ "$1" = "--stop" ]; then
    if [ -f "$PANEL_PID_FILE" ]; then
        kill $(cat "$PANEL_PID_FILE") 2>/dev/null
        rm -f "$PANEL_PID_FILE"
        echo -e "${GREEN}✅ 面板已停止${NC}"
    else
        echo -e "${YELLOW}⚠️  面板未运行${NC}"
    fi
    exit 0
fi

# ===== 启动面板（不管是否 --server 都先启动面板） =====
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}      MC Web 通用面板${NC}"
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}📋 ${SERVER_NAME}${NC}"
echo -e "${GREEN}📁 ${SERVER_DIR}${NC}"
echo -e ""

# 扫描 jar 包
echo -e "${YELLOW}🔍 扫描 jar 包...${NC}"
python3 "$PANEL_DIR/discover.py" --check "$SERVER_DIR" 2>&1 | sed 's/^/  /'
echo -e ""

# 清理旧面板（多重兜底）
pkill -f "python3.*panel.py" 2>/dev/null
sleep 1
if [ -f "$PANEL_PID_FILE" ]; then
    kill $(cat "$PANEL_PID_FILE") 2>/dev/null; rm -f "$PANEL_PID_FILE"
fi
if ss -tln 2>/dev/null | grep -q ":$PANEL_PORT "; then
    fuser -k "${PANEL_PORT}/tcp" 2>/dev/null; sleep 1
fi

# 启动面板
echo -e "${GREEN}🚀 启动面板...${NC}"
cd "$PANEL_DIR"
nohup python3 panel.py --config "$PANEL_DIR/config.yaml" </dev/null >"$PANEL_LOG" 2>&1 &
PANEL_PID=$!
echo "$PANEL_PID" > "$PANEL_PID_FILE"

for i in $(seq 1 10); do
    sleep 1
    if ss -tln 2>/dev/null | grep -q ":$PANEL_PORT "; then
        echo -e "${GREEN}✅ 面板已启动: http://localhost:${PANEL_PORT}${NC}"
        # 尝试获取 IP
        IP=$(ip -4 addr show | grep -oP 'inet \K[\d.]+' | grep -v '127.0.0.1' | head -1)
        [ -n "$IP" ] && echo -e "   ${CYAN}局域网: http://${IP}:${PANEL_PORT}${NC}"
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "${RED}❌ 面板启动失败${NC}"
        tail -5 "$PANEL_LOG" | sed 's/^/  /'
        rm -f "$PANEL_PID_FILE"
        exit 1
    fi
done

# ===== 如果带 --server 参数，启动 MC 服务器 =====
if [ "$1" = "--server" ]; then
    echo -e ""
    echo -e "${GREEN}🚀 启动 Minecraft 服务器...${NC}"
    mkdir -p "$LOG_DIR"

    # 检查是否已有服务器
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            echo -e "${YELLOW}⚠️  服务器已在运行 (PID: $OLD_PID)${NC}"
            echo -e "${GREEN}  ✅ 面板: http://localhost:${PANEL_PORT}${NC}"
            exit 0
        fi
        rm -f "$PID_FILE"
    fi

    # 退出清理
    cleanup() {
        echo -e ""; echo -e "${YELLOW}🧹 清理...${NC}"
        [ -f "$PANEL_PID_FILE" ] && kill $(cat "$PANEL_PID_FILE") 2>/dev/null && rm -f "$PANEL_PID_FILE" && echo -e "  ${GREEN}✅ 面板已停止${NC}"
        [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
        echo -e "${GREEN}👋 再见！${NC}"
    }
    trap cleanup EXIT
    echo $$ > "$PID_FILE"

    # 查找 Java 启动命令
    JAVA_CMD=""
    if [ -f "run.sh" ]; then
        JAVA_CMD="bash run.sh"
    elif [ -f "start.sh" ] && [ "$(basename "$0")" != "start.sh" ]; then
        JAVA_CMD="bash start.sh"
    elif ls *.jar 2>/dev/null | grep -q -E 'server|forge|fabric|paper'; then
        JAR_FILE=$(ls *.jar | grep -E 'server|forge|fabric|paper' | head -1)
        JAVA_CMD="java -Xmx4G -Xms2G -jar $JAR_FILE nogui"
    else
        echo -e "${YELLOW}⚠️  未找到服务器启动脚本${NC}"
        echo -e "  面板已启动，请手动启动服务器"
        wait $PANEL_PID 2>/dev/null
        exit 0
    fi

    echo -e "  ${GREEN}执行: $JAVA_CMD${NC}"; echo -e ""
    eval "$JAVA_CMD"
    EXIT_CODE=$?
    echo -e ""; echo -e "${RED}❌ 服务器已关闭 (退出码: $EXIT_CODE)${NC}"

    # 自动重启
    if [ $EXIT_CODE -ne 0 ] && [ $EXIT_CODE -ne 130 ] && [ $EXIT_CODE -ne 143 ]; then
        echo -e "${YELLOW}   10 秒后自动重启...${NC}"
        echo -e "${YELLOW}   按 Ctrl+C 取消${NC}"
        sleep 10
        exec "$0" --server "$@"
    fi
else
    # 纯面板模式：提示用户
    echo -e ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${GREEN}  ✅ 面板已就绪${NC}"
    echo -e ""
    echo -e "  ${YELLOW}启动服务器:${NC} bash mc-web/start.sh --server"
    echo -e "  ${YELLOW}停止面板:${NC}   bash mc-web/start.sh --stop"
    echo -e "${CYAN}========================================${NC}"
    echo -e ""
    echo -e "  面板运行在后台 (PID: $PANEL_PID)"
    echo -e "  日志: $PANEL_LOG"
fi