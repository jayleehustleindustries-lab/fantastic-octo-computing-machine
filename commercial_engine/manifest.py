"""Load and validate a commercial manifest CSV before any paid call is made.

One CSV row = one scene. Rows sharing ``video_id`` form one commercial, ordered
by ``scene_num``. Validation is strict and collects every problem so an
operator fixes the sheet once instead of discovering errors mid-render.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

from .config import settings

REQUIRED_COLUMNS = (
    "video_id",
    "concept_name",
    "trade",
    "scene_num",
    "source",
    "visual_prompt",
    "hud_overlay_text",
    "voiceover_script",
)
SOURCES = ("presenter", "broll", "screen_recording")
MANIFEST_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,80}\.csv$")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,40}$")
# HUD text is burned via drawtext textfile=, so special chars are safe, but keep
# it to printable characters a phone viewer can read.
HUD_ALLOWED_RE = re.compile(r"^[A-Za-z0-9 .,:;!?'&$%+=/#@\-]+$")


class ManifestError(ValueError):
    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


@dataclass(frozen=True)
class Scene:
    video_id: str
    scene_num: int
    source: str
    visual_prompt: str
    hud_overlay_text: str
    voiceover_script: str

    @property
    def scene_id(self) -> str:
        return f"{self.video_id}-{self.scene_num:02d}"


@dataclass(frozen=True)
class Commercial:
    video_id: str
    concept_name: str
    trade: str
    scenes: tuple[Scene, ...] = field(default_factory=tuple)


def resolve_manifest_path(name: str, manifests_dir: str | None = None) -> Path:
    """Map a bare manifest file name to a path inside MANIFESTS_DIR.

    Rejects anything that is not a plain ``name.csv`` so a request can never
    read files outside the manifests directory.
    """
    if not MANIFEST_NAME_RE.match(name or ""):
        raise ManifestError([f"invalid manifest name {name!r}: use a plain file name like 'jobcommand_v2.csv'"])
    root = Path(manifests_dir or settings.manifests_dir).resolve()
    path = (root / name).resolve()
    if path.parent != root:
        raise ManifestError([f"manifest {name!r} escapes the manifests directory"])
    if not path.is_file():
        raise ManifestError([f"manifest {name!r} not found in {root}"])
    return path


def _clean(value: str | None) -> str:
    return (value or "").strip()


def parse_manifest(path: Path, *, hud_max_chars: int | None = None) -> list[Commercial]:
    hud_max = hud_max_chars or settings.hud_max_chars
    problems: list[str] = []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ManifestError([f"missing columns: {', '.join(missing)}"])
        rows = list(reader)
    if not rows:
        raise ManifestError(["manifest has no rows"])

    grouped: dict[str, list[tuple[int, dict[str, str]]]] = {}
    for line_no, raw in enumerate(rows, start=2):
        row = {k: _clean(raw.get(k)) for k in REQUIRED_COLUMNS}
        where = f"line {line_no}"
        for col in REQUIRED_COLUMNS:
            if not row[col]:
                problems.append(f"{where}: {col} is empty")
        if row["video_id"] and not ID_RE.match(row["video_id"]):
            problems.append(f"{where}: video_id {row['video_id']!r} must be letters, digits, '-' or '_'")
        if row["source"] and row["source"] not in SOURCES:
            problems.append(f"{where}: source {row['source']!r} must be one of {', '.join(SOURCES)}")
        hud = row["hud_overlay_text"]
        if hud and len(hud) > hud_max:
            problems.append(f"{where}: hud_overlay_text is {len(hud)} chars (max {hud_max}) — readable in ~2s on a phone")
        if hud and not HUD_ALLOWED_RE.match(hud):
            problems.append(f"{where}: hud_overlay_text has unsupported characters")
        try:
            num = int(row["scene_num"])
            if num < 1:
                raise ValueError
        except ValueError:
            problems.append(f"{where}: scene_num {row['scene_num']!r} must be a positive integer")
            num = -1
        grouped.setdefault(row["video_id"], []).append((num, row))

    commercials: list[Commercial] = []
    for video_id, items in grouped.items():
        if not video_id:
            continue
        nums = sorted(n for n, _ in items)
        if nums != list(range(1, len(items) + 1)):
            problems.append(f"{video_id}: scene_num must run 1..{len(items)} with no gaps or duplicates (got {nums})")
        for key in ("concept_name", "trade"):
            values = {r[key] for _, r in items}
            if len(values) > 1:
                problems.append(f"{video_id}: {key} must be the same on every scene (got {sorted(values)})")
        first = items[0][1]
        scenes = tuple(
            Scene(
                video_id=video_id,
                scene_num=n,
                source=r["source"],
                visual_prompt=r["visual_prompt"],
                hud_overlay_text=r["hud_overlay_text"],
                voiceover_script=r["voiceover_script"],
            )
            for n, r in sorted(items, key=lambda t: t[0])
        )
        commercials.append(Commercial(video_id=video_id, concept_name=first["concept_name"], trade=first["trade"], scenes=scenes))

    if problems:
        raise ManifestError(problems)
    return commercials
