#!/usr/bin/env python3
"""把 content/episodes 下的中文讲稿转成 MP3，并更新 public/catalog.json。"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
EPISODES_DIR = ROOT / "content" / "episodes"
AUDIO_DIR = ROOT / "public" / "audio"
CATALOG_PATH = ROOT / "public" / "catalog.json"

# 默认：晓晓 — 自然清晰，适合走路听。可按喜好改。
DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"

# 可选参考：zh-CN-YunxiNeural（男）、zh-CN-XiaoyiNeural、zh-CN-YunyangNeural


def slug_from_stem(stem: str) -> str:
    return re.sub(r"[^\w\-]+", "-", stem, flags=re.UNICODE).strip("-").lower() or "episode"


def read_script(path: Path) -> tuple[str, str]:
    """返回 (标题, 正文)。首行 # 标题 可选。"""
    text = path.read_text(encoding="utf-8").strip()
    lines = text.splitlines()
    if lines and lines[0].startswith("#"):
        title = lines[0].lstrip("#").strip()
        body = "\n".join(lines[1:]).strip()
    else:
        title = path.stem
        body = text
    if not body:
        raise SystemExit(f"文稿为空: {path}")
    return title, body


def load_catalog() -> dict:
    if CATALOG_PATH.exists():
        return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return {"episodes": []}


def save_catalog(catalog: dict) -> None:
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_PATH.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


async def synthesize(text: str, out_mp3: Path, voice: str) -> None:
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(out_mp3))


def upsert_episode(catalog: dict, episode: dict) -> None:
    episodes = catalog.setdefault("episodes", [])
    for i, existing in enumerate(episodes):
        if existing["id"] == episode["id"]:
            episodes[i] = {**existing, **episode}
            return
    episodes.append(episode)


async def process_file(path: Path, voice: str) -> None:
    title, body = read_script(path)
    ep_id = slug_from_stem(path.stem)
    audio_rel = f"audio/{ep_id}.mp3"
    out_mp3 = ROOT / "public" / audio_rel

    print(f"配音中: {title} → {audio_rel} ({voice})")
    await synthesize(body, out_mp3, voice)

    catalog = load_catalog()
    upsert_episode(
        catalog,
        {
            "id": ep_id,
            "title": title,
            "description": body[:80].replace("\n", " ") + ("…" if len(body) > 80 else ""),
            "audio": f"/{audio_rel}",
            "script": str(path.relative_to(ROOT)).replace("\\", "/"),
            "voice": voice,
        },
    )
    save_catalog(catalog)
    print(f"完成: {title}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="中文讲稿 → MP3（edge-tts）")
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="讲稿路径；省略则处理 content/episodes 下全部 .md",
    )
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="edge-tts 音色名")
    args = parser.parse_args()

    files = args.files
    if not files:
        EPISODES_DIR.mkdir(parents=True, exist_ok=True)
        files = sorted(EPISODES_DIR.glob("*.md"))
        if not files:
            raise SystemExit(f"没有讲稿。请把 .md 放到 {EPISODES_DIR}")

    for f in files:
        path = f if f.is_absolute() else ROOT / f
        if not path.exists():
            raise SystemExit(f"找不到文件: {path}")
        await process_file(path, args.voice)


if __name__ == "__main__":
    asyncio.run(main())
