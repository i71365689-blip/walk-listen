#!/usr/bin/env python3
"""把 content/episodes 下的中文讲稿转成 MP3，并更新 public/catalog.json。"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import edge_tts

from episode_lib import (
    DEFAULT_PITCH,
    DEFAULT_RATE,
    DEFAULT_VOICE,
    EPISODES_DIR,
    ROOT,
    VOICES,
    load_episode_file,
    list_episode_paths,
    rebuild_catalog_from_disk,
    upsert_catalog_episode,
)


async def synthesize(
    text: str,
    out_mp3: Path,
    voice: str,
    rate: str = DEFAULT_RATE,
    pitch: str = DEFAULT_PITCH,
) -> None:
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(str(out_mp3))


async def process_episode(path: Path, voice_override: str | None = None) -> dict:
    ep = load_episode_file(path)
    voice = voice_override or ep["voice"] or DEFAULT_VOICE
    rate = ep.get("rate") or DEFAULT_RATE
    pitch = ep.get("pitch") or DEFAULT_PITCH
    body = ep["body"]
    if not body.strip():
        raise SystemExit(f"文稿为空: {path}")

    ep_id = ep["id"]
    audio_rel = f"audio/{ep_id}.mp3"
    out_mp3 = ROOT / "public" / audio_rel

    print(f"配音中: {ep['title']} → {audio_rel} ({voice}, {rate}, {pitch})")
    await synthesize(body, out_mp3, voice, rate=rate, pitch=pitch)

    entry = {
        "id": ep_id,
        "title": ep["title"],
        "description": ep["description"],
        "audio": f"/{audio_rel}",
        "script": ep["path"],
        "voice": voice,
        "rate": rate,
        "pitch": pitch,
        "tone": ep.get("tone") or "",
    }
    upsert_catalog_episode(entry)
    print(f"完成: {ep['title']}")
    return entry


async def preview_clip(
    text: str,
    voice: str,
    rate: str,
    pitch: str,
    out_mp3: Path,
) -> None:
    sample = text.strip()[:120] or "这是走路听的试听片段。"
    await synthesize(sample, out_mp3, voice, rate=rate, pitch=pitch)


async def main() -> None:
    parser = argparse.ArgumentParser(description="中文讲稿 → MP3（edge-tts）")
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="讲稿路径；省略则处理 content/episodes 下全部 .md",
    )
    parser.add_argument("--voice", default=None, help="覆盖 frontmatter 中的音色")
    parser.add_argument(
        "--preview",
        action="store_true",
        help="仅试听：读 stdin JSON {text,voice,rate,pitch,out}",
    )
    parser.add_argument("--list-voices", action="store_true", help="打印可用音色 JSON")
    args = parser.parse_args()

    if args.list_voices:
        print(json.dumps(VOICES, ensure_ascii=False, indent=2))
        return

    if args.preview:
        payload = json.loads(sys.stdin.read())
        out = Path(payload["out"])
        await preview_clip(
            payload.get("text") or "",
            payload.get("voice") or DEFAULT_VOICE,
            payload.get("rate") or DEFAULT_RATE,
            payload.get("pitch") or DEFAULT_PITCH,
            out,
        )
        print(str(out))
        return

    files = args.files
    if not files:
        files = list_episode_paths()
        if not files:
            print(f"没有讲稿。请把 .md 放到 {EPISODES_DIR}")
            rebuild_catalog_from_disk()
            return

    for f in files:
        path = f if f.is_absolute() else ROOT / f
        if not path.exists():
            raise SystemExit(f"找不到文件: {path}")
        if path.name.startswith("_"):
            print(f"跳过模板: {path.name}")
            continue
        await process_episode(path, args.voice)

    rebuild_catalog_from_disk()


if __name__ == "__main__":
    asyncio.run(main())

