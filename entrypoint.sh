#!/bin/bash
# MC Panel Docker Entrypoint
# ============================================
# mc-web-generic Panel
# ============================================

set -e

PANEL_DIR="/mc-web"
CONFIG_DIR="/panel-data"
MC_DATA="/mc-data"

cd "$PANEL_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   🖥️  MC 管理面板"
echo "   mc-web-generic"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

mkdir -p "$CONFIG_DIR"/cache

# 复制 config.yaml（首次启动）
if [ ! -f "$CONFIG_DIR/config.yaml" ] && [ -f "$PANEL_DIR/config.yaml" ]; then
  cp "$PANEL_DIR/config.yaml" "$CONFIG_DIR/config.yaml"
fi

# 注入正确的 server_dir 指向 MC 数据目录
if [ -f "$CONFIG_DIR/config.yaml" ]; then
  sed -i "s|server_dir: .*|server_dir: ${MC_DATA}|" "$CONFIG_DIR/config.yaml"
fi

# 软链接 config 和 cache
rm -f "$PANEL_DIR/config.yaml"
ln -sfn "$CONFIG_DIR/config.yaml" "$PANEL_DIR/config.yaml"
rm -rf "$PANEL_DIR/cache"
ln -sfn "$CONFIG_DIR/cache" "$PANEL_DIR/cache"

echo "  ▶ 启动面板 (port 19888)..."
echo "  ▶ RCON → 127.0.0.1:25575"
echo ""

exec python3 panel.py --config "$CONFIG_DIR/config.yaml"
