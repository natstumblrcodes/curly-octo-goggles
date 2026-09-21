#!/usr/bin/env python3
"""Create byte-controlled bubble diagnostics without changing the theme source."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "diagnostics" / "runs"
BASELINE = ROOT / "diagnostics" / "baseline"
SOURCES = ("TheFinalCode.html", "THEFINALCODE.txt")
BUBBLE = re.compile(rb'<img class="effect bubble"[^>]*>')
REGION = re.compile(rb'<div class="effect-region (?:desktop|mobile)-bubbles"[^>]*>')

class AuditParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.errors: list[str] = []
        self.ids: list[str] = []
        self.bubbles: list[dict[str, str]] = []
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if "id" in data: self.ids.append(data["id"])
        if tag == "img" and data.get("class") == "effect bubble": self.bubbles.append(data)
    def error(self, message): self.errors.append(message)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def remove_indices(source: bytes, indices: set[int]) -> tuple[bytes, list[bytes]]:
    tags = list(BUBBLE.finditer(source))
    removed = [m.group() for i, m in enumerate(tags, 1) if i in indices]
    output = bytearray()
    cursor = 0
    for i, m in enumerate(tags, 1):
        if i in indices:
            output.extend(source[cursor:m.start()])
            cursor = m.end()
    output.extend(source[cursor:])
    return bytes(output), removed

def write_variant(base: Path, label: str, data: bytes, removed: list[bytes]) -> dict:
    path = OUT / f"{base.stem}.{label}{base.suffix}"
    path.write_bytes(data)
    return {"file": path.name, "bytes": len(data), "sha256": sha(data),
            "removed_bubble_indices": [i + 1 for i, _ in enumerate(removed)],
            "removed_bytes": sum(map(len, removed))}

def minify_effects(source: bytes) -> bytes:
    # This expression only operates inside .effects containers and removes whitespace
    # between tags; it cannot change an attribute, URL, CSS value, or element.
    def compact(match: re.Match[bytes]) -> bytes:
        return re.sub(rb">\s+<", b"><", match.group())
    return re.sub(rb'<div class="effects"[^>]*><div class="effect-region [^>]*>.*?</div></div>',
                  compact, source, flags=re.DOTALL)

def audit(source: bytes) -> dict:
    parser = AuditParser()
    parser.feed(source.decode("utf-8"))
    parser.close()
    bubble_tags = [m.group() for m in BUBBLE.finditer(source)]
    urls = [re.search(rb'\bsrc="([^"]+)"', tag).group(1).decode() for tag in bubble_tags]
    styles = [re.search(rb'\bstyle="([^"]+)"', tag).group(1).decode() for tag in bubble_tags]
    return {
        "bubble_count": len(bubble_tags), "region_count": len(REGION.findall(source)),
        "unique_bubble_urls": sorted(set(urls)), "url_counts": {u: urls.count(u) for u in sorted(set(urls))},
        "unquoted_src": source.count(b" src=https://"), "unquoted_style": source.count(b" style="),
        "control_bytes": sorted(set(x for x in source if x < 32 and x not in (9, 10, 13))),
        "duplicate_ids": sorted({i for i in parser.ids if parser.ids.count(i) > 1}),
        "html_parser_errors": parser.errors,
        "malformed_style_indices": [i + 1 for i, s in enumerate(styles)
                                    if any(not part or ":" not in part for part in s.split(";"))],
        "url_syntax": [{"url": u, "https": urlparse(u).scheme == "https",
                         "host": urlparse(u).netloc, "path": urlparse(u).path,
                         "has_whitespace": any(c.isspace() for c in u)} for u in sorted(set(urls))],
    }

def run(source_path: Path) -> dict:
    source = source_path.read_bytes()
    tags = list(BUBBLE.finditer(source))
    if len(tags) != 16:
        raise ValueError(f"Expected 16 bubble elements in {source_path}; found {len(tags)}")
    original = OUT / f"{source_path.name}.original"
    shutil.copyfile(source_path, original)
    restored = OUT / f"{source_path.stem}.restored{source_path.suffix}"
    shutil.copyfile(original, restored)
    variants = {}
    # The order is document order: desktop bubbles 1–8, mobile bubbles 9–16.
    for label, indices in {
        "bubbles-removed": set(range(1, 17)),
        "group-a": set(range(5, 17)),       # only group A (desktop 1–4)
        "group-b": set(range(1, 5)) | set(range(9, 17)), # only group B (desktop 5–8)
        "groups-a-b": set(range(9, 17)),    # desktop 1–8
        "25-percent": set(range(5, 17)),
        "50-percent": set(range(9, 17)),
        "75-percent": set(range(13, 17)),
        "one": set(range(2, 17)),
        "two": set(range(3, 17)),
        "three": set(range(4, 17)),
        "four": set(range(5, 17)),
        "eight": set(range(9, 17)),
        "twelve": set(range(13, 17)),
    }.items():
        data, removed = remove_indices(source, indices)
        variants[label] = write_variant(source_path, label, data, removed)
        variants[label]["kept_bubble_indices"] = [i for i in range(1, 17) if i not in indices]
    mini = minify_effects(source)
    variants["effects-whitespace-minified"] = write_variant(source_path, "effects-whitespace-minified", mini, [])
    variants["effects-whitespace-minified"]["changed_bytes"] = len(source) - len(mini)
    return {"source": source_path.name, "original_bytes": len(source), "original_sha256": sha(source),
            "restored_sha256": sha(restored.read_bytes()), "restored_matches_original": source == restored.read_bytes(),
            "audit": audit(source), "variants": variants}

def main() -> None:
    BASELINE.mkdir(parents=True, exist_ok=True)
    checksums = []
    for filename in SOURCES:
        source = ROOT / filename
        backup = BASELINE / f"{filename}.original"
        shutil.copyfile(source, backup)
        checksums.append(f"{sha(source.read_bytes())}  {filename}\n")
        checksums.append(f"{sha(backup.read_bytes())}  {backup.name}\n")
    (BASELINE / "SHA256SUMS").write_text("".join(checksums))
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    result = {path: run(ROOT / path) for path in SOURCES}
    (OUT / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
if __name__ == "__main__": main()
