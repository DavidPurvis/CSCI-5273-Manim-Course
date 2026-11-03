"""Portable playback: only Python's standard library, no authoring environment."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

if __package__:
    from .local_server import serve
else:
    from local_server import serve

LAUNCHER = "play.py"
COMMAND = "Play Course.command"
MANIFEST = "playback-assets.json"


def mounts(root):
    root = Path(root).resolve()
    return {"/": root / "player", **{f"/{name}/": root / name
            for name in ("video", "captions", "notes", "decks")}}


def asset_path(root, url):
    """Resolve a local player URL, rejecting escapes and remote dependencies."""
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc:
        raise ValueError(f"Nonlocal asset: {url}")
    path = unquote(parsed.path)
    if not path.startswith("/"):
        path = "/" + path
    for prefix, folder in sorted(mounts(root).items(), key=lambda x: -len(x[0])):
        if path.startswith(prefix):
            target = (folder / path[len(prefix):]).resolve()
            if not target.is_relative_to(folder.resolve()):
                raise ValueError(f"Asset escapes its mount: {url}")
            return target
    raise ValueError(f"Unknown asset: {url}")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_assets(root):
    """Return missing/corrupt playback dependencies, without importing the kitchen."""
    root = Path(root).resolve()
    errors = []
    def require(url):
        try:
            path = asset_path(root, url)
            if not path.is_file() or path.stat().st_size == 0:
                errors.append(f"Missing or empty asset: {url}")
        except ValueError as exc:
            errors.append(str(exc))
    for name in ("index.html", "data.json", "player.js", "style.css", "tokens.css"):
        require("/" + name)
    try:
        data = json.loads((root / "player/data.json").read_text(encoding="utf-8"))
        dishes = data["dishes"]
        if not isinstance(dishes, dict) or not dishes:
            raise ValueError("dishes must be a nonempty object")
        for dish in dishes.values():
            # Uncooked dishes intentionally provide only transcript and slides.
            if dish.get("cooked"):
                require(dish["video"])
                require(dish["vtt"])
            for beat in dish.get("beats", []):
                require("/slides/" + beat["slide"])
                require("/decks/" + beat["deck"])
        for concept in data.get("concepts", {}).values():
            require(concept["note"])
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        errors.append(f"Invalid player/data.json: {exc}")
    manifest = root / MANIFEST
    if manifest.exists():
        try:
            records = json.loads(manifest.read_text(encoding="utf-8"))["files"]
            if not isinstance(records, dict) or not records:
                raise ValueError("files must be a nonempty object")
            for relative, expected in records.items():
                path = (root / relative).resolve()
                if not path.is_relative_to(root):
                    errors.append(f"Manifest path escapes bundle: {relative}")
                elif not path.is_file() or sha256(path) != expected:
                    errors.append(f"Asset hash mismatch: {relative}")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"Invalid {MANIFEST}: {exc}")
    return sorted(set(errors))


def write_launcher(destination):
    """Install the two stdlib Python files and macOS double-click entry point."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    here = Path(__file__).resolve().parent
    (destination / LAUNCHER).write_bytes(Path(__file__).read_bytes())
    (destination / "local_server.py").write_bytes((here / "local_server.py").read_bytes())
    command = destination / COMMAND
    command.write_text('#!/bin/bash\nset -e\ncd "$(dirname "$0")"\nexec python3 play.py "$@"\n', encoding="utf-8")
    command.chmod(0o755)
    return destination / LAUNCHER


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    default = Path(__file__).resolve().parent
    if __package__:
        default = default.parents[1].parent
    parser.add_argument("--root", type=Path, default=default)
    parser.add_argument("--port", type=int, default=5273)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--check", action="store_true", help="validate assets and exit")
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")
    errors = validate_assets(args.root)
    if errors:
        print("Playback validation failed:\n" + "\n".join(errors))
        return 1
    if args.check:
        print("Playback assets validated.")
        return 0
    serve(mounts(args.root), port=args.port, open_browser=not args.no_browser)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
