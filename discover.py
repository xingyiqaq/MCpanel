#!/usr/bin/env python3
"""
MC 通用面板 — 离线扫描工具
扫描服务端 jar 包 + 模组 jar 包，提取物品/实体/附魔的中英文名。
输出到 cache/ 目录供 panel.py 使用。
"""
import json
import os
import sys
import zipfile
import re
import shutil
import tempfile
from pathlib import Path

# ===== 配置 =====
CACHE_DIR = "cache"
LANG_OUTPUT = "cache/lang_zh_all.json"
ITEMS_OUTPUT = "cache/items.json"
ENTITIES_OUTPUT = "cache/entities.json"
EFFECTS_OUTPUT = "cache/effects.json"

# 需要扫描的 jar 包路径模式
JAR_PATTERNS = [
    "server.jar",
    "minecraft_server*.jar",
    "versions/*/server.jar",
    "versions/*/*.jar",
    "libraries/net/minecraft/server/*/server-*.jar",
    "libraries/net/minecraft/*/server-*.jar",
]

# 已知的 Minecraft 版本 jar 包名（libraries 路径）
VANILLA_JAR_PATTERNS = [
    "libraries/net/minecraft/server/*/server-*.jar",
    "libraries/net/minecraft/*/server-*.jar",
]

MODS_DIR = "mods"


def find_jars(server_dir):
    """查找所有可扫描的 jar 包"""
    jars = []
    server_dir = Path(server_dir)

    # 按模式搜索
    for pattern in JAR_PATTERNS:
        for p in server_dir.glob(pattern):
            if p.is_file() and p.suffix == '.jar':
                jars.append(p)

    # 搜索 mods 目录
    mods_path = server_dir / MODS_DIR
    if mods_path.is_dir():
        for p in mods_path.glob("*.jar"):
            if p not in jars:
                jars.append(p)

    # 去重
    seen = set()
    unique = []
    for j in jars:
        s = str(j.resolve())
        if s not in seen:
            seen.add(s)
            unique.append(j)
    return unique


def extract_lang_from_jar(jar_path, lang="zh_cn"):
    """从 jar 包中提取语言文件"""
    results = {}
    try:
        with zipfile.ZipFile(jar_path, 'r') as zf:
            for name in zf.namelist():
                # 匹配语言文件: assets/<modid>/lang/zh_cn.json
                m = re.match(r'assets/([^/]+)/lang/(\w+\.json)', name)
                if not m:
                    continue
                modid = m.group(1)
                lang_file = m.group(2)
                lang_key = lang_file.replace('.json', '')
                if lang_key not in (lang, 'en_us'):
                    continue
                try:
                    data = json.loads(zf.read(name))
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if isinstance(value, str):
                                results.setdefault(lang_key, {})[key] = value
                except:
                    pass
    except Exception as ex:
        print(f"  ⚠ {jar_path.name}: {ex}", file=sys.stderr)
    return results


def classify_lang_entries(zh_data, en_data):
    """将语言条目分类为物品、实体、附魔、效果"""
    items = {}
    entities = {}
    enchantments = {}
    effects = {}
    namespaces = {}

    # 优先使用中文，缺失时用英文补充
    all_keys = set(zh_data.keys()) | set(en_data.keys())

    for key in all_keys:
        cn = zh_data.get(key, "")
        en = en_data.get(key, "")
        name = cn or en or key

        # 提取命名空间
        if ':' in key:
            ns = key.split('.')[0] if key.startswith('item.') or key.startswith('entity.') or key.startswith('enchantment.') or key.startswith('effect.') else 'minecraft'
        else:
            ns = 'minecraft'

        # 分类
        if key.startswith('item.'):
            # item.minecraft.diamond -> minecraft:diamond
            item_id = key[5:]  # 去掉 "item."
            items[item_id] = name
        elif key.startswith('entity.minecraft.'):
            ent_id = 'minecraft:' + key[18:]
            entities[ent_id] = name
        elif key.startswith('entity.'):
            # entity.<modid>.<name> -> <modid>:<name>
            ent_id = key[7:]  # 去掉 "entity."
            entities[ent_id] = name
        elif key.startswith('enchantment.minecraft.'):
            ench_id = 'minecraft:' + key[22:]
            enchantments[ench_id] = name
        elif key.startswith('enchantment.'):
            ench_id = key[12:]
            enchantments[ench_id] = name
        elif key.startswith('effect.minecraft.'):
            eff_id = 'minecraft:' + key[17:]
            effects[eff_id] = name
        elif key.startswith('effect.'):
            eff_id = key[7:]
            effects[eff_id] = name
        # 跳过其他类型（如 block.、biome.、subtitles. 等）

    return items, entities, enchantments, effects


def extract_namespace_from_jar(jar_path):
    """从 jar 包中提取命名空间中文名（模组名）"""
    ns_names = {}
    try:
        with zipfile.ZipFile(jar_path, 'r') as zf:
            # 查找 META-INF/mods.toml, pack.mcmeta 或 fabric.mod.json
            for name in zf.namelist():
                if name == 'META-INF/mods.toml':
                    content = zf.read(name).decode('utf-8', errors='replace')
                    m = re.search(r'modId\s*=\s*"([^"]+)"', content)
                    modid = m.group(1) if m else None
                    m2 = re.search(r'displayName\s*=\s*"([^"]+)"', content)
                    display_name = m2.group(1) if m2 else None
                    if modid and display_name:
                        ns_names[modid] = display_name
                elif name == 'fabric.mod.json':
                    data = json.loads(zf.read(name))
                    modid = data.get('id', '')
                    name_field = data.get('name', '')
                    if modid and name_field:
                        ns_names[modid] = name_field
                elif name == 'pack.mcmeta':
                    data = json.loads(zf.read(name))
                    pack = data.get('pack', {})
                    desc = pack.get('description', '')
                    if isinstance(desc, str) and desc:
                        # 有些 pack 的 description 是 JSON 文本
                        if desc.startswith('{'):
                            try:
                                desc = json.loads(desc).get('text', desc)
                            except:
                                pass
                        # 提取模组名（取 #FFFFFF 后面的文本）
                        m = re.search(r'§[0-9a-fklmnor]([^§]+)', desc)
                        if m:
                            # 可能在 sections 里
                            pass
                        # 从 jar 包名推断
                        stem = jar_path.stem
                        # 去掉版本号后缀
                        clean = re.sub(r'-\d+[\d.]*-.*$', '', stem)
                        clean = re.sub(r'-\d+\.\d+.*$', '', clean)
                        ns_names[stem] = clean
    except:
        pass
    return ns_names


def extract_namespace_from_toml(jar_path):
    """更精确地从 mods.toml 提取命名空间中文名"""
    ns_names = {}
    try:
        with zipfile.ZipFile(jar_path, 'r') as zf:
            for name in zf.namelist():
                if name == 'META-INF/mods.toml':
                    content = zf.read(name).decode('utf-8', errors='replace')
                    # 解析 mods.toml
                    mods_section = False
                    current_mod = {}
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.startswith('[[') and 'mods' in line:
                            if current_mod.get('modId') and current_mod.get('displayName'):
                                ns_names[current_mod['modId']] = current_mod['displayName']
                            current_mod = {}
                            mods_section = True
                            continue
                        if mods_section and '=' in line:
                            m = re.match(r'(\w+)\s*=\s*"([^"]*)"', line)
                            if m:
                                current_mod[m.group(1)] = m.group(2)
                    # 最后一个
                    if current_mod.get('modId') and current_mod.get('displayName'):
                        ns_names[current_mod['modId']] = current_mod['displayName']
    except:
        pass
    return ns_names


def scan(server_dir):
    """主扫描流程"""
    server_dir = Path(server_dir)
    if not server_dir.is_dir():
        print(f"❌ 目录不存在: {server_dir}")
        return False

    print(f"🔍 扫描服务端目录: {server_dir}")
    jars = find_jars(server_dir)
    print(f"📦 找到 {len(jars)} 个 jar 包")

    if not jars:
        print("⚠️  未找到任何 jar 包，无法扫描")
        return False

    # 提取语言文件
    merged_zh = {}
    merged_en = {}
    ns_names = {}

    jar_count = 0
    for jar_path in jars:
        try:
            lang_data = extract_lang_from_jar(jar_path, 'zh_cn')
            if 'zh_cn' in lang_data:
                merged_zh.update(lang_data['zh_cn'])
            if 'en_us' in lang_data:
                merged_en.update(lang_data['en_us'])

            # 提取命名空间名
            ns_from_jar = extract_namespace_from_toml(jar_path)
            ns_names.update(ns_from_jar)

            jar_count += 1
            if jar_count % 20 == 0:
                print(f"  已处理 {jar_count}/{len(jars)} 个 jar 包...")
        except Exception as ex:
            print(f"  ⚠ {jar_path.name}: {ex}")
            continue

    print(f"  处理完成: {jar_count} 个 jar 包")
    print(f"  📝 中文条目: {len(merged_zh)}, 英文条目: {len(merged_en)}")

    # 分类
    items, entities, enchantments, effects = classify_lang_entries(merged_zh, merged_en)

    print(f"  🏷️  物品: {len(items)}")
    print(f"  👾 实体: {len(entities)}")
    print(f"  ✨ 附魔: {len(enchantments)}")
    print(f"  🧪 效果: {len(effects)}")
    print(f"  📛 命名空间: {len(ns_names)}")

    # 确保缓存目录存在
    cache_dir = server_dir / CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)

    # 写入 cache 文件
    lang_data = {
        'items': items,
        'entities': entities,
        'enchantments': enchantments,
        'effects': effects,
        'namespaces': ns_names,
    }
    with open(cache_dir / 'lang_zh_all.json', 'w', encoding='utf-8') as f:
        json.dump(lang_data, f, ensure_ascii=False, indent=2)

    # 单独输出物品/实体列表（供前端直接使用）
    with open(cache_dir / 'items.json', 'w', encoding='utf-8') as f:
        json.dump([{'id': k, 'name': v} for k, v in sorted(items.items())], f, ensure_ascii=False, indent=2)

    with open(cache_dir / 'entities.json', 'w', encoding='utf-8') as f:
        json.dump([{'id': k, 'name': v} for k, v in sorted(entities.items())], f, ensure_ascii=False, indent=2)

    with open(cache_dir / 'effects.json', 'w', encoding='utf-8') as f:
        json.dump(enchantments, f, ensure_ascii=False, indent=2)

    print(f"✅ 扫描完成，缓存写入: {cache_dir}")
    return True


def cache_is_fresh(cache_dir, jars):
    """检查缓存是否最新（jar 包未变动）"""
    cache_file = cache_dir / 'items.json'
    if not cache_file.exists():
        return False
    cache_mtime = cache_file.stat().st_mtime
    for jar in jars:
        if jar.stat().st_mtime > cache_mtime:
            return False
    return True


def main():
    check_only = False
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--check' in sys.argv:
        check_only = True

    if args:
        server_dir = args[0]
    else:
        server_dir = '.'

    server_dir = Path(server_dir)
    cache_dir = server_dir / CACHE_DIR

    if check_only:
        if cache_dir.exists() and (cache_dir / 'items.json').exists():
            print(f"✅ 缓存已存在，跳过扫描")
            sys.exit(0)
        else:
            # 需要扫描
            success = scan(server_dir)
            sys.exit(0 if success else 1)
    else:
        success = scan(server_dir)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()