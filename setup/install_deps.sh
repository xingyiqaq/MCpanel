#!/bin/bash
# ============================================================================
# MCpanel 依赖安装器 — 离线安装 PyYAML，检测 Python
# 支持 Debian/Ubuntu(apt)、CentOS/RHEL(yum/dnf)、Arch(pacman) 自动安装 Python
# PyYAML 支持离线 wheel 安装（Python 3.8~3.14），处理 PEP 668 环境
# ============================================================================
# 用法: bash setup/install_deps.sh
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

# ============ pip 安装辅助函数（自动处理 PEP 668）============
pip_install() {
    local PY_BIN="${1:-python3}"; shift
    local PKG="$1"; shift

    # 方式 1: --user（大部分环境可用）
    "$PY_BIN" -m pip install --user --no-input -q "$PKG" "$@" 2>/dev/null && return 0

    # 方式 2: --break-system-packages（Debian/Ubuntu 新 Python）
    "$PY_BIN" -m pip install --break-system-packages --no-input -q "$PKG" "$@" 2>/dev/null && return 0

    # 方式 3: 无保护参数直接安装（较老环境）
    "$PY_BIN" -m pip install --no-input -q "$PKG" "$@" 2>/dev/null && return 0

    return 1
}

pip_install_wheel() {
    local PY_BIN="${1:-python3}"; shift
    local WHEELS_DIR="$1"; shift

    PY_MINOR=$("$PY_BIN" -c "import sys; print(f'{sys.version_info.major}{sys.version_info.minor}')")

    # 找匹配 wheel
    local WHEEL=""
    for f in "$WHEELS_DIR"/pyyaml-*-cp${PY_MINOR}-*.whl; do
        [ -f "$f" ] && { WHEEL="$f"; break; }
    done
    [ -z "$WHEEL" ] && for f in "$WHEELS_DIR"/PyYAML-*-cp${PY_MINOR}-*.whl; do
        [ -f "$f" ] && { WHEEL="$f"; break; }
    done

    if [ -z "$WHEEL" ]; then
        return 2
    fi

    echo -e "  ${BLUE}📦${NC}  离线安装: $(basename "$WHEEL")"

    # 方式 1: --user（找 pyyaml 包名，从 wheel 目录安装）
    "$PY_BIN" -m pip install --user --no-index --no-deps --find-links="$WHEELS_DIR" pyyaml -q 2>/dev/null && return 0
    # 方式 2: --break-system-packages
    "$PY_BIN" -m pip install --break-system-packages --no-index --no-deps --find-links="$WHEELS_DIR" pyyaml -q 2>/dev/null && return 0
    # 方式 3: 直接安装
    "$PY_BIN" -m pip install --no-index --no-deps --find-links="$WHEELS_DIR" pyyaml -q 2>/dev/null && return 0

    return 1
}

# ============ 检测 Python3 ============
PY_BIN=""
for candidate in python3 python3.12 python3.11 python3.10 python3.9 python3.8 python; do
    if command -v "$candidate" &>/dev/null; then
        PY_BIN="$candidate"
        break
    fi
done

if [ -n "$PY_BIN" ]; then
    PYVER=$($PY_BIN --version 2>&1)
    echo -e "  ${GREEN}✅${NC} Python 已安装: ${PYVER} ($PY_BIN)"
else
    echo -e "  ${YELLOW}⚠️${NC}  未找到 python3，尝试安装..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update -qq 2>/dev/null
        sudo apt-get install -y -qq python3 python3-pip 2>&1 | tail -3
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
        PY_BIN="python3"
        echo -e "  ${GREEN}✅${NC} Python 安装成功: $($PY_BIN --version 2>&1)"
    else
        echo -e "  ${RED}❌ Python 安装失败${NC}"; exit 1
    fi
fi

# ============ 检测/安装 pip ============
if ! $PY_BIN -m pip --version &>/dev/null; then
    echo -e "  ${YELLOW}⚠️${NC}  pip 未安装，尝试安装..."
    $PY_BIN -m ensurepip --upgrade 2>/dev/null || $PY_BIN -m pip install --upgrade pip 2>/dev/null || true
    if ! $PY_BIN -m pip --version &>/dev/null; then
        echo -e "  ${YELLOW}⚠️${NC}  pip 安装失败，但 PyYAML 可能已随系统安装"
    fi
fi

# ============ 检测/安装 PyYAML ============
if $PY_BIN -c "import yaml; print('PyYAML', yaml.__version__)" 2>/dev/null; then
    echo -e "  ${GREEN}✅${NC} PyYAML 已安装"
else
    echo -e "  ${YELLOW}⚠️${NC}  PyYAML 未安装，尝试安装..."

    if [ -d "$WHEELS_DIR" ]; then
        pip_install_wheel "$PY_BIN" "$WHEELS_DIR" || true
    fi

    # 离线安装失败则尝试联网
    if ! $PY_BIN -c "import yaml" 2>/dev/null; then
        echo -e "  ${YELLOW}⚠️${NC}  离线安装失败，尝试联网安装..."
        pip_install "$PY_BIN" pyyaml || {
            echo -e "  ${RED}❌ PyYAML 安装失败，请手动: pip3 install pyyaml${NC}"
            exit 1
        }
    fi

    $PY_BIN -c "import yaml" 2>/dev/null && echo -e "  ${GREEN}✅${NC} PyYAML 安装成功" || {
        echo -e "  ${RED}❌ PyYAML 安装失败${NC}"; exit 1
    }
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ 所有依赖已就绪！${NC}"
echo -e "${GREEN}════════════════════════════════════════════${NC}"