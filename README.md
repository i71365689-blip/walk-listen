# 走路听

边走路、边用耳机听中文知识。内容可离线缓存，插上耳机随时播。

## 技术栈（已定）

| 层 | 选型 | 原因 |
|---|---|---|
| 手机端 | **Vite + React + TypeScript + PWA** | 可加到主屏幕，像 App；Service Worker 离线缓存音频 |
| 播放 | HTML5 Audio + Media Session | 锁屏/耳机键可控；后台继续播 |
| 配音 | **edge-tts**（微软神经语音） | 中文音色自然好听；预先生成 MP3，完全离线 |
| 文稿 | `content/episodes/*.md` | 你之后让我用「别样口吻」改写；再跑 TTS 出音频 |
| 目录 | `public/catalog.json` | 播放器读取节目列表 |

**不做原生 App（暂定）**：PWA 已够用「离线 + 耳机 + 锁屏播放」，开发和装到手机更快。若以后要上架应用商店再迁。

## 工作流（内容阶段）

1. 你给主题 / 书面材料  
2. 我按你要的口吻改写成「适合听」的中文讲稿 → `content/episodes/`  
3. 跑 TTS 生成 MP3 → `public/audio/`，并更新 `catalog.json`  
4. 手机打开（或已安装的 PWA）→ 点「下载离线」→ 走路听  

## 本地开发

```bash
npm install
npm run dev -- --host   # 手机连同一 WiFi 用电脑 IP 访问
```

配音（有文稿后）：

```bash
pip install -r scripts/requirements.txt
python scripts/tts.py content/episodes/示例.md
```

构建离线包：

```bash
npm run build
npm run preview -- --host
```

## 手机使用要点

1. 用 Chrome / Safari 打开站点，选「添加到主屏幕」  
2. 有网时点节目旁的「下载离线」  
3. 断网后仍可播放已下载内容  
4. 插上耳机即可听；锁屏后也可继续  

## 默认音色

`zh-CN-XiaoxiaoNeural`（晓晓）— 清晰、自然。可在 `scripts/tts.py` 里换成其他中文神经音色。
