#!/usr/bin/env python3
"""讲稿 frontmatter 解析与 catalog 读写（供 tts.py / GitHub Actions 共用）。"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EPISODES_DIR = ROOT / "content" / "episodes"
AUDIO_DIR = ROOT / "public" / "audio"
CATALOG_PATH = ROOT / "public" / "catalog.json"

DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"
DEFAULT_RATE = "+0%"
DEFAULT_PITCH = "+0Hz"

VOICES = [
    {"id": "zh-CN-XiaoxiaoNeural", "label": "晓晓（女·清晰）"},
    {"id": "zh-CN-XiaoyiNeural", "label": "晓伊（女·柔和）"},
    {"id": "zh-CN-YunxiNeural", "label": "云希（男·沉稳）"},
    {"id": "zh-CN-YunyangNeural", "label": "云扬（男·播音）"},
    {"id": "zh-CN-YunjianNeural", "label": "云健（男·活力）"},
    {"id": "zh-CN-XiaohanNeural", "label": "晓涵（女·热情）"},
]


def slugify(value: str) -> str:
    s = re.sub(r"[^\w\-]+", "-", value.strip(), flags=re.UNICODE)
    s = re.sub(r"-{2,}", "-", s).strip("-").lower()
    return s or "episode"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """解析 --- frontmatter --- 正文。无 frontmatter 时 meta 为空。"""
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n") and text != "---":
        # 也允许文件以 ---\r 开头已处理
        if not text.startswith("---"):
            return {}, text.strip()
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text.strip()
    raw_meta, body = parts[1], parts[2]
    meta: dict = {}
    for line in raw_meta.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, val = line.split(":", 1)
        meta[key.strip()] = val.strip().strip('"').strip("'")
    return meta, body.lstrip("\n").strip()


def extract_title_body(meta: dict, body: str, fallback_stem: str) -> tuple[str, str]:
    lines = body.splitlines()
    title = meta.get("title") or fallback_stem
    script = body
    if lines and lines[0].startswith("#"):
        heading = lines[0].lstrip("#").strip()
        if not meta.get("title"):
            title = heading
        script = "\n".join(lines[1:]).strip()
    return title, script


def build_markdown(meta: dict, body: str) -> str:
    ordered = ["id", "title", "description", "voice", "rate", "pitch", "tone"]
    lines = ["---"]
    seen = set()
    for key in ordered:
        if key in meta and meta[key] is not None and str(meta[key]) != "":
            lines.append(f"{key}: {meta[key]}")
            seen.add(key)
    for key, val in meta.items():
        if key in seen or val is None or str(val) == "":
            continue
        lines.append(f"{key}: {val}")
    lines.append("---")
    lines.append("")
    title = meta.get("title") or "未命名"
    body = body.strip()
    if not body.startswith("#"):
        lines.append(f"# {title}")
        lines.append("")
    lines.append(body)
    lines.append("")
    return "\n".join(lines)


def load_episode_file(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)
    ep_id = meta.get("id") or slugify(path.stem)
    title, script = extract_title_body(meta, body, path.stem)
    description = meta.get("description") or (
        script[:80].replace("\n", " ") + ("…" if len(script) > 80 else "")
    )
    voice = meta.get("voice") or DEFAULT_VOICE
    rate = meta.get("rate") or DEFAULT_RATE
    pitch = meta.get("pitch") or DEFAULT_PITCH
    tone = meta.get("tone") or ""
    audio_rel = f"audio/{ep_id}.mp3"
    audio_path = ROOT / "public" / audio_rel
    return {
        "id": ep_id,
        "title": title,
        "description": description,
        "voice": voice,
        "rate": rate,
        "pitch": pitch,
        "tone": tone,
        "body": script,
        "raw": raw,
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "audio": f"/{audio_rel}",
        "hasAudio": audio_path.is_file() and audio_path.stat().st_size > 0,
    }


def write_episode_file(path: Path, data: dict) -> dict:
    ep_id = slugify(str(data.get("id") or path.stem))
    meta = {
        "id": ep_id,
        "title": data.get("title") or ep_id,
        "description": data.get("description") or "",
        "voice": data.get("voice") or DEFAULT_VOICE,
        "rate": data.get("rate") or DEFAULT_RATE,
        "pitch": data.get("pitch") or DEFAULT_PITCH,
        "tone": data.get("tone") or "",
    }
    body = (data.get("body") or "").strip()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_markdown(meta, body), encoding="utf-8")
    return load_episode_file(path)


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


def upsert_catalog_episode(episode: dict) -> None:
    catalog = load_catalog()
    episodes = catalog.setdefault("episodes", [])
    for i, existing in enumerate(episodes):
        if existing["id"] == episode["id"]:
            episodes[i] = {**existing, **episode}
            save_catalog(catalog)
            return
    episodes.append(episode)
    save_catalog(catalog)


def remove_catalog_episode(ep_id: str) -> None:
    catalog = load_catalog()
    catalog["episodes"] = [e for e in catalog.get("episodes", []) if e.get("id") != ep_id]
    save_catalog(catalog)


def list_episode_paths(*, include_templates: bool = False) -> list[Path]:
    EPISODES_DIR.mkdir(parents=True, exist_ok=True)
    paths = sorted(EPISODES_DIR.glob("*.md"))
    if include_templates:
        return paths
    return [p for p in paths if not p.name.startswith("_")]


def rebuild_catalog_from_disk() -> dict:
    """按磁盘上的讲稿与音频重建 catalog（去掉已删除节目）。"""
    episodes = []
    for path in list_episode_paths():
        ep = load_episode_file(path)
        if not ep["body"].strip():
            continue
        # 尚未生成音频的不进播放列表
        if not ep["hasAudio"]:
            continue
        episodes.append(
            {
                "id": ep["id"],
                "title": ep["title"],
                "description": ep["description"],
                "audio": ep["audio"],
                "script": ep["path"],
                "voice": ep["voice"],
                "rate": ep["rate"],
                "pitch": ep["pitch"],
                "tone": ep["tone"],
            }
        )
    catalog = {"episodes": episodes}
    save_catalog(catalog)
    return catalog
