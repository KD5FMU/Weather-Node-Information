#!/usr/bin/env python3
import argparse
import os
import shutil
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCRIPT = '<script src="node-weather.js" defer></script>\n'
SCRIPT_ANCHOR = '<script type="text/javascript">\n// when DOM is ready'
ROW = "$('#table_' + localNode + ' tbody:first').html(tablehtml);"
HOOK = (
    "\n      if (window.supermonNodeWeather) {\n"
    "        window.supermonNodeWeather(localNode, document.getElementById('table_' + localNode)?.tBodies[0]);\n"
    "      }"
)
WEATHER = "// Added WA3DSP Weather conditions\n"
END = 'print "</p>";\n\n#print'
GUARD = "if (empty($NODE_WEATHER_HIDE_LEGACY)) {\n"


def transform(source):
    changes = [
        (SCRIPT_ANCHOR, SCRIPT + SCRIPT_ANCHOR),
        (ROW, ROW + HOOK),
    ]
    for before, after in changes:
        if source.count(before) != 1:
            raise ValueError("Unexpected link.php layout. No changes written.")
        if after not in source:
            source = source.replace(before, after, 1)
    if source.count(WEATHER) != 1:
        raise ValueError("Unexpected page-level weather block. No changes written.")
    start = source.index(WEATHER)
    end = source.index(END, start)
    if source[start - len(GUARD):start] != GUARD:
        source = source[:start] + GUARD + source[start:end] + "}\n\n" + source[end:]
    return source


def remove(source):
    if GUARD in source:
        start = source.index(GUARD) + len(GUARD)
        if not source.startswith(WEATHER, start):
            raise ValueError("Modified add-on weather block. No changes written.")
        end = source.index(END, start)
        if source[end - 3:end] != "}\n\n":
            raise ValueError("Modified add-on weather block. No changes written.")
        source = source[:start - len(GUARD)] + source[start:end - 3] + source[end:]
    for snippet in (SCRIPT, HOOK):
        if source.count(snippet) > 1:
            raise ValueError("Duplicate add-on integration. No changes written.")
        source = source.replace(snippet, "", 1)
    if "node-weather.js" in source or "supermonNodeWeather" in source:
        raise ValueError("Modified add-on integration. No changes written.")
    return source


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("link_php", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--remove", action="store_true")
    args = parser.parse_args()
    path = args.link_php
    original = path.read_bytes()
    newline = "\r\n" if b"\r\n" in original else "\n"
    operation = remove if args.remove else transform
    updated = operation(original.decode("utf-8").replace("\r\n", "\n"))
    updated = updated.replace("\n", newline).encode("utf-8")
    if original == updated:
        print(f"{path} already in the requested state")
        return
    if args.check:
        print(f"{path} is compatible")
        return
    attributes = path.stat()
    backup_dir = Path("/var/backups/supermon-node-weather")
    backup_dir.mkdir(mode=0o700, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = backup_dir / f"link.php.{timestamp}"
    shutil.copy2(path, backup)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(updated)
    try:
        os.chown(temporary, attributes.st_uid, attributes.st_gid)
        temporary.chmod(stat.S_IMODE(attributes.st_mode))
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Updated {path}. Backup saved to {backup}")


if __name__ == "__main__":
    main()
