#!/usr/bin/python3
import json
import os
from pathlib import Path
import re
import stat
import tempfile


def change_width(path):
    settings = json.loads(path.read_text())
    if not isinstance(settings, dict) or not isinstance(settings.get("nodes"), dict):
        raise ValueError("Invalid node weather settings.")

    print(f"Current table width: {settings.get('table_width', 'automatic')}")
    while True:
        answer = input("New width in pixels (640–2000), auto, or Enter to cancel: ").strip().lower()
        if not answer:
            print("Cancelled.")
            return
        if answer == "auto":
            settings.pop("table_width", None)
            break
        if re.fullmatch(r"[0-9]{3,4}", answer) and 640 <= int(answer) <= 2000:
            settings["table_width"] = int(answer)
            break
        print("Enter a width from 640 to 2000, or type auto.")

    attributes = path.stat()
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
    try:
        temporary.write_text(json.dumps(settings, indent=2) + "\n")
        os.chown(temporary, attributes.st_uid, attributes.st_gid)
        temporary.chmod(stat.S_IMODE(attributes.st_mode))
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)

    print("Table width saved. Refresh your Supermon page.")


if __name__ == "__main__":
    if os.geteuid() != 0:
        raise SystemExit("Run: sudo supermon-node-weather-width")
    try:
        change_width(Path("/etc/supermon-node-weather.json"))
    except (EOFError, KeyboardInterrupt):
        raise SystemExit("\nCancelled.")
    except FileNotFoundError:
        raise SystemExit("Node Weather configuration is missing. Run the installer first.")
    except (OSError, ValueError) as error:
        raise SystemExit(f"Could not update table width: {error}")
