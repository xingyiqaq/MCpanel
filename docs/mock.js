// MCpanel Demo — 模拟数据（GitHub Pages 静态演示版）
// 此文件在 main <script> 之前加载，mock 所有 API 调用

(function(){
'use strict';

// ===== 模拟壁纸 =====
(function applyDemoWallpaper(){
  var img=document.getElementById('bg-wallpaper');
  if(img){
    img.src='data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="%231a0a2e"/><stop offset="0.5" stop-color="%2316213e"/><stop offset="1" stop-color="%230f3460"/></linearGradient></defs><rect width="1920" height="1080" fill="url(%23g)"/><circle cx="300" cy="200" r="80" fill="rgba(108,92,231,0.15)"/><circle cx="1600" cy="800" r="120" fill="rgba(0,210,211,0.1)"/><circle cx="960" cy="540" r="60" fill="rgba(162,155,254,0.1)"/></svg>';
  }
  window.wpList=['demo.svg']; // 非空数组，让 loadWallpaper 能正常判断
})();

// ===== 认证 =====
window.AUTH_STATE={authenticated:true,username:'admin',must_change:false};

// ===== 在线玩家 =====
window.ONLINE_PLAYERS=['xingyi','Steve','Alex','Notch','jerry','mike'];

// ===== 物品数据 =====
window.ITEMS_LIST=[
  {id:'minecraft:stone',name:'石头',_catId:'bb',_catName:'建筑方块',_catIcon:'🧱'},
  {id:'minecraft:cobblestone',name:'圆石',_catId:'bb',_catName:'建筑方块',_catIcon:'🧱'},
  {id:'minecraft:dirt',name:'泥土',_catId:'bb',_catName:'建筑方块',_catIcon:'🧱'},
  {id:'minecraft:oak_planks',name:'橡木木板',_catId:'bb',_catName:'建筑方块',_catIcon:'🧱'},
  {id:'minecraft:bedrock',name:'基岩',_catId:'bb',_catName:'建筑方块',_catIcon:'🧱'},
  {id:'minecraft:obsidian',name:'黑曜石',_catId:'bb',_catName:'建筑方块',_catIcon:'🧱'},
  {id:'minecraft:diamond_block',name:'钻石块',_catId:'bb',_catName:'建筑方块',_catIcon:'🧱'},
  {id:'minecraft:gold_block',name:'金块',_catId:'bb',_catName:'建筑方块',_catIcon:'🧱'},
  {id:'minecraft:chest',name:'箱子',_catId:'db',_catName:'装饰方块',_catIcon:'🏠'},
  {id:'minecraft:torch',name:'火把',_catId:'db',_catName:'装饰方块',_catIcon:'🏠'},
  {id:'minecraft:crafting_table',name:'工作台',_catId:'db',_catName:'装饰方块',_catIcon:'🏠'},
  {id:'minecraft:furnace',name:'熔炉',_catId:'db',_catName:'装饰方块',_catIcon:'🏠'},
  {id:'minecraft:ender_chest',name:'末影箱',_catId:'db',_catName:'装饰方块',_catIcon:'🏠'},
  {id:'minecraft:bed',name:'床',_catId:'db',_catName:'装饰方块',_catIcon:'🏠'},
  {id:'minecraft:apple',name:'苹果',_catId:'food',_catName:'食物饮品',_catIcon:'🍖'},
  {id:'minecraft:cooked_beef',name:'牛排',_catId:'food',_catName:'食物饮品',_catIcon:'🍖'},
  {id:'minecraft:bread',name:'面包',_catId:'food',_catName:'食物饮品',_catIcon:'🍖'},
  {id:'minecraft:golden_apple',name:'金苹果',_catId:'food',_catName:'食物饮品',_catIcon:'🍖'},
  {id:'minecraft:enchanted_golden_apple',name:'附魔金苹果',_catId:'food',_catName:'食物饮品',_catIcon:'🍖'},
  {id:'minecraft:diamond_pickaxe',name:'钻石镐',_catId:'tools',_catName:'工具',_catIcon:'🔨'},
  {id:'minecraft:diamond_sword',name:'钻石剑',_catId:'weapons',_catName:'武器',_catIcon:'⚔️'},
  {id:'minecraft:bow',name:'弓',_catId:'weapons',_catName:'武器',_catIcon:'⚔️'},
  {id:'minecraft:trident',name:'三叉戟',_catId:'weapons',_catName:'武器',_catIcon:'⚔️'},
  {id:'minecraft:diamond_helmet',name:'钻石头盔',_catId:'armor',_catName:'盔甲',_catIcon:'🛡️'},
  {id:'minecraft:diamond_chestplate',name:'钻石胸甲',_catId:'armor',_catName:'盔甲',_catIcon:'🛡️'},
  {id:'minecraft:elytra',name:'鞘翅',_catId:'armor',_catName:'盔甲',_catIcon:'🛡️'},
  {id:'minecraft:potion',name:'药水',_catId:'potions',_catName:'药水酿造',_catIcon:'🧪'},
  {id:'minecraft:splash_potion',name:'喷溅药水',_catId:'potions',_catName:'药水酿造',_catIcon:'🧪'},
  {id:'minecraft:redstone',name:'红石粉',_catId:'redstone',_catName:'红石电路',_catIcon:'⚡'},
  {id:'minecraft:tnt',name:'TNT',_catId:'redstone',_catName:'红石电路',_catIcon:'⚡'},
  {id:'minecraft:piston',name:'活塞',_catId:'redstone',_catName:'红石电路',_catIcon:'⚡'},
  {id:'minecraft:wheat_seeds',name:'小麦种子',_catId:'plants',_catName:'植物种子',_catIcon:'🌱'},
  {id:'minecraft:poppy',name:'虞美人',_catId:'plants',_catName:'植物种子',_catIcon:'🌱'},
  {id:'minecraft:diamond',name:'钻石',_catId:'material',_catName:'材料',_catIcon:'📎'},
  {id:'minecraft:emerald',name:'绿宝石',_catId:'material',_catName:'材料',_catIcon:'📎'},
  {id:'minecraft:nether_star',name:'下界之星',_catId:'material',_catName:'材料',_catIcon:'📎'},
  {id:'minecraft:totem_of_undying',name:'不死图腾',_catId:'material',_catName:'材料',_catIcon:'📎'},
  {id:'minecraft:music_disc_13',name:'唱片 13',_catId:'music',_catName:'音乐唱片',_catIcon:'🎵'},
  {id:'minecraft:music_disc_pigstep',name:'唱片 Pigstep',_catId:'music',_catName:'音乐唱片',_catIcon:'🎵'},
  {id:'minecraft:command_block',name:'命令方块',_catId:'other',_catName:'其他',_catIcon:'📦'},
  {id:'minecraft:ender_pearl',name:'末影珍珠',_catId:'other',_catName:'其他',_catIcon:'📦'},
  {id:'minecraft:experience_bottle',name:'经验瓶',_catId:'other',_catName:'其他',_catIcon:'📦'}
];

// ===== 实体数据 =====
window.ENTITIES_LIST=[
  {id:'minecraft:zombie',name:'僵尸',cat:'亡灵'},
  {id:'minecraft:skeleton',name:'骷髅',cat:'亡灵'},
  {id:'minecraft:creeper',name:'苦力怕',cat:'敌对'},
  {id:'minecraft:enderman',name:'末影人',cat:'中立'},
  {id:'minecraft:spider',name:'蜘蛛',cat:'敌对'},
  {id:'minecraft:blaze',name:'烈焰人',cat:'敌对'},
  {id:'minecraft:ghast',name:'恶魂',cat:'敌对'},
  {id:'minecraft:wither',name:'凋灵',cat:'BOSS'},
  {id:'minecraft:ender_dragon',name:'末影龙',cat:'BOSS'},
  {id:'minecraft:warden',name:'监守者',cat:'BOSS'},
  {id:'minecraft:iron_golem',name:'铁傀儡',cat:'友好'},
  {id:'minecraft:villager',name:'村民',cat:'友好'},
  {id:'minecraft:wolf',name:'狼',cat:'友好'},
  {id:'minecraft:cat',name:'猫',cat:'友好'},
  {id:'minecraft:pig',name:'猪',cat:'友好'},
  {id:'minecraft:cow',name:'牛',cat:'友好'},
  {id:'minecraft:sheep',name:'羊',cat:'友好'},
  {id:'minecraft:chicken',name:'鸡',cat:'友好'},
  {id:'minecraft:rabbit',name:'兔子',cat:'友好'},
  {id:'minecraft:bee',name:'蜜蜂',cat:'友好'},
  {id:'minecraft:guardian',name:'守卫者',cat:'敌对'},
  {id:'minecraft:phantom',name:'幻翼',cat:'敌对'}
];

// ===== 附魔数据 =====
window.ENCHANT_LIST=[
  {id:'sharpness',name:'锋利',target:'武器'},
  {id:'smite',name:'亡灵杀手',target:'武器'},
  {id:'knockback',name:'击退',target:'武器'},
  {id:'fire_aspect',name:'火焰附加',target:'武器'},
  {id:'looting',name:'抢夺',target:'武器'},
  {id:'sweeping',name:'横扫之刃',target:'剑'},
  {id:'protection',name:'保护',target:'盔甲'},
  {id:'fire_protection',name:'火抗',target:'盔甲'},
  {id:'blast_protection',name:'爆炸保护',target:'盔甲'},
  {id:'thorns',name:'荆棘',target:'盔甲'},
  {id:'respiration',name:'水下呼吸',target:'头盔'},
  {id:'aqua_affinity',name:'水下速掘',target:'头盔'},
  {id:'feather_falling',name:'弹跳',target:'靴子'},
  {id:'unbreaking',name:'耐久',target:'所有'},
  {id:'mending',name:'经验修补',target:'所有'},
  {id:'fortune',name:'时运',target:'工具'},
  {id:'efficiency',name:'效率',target:'工具'},
  {id:'silk_touch',name:'精准采集',target:'工具'},
  {id:'power',name:'力量',target:'弓'},
  {id:'infinity',name:'无限',target:'弓'},
  {id:'loyalty',name:'忠诚',target:'三叉戟'},
  {id:'riptide',name:'浪涌',target:'三叉戟'},
  {id:'channeling',name:'引雷',target:'三叉戟'},
  {id:'impaling',name:'穿刺',target:'三叉戟'}
];

// ===== 玩家统计数据 =====
window.PLAYER_STATS={
  players:{
    xingyi:{total_playtime_seconds:86400,session_count:42,last_login:'2026-08-23 14:00',last_logout:null,online:true},
    Steve:{total_playtime_seconds:43200,session_count:18,last_login:'2026-08-23 13:30',last_logout:'2026-08-23 13:45',online:false},
    Alex:{total_playtime_seconds:36000,session_count:12,last_login:'2026-08-22 20:00',last_logout:'2026-08-22 22:00',online:false},
    Notch:{total_playtime_seconds:72000,session_count:30,last_login:'2026-08-23 12:00',last_logout:'2026-08-23 14:30',online:false},
    jerry:{total_playtime_seconds:18000,session_count:8,last_login:'2026-08-23 14:10',last_logout:null,online:true},
    mike:{total_playtime_seconds:54000,session_count:22,last_login:'2026-08-23 10:00',last_logout:'2026-08-23 11:30',online:false}
  },
  online_count:2
};

// ===== 游戏配置 =====
window.GAME_CONFIG={
  'online-mode':'true',
  'server-port':'25565',
  'gamemode':'survival',
  'difficulty':'normal',
  'pvp':'true',
  'allow-flight':'false',
  'allow-nether':'true',
  'generate-structures':'true',
  'spawn-animals':'true',
  'spawn-monsters':'true',
  'max-players':'20',
  'view-distance':'10',
  'simulation-distance':'10',
  'spawn-protection':'16',
  'level-name':'world',
  'motd':'A Minecraft Server',
  'enable-command-block':'true',
  'op-permission-level':'4',
  'network-compression-threshold':'256',
  'player-idle-timeout':'0'
};

window.GAME_CONFIG_DEFS=[
  ['安全与网络', null],
  ['online-mode','正版认证','switch',''],
  ['enable-rcon','启用RCON','switch',''],
  ['enable-status','启用状态','switch',''],
  ['server-port','服务器端口','number','1-65535'],
  ['server-ip','服务器IP','text','留空=所有IP'],
  ['世界与游戏', null],
  ['gamemode','游戏模式','select','survival=生存,creative=创造,adventure=冒险,spectator=旁观'],
  ['difficulty','难度','select','peaceful=和平,easy=简单,normal=普通,hard=困难'],
  ['pvp','PVP伤害','switch',''],
  ['allow-flight','允许飞行','switch',''],
  ['allow-nether','允许下界','switch',''],
  ['generate-structures','生成结构','switch',''],
  ['spawn-animals','动物刷怪','switch',''],
  ['spawn-monsters','怪物刷怪','switch',''],
  ['max-players','最大玩家数','number','1-1024'],
  ['view-distance','视距','number','3-32'],
  ['simulation-distance','模拟距离','number','3-32'],
  ['spawn-protection','出生点保护','number','0-16'],
  ['level-name','世界名称','text',''],
  ['motd','服务器标语','text',''],
  ['性能与网络', null],
  ['network-compression-threshold','压缩阈值','number','0-32767'],
  ['sync-chunk-writes','同步区块写入','switch',''],
  ['enable-command-block','命令方块','switch',''],
  ['player-idle-timeout','闲置超时(分钟)','number','0=关闭'],
  ['op-permission-level','OP权限等级','number','0-4']
];

// ===== 面板配置 =====
window.PANEL_CONFIG={
  host:'0.0.0.0',port:19888,name:'MC 服务端管理面板',
  mode:'auto',rcon_host:'127.0.0.1',rcon_port:25575,
  rcon_password:'demo_pass_123',server_dir:'.'
};

// ===== 命令数据 =====
window.MOCK_COMMANDS={
  total:24,
  categories:['','信息','玩家','世界','物品','实体','管理','技术'],
  commands:[
    {cmd:'/say 你好世界',cn:'全服消息',cat:'信息',desc:'向所有玩家发送消息'},
    {cmd:'/tp @a 0 64 0',cn:'传送玩家',cat:'世界',desc:'将所有玩家传送到坐标'},
    {cmd:'/gamemode creative @p',cn:'创造模式',cat:'玩家',desc:'设置最近玩家为创造模式'},
    {cmd:'/give @p diamond 64',cn:'给钻石',cat:'物品',desc:'给最近玩家64个钻石'},
    {cmd:'/summon minecraft:zombie',cn:'生成僵尸',cat:'实体',desc:'在当前位置生成一个僵尸'},
    {cmd:'/time set day',cn:'设置白天',cat:'世界',desc:'将游戏时间设为白天'},
    {cmd:'/weather clear',cn:'放晴',cat:'世界',desc:'清除天气效果'},
    {cmd:'/xp give @p 100',cn:'给经验',cat:'玩家',desc:'给最近玩家100经验'},
    {cmd:'/effect give @p speed 30 1',cn:'速度效果',cat:'玩家',desc:'给最近玩家速度效果30秒'},
    {cmd:'/kill @e[type=!player]',cn:'清除实体',cat:'实体',desc:'杀死所有非玩家实体'},
    {cmd:'/ban xingyi 违规',cn:'封禁玩家',cat:'管理',desc:'封禁指定玩家'},
    {cmd:'/op xingyi',cn:'授权OP',cat:'管理',desc:'给玩家管理员权限'},
    {cmd:'/deop xingyi',cn:'取消OP',cat:'管理',desc:'撤销玩家管理员权限'},
    {cmd:'/particle flame ~ ~1 ~ 1 1 1 0 100',cn:'粒子效果',cat:'技术',desc:'在当前上方播放火焰粒子'},
    {cmd:'/save-all',cn:'保存世界',cat:'管理',desc:'保存所有世界数据'},
    {cmd:'/reload',cn:'重载配置',cat:'管理',desc:'reload'},
    {cmd:'/stop',cn:'安全停止',cat:'管理',desc:'安全关闭服务器'},
    {cmd:'/seed',cn:'查看种子',cat:'信息',desc:'显示当前世界种子'},
    {cmd:'/gamerule keepInventory true',cn:'保留物品',cat:'技术',desc:'死亡后保留物品'},
    {cmd:'/gamerule doDaylightCycle false',cn:'冻结时间',cat:'技术',desc:'停止时间流逝'},
    {cmd:'/gamemode spectator @p',cn:'旁观模式',cat:'玩家',desc:'设置旁观模式'},
    {cmd:'/enchant @p sharpness 5',cn:'附魔物品',cat:'物品',desc:'给手中物品附魔锋利5'},
    {cmd:'/clear @p',cn:'清空背包',cat:'管理',desc:'清空最近玩家背包'},
    {cmd:'/list',cn:'查看在线玩家',cat:'信息',desc:'列出所有在线玩家'}
  ]
};

// ===== 日志 =====
var DEMO_LOGS=[
  '[16:30:01] [Server thread/INFO]: Starting minecraft server version 1.21.4',
  '[16:30:01] [Server thread/INFO]: Loading properties',
  '[16:30:02] [Server thread/INFO]: Starting Minecraft server on 0.0.0.0:25565',
  '[16:30:03] [Server thread/INFO]: Preparing level "world"',
  '[16:30:05] [Server thread/INFO]: Preparing spawn area: 40%',
  '[16:30:07] [Server thread/INFO]: Preparing spawn area: 80%',
  '[16:30:08] [Server thread/INFO]: Done (8.2s)! For help, type "help"',
  '[16:30:08] [Server thread/INFO]: xingyi joined the game',
  '[16:30:10] [Server thread/INFO]: Steve joined the game',
  '[16:30:15] [Server thread/INFO]: <xingyi> 大家好！',
  '[16:30:20] [Server thread/INFO]: xingyi: /gamemode creative',
  '[16:30:22] [Server thread/INFO]: xingyi: /tp Steve 0 64 0',
  '[16:30:25] [Server thread/WARN]: Can\'t keep up! Is the server overloaded? Running 5012ms or 100 ticks behind',
  '[16:30:30] [Server thread/INFO]: Alex joined the game',
  '[16:30:35] [Server thread/INFO]: Gave 64 diamond to xingyi',
  '[16:30:40] [Server thread/INFO]: Notch joined the game',
  '[16:30:45] [Server thread/INFO]: Summoned creeper at (100, 65, 200)',
  '[16:30:50] [Server thread/INFO]: Granted Speed II to Steve',
  '[16:30:55] [Server thread/INFO]: The weather is now clear',
  '[16:31:00] [Server thread/INFO]: jerry joined the game',
  '[16:31:05] [Server thread/INFO]: xingyi: /save-all',
  '[16:31:06] [Server thread/INFO]: Saving chunks for level \'world\'',
  '[16:31:06] [Server thread/INFO]: Saved the game',
  '[16:31:10] [Server thread/INFO]: xingyi: /list',
  '[16:31:10] [Server thread/INFO]: There are 6 players online: xingyi, Steve, Alex, Notch, jerry, mike',
  '[16:31:15] [Server thread/INFO]: xingyi: /time set day',
  '[16:31:15] [Server thread/INFO]: Set the time to day',
  '[16:31:20] [Server thread/INFO]: Steve left the game',
  '[16:31:25] [Server thread/INFO]: xingyi: /effect give @p speed 30 1',
  '[16:31:25] [Server thread/INFO]: Granted Speed II to xingyi'
];

var _logIdx=0;
function getNextLog(){
  var logs=[];
  var count=Math.min(2,DEMO_LOGS.length-_logIdx);
  for(var i=0;i<count;i++){
    logs.push(DEMO_LOGS[_logIdx+i]);
  }
  _logIdx+=count;
  if(_logIdx>=DEMO_LOGS.length){
    _logIdx=0;
    var now=new Date().toLocaleTimeString();
    logs.push('['+now+'] [Server thread/INFO]: xingyi: /list');
    logs.push('['+now+'] [Server thread/INFO]: There are '+Math.floor(Math.random()*4+2)+' players online');
  }
  return logs;
}

function mockCommandReply(cmd){
  var c=(cmd||'').trim();
  if(c==='help'){return '✅ 可用指令: say, tp, gamemode, give, summon, time, weather, xp, effect, kill, ban, op, list, seed, save-all, reload, stop, clear'}
  if(c.indexOf('/say')===0){return '✅ <admin> '+c.substring(4)}
  if(c==='save-all'){return '✅ Saved the game'}
  if(c==='reload'){return '✅ Reload complete'}
  if(c==='stop'){return '✅ Stopping the server...'}
  if(c==='list'){return '✅ There are 6 players online: '+window.ONLINE_PLAYERS.join(', ')}
  if(c==='seed'){return '✅ Level seed: 382910472638291'}
  if(c.indexOf('/give')===0){return '✅ Gave 64 diamond to xingyi'}
  if(c.indexOf('/summon')===0){return '✅ Summoned entity at (100, 65, 200)'}
  if(c.indexOf('/tp')===0){return '✅ Teleported Steve to (0, 64, 0)'}
  if(c.indexOf('/gamemode')===0){return '✅ Set gamemode to CREATIVE for Steve'}
  if(c.indexOf('/effect')===0){return '✅ Granted Speed II to xingyi'}
  if(c.indexOf('/weather')===0){return '✅ The weather is now clear'}
  if(c.indexOf('/time')===0){return '✅ Set the time to day'}
  if(c.indexOf('/ban')===0){return '✅ Banned player xingyi'}
  if(c.indexOf('/op')===0){return '✅ Made xingyi a server operator'}
  if(c.indexOf('/deop')===0){return '✅ xingyi is no longer a server operator'}
  if(c.indexOf('/clear')===0){return '✅ Cleared 12 items from xingyi\'s inventory'}
  if(c.indexOf('/gamerule')===0){return '✅ Set gamerule keepInventory to true'}
  if(c.indexOf('/enchant')===0){return '✅ Enchanted item with Sharpness V'}
  if(c.indexOf('kill')===0){return '✅ Removed 1 entity'}
  return '❌ Unknown command: '+c;
}

// ===== 重写 fetch =====
var _realFetch=window.fetch;
window.fetch=function(url,opts){
  return new Promise(function(resolve,reject){
    var data=null;

    try{
      if(url==='/api/auth/check'){
        data=window.AUTH_STATE;
      }else if(url==='/api/auth/logout'){
        data={ok:true};
      }else if(url==='/api/auth/change_password'){
        data={ok:true};
      }else if(url==='/api/auth/change_username'){
        data={ok:true};
      }else if(url==='/api/wallpapers'){
        data={wallpapers:['demo.svg'],count:1};
      }else if(url==='/api/status'){
        data={
          tps:19+Math.random()*0.9,
          playerCount:window.ONLINE_PLAYERS.length,
          players:window.ONLINE_PLAYERS.slice(),
          memoryUsed:Math.floor(Math.random()*1073741824+1073741824),
          timestamp:new Date().toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit',second:'2-digit'}),
          pids:[Math.floor(Math.random()*9000+1000)]
        };
      }else if(url==='/api/serverinfo'){
        data={serverType:'vanilla',serverVersion:'1.21.4',mode:'生存',itemCount:window.ITEMS_LIST.length,entityCount:window.ENTITIES_LIST.length,optimizeMode:'auto'};
      }else if(url==='/api/items'){
        data={items:window.ITEMS_LIST.slice(),enchantments:window.ENCHANT_LIST.slice(),namespaces:[{namespace:'minecraft',name:'原版',count:window.ITEMS_LIST.length}]};
      }else if(url==='/api/entities'){
        data={entities:window.ENTITIES_LIST.slice(),namespaces:[{namespace:'minecraft',name:'原版',count:window.ENTITIES_LIST.length}]};
      }else if(url==='/api/player_stats'){
        data=window.PLAYER_STATS;
      }else if(url==='/api/log'){
        data={lines:getNextLog()};
      }else if(url==='/api/commands/cats'){
        data={categories:window.MOCK_COMMANDS.categories,total:window.MOCK_COMMANDS.total};
      }else if(url==='/api/commands'){
        var body=opts&&opts.body?JSON.parse(opts.body):{};
        var kw=(body.kw||'').toLowerCase();
        var cat=body.category||'';
        var cmds=window.MOCK_COMMANDS.commands.slice();
        if(cat){cmds=cmds.filter(function(c){return c.cat===cat})}
        if(kw){cmds=cmds.filter(function(c){return c.cmd.toLowerCase().indexOf(kw)>=0||c.cn.indexOf(kw)>=0||c.desc.indexOf(kw)>=0||c.cat.indexOf(kw)>=0})}
        data={commands:cmds,total:cmds.length};
      }else if(url==='/api/gen'){
        var body=opts&&opts.body?JSON.parse(opts.body):{};
        var type=body.type||'';
        var params=body.params||{};
        var cmdMap={
          tp:'tp '+params.player+' '+params.x+' '+params.y+' '+params.z,
          gamemode:'gamemode '+params.mode+' '+params.player,
          give:'give '+params.player+' '+params.item+' '+params.count,
          summon:'summon '+params.entity+' '+params.x+' '+params.y+' '+params.z,
          time:'time set '+params.time,
          weather:'weather '+params.weather,
          say:'say '+params.msg,
          xp:'xp give '+params.player+' '+params.amount,
          effect:'effect give '+params.player+' '+params.effect+' '+params.duration+' '+params.amplifier,
          kill:'kill '+params.target,
          particle:'particle '+params.particle+' '+params.x+' '+params.y+' '+params.z+' 0 1 '+params.count,
          ban:'ban '+params.player+' '+params.reason,
          op:'op '+params.player,
          deop:'deop '+params.player
        };
        data={command:'/'+(cmdMap[type]||'unknown '+JSON.stringify(params))};
      }else if(url==='/api/command'){
        data={output:mockCommandReply(opts&&opts.body?JSON.parse(opts.body).command:'')};
      }else if(url==='/api/control'){
        data={output:mockCommandReply(opts&&opts.body?JSON.parse(opts.body).action:'')};
      }else if(url==='/api/config'){
        data={config:window.GAME_CONFIG,definitions:window.GAME_CONFIG_DEFS};
      }else if(url==='/api/config/save'){
        data={ok:true};
      }else if(url==='/api/panel_config'){
        data=window.PANEL_CONFIG;
      }else if(url==='/api/panel_config/save'){
        data={ok:true};
      }else if(url.indexOf('/api/port/check')===0){
        data={note:'端口可用',level:'ok'};
      }else if(url.indexOf('/api/pass/check')===0){
        data={note:'密码一致',level:'ok'};
      }else if(url.indexOf('/api/path/check')===0){
        data={note:'路径存在',level:'ok'};
      }else if(url==='/api/auth'){
        data={ok:true};
      }
    }catch(e){
      data={error:String(e.message)};
    }

    var res={
      ok:true,
      status:200,
      headers:new Map([['content-type','application/json']]),
      json:function(){return Promise.resolve(data)}
    };
    resolve(res);
  });
};

// ===== TPS/内存实时跳动 =====
(function tpsLoop(){
  setInterval(function(){
    var el=document.getElementById('v-tps');
    if(el){el.textContent=(19+Math.random()*0.9).toFixed(1)}
    var memEl=document.getElementById('v-mem');
    if(memEl){memEl.textContent=(1.5+Math.random()*0.5).toFixed(1)+' GB'}
    var timeEl=document.getElementById('v-time');
    if(timeEl){timeEl.textContent=new Date().toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit',second:'2-digit'})}
  },3000);
})();

// ===== 页面标题 =====
document.title='MCpanel 演示 · Minecraft 服务器管理面板';

// ===== 玩家统计定时刷新 =====
(function statsLoop(){
  setInterval(function(){
    var el=document.getElementById('ps-count');
    if(el){
      el.textContent='在线: 2  ·  总计: 6 人';
    }
  },10000);
})();

})();
