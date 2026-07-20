# 走路听

边走路、边用耳机听中文知识。内容在 GitHub 上更新，Actions 自动配音，手机打开网站就能听。

**网站：** https://i71365689-blip.github.io/walk-listen/

## 你怎么更新节目（不用在电脑开后台）

1. 跟我说要听什么、什么口吻  
2. 我写成讲稿（`content/episodes/*.md`）  
3. 你用网页上传到仓库（或直接在 GitHub 网页改文件）：  
   https://github.com/i71365689-blip/walk-listen/upload/main/content/episodes  
4. 等 Actions 里 **Generate TTS** 跑完（自动生成 MP3 + 更新目录）  
5. 再等 **Deploy to GitHub Pages** 完成  
6. 手机刷新网站即可听  

调音色：改讲稿开头的 `voice` / `rate` / `pitch`，保存后再等 Actions。

## 讲稿格式

放在 `content/episodes/`，文件名建议与 `id` 一致。以下划线开头的文件（如 `_template.md`）是模板，**不会**配音。

```markdown
---
id: demo-001
title: 节目标题
description: 一两句简介
voice: zh-CN-XiaoxiaoNeural
rate: +0%
pitch: +0Hz
tone: 口语闲聊
---

# 节目标题

正文讲稿（适合边走边听的中文）……
```

自动产物：

- `public/audio/{id}.mp3`
- `public/catalog.json`（播放器只读这个）

## 常用音色

| voice | 说明 |
|---|---|
| `zh-CN-XiaoxiaoNeural` | 晓晓（女·清晰，默认） |
| `zh-CN-XiaoyiNeural` | 晓伊（女·柔和） |
| `zh-CN-YunxiNeural` | 云希（男·沉稳） |
| `zh-CN-YunyangNeural` | 云扬（男·播音） |
| `zh-CN-YunjianNeural` | 云健（男·活力） |
| `zh-CN-XiaohanNeural` | 晓涵（女·热情） |

`rate` 例：`+0%`、`+10%`、`-10%`。`pitch` 例：`+0Hz`、`+5Hz`、`-5Hz`。

## 技术栈

| 层 | 选型 |
|---|---|
| 手机听 | Vite + React + PWA（GitHub Pages） |
| 配音 | edge-tts（GitHub Actions 自动跑） |
| 文稿 | `content/episodes/*.md` + frontmatter |

## 本地开发（可选，不是更新节目所必需）

```bash
npm install
npm run dev
```

本地试配音：

```bash
pip install -r scripts/requirements.txt
python scripts/tts.py
```

