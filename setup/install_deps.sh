#!/bin/bash
# ============================================================================
# MCpanel 依赖安装器 — 离线安装 PyYAML，检测 Python
# ============================================================================
# 用法: bash setup/install_deps.sh
# 从项目根目录运行，或从任意位置运行脚本。
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHEELS_DIR="$SCRIPT_DIR/wheels"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BLUE='\033[0;34m'; NC='\033[0m'

echo -e "${CYAN}════════════════════════════════════════════${NC}"
echo -e "${CYAN}  MCpanel 依赖检测与安装${NC}"
echo -e "${CYAN}════════════════════════════════════════════${NC}"
echo ""

# ============ 检测 Python3 ============
if command -v python3 &>/dev/null; then
    PYVER=$(python3 --version 2>&1)
    echo -e "  ${GREEN}✅${NC} Python 已安装: ${PYVER}"
else
    echo -e "  ${YELLOW}⚠️${NC}  未找到 python3，尝试安装..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update -qq && sudo apt-get install -y -qq python3 python3-pip 2>&1 | tail -3
    elif command -v yum &>/dev/null; then
        sudo yum install -y python3 python3-pip 2>&1 | tail -3
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3 python3-pip 2>&1 | tail -3
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm python python-pip 2>&1 | tail -3
    else
        echo -e "  ${RED}❌ 无法自动安装 Python。请手动安装 Python 3.8+ 后重试。${NC}"
        exit 1
    fi
    if command -v python3 &>/dev/null; then
        echo -e "  ${GREEN}✅${NC} Python 安装成功: $(python3 --version 2>&1)"
    else
        echo -e "  ${RED}❌ Python 安装失败，请手动安装 Python 3.8+${NC}"
        exit 1
    fi
fi

# ============ 检测 PyYAML ============
if python3 -c "import yaml; print('PyYAML', yaml.__version__)" 2>/dev/null; then
    echo -e "  ${GREEN}✅${NC} PyYAML 已安装"
else
    echo -e "  ${YELLOW}⚠️${NC}  PyYAML 未安装，尝试离线安装..."

    if [ ! -d "$WHEELS_DIR" ]; then
        echo -e "  ${YELLOW}⚠️${NC}  未找到离线安装包目录，尝试联网安装..."
        if command -v pip3 &>/dev/null; then
            pip3 install pyyaml -q 2>/dev/null && { echo -e "  ${GREEN}✅${NC} PyYAML 联网安装成功"; } || {
                echo -e "  ${RED}❌ 安装失败${NC}"; exit 1
            }
        elif command -v pip &>/dev/null; then
            pip install pyyaml -q 2>/dev/null && { echo -e "  ${GREEN}✅${NC} PyYAML 联网安装成功"; } || {
                echo -e "  ${RED}❌ 安装失败${NC}"; exit 1
            }
        else
            echo -e "  ${RED}❌ 未找到 pip，且无离线包${NC}"; exit 1
        fi
    else
        # 找到当前 Python 对应的 wheel 文件
        PY_MINOR=$(python3 -c "import sys; print(f'{sys.version_info.major}{sys.version_info.minor}')")
        WHEEL_NAME=""
        for f in "$WHEELS_DIR"/pyyaml-*-cp${PY_MINOR}-*.whl; do
            if [ -f "$f" ]; then WHEEL_NAME="$f"; break; fi
        done
        if [ -z "$WHEEL_NAME" ]; then
            for f in "$WHEELS_DIR"/PyYAML-*-cp${PY_MINOR}-*.whl; do
                if [ -f "$f" ]; then WHEEL_NAME="$f"; break; fi
            done
        fi
        if [ -z "$WHEEL_NAME" ]; then
            echo -e "  ${RED}❌ 未找到匹配 Python ${PY_MINOR} 的 wheel 文件${NC}"
            echo -e "     可用 wheel:"
            ls "$WHEELS_DIR"/*.whl 2>/dev/null | xargs -n1 basename
            echo -e "     尝试联网安装..."
            pip3 install pyyaml -q 2>/dev/null && { echo -e "  ${GREEN}✅${NC} PyYAML 联网安装成功"; } || {
                echo -e "  ${RED}❌ 安装失败${NC}"; exit 1
            }
        else
            echo -e "  ${BLUE}📦${NC}  安装 wheel: $(basename "$WHEEL_NAME")"
            if command -v pip3 &>/dev/null; then
                pip3 install --no-index --find-links="$WHEELS_DIR" pyyaml -q 2>/dev/null
            elif command -v pip &>/dev/null; then
                pip install --no-index --find-links="$WHEELS_DIR" pyyaml -q 2>/dev/null
            else
                echo -e "  ${RED}❌ 未找到 pip，无法安装${NC}"; exit 1
            fi
        fi
    fi

    if python3 -c "import yaml" 2>/dev/null; then
        echo -e "  ${GREEN}✅${NC} PyYAML 安装成功"
    else
        echo -e "  ${RED}❌ PyYAML 安装失败${NC}"
        exit 1
    fi
fi

# ============ 检测 pip 是否存在（用于后续 pip3 --user 等）============
if ! command -v pip3 &>/dev/null && ! command -v pip &>/dev/null; then
    echo -e "  ${YELLOW}⚠️${NC}  pip 未安装，尝试安装..."
    python3 -m ensurepip --upgrade 2>/dev/null || python3 -m pip install --upgrade pip 2>/dev/null || true
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ 所有依赖已就绪！${NC}"
echo -e "${GREEN}════════════════════════════════════════════${NC}"