#!/usr/bin/env python3
"""MC Web 通用面板 v2 — 通过 config.yaml 配置，可复用于任意 MC 服务器。"""
import http.server,socketserver,json,threading,time,re,os,struct,subprocess,signal,select,socket,sys,yaml,gzip,secrets,string,hmac,hashlib
from urllib.parse import urlparse,parse_qs
from datetime import datetime
from pathlib import Path

# 加载配置
CONFIG_PATH='config.yaml'
# 优先查找脚本所在目录的 config.yaml
_SCRIPT_DIR=os.path.dirname(os.path.abspath(__file__))
_SCRIPT_CONFIG=os.path.join(_SCRIPT_DIR,'config.yaml')
if os.path.exists(_SCRIPT_CONFIG): CONFIG_PATH=_SCRIPT_CONFIG
for i,arg in enumerate(sys.argv):
    if arg=='--config' and i+1<len(sys.argv): CONFIG_PATH=sys.argv[i+1]
if not os.path.exists(CONFIG_PATH): print(f'❌ 配置不存在: {CONFIG_PATH}'); sys.exit(1)
with open(CONFIG_PATH,encoding='utf-8') as f: CONFIG=yaml.safe_load(f)

sv=CONFIG.get('server',{})
HOST=sv.get('host','0.0.0.0'); PORT=sv.get('port',8690); SERVER_NAME=sv.get('name','MC Server')
SERVER_DIR=os.path.abspath(CONFIG.get('server_dir','.'))
rc=CONFIG.get('rcon',{})
RCON_HOST=rc.get('host','127.0.0.1'); RCON_PORT=rc.get('port',25575); RCON_PASSWORD=str(rc.get('password',''))
MODE=CONFIG.get('mode','auto').lower()
JAVA_KEYWORD=CONFIG.get('java_process_keyword','unix_args.txt')
LOG_FILE=os.path.join(SERVER_DIR,CONFIG.get('log_path','logs/latest.log'))
WALLPAPER_DIR=CONFIG.get('wallpaper_dir','')
LANG_ZH_FILE=CONFIG.get('lang_zh_file','cache/lang_zh_all.json')
if LANG_ZH_FILE and not os.path.isabs(LANG_ZH_FILE): LANG_ZH_FILE=os.path.join(os.path.dirname(os.path.abspath(__file__)),LANG_ZH_FILE)

WALLPAPERS=[]
if WALLPAPER_DIR:
    wd=WALLPAPER_DIR if os.path.isabs(WALLPAPER_DIR) else os.path.join(os.path.dirname(os.path.abspath(__file__)),WALLPAPER_DIR)
    if os.path.isdir(wd):
        for ext in ('png','jpg','jpeg','webp'):
            for f in sorted(Path(wd).glob(f'*.{ext}')): WALLPAPERS.append(str(f))

print(f'🎮 {SERVER_NAME}\n📁 {SERVER_DIR}\n🔌 {HOST}:{PORT}\n📡 {MODE}\n🔑 RCON: {RCON_HOST}:{RCON_PORT}\n📜 {LOG_FILE}\n🖼️ {len(WALLPAPERS)}张')

# ===== 认证模块 =====
_DEFAULT_USER='admin';_DEFAULT_PASS='admin';_SESSION_TTL=7200

def _make_hash(pwd,salt=None):
    if salt is None: salt=os.urandom(16)
    return salt+hashlib.pbkdf2_hmac('sha256',pwd.encode('utf-8'),salt,100000)

_AUTH_USER=_DEFAULT_USER
_AUTH_PASS_HASH=_make_hash(_DEFAULT_PASS)
_AUTH_MUST_CHANGE=True
_AUTH_SESSIONS={};_AUTH_LOCK=threading.Lock()

def _verify_hash(pwd,stored):
    s=stored[:16];e=stored[16:]
    dk=hashlib.pbkdf2_hmac('sha256',pwd.encode('utf-8'),s,100000)
    return hmac.compare_digest(dk,e)

def _load_auth():
    global _AUTH_USER,_AUTH_PASS_HASH,_AUTH_MUST_CHANGE
    ca=CONFIG.get('auth',{})
    if not ca: _save_auth();return
    _AUTH_USER=ca.get('username',_DEFAULT_USER)
    hx=ca.get('password_hash','')
    if hx:
        try:
            h=bytes.fromhex(hx)
            if len(h)!=48:
                _AUTH_PASS_HASH=_make_hash(_DEFAULT_PASS);_AUTH_MUST_CHANGE=True
            else:
                _AUTH_PASS_HASH=h
        except:_AUTH_PASS_HASH=_make_hash(_DEFAULT_PASS);_AUTH_MUST_CHANGE=True
    else:_AUTH_PASS_HASH=_make_hash(_DEFAULT_PASS);_AUTH_MUST_CHANGE=True
    _AUTH_MUST_CHANGE=bool(ca.get('must_change',True))

def _save_auth():
    global _AUTH_PASS_HASH
    cfg=CONFIG.copy()
    cfg['auth']={'username':_AUTH_USER,'password_hash':_AUTH_PASS_HASH.hex(),'must_change':_AUTH_MUST_CHANGE}
    with open(CONFIG_PATH,'w',encoding='utf-8') as f:
        yaml.dump(cfg,f,allow_unicode=True,default_flow_style=False)

def _create_session():
    tok=secrets.token_hex(32)
    with _AUTH_LOCK:_AUTH_SESSIONS[tok]={'user':_AUTH_USER,'expires':time.time()+_SESSION_TTL,'must_change':_AUTH_MUST_CHANGE}
    return tok

def _validate(tok):
    if not tok:return None
    with _AUTH_LOCK:
        s=_AUTH_SESSIONS.get(tok)
        if not s:return None
        if time.time()>s['expires']:del _AUTH_SESSIONS[tok];return None
        s['expires']=time.time()+_SESSION_TTL
        return s

def _destroy(tok):
    if tok:
        with _AUTH_LOCK:_AUTH_SESSIONS.pop(tok,None)

def _get_tok(headers):
    ck=headers.get('Cookie','')
    for p in ck.split(';'):
        p=p.strip()
        if p.startswith('mc_panel_session='):return p.split('=',1)[1]
    return None

_load_auth()
print(f'🔐 Auth: user={_AUTH_USER}, must_change={_AUTH_MUST_CHANGE}')

# 加载登录页
_SCRIPT_DIR_=os.path.dirname(os.path.abspath(__file__))
_LOGIN_PAGE_PATH=os.path.join(_SCRIPT_DIR_,'login.html')
with open(_LOGIN_PAGE_PATH,'r',encoding='utf-8') as f:LOGIN_PAGE=f.read()
print(f'🔐 登录页已加载: {_LOGIN_PAGE_PATH}')

# RCON 客户端
class RCON:
    def __init__(self,host,port,pswd): self.host,self.port,self.password=host,port,pswd; self._socket=None; self._rid=0
    def connect(self):
        if self._socket:
            try: self._socket.close()
            except: pass
        self._socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM); self._socket.settimeout(10)
        self._socket.connect((self.host,self.port)); self._rid=0
        self._send_packet(0,3,self.password)
        rid, ptype, payload = self._recv_response()
        if rid != 0:
            self.close()
            raise ConnectionError(f'认证失败 rid={rid} payload={payload[:50]}')
    def _send_packet(self,rid,ptype,payload):
        if not self._socket: raise ConnectionError('socket is None')
        d=payload.encode('utf-8')+b'\0\0'; r=len(d)+8
        self._socket.sendall(struct.pack('<II',r,rid)+struct.pack('<H',ptype)+b'\0\0'+d)
    def _recv_response(self):
        if not self._socket: raise ConnectionError('socket is None')
        h=b''
        while len(h)<4:
            try: ch=self._socket.recv(4-len(h))
            except(OSError,ConnectionResetError,ConnectionAbortedError)as ex: self._socket=None;raise ConnectionError('recv: '+str(ex))
            if not ch: self._socket=None;raise ConnectionError('EOF')
            h+=ch
        l=struct.unpack('<I',h)[0]
        if l<=0 or l>10_000_000: self._socket=None;raise ConnectionError('bad len: '+str(l))
        b=b''
        while len(b)<l:
            try: ch=self._socket.recv(4096)
            except(OSError,ConnectionResetError,ConnectionAbortedError)as ex: self._socket=None;raise ConnectionError('recv: '+str(ex))
            if not ch: self._socket=None;raise ConnectionError('EOF')
            b+=ch
        return struct.unpack('<I',b[:4])[0],struct.unpack('<H',b[4:6])[0],b[8:].rstrip(b'\0').decode('utf-8',errors='replace')
    def command(self,cmd):
        for a in range(2):
            try:
                self._send_packet(self._rid,2,cmd); self._rid+=1
                r,_,p=self._recv_response(); return '❌ 命令执行失败' if r==0xFFFFFFFF else p
            except(ConnectionError,OSError,BrokenPipeError,AttributeError):
                if a==0: self.close();self.connect();continue
                return '❌ RCON 连接失败'
        return '❌ RCON 连接失败'
    def close(self):
        if self._socket:
            try: self._socket.close()
            except: pass
            self._socket=None

# RCON 管理器
_rcon_lock,_rcon_client=threading.Lock(),None
def get_rcon():
    global _rcon_client
    if _rcon_client is None: _rcon_client=RCON(RCON_HOST,RCON_PORT,RCON_PASSWORD)
    return _rcon_client
def rcon_command(cmd):
    global _rcon_client
    with _rcon_lock:
        try: return get_rcon().command(cmd)
        except Exception: _rcon_client=None; return '❌ RCON 连接失败'
if MODE in('rcon','auto'):
    def _hb():
        while True:
            time.sleep(30)
            try:
                with _rcon_lock: get_rcon().command('list')
            except: pass
    threading.Thread(target=_hb,daemon=True).start()

# 管道模式
def pipe_send(cmd):
    try:
        r=subprocess.run(['pgrep','-f',JAVA_KEYWORD],capture_output=True,text=True,timeout=5)
        pids=[p.strip() for p in r.stdout.strip().split('\n') if p.strip().isdigit()]
        if not pids: return '❌ 未找到服务器进程'
        sp=f'/proc/{pids[0]}/fd/0'
        if not os.path.exists(sp): return '❌ 无法访问 stdin'
        with open(sp,'w') as f: f.write(cmd+'\n')
        return f'✅ 命令已发送: {cmd}\n（管道模式，输出请看日志）'
    except: return '❌ 管道写入失败'

def send_cmd(cmd):
    if MODE=='pipe': return pipe_send(cmd)
    r=rcon_command(cmd)
    if MODE=='auto' and r.startswith('❌'): return pipe_send(cmd)
    return r

# 全局状态
class State:
    def __init__(s):
        s.tps=None;s.player_count=0;s.players=[];s.memory_used=None;s.memory_max=None
        s.log_lines=[];s.log_max=600;s.pids=[]
state=State()

# 快捷指令
QUICK=[
    {'name':'保存世界','cmd':'save-all','desc':'保存所有世界','cat':'管理'},
    {'name':'重载配置','cmd':'reload','desc':'重新加载服务端配置','cat':'管理'},
    {'name':'玩家列表','cmd':'list','desc':'显示所有在线玩家','cat':'信息'},
    {'name':'显示TPS','cmd':'forge tps','desc':'查看服务器TPS','cat':'信息'},
    {'name':'白名单开','cmd':'whitelist on','desc':'启用白名单','cat':'管理'},
    {'name':'白名单关','cmd':'whitelist off','desc':'关闭白名单','cat':'管理'},
    {'name':'天气晴天','cmd':'weather clear','desc':'设置为晴天','cat':'世界'},
    {'name':'天气雨天','cmd':'weather rain','desc':'设置为雨天','cat':'世界'},
    {'name':'时间白天','cmd':'time set day','desc':'设置时间为白天','cat':'世界'},
    {'name':'时间夜晚','cmd':'time set night','desc':'设置时间为夜晚','cat':'世界'},
    {'name':'暂停时间','cmd':'gamerule doDaylightCycle false','desc':'暂停昼夜循环','cat':'世界'},
    {'name':'停止怪物刷','cmd':'gamerule doMobSpawning false','desc':'停止怪物生成','cat':'世界'},
    {'name':'死亡保留物品','cmd':'gamerule keepInventory true','desc':'死亡保留物品','cat':'游戏'},
    {'name':'全服通知','cmd':'say 服务器公告','desc':'发送全服消息','cat':'管理'},
]

# 全部指令
ALL_CMDS=[
    {'cmd':'help','cn':'帮助','usage':'help [<command>]','cat':'信息','desc':'显示所有可用指令'},
    {'cmd':'list','cn':'玩家列表','usage':'list [uuids]','cat':'信息','desc':'显示所有在线玩家'},
    {'cmd':'seed','cn':'世界种子','usage':'seed','cat':'信息','desc':'显示世界种子'},
    {'cmd':'forge tps','cn':'TPS检测','usage':'forge tps','cat':'信息','desc':'查看各维度TPS'},
    {'cmd':'op','cn':'授予OP','usage':'op <targets>','cat':'玩家','desc':'给予管理员权限'},
    {'cmd':'deop','cn':'取消OP','usage':'deop <targets>','cat':'玩家','desc':'移除管理员权限'},
    {'cmd':'ban','cn':'封禁','usage':'ban <targets> [<reason>]','cat':'玩家','desc':'封禁玩家'},
    {'cmd':'kick','cn':'踢出','usage':'kick <targets> [<reason>]','cat':'玩家','desc':'踢出玩家'},
    {'cmd':'whitelist','cn':'白名单','usage':'whitelist (on|off|list|add|remove|reload)','cat':'玩家','desc':'管理白名单'},
    {'cmd':'pardon','cn':'解封','usage':'pardon <targets>','cat':'玩家','desc':'解除封禁'},
    {'cmd':'msg','cn':'私聊','usage':'msg <targets> <message>','cat':'玩家','desc':'发送私聊'},
    {'cmd':'time','cn':'时间','usage':'time (set|add|query)','cat':'世界','desc':'设置/增加/查询时间'},
    {'cmd':'weather','cn':'天气','usage':'weather (clear|rain|thunder)','cat':'世界','desc':'设置天气'},
    {'cmd':'difficulty','cn':'难度','usage':'difficulty (peaceful|easy|normal|hard)','cat':'世界','desc':'设置游戏难度'},
    {'cmd':'gamemode','cn':'游戏模式','usage':'gamemode <mode> [<target>]','cat':'世界','desc':'切换游戏模式'},
    {'cmd':'gamerule','cn':'游戏规则','usage':'gamerule <rule> <value>','cat':'世界','desc':'查看/修改游戏规则'},
    {'cmd':'setworldspawn','cn':'世界出生点','usage':'setworldspawn [<pos>]','cat':'世界','desc':'设置世界出生点'},
    {'cmd':'locate','cn':'定位','usage':'locate (structure|biome|poi)','cat':'世界','desc':'定位结构/群系'},
    {'cmd':'give','cn':'给予物品','usage':'give <targets> <item> [<count>]','cat':'物品','desc':'给玩家物品'},
    {'cmd':'clear','cn':'清空','usage':'clear [<targets>]','cat':'物品','desc':'清空物品栏'},
    {'cmd':'setblock','cn':'放置方块','usage':'setblock <pos> <block> [destroy|keep|replace]','cat':'物品','desc':'放置方块'},
    {'cmd':'fill','cn':'填充区域','usage':'fill <from> <to> <block> [replace|...]','cat':'物品','desc':'批量填充方块'},
    {'cmd':'enchant','cn':'附魔','usage':'enchant <targets> <enchantment> [<level>]','cat':'物品','desc':'给物品附魔'},
    {'cmd':'teleport','cn':'传送','usage':'teleport <location>|<targets>','cat':'实体','desc':'传送实体'},
    {'cmd':'tp','cn':'传送','usage':'tp <targets> <location>','cat':'实体','desc':'传送实体'},
    {'cmd':'summon','cn':'生成实体','usage':'summon <entity> [<pos>]','cat':'实体','desc':'生成实体'},
    {'cmd':'kill','cn':'杀死','usage':'kill [<targets>]','cat':'实体','desc':'杀死目标'},
    {'cmd':'effect','cn':'药水效果','usage':'effect (clear|give)','cat':'实体','desc':'给实体药水效果'},
    {'cmd':'particle','cn':'粒子','usage':'particle <name> [<pos>]','cat':'实体','desc':'生成粒子'},
    {'cmd':'playsound','cn':'播放声音','usage':'playsound <sound> <source>','cat':'实体','desc':'播放声音'},
    {'cmd':'xp','cn':'经验','usage':'xp <amount> <targets>','cat':'实体','desc':'增加经验'},
    {'cmd':'data','cn':'数据操作','usage':'data (merge|get|remove|modify)','cat':'技术','desc':'操作NBT数据'},
    {'cmd':'datapack','cn':'数据包','usage':'datapack (enable|disable|list)','cat':'技术','desc':'管理数据包'},
    {'cmd':'function','cn':'函数','usage':'function <name>','cat':'技术','desc':'执行函数'},
    {'cmd':'execute','cn':'条件执行','usage':'execute (run|if|unless|as|at|...)','cat':'技术','desc':'按条件执行指令'},
    {'cmd':'scoreboard','cn':'计分板','usage':'scoreboard (objectives|players)','cat':'技术','desc':'管理计分板'},
    {'cmd':'tellraw','cn':'JSON消息','usage':'tellraw <targets> <message>','cat':'技术','desc':'发送JSON消息'},
    {'cmd':'title','cn':'标题','usage':'title <targets> (clear|reset|title|...)','cat':'技术','desc':'屏幕标题消息'},
    {'cmd':'say','cn':'全服消息','usage':'say <message>','cat':'技术','desc':'发送全服消息'},
    {'cmd':'reload','cn':'重载','usage':'reload','cat':'技术','desc':'重新加载数据包'},
    {'cmd':'save-all','cn':'保存世界','usage':'save-all [flush]','cat':'管理','desc':'保存所有世界'},
    {'cmd':'save-off','cn':'关闭保存','usage':'save-off','cat':'管理','desc':'暂停自动保存'},
    {'cmd':'save-on','cn':'开启保存','usage':'save-on','cat':'管理','desc':'恢复自动保存'},
    {'cmd':'stop','cn':'停止服务器','usage':'stop','cat':'管理','desc':'安全停止服务器'},
]

# 附魔列表
ENCHANTS=[
    {'id':'sharpness','name':'锋利','target':'sword'},{'id':'bane_of_arthropods','name':'节肢杀手','target':'sword'},
    {'id':'knockback','name':'击退','target':'sword'},{'id':'fire_aspect','name':'火焰附加','target':'sword'},
    {'id':'looting','name':'掠夺','target':'sword'},{'id':'sweeping_edge','name':'横扫之刃','target':'sword'},
    {'id':'efficiency','name':'效率','target':'pickaxe'},{'id':'fortune','name':'时运','target':'pickaxe'},
    {'id':'silk_touch','name':'精准采集','target':'pickaxe'},{'id':'power','name':'力量','target':'bow'},
    {'id':'punch','name':'击退','target':'bow'},{'id':'flame','name':'火矢','target':'bow'},
    {'id':'infinity','name':'无限','target':'bow'},{'id':'protection','name':'保护','target':'armor'},
    {'id':'fire_protection','name':'防火','target':'armor'},{'id':'blast_protection','name':'爆炸保护','target':'armor'},
    {'id':'projectile_protection','name':'弹射物保护','target':'armor'},{'id':'feather_falling','name':'摔落保护','target':'boots'},
    {'id':'thorns','name':'荆棘','target':'armor'},{'id':'unbreaking','name':'耐久','target':'all'},
    {'id':'mending','name':'经验修补','target':'all'},{'id':'curse_of_vanishing','name':'消失诅咒','target':'all'},
    {'id':'curse_of_binding','name':'绑定诅咒','target':'armor'},{'id':'depth_strider','name':'深海探索者','target':'boots'},
    {'id':'frost_walker','name':'冰霜行者','target':'boots'},{'id':'aqua_affinity','name':'水下呼吸','target':'helmet'},
    {'id':'respiration','name':'水下呼吸增强','target':'helmet'},{'id':'loyalty','name':'忠诚','target':'trident'},
    {'id':'riptide','name':'激流','target':'trident'},{'id':'channeling','name':'引雷','target':'trident'},
    {'id':'impaling','name':'穿刺','target':'trident'},{'id':'multishot','name':'快速射击','target':'crossbow'},
    {'id':'piercing','name':'穿透','target':'crossbow'},{'id':'quick_charge','name':'快速装填','target':'crossbow'},
    {'id':'luck_of_the_sea','name':'海之眷顾','target':'fishing_rod'},{'id':'lure','name':'饵钓','target':'fishing_rod'},
    {'id':'soul_speed','name':'灵魂疾行','target':'boots'},{'id':'swift_sneak','name':'迅速潜行','target':'leggings'},
]
ENCH_KW=['sword','axe','pickaxe','shovel','hoe','bow','crossbow','trident','helmet','chestplate','leggings','boots','elytra','fishing_rod','shield']

# 注册表缓存
_REG={'items':[],'items_by_ns':{},'entities':[],'entities_by_ns':{}}
_REG_LOCK=threading.Lock(); _ZH_I={}; _ZH_E={}; _ZH_N={}
def _load_cache():
    global _ZH_I,_ZH_E,_ZH_N,_REG
    cd=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
    lp=LANG_ZH_FILE if os.path.exists(LANG_ZH_FILE) else os.path.join(cd,'lang_zh_all.json')
    if os.path.exists(lp):
        try:
            with open(lp,encoding='utf-8') as f: d=json.load(f)
            _ZH_I=d.get('items',{}); _ZH_E=d.get('entities',{}); _ZH_N=d.get('namespaces',{})
            print(f'[CACHE] zh: {len(_ZH_I)}i {len(_ZH_E)}e {len(_ZH_N)}ns')
        except: pass
    ip=os.path.join(cd,'items.json')
    if os.path.exists(ip):
        try:
            with open(ip,encoding='utf-8') as f: idata=json.load(f)
            ibn={}
            for it in idata:
                ns=it['id'].split(':')[0] if ':' in it['id'] else 'unknown'
                ibn.setdefault(ns,[]).append(it)
            _REG['items']=idata; _REG['items_by_ns']=ibn; print(f'[CACHE] {len(idata)} items')
        except: pass
    ep=os.path.join(cd,'entities.json')
    if os.path.exists(ep):
        try:
            with open(ep,encoding='utf-8') as f: edata=json.load(f)
            ebn={}
            for e in edata:
                ns=e['id'].split(':')[0] if ':' in e['id'] else 'minecraft'
                ebn.setdefault(ns,[]).append(e)
            _REG['entities']=edata; _REG['entities_by_ns']=ebn; print(f'[CACHE] {len(edata)} entities')
        except: pass
_load_cache()

def id2name(iid,kind='item'):
    t=_ZH_I if kind=='item' else _ZH_E
    if iid in t and t[iid]: return t[iid]
    if ':' not in iid: return iid
    ns,p=iid.split(':',1); return (_ZH_N.get(ns,ns))+' · '+p.replace('_',' ').replace('-',' ').title()

# 服务器配置读取/写入（server.properties）
PROPS_FILE = os.path.join(SERVER_DIR, 'server.properties')
# 支持切换/编辑的配置项定义：{key: [cn_name, type, options/cn_hint]}
CONFIG_DEF = [
    # 安全与网络
    ('安全与网络', None),
    ('online-mode', '正版认证', 'switch', ''),
    ('enforce-secure-profile', '强制安全配置', 'switch', ''),
    ('prevent-proxy-connections', '防止代理连接', 'switch', ''),
    ('require-resource-pack', '强制资源包', 'switch', ''),
    ('broadcast-console-to-ops', '控制台广播给OP', 'switch', ''),
    ('broadcast-rcon-to-ops', 'RCON广播给OP', 'switch', ''),
    ('enable-rcon', '启用RCON', 'switch', ''),
    ('enable-status', '启用状态', 'switch', ''),
    ('enable-query', '启用查询', 'switch', ''),
    ('server-port', '服务器端口', 'number', '1-65535'),
    ('server-ip', '服务器IP', 'text', '留空=所有IP'),
    # 世界与游戏
    ('世界与游戏', None),
    ('gamemode', '游戏模式', 'select', 'survival=生存,creative=创造,adventure=冒险,spectator=旁观'),
    ('difficulty', '难度', 'select', 'peaceful=和平,easy=简单,normal=普通,hard=困难'),
    ('pvp', 'PVP伤害', 'switch', ''),
    ('hardcore', '硬核模式', 'switch', ''),
    ('allow-flight', '允许飞行', 'switch', ''),
    ('allow-nether', '允许下界', 'switch', ''),
    ('force-gamemode', '强制游戏模式', 'switch', ''),
    ('generate-structures', '生成结构', 'switch', ''),
    ('enforce-whitelist', '强制白名单', 'switch', ''),
    ('white-list', '白名单模式', 'switch', ''),
    ('spawn-animals', '动物刷怪', 'switch', ''),
    ('spawn-monsters', '怪物刷怪', 'switch', ''),
    ('spawn-npcs', 'NPC刷怪', 'switch', ''),
    ('max-players', '最大玩家数', 'number', '1-1024'),
    ('max-tick-time', '最大tick时间(毫秒)', 'number', '≥0'),
    ('max-chained-neighbor-updates', '连锁邻居更新', 'number', ''),
    ('max-world-size', '最大世界半径', 'number', '≥10'),
    ('view-distance', '视距', 'number', '3-32'),
    ('simulation-distance', '模拟距离', 'number', '3-32'),
    ('spawn-protection', '出生点保护', 'number', '0-16'),
    ('level-name', '世界名称', 'text', ''),
    ('level-type', '世界类型', 'text', ''),
    ('level-seed', '世界种子', 'text', '留空=随机'),
    ('motd', '服务器标语', 'text', ''),
    # 性能与网络
    ('性能与网络', None),
    ('network-compression-threshold', '压缩阈值', 'number', '0-32767'),
    ('rate-limit', '速率限制(数据包/秒)', 'number', '0=关闭'),
    ('sync-chunk-writes', '同步区块写入', 'switch', ''),
    ('use-native-transport', '原生传输', 'switch', ''),
    ('hide-online-players', '隐藏在线玩家', 'switch', ''),
    ('enable-command-block', '命令方块', 'switch', ''),
    ('enable-jmx-monitoring', 'JMX监控', 'switch', ''),
    ('player-idle-timeout', '闲置超时(分钟)', 'number', '0=关闭'),
    ('op-permission-level', 'OP权限等级', 'number', '0-4'),
    ('function-permission-level', '函数权限等级', 'number', '0-4'),
]

def _read_props():
    """读取 server.properties 返回 dict"""
    props = {}
    if not os.path.exists(PROPS_FILE):
        return props
    with open(PROPS_FILE, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('!'):
                continue
            if '=' in line:
                k, v = line.split('=', 1)
                props[k.strip()] = v.strip()
    return props

def _write_props(props):
    """将 dict 写回 server.properties，保留已有行，追加缺失行"""
    existing = {}
    lines = []
    new_lines = []
    if os.path.exists(PROPS_FILE):
        with open(PROPS_FILE, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                stripped = line.strip()
                if stripped and '=' in stripped and not stripped.startswith('#') and not stripped.startswith('!'):
                    k, v = stripped.split('=', 1)
                    k = k.strip(); v = v.strip()
                    if k in props:
                        lines.append(f'{k}={props[k]}\n')
                        existing[k] = True
                    else:
                        lines.append(line)
                else:
                    lines.append(line)
        # 追加之前不存在的行
        for k, v in props.items():
            if k not in existing:
                new_lines.append(f'{k}={v}\n')
    else:
        for k, v in props.items():
            new_lines.append(f'{k}={v}\n')
    with open(PROPS_FILE, 'w', encoding='utf-8') as f:
        f.writelines(lines)
        f.writelines(new_lines)

# === RCON 密码自动同步 ===
def _gen_rcon_password():
    """生成一个强随机 RCON 密码"""
    chars = string.ascii_letters + string.digits + '!@#$%^&*()_+-='
    return ''.join(secrets.choice(chars) for _ in range(16))

def _save_config():
    """保存 config.yaml"""
    try:
        cfg=CONFIG.copy()
        cfg['auth']={'username':_AUTH_USER,'password_hash':_AUTH_PASS_HASH.hex(),'must_change':_AUTH_MUST_CHANGE}
        with open(CONFIG_PATH,'w',encoding='utf-8') as f:
            yaml.dump(cfg,f,allow_unicode=True,default_flow_style=False)
    except Exception as e:
        print(f'⚠️ 保存 config.yaml 失败: {e}')

def _sync_rcon_password():
    """自动检测/生成 RCON 密码并同步 config.yaml ↔ server.properties

    优先级:
      1. server.properties 已有 rcon.password → 同步到 config.yaml
      2. config.yaml 已有 password → 写入 server.properties
      3. 两者都没有 → 生成随机密码写入两边
    返回: 当前使用的 RCON 密码
    """
    r = CONFIG.get('rcon', {})
    cfg_pass = str(r.get('password', '')).strip()
    props = _read_props()
    props_pass = str(props.get('rcon.password', '')).strip()

    if props_pass:
        # 场景1: server.properties 已有 RCON 密码
        if cfg_pass != props_pass:
            r['password'] = props_pass
            CONFIG['rcon'] = r
            _save_config()
            print(f'  🔑 从 server.properties 检测到 RCON 密码 → 已同步到 config.yaml')
        else:
            print(f'  🔑 RCON 密码已一致')
        return props_pass
    elif cfg_pass:
        # 场景2: config.yaml 有密码，server.properties 没有
        props['rcon.password'] = cfg_pass
        props['enable-rcon'] = 'true'
        _write_props(props)
        print(f'  🔑 config.yaml 密码已写入 server.properties (enable-rcon=true)')
        return cfg_pass
    else:
        # 场景3: 两者都无密码，生成新的
        new_pass = _gen_rcon_password()
        r['password'] = new_pass
        CONFIG['rcon'] = r
        _save_config()
        props['rcon.password'] = new_pass
        props['enable-rcon'] = 'true'
        _write_props(props)
        print(f'  🔑 RCON 未配置，已自动生成随机密码并写入两边')
        return new_pass

# === RCON 自动恢复 ===
def _recover_rcon():
    """检测 RCON 连通性，失败则自动恢复默认配置

    注意: 如果 MC 服务端未启动，RCON 连接必然失败。
    此时如果已从 server.properties 同步了密码，保留它（服务端启动后生效）。
    只有完全无密码时才生成新密码。
    """
    global RCON_PASSWORD, RCON_PORT
    print(f'🔍 检测 RCON 连通性 ({RCON_HOST}:{RCON_PORT})...')
    test_rcon = RCON(RCON_HOST, RCON_PORT, RCON_PASSWORD)
    try:
        test_rcon.connect()
        resp = test_rcon.command('list')
        test_rcon.close()
        print(f'  ✅ RCON 连接正常 (密码: {RCON_PASSWORD[:4]}****)')
        return True
    except Exception:
        pass
    print(f'  ❌ RCON 连接失败（服务端可能未启动）')

    # 尝试常见默认密码（仅当当前密码为空时才尝试）
    if not RCON_PASSWORD:
        for trial in ['1', '1234', '']:
            test_rcon2 = RCON(RCON_HOST, RCON_PORT, trial)
            try:
                test_rcon2.connect()
                resp = test_rcon2.command('list')
                test_rcon2.close()
                CONFIG.setdefault('rcon', {})['password'] = trial
                _save_config()
                props = _read_props()
                props['rcon.password'] = trial
                _write_props(props)
                RCON_PASSWORD = trial
                RCON_PORT = CONFIG.get('rcon', {}).get('port', 25575)
                print(f'  ✅ 已恢复 RCON 密码为: {trial}')
                return True
            except Exception:
                try: test_rcon2.close()
                except: pass

    # 如果已有密码（从 server.properties 同步的），保留它
    if RCON_PASSWORD:
        print(f'  📋 已从 server.properties 同步密码，等待服务端启动后生效')
        return True

    # 完全没有密码，生成新的
    new_pass = _gen_rcon_password()
    CONFIG.setdefault('rcon', {})['password'] = new_pass
    CONFIG.setdefault('rcon', {})['port'] = 25575
    _save_config()
    props = _read_props()
    props['rcon.password'] = new_pass
    # 不覆盖已有的 rcon.port
    if not str(props.get('rcon.port', '')).strip():
        props['rcon.port'] = '25575'
    _write_props(props)
    RCON_PASSWORD = new_pass
    RCON_PORT = 25575
    print(f'  🔑 RCON 未配置，已生成随机密码')
    print(f'  🔑 密码: {new_pass}')
    print(f'  ⚠️  请在服务端启动后重启面板，RCON 即可生效')
    return False

# === 启动时自动恢复 ===
print(f'\n🔑 RCON 密码自动同步...')
_SYNCED_RCON_PASS = _sync_rcon_password()
if _SYNCED_RCON_PASS:
    RCON_PASSWORD = _SYNCED_RCON_PASS
    print(f'🔑 当前 RCON 密码: {_SYNCED_RCON_PASS}\n')

# 检测并恢复 RCON
_recover_rcon()

# 玩家统计
PS_FILE=os.path.join(SERVER_DIR,'player_stats.json')
_ps={};_ps_lock=threading.Lock();_ps_dirty=False
_JR=re.compile(r'\[(\d{2}\w{3}\d{4} \d{2}:\d{2}:\d{2})\.\d+\].*?/\]:\s+(.+?)\s+joined the game')
_LR=re.compile(r'\[(\d{2}\w{3}\d{4} \d{2}:\d{2}:\d{2})\.\d+\].*?/\]:\s+(.+?)\s+left the game')
_MM={'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06','Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}
def _pdt(s):
    try: return datetime.strptime(f'{s[:2]}/{_MM.get(s[2:5],"01")}/{s[5:]}','%d/%m/%Y %H:%M:%S')
    except: return None
def _parse_ps():
    sessions={};events=[]
    ld=os.path.join(SERVER_DIR,'logs');files=[]
    try:
        for fn in sorted(os.listdir(ld)):
            if fn.endswith('.log.gz') and fn.startswith('20'): files.append(('gz',os.path.join(ld,fn)))
    except: pass
    if os.path.exists(LOG_FILE): files.append(('txt',LOG_FILE))
    for ft,fp in files:
        try:
            f=gzip.open(fp,'rt',encoding='utf-8',errors='replace') if ft=='gz' else open(fp,'r',encoding='utf-8',errors='replace')
            with f:
                for line in f:
                    m=_JR.search(line)
                    if m:
                        dt=_pdt(m.group(1))
                        if dt: events.append((dt,m.group(2),True))
                        continue
                    m=_LR.search(line)
                    if m:
                        dt=_pdt(m.group(1))
                        if dt: events.append((dt,m.group(2),False))
        except: pass
    events.sort(key=lambda x:x[0]);js={}
    for i,(ts,p,join) in enumerate(events):
        if join: js.setdefault(p,[]).append((ts,i))
        else:
            jl=js.get(p,[])
            if jl:
                jt,_=jl.pop(); sessions.setdefault(p,[]).append((jt,ts))
    online={}
    for p,jl in js.items():
        if jl: online[p]=jl[-1][0]
    stats={}
    for p,sl in sessions.items():
        total=int(sum((l-j).total_seconds() for j,l in sl))
        lj=max(sl,key=lambda x:x[0])[0] if sl else None
        ll=max(sl,key=lambda x:x[1])[1] if sl else None
        stats[p]={'total_playtime_seconds':total,'session_count':len(sl),
            'last_login':lj.strftime('%Y-%m-%d %H:%M:%S') if lj else None,
            'last_logout':ll.strftime('%Y-%m-%d %H:%M:%S') if ll else None,'online':p in online}
    now=datetime.now()
    for p,jt in online.items():
        if p in stats:
            stats[p]['online']=True;stats[p]['last_login']=jt.strftime('%Y-%m-%d %H:%M:%S')
            cur=(now-jt).total_seconds()
            sl=sessions.get(p,[])
            stats[p]['total_playtime_seconds']=int(sum((l-j).total_seconds() for j,l in sl)+cur)
            stats[p]['session_count']=len(sl)+1
        else:
            stats[p]={'total_playtime_seconds':int((now-jt).total_seconds()),'session_count':1,
                'last_login':jt.strftime('%Y-%m-%d %H:%M:%S'),'last_logout':None,'online':True}
    return stats
def _save_ps():
    global _ps_dirty
    try:
        with _ps_lock:
            snapshot = dict(_ps)
        with open(PS_FILE,'w',encoding='utf-8') as f:
            json.dump({'last_updated':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'players':snapshot},f,ensure_ascii=False,indent=2)
        with _ps_lock: _ps_dirty=False
    except: pass
def _load_ps():
    global _ps
    if _ps: return _ps
    try:
        with open(PS_FILE,encoding='utf-8') as f: _ps=json.load(f).get('players',{})
    except: pass
    if not _ps:
        try:
            for p,s in _parse_ps().items(): _ps[p]=s
        except: pass
        try: _save_ps()
        except: pass
    return _ps
def _refresh_ps():
    global _ps
    while True:
        time.sleep(30)
        try:
            new_data = _parse_ps()
            changed = False
            for p,s in new_data.items():
                with _ps_lock:
                    if _ps.get(p,{}).get('total_playtime_seconds') != s.get('total_playtime_seconds'):
                        _ps[p]=s;changed=True
            if changed: _save_ps()
        except: pass

# 状态采集
def poll_status():
    while True:
        try:
            r=send_cmd('list');state.players=[];state.player_count=0
            m=re.search(r'(\d+)\s+of\s+a\s+max\s+of\s+\d+\s+players\s+online',r)
            if m: state.player_count=int(m.group(1))
            names=re.findall(r':\s+([^:\n]+)',r)
            if names: state.players=[n.strip() for n in names if n.strip()]
            if MODE!='pipe':
                t=send_cmd('forge tps');state.tps=None
                for p in[r'TPS\s*[:=]?\s*([\d.]+)',r'([\d.]+)\s*tps',r'([\d.]+)\s+ticks/s']:
                    m2=re.search(p,t,re.I)
                    if m2: state.tps=float(m2.group(1));break
        except: pass
        time.sleep(5)

# 日志
_log_off=0
def tail_log():
    global _log_off
    try:
        if not os.path.exists(LOG_FILE): return
        with open(LOG_FILE,'r',encoding='utf-8',errors='replace') as f:
            sz=os.path.getsize(LOG_FILE)
            if sz<_log_off: _log_off=0
            f.seek(_log_off); nl=f.read().splitlines(); _log_off=f.tell()
        if nl: state.log_lines.extend(nl); state.log_lines=state.log_lines[-state.log_max:]
    except: pass
def log_tailer():
    while True:
        try: tail_log()
        except: pass
        time.sleep(1)

_sic=None;_sic_ts=0.0
def get_sys(use_cache=True):
    global _sic,_sic_ts
    now=time.time()
    if use_cache and _sic and (now-_sic_ts)<10: return _sic
    info={'pids':state.pids}
    try:
        r=subprocess.run(['pgrep','-f',JAVA_KEYWORD],capture_output=True,text=True,timeout=5)
        pids=[p for p in r.stdout.strip().split('\n') if p.isdigit()]
        if not pids:
            r=subprocess.run(['pgrep','-f','run.sh'],capture_output=True,text=True,timeout=5)
            pids=[p for p in r.stdout.strip().split('\n') if p.isdigit()]
        info['pids']=pids;state.pids=pids
        for pid in pids:
            try:
                with open(f'/proc/{pid}/status') as f:
                    for line in f:
                        if 'VmRSS:' in line: state.memory_used=line.split(':')[1].strip().replace(' kB','')
                        if 'VmPeak:' in line: state.memory_max=line.split(':')[1].strip().replace(' kB','')
                break
            except: continue
        _sic=info;_sic_ts=time.time()
    except: pass
    return info

# HTTP 请求处理
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def _json(self,d):
        b=json.dumps(d,ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        for k,v in [('Content-Type','application/json; charset=utf-8'),('Content-Length',str(len(b))),('Access-Control-Allow-Origin','*')]:
            self.send_header(k,v)
        self.end_headers();self.wfile.write(b)
    def _file(self,p,ct='text/html; charset=utf-8'):
        try:
            fp=os.path.join(os.path.dirname(__file__),p.lstrip('/'))
            with open(fp,'rb') as f: c=f.read()
            self.send_response(200)
            for k,v in [('Content-Type',ct),('Content-Length',str(len(c))),('Access-Control-Allow-Origin','*')]:
                self.send_header(k,v)
            self.end_headers();self.wfile.write(c)
        except: self.send_response(404);self.end_headers()
    def _img(self,p):
        try:
            with open(os.path.abspath(p),'rb') as f: c=f.read()
            e=os.path.splitext(p)[1].lower()
            ct={'png':'image/png','jpg':'image/jpeg','jpeg':'image/jpeg','webp':'image/webp','gif':'image/gif'}.get(e,'application/octet-stream')
            self.send_response(200)
            for k,v in [('Content-Type',ct),('Content-Length',str(len(c))),('Access-Control-Allow-Origin','*')]:
                self.send_header(k,v)
            self.end_headers();self.wfile.write(c)
        except: self.send_response(404);self.end_headers()
    def _html(self,content):
        b=content.encode('utf-8')
        self.send_response(200)
        for k,v in [('Content-Type','text/html; charset=utf-8'),('Content-Length',str(len(b))),('Access-Control-Allow-Origin','*')]:
            self.send_header(k,v)
        self.end_headers();self.wfile.write(b)
    def do_OPTIONS(self):
        self.send_response(200)
        for k,v in [('Access-Control-Allow-Origin','*'),('Access-Control-Allow-Methods','GET, POST, OPTIONS'),('Access-Control-Allow-Headers','Content-Type')]:
            self.send_header(k,v)
        self.end_headers()
    def do_GET(self):
        p=self.path.split('?')[0]
        qs=parse_qs(urlparse(self.path).query)
        token=_get_tok(self.headers)
        session=_validate(token)
        is_auth=session is not None
        if p=='/api/auth/check':
            if is_auth:
                self._json({'authenticated':True,'username':session['user'],'must_change':session['must_change'],'serverName':SERVER_NAME})
            else:
                self._json({'authenticated':False,'serverName':SERVER_NAME})
            return
        if p=='/api/auth/logout':
            _destroy(token)
            self._json({'ok':True})
            return
        # 壁纸公开访问，无需登录
        if p=='/api/wallpapers':
            self._json({'wallpapers':WALLPAPERS,'count':len(WALLPAPERS)});return
        if p.startswith('/wp/'):
            try:
                idx=int(p.replace('/wp/',''))
                if 0<=idx<len(WALLPAPERS): self._img(WALLPAPERS[idx]);return
            except: pass
            self.send_response(404);self.end_headers();return

        if not is_auth:
            if p in ('/','/index.html'):
                self._html(LOGIN_PAGE)
            else:
                self.send_response(401);self.end_headers()
            return
        if p=='/api/port/check':
            try:
                target_port=int(qs.get('port',[''])[0])
            except: self._json({'in_use':True,'note':'❌ 无效端口号'});return
            if target_port<1 or target_port>65535:
                self._json({'in_use':True,'note':'❌ 端口必须在 1-65535 之间'});return
            try:
                s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.settimeout(0.5);s.bind(('',target_port));s.close()
                note='✅ 端口可用' if target_port>=1024 else '⚠️ 端口可用（<1024需root权限）'
                self._json({'in_use':False,'note':note})
            except OSError:
                # 被占用时判断是本服务还是其他进程
                rcon_port=CONFIG.get('rcon',{}).get('port',25575)
                if target_port==PORT:
                    self._json({'in_use':False,'note':'🔒 当前面板正在使用','level':'info'})
                elif target_port==rcon_port:
                    self._json({'in_use':False,'note':'🔒 当前RCON正在使用','level':'info'})
                else:
                    self._json({'in_use':True,'note':'❌ 端口已被其他进程占用','level':'error'})
        elif p=='/api/pass/check':
            pwd=qs.get('pwd',[''])[0]
            if not pwd:
                self._json({'note':'','level':'info'});return
            score=0
            note_parts=[]
            if len(pwd)>=8: score+=1;note_parts.append('长度≥8')
            else: note_parts.append('长度<8')
            if len(pwd)>=12: score+=1
            if re.search(r'[a-z]',pwd): score+=1;note_parts.append('小写字母')
            if re.search(r'[A-Z]',pwd): score+=1;note_parts.append('大写字母')
            if re.search(r'\d',pwd): score+=1;note_parts.append('数字')
            if re.search(r'[^a-zA-Z0-9]',pwd): score+=1;note_parts.append('特殊字符')
            if score<=2: level='error';note='❌ 弱密码 — '+', '.join(note_parts)
            elif score<=4: level='warn';note='⚠️ 中 — '+', '.join(note_parts)
            else: level='ok';note='✅ 强密码 — '+', '.join(note_parts)
            self._json({'note':note,'level':level})
        elif p=='/api/path/check':
            pth=qs.get('path',[''])[0]
            if not pth:
                self._json({'note':'','level':'info'});return
            if os.path.exists(pth):
                self._json({'note':'✅ 路径存在','level':'ok'})
            else:
                self._json({'note':'❌ 路径不存在','level':'error'})
        elif p=='/api/status':
            info=get_sys()
            self._json({'tps':state.tps,'playerCount':state.player_count,'players':state.players,
                'memoryUsed':state.memory_used,'memoryMax':state.memory_max,'pids':info.get('pids',[]),
                'timestamp':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'mode':MODE,'serverName':SERVER_NAME})
        elif p=='/api/log': self._json({'lines':state.log_lines[-500:]})
        elif p=='/api/log/clear':
            global _log_off
            _log_off = os.path.getsize(LOG_FILE) if os.path.exists(LOG_FILE) else 0
            state.log_lines=[]
            self._json({'ok':True})
        elif p=='/api/panel_config':
            cfg = CONFIG
            s = cfg.get('server', {})
            self._json({'host': s.get('host','0.0.0.0'), 'port': s.get('port', PORT), 'name': s.get('name', SERVER_NAME), 'mode': cfg.get('mode','auto'), 'rcon_host': cfg.get('rcon',{}).get('host','127.0.0.1'), 'rcon_port': cfg.get('rcon',{}).get('port', 25575), 'rcon_password': cfg.get('rcon',{}).get('password',''), 'server_dir': cfg.get('server_dir', SERVER_DIR)})
        elif p=='/api/config':
            self._json({'config':_read_props(),'definitions':CONFIG_DEF})
        elif p=='/api/wallpapers': self._json({'wallpapers':WALLPAPERS,'count':len(WALLPAPERS)})
        elif p=='/api/commands/cats':
            cats=[];seen=set()
            for c in ALL_CMDS:
                if c['cat'] not in seen: seen.add(c['cat']);cats.append(c['cat'])
            self._json({'categories':cats,'total':len(ALL_CMDS)})
        elif p=='/api/player_stats':
            global _ps
            with _ps_lock:
                if not _ps: self._json({'players':{},'online_count':0,'loading':True});return
                stats=dict(_ps)
            try:
                for pn in stats: stats[pn]['online']=pn in state.players
                for pn in state.players:
                    if pn not in stats: stats[pn]={'total_playtime_seconds':0,'session_count':0,'last_login':None,'last_logout':None,'online':True}
            except: pass
            self._json({'players':stats,'online_count':state.player_count})
        elif p=='/api/serverinfo':
            with _REG_LOCK:
                itotal=len(_REG.get('items',[])); etotal=len(_REG.get('entities',[]))
                inss=dict(_REG.get('items_by_ns',{})); enss=dict(_REG.get('entities_by_ns',{}))
            # 检测服务端类型
            stype='vanilla'
            mods=[]; plugins=[]
            for n,vs in inss.items():
                if n!='minecraft':
                    mods.append({'namespace':n,'name':_ZH_N.get(n,n),'count':len(vs)})
            if mods: stype='modded'
            # 通过RCON探测插件服
            try:
                plug_out=send_cmd('bukkit version')
                if plug_out and not plug_out.startswith('❌') and 'unknown command' not in plug_out.lower():
                    stype='plugin'
                    plugins.append('Bukkit/Spigot')
            except: pass
            try:
                ver_out=send_cmd('version')
                if ver_out and not ver_out.startswith('❌'):
                    m2=re.search(r'(\d+\.\d+(?:\.\d+)?)',ver_out)
                    if m2: server_ver=m2.group(1)
                    else: server_ver='?'
                else: server_ver='?'
            except: server_ver='?'
            item_ns=[{'namespace':n,'name':_ZH_N.get(n,n),'count':len(vs)} for n,vs in sorted(inss.items())]
            ent_ns=[{'namespace':n,'name':_ZH_N.get(n,n),'count':len(vs)} for n,vs in sorted(enss.items())]
            self._json({'serverType':stype,'serverVersion':server_ver,'itemCount':itotal,'entityCount':etotal,
                'itemNamespaces':item_ns,'entityNamespaces':ent_ns,'mods':mods,'plugins':plugins,
                'mode':MODE,'serverName':SERVER_NAME,'optimizeMode':'auto'})
            return
        elif p=='/api/items':
            qs=parse_qs(urlparse(self.path).query)
            q=(qs.get('q',[''])[0] or '').strip().lower()
            ns=(qs.get('ns',[''])[0] or '').strip()
            with _REG_LOCK:
                items=list(_REG.get('items',[])); ibn=dict(_REG.get('items_by_ns',{}))
            if ns: items=ibn.get(ns,[])
            if q: items=[i for i in items if q in i['id'].lower() or q in i['name'].lower()]
            nss=[{'namespace':n,'name':_ZH_N.get(n,n),'count':len(vs)} for n,vs in sorted(ibn.items())]
            self._json({'items':items,'total':len(items),'namespaces':nss if not ns else [],'enchantments':ENCHANTS,'enchantable_keywords':ENCH_KW})
        elif p=='/api/entities':
            qs=parse_qs(urlparse(self.path).query)
            q=(qs.get('q',[''])[0] or '').strip().lower()
            ns=(qs.get('ns',[''])[0] or '').strip()
            with _REG_LOCK:
                ents=list(_REG.get('entities',[])); ebn=dict(_REG.get('entities_by_ns',{}))
            if ns: ents=ebn.get(ns,[])
            if q: ents=[e for e in ents if q in e['id'].lower() or q in e['name'].lower()]
            nss=[{'namespace':n,'name':_ZH_N.get(n,n),'count':len(vs)} for n,vs in sorted(ebn.items())]
            self._json({'entities':ents,'total':len(ents),'namespaces':nss if not ns else []})
        elif p.startswith('/wp/'):
            try:
                idx=int(p.replace('/wp/',''))
                if 0<=idx<len(WALLPAPERS): self._img(WALLPAPERS[idx]);return
            except: pass
            self.send_response(404);self.end_headers()
        elif p in ('/','/index.html'): self._file('/static/index.html')
        elif p.startswith('/static/'):
            e=os.path.splitext(p)[1].lower()
            ct={'html':'text/html; charset=utf-8','.js':'application/javascript; charset=utf-8','.css':'text/css; charset=utf-8'}.get(e,'application/octet-stream')
            self._file(p,ct)
        else: self._file('/static/index.html')
    def do_POST(self):
        cl=int(self.headers.get('Content-Length',0))
        try: data=json.loads(self.rfile.read(cl).decode('utf-8',errors='replace'))
        except: data={}
        p=self.path
        token=_get_tok(self.headers)
        session=_validate(token)
        is_auth=session is not None
        global _AUTH_USER,_AUTH_PASS_HASH,_AUTH_MUST_CHANGE
        if p=='/api/auth/login':
            user=data.get('username','').strip();pwd=data.get('password','')
            if not user or not pwd: self._json({'ok':False,'message':'用户名和密码不能为空'});return
            if user!=_AUTH_USER: self._json({'ok':False,'message':'用户名或密码错误'});return
            if not _verify_hash(pwd,_AUTH_PASS_HASH): self._json({'ok':False,'message':'用户名或密码错误'});return
            tok=_create_session()
            self.send_response(200)
            for k,v in [('Content-Type','application/json; charset=utf-8'),('Access-Control-Allow-Origin','*'),('Set-Cookie',f'mc_panel_session={tok}; HttpOnly; Path=/; Max-Age={_SESSION_TTL}')]:
                self.send_header(k,v)
            self.end_headers()
            self.wfile.write(json.dumps({'ok':True,'must_change':_AUTH_MUST_CHANGE},ensure_ascii=False).encode('utf-8'))
            return
        if p=='/api/auth/change_password':
            if not is_auth: self._json({'ok':False,'message':'未登录'});return
            old_pwd=data.get('old_password','');new_pwd=data.get('new_password','')
            if not new_pwd or len(new_pwd)<3: self._json({'ok':False,'message':'新密码长度至少3位'});return
            if old_pwd and not _verify_hash(old_pwd,_AUTH_PASS_HASH): self._json({'ok':False,'message':'旧密码错误'});return
            _AUTH_PASS_HASH=_make_hash(new_pwd);_AUTH_MUST_CHANGE=False
            _save_auth()
            with _AUTH_LOCK:
                if token and token in _AUTH_SESSIONS:_AUTH_SESSIONS[token]['must_change']=False
            self._json({'ok':True,'message':'密码修改成功'})
            return
        if p=='/api/auth/change_username':
            if not is_auth: self._json({'ok':False,'message':'未登录'});return
            new_user=data.get('username','').strip()
            if not new_user or len(new_user)<1 or len(new_user)>32: self._json({'ok':False,'message':'用户名长度1-32位'});return
            if re.search(r'[^\w\-]',new_user): self._json({'ok':False,'message':'用户名只能包含字母、数字、下划线和连字符'});return
            _AUTH_USER=new_user
            with _AUTH_LOCK:
                for s in _AUTH_SESSIONS.values():s['user']=new_user
            _save_auth()
            self._json({'ok':True,'message':'用户名修改成功'})
            return
        if not is_auth: self._json({'ok':False,'message':'请先登录'});return
        if p=='/api/command':
            cmd=data.get('command','')
            if not cmd: self._json({'output':'❌ 命令为空'});return
            try: self._json({'output':send_cmd(cmd),'command':cmd})
            except Exception as e: self._json({'output':f'❌ {str(e)}'})
        elif p=='/api/control':
            a=data.get('action','')
            try:
                if a=='save': send_cmd('save-all');self._json({'output':'✅ 世界已保存'})
                elif a=='stop': send_cmd('stop');self._json({'output':'✅ 服务器正在停止'})
                elif a=='reload': send_cmd('reload');self._json({'output':'✅ 已重新加载'})
                elif a=='kill':
                    info=get_sys();killed=[]
                    for pid in info['pids']:
                        try: os.kill(int(pid),signal.SIGTERM);killed.append(pid)
                        except: pass
                    self._json({'output':f'✅ 已终止: {", ".join(killed)}' if killed else '❌ 未找到进程'})
                else: self._json({'output':f'❌ 未知: {a}'})
            except Exception as e: self._json({'output':f'❌ {str(e)}'})
        elif p=='/api/log/clear':
            state.log_lines=[]
            self._json({'ok':True})
        elif p=='/api/quick':
            cat=data.get('category','')
            self._json({'commands':[c for c in QUICK if not cat or c['cat']==cat]})
        elif p=='/api/commands':
            cat=data.get('category','');kw=data.get('kw','').strip().lower()
            cmds=ALL_CMDS
            if cat: cmds=[c for c in cmds if c['cat']==cat]
            if kw: cmds=[c for c in cmds if kw in c['cmd'].lower() or kw in c['cn'].lower() or kw in c['desc'].lower()]
            self._json({'commands':cmds,'total':len(cmds)})
        elif p=='/api/gen':
            gt=data.get('type','');pr=data.get('params',{});cmd=''
            if gt=='tp': cmd=f'tp {pr.get("player","@p")} {pr.get("x",0)} {pr.get("y",64)} {pr.get("z",0)}'
            elif gt=='gamemode':
                gm={'0':'survival','1':'creative','2':'adventure','3':'spectator'}.get(pr.get('mode','0'),pr.get('mode','survival'))
                cmd=f'gamemode {gm} {pr.get("player","@p")}'
            elif gt=='give':
                player=pr.get("player","@p");item=pr.get("item","minecraft:diamond");count=pr.get("count",64)
                ench=pr.get("enchant","");lv=pr.get("level",1)
                cmd=f'give {player} {item} {count}'
                if ench: cmd+=f' 0 {{Enchantments:[{{id:"minecraft:{ench}",lvl:{lv}}}]}}'
            elif gt=='summon': cmd=f'summon {pr.get("entity","minecraft:zombie")} {pr.get("x",0)} {pr.get("y",64)} {pr.get("z",0)}'
            elif gt=='time': cmd=f'time set {pr.get("time","day")}'
            elif gt=='weather': cmd=f'weather {pr.get("weather","clear")}'
            elif gt=='difficulty':
                d={'0':'peaceful','1':'easy','2':'normal','3':'hard'}.get(pr.get('d','2'),pr.get('d','normal'))
                cmd=f'difficulty {d}'
            elif gt=='say': cmd=f'say {pr.get("msg","")}'
            elif gt=='execute': cmd=f'execute as {pr.get("player","@p")} run say {pr.get("msg","")}'
            elif gt=='xp': cmd=f'xp add {pr.get("player","@p")} {pr.get("amount",10)}'
            elif gt=='pardon': cmd=f'pardon {pr.get("player","")}'
            elif gt=='ban': cmd=f'ban {pr.get("player","")} {pr.get("reason","违规")}'
            elif gt=='op': cmd=f'op {pr.get("player","")}'
            elif gt=='deop': cmd=f'deop {pr.get("player","")}'
            elif gt=='kill': cmd=f'kill {pr.get("target","@e[type=!player]")}'
            elif gt=='effect': cmd=f'effect give {pr.get("player","@p")} {pr.get("effect","minecraft:speed")} {pr.get("duration",30)} {pr.get("amplifier",1)}'
            elif gt=='particle': cmd=f'particle {pr.get("particle","minecraft:flame")} {pr.get("x",0)} {pr.get("y",64)} {pr.get("z",0)} {pr.get("delta",1)} {pr.get("count",100)}'
            else: cmd=f'//未知: {gt}'
            self._json({'command':cmd,'type':gt})
        elif p=='/api/panel_config':
            changes = data.get('changes', {})
            if not changes: self._json({'output':'❌ 无更改'});return
            try:
                cfg = CONFIG
                s = cfg.setdefault('server', {})
                for k in ('host','port','name'):
                    if k in changes:
                        v = changes[k]
                        s[k] = int(v) if k=='port' else str(v)
                # rcon
                r = cfg.setdefault('rcon', {})
                rcon_password_changed = False
                for k in ('host','port','password'):
                    if f'rcon_{k}' in changes:
                        v = changes[f'rcon_{k}']
                        r[k] = int(v) if k=='port' else str(v)
                        if k == 'password': rcon_password_changed = True
                if 'mode' in changes:
                    cfg['mode'] = str(changes['mode'])
                if 'server_dir' in changes:
                    cfg['server_dir'] = str(changes['server_dir'])
                with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                    yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False)
                # 同步 RCON 密码到 server.properties
                if rcon_password_changed:
                    new_pass = r.get('password', '')
                    props = _read_props()
                    old_pass = props.get('rcon.password', '')
                    props['rcon.password'] = new_pass
                    props['enable-rcon'] = 'true'
                    _write_props(props)
                    # 更新 CONFIG 供后续重连使用
                    CONFIG['rcon']['password'] = new_pass
                    _save_config()
                    if old_pass:
                        self._json({'output':f'✅ 面板配置已保存，RCON密码已同步到 server.properties，重启后生效','changed':list(changes.keys())})
                    else:
                        self._json({'output':f'✅ 面板配置已保存，RCON密码已写入 server.properties，重启后生效','changed':list(changes.keys())})
                else:
                    self._json({'output':'✅ 面板配置已保存，重启后生效','changed':list(changes.keys())})
            except Exception as e:
                self._json({'output':f'❌ 保存失败: {e}'})
        elif p=='/api/config':
            changes = data.get('changes', {})
            if not changes: self._json({'output':'❌ 无更改'});return
            try:
                props = _read_props()
                for k, v in changes.items():
                    props[k] = str(v)
                _write_props(props)
                # 同步 RCON 相关设置到 config.yaml
                synced_keys = []
                if 'rcon.port' in changes:
                    CONFIG.setdefault('rcon', {})['port'] = int(props.get('rcon.port', RCON_PORT))
                    synced_keys.append('rcon.port')
                if 'rcon.password' in changes:
                    CONFIG.setdefault('rcon', {})['password'] = str(props.get('rcon.password', ''))
                    synced_keys.append('rcon.password')
                if synced_keys:
                    _save_config()
                    self._json({'output':f'✅ 配置已保存，RCON设置已同步到 config.yaml','changed':list(changes.keys())})
                else:
                    self._json({'output':'✅ 配置已保存','changed':list(changes.keys())})
            except Exception as e:
                self._json({'output':f'❌ 保存失败: {e}'})
        else: self._json({'output':'❌ 未知端点'})

# 启动
class TS(socketserver.ThreadingMixIn,socketserver.TCPServer):
    daemon_threads=True;allow_reuse_address=True
def main():
    global PORT
    import sys; sys.stdout.reconfigure(line_buffering=True)
    # 尝试配置端口，失败自动回退默认端口
    actual_port = PORT
    try:
        svr = TS((HOST, PORT), H)
    except OSError:
        print(f'❌ 端口 {PORT} 无法绑定，自动恢复默认端口 19888...', flush=True)
        actual_port = 19888
        svr = TS((HOST, actual_port), H)
        # 更新 config.yaml
        CONFIG.setdefault('server', {})['port'] = actual_port
        _save_config()
        PORT = actual_port
        print(f'✅ 已恢复面板端口: {actual_port}，config.yaml 已更新', flush=True)
    print(f'🎮 {SERVER_NAME} 面板: http://localhost:{actual_port}',flush=True)
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.connect(('8.8.8.8',80))
        print(f'🌐 局域网: http://{s.getsockname()[0]}:{actual_port}',flush=True);s.close()
    except: pass
    # 后台线程直接启动（不依赖 _init）
    threading.Thread(target=log_tailer,daemon=True).start()
    threading.Thread(target=poll_status,daemon=True).start()
    threading.Thread(target=_refresh_ps,daemon=True).start()
    # 一次性初始化放后台
    def _init():
        try: get_sys()
        except: pass
        try: tail_log()
        except: pass
    threading.Thread(target=_init,daemon=True).start()
    # 玩家统计单独线程（日志文件可能很大，不能阻塞主线程）
    threading.Thread(target=_load_ps,daemon=True).start()
    try: svr.serve_forever()
    except KeyboardInterrupt: print('\n👋 已停止');svr.shutdown()


if __name__=='__main__': main()