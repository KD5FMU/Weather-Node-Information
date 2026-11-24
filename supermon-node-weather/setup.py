import getpass
import json
from pathlib import Path
import re
import subprocess
import sys

settings, key, staging, dashboard = map(Path, sys.argv[1:5])


def ask(prompt, pattern):
    while True:
        answer = input(prompt).strip()
        if re.fullmatch(pattern, answer):
            return answer
        print("Enter one of the requested values.")


def local_nodes():
    result = subprocess.check_output([
        "php", "-r",
        r"""
        $config = parse_ini_file($argv[1], true, INI_SCANNER_RAW);
        if ($config === false) exit(1);
        foreach ($config as $node => $section) {
            $host = $section['host'] ?? '';
            if (preg_match('/^[0-9]+$/D', (string) $node) &&
                preg_match('/^(?:localhost|127(?:\.\d{1,3}){3}|\[::1\])(?::\d+)?$|^::1$/i', $host)) {
                echo $node, PHP_EOL;
            }
        }
        """,
        str(dashboard / "allmon.ini"),
    ], text=True)
    return list(dict.fromkeys(result.splitlines()))


if not settings.exists() or "--configure" in sys.argv[5:]:
    current = json.loads(settings.read_text()) if settings.exists() else {}
    previous = current.get("nodes", {})
    scope = ask("Enable weather for [1] one node or [2] all local Supermon nodes? [1] ", r"[12]?")
    if scope == "2":
        nodes = local_nodes()
        if not nodes:
            raise SystemExit("No local nodes found in allmon.ini. Rerun and choose one node by ID.")
        print("Local nodes found: " + ", ".join(nodes))
    else:
        nodes = [ask("AllStar node ID: ", r"[0-9]+")]

    config = Path("/usr/local/bin/SkywarnPlus/config.yaml")
    selected = {}
    for node in nodes:
        entry = dict(previous.get(node, {}))
        old_zip = entry.get("zip")
        if old_zip and re.fullmatch(r"[0-9]{5}", old_zip):
            entry["zip"] = ask(f"Five-digit U.S. ZIP for {node} [{old_zip}]: ", r"(?:[0-9]{5})?") or old_zip
        else:
            entry["zip"] = ask(f"Five-digit U.S. ZIP for {node}: ", r"[0-9]{5}")
        skywarn = Path(entry.get("skywarn_config", config))
        if skywarn.is_file():
            use = ask(f"Show local SkywarnPlus for {node}? [Y/n] ", r"[yYnN]?")
            if use.lower() == "n":
                entry.pop("skywarn_config", None)
            else:
                entry["skywarn_config"] = str(skywarn)
        selected[node] = entry

    fixed = ask("Use the same fixed width for all node tables? [y/N] ", r"[yYnN]?")
    current["nodes"] = selected
    if fixed.lower() == "y":
        while True:
            width = int(ask("Width in pixels, 640–2000 [1100]: ", r"(?:[0-9]{3,4})?") or "1100")
            if 640 <= width <= 2000:
                current["table_width"] = width
                break
            print("Enter a width from 640 to 2000 pixels.")
    else:
        current.pop("table_width", None)
    (staging / "settings").write_text(json.dumps(current, indent=2) + "\n")

if not key.is_file() or not key.read_text().strip():
    value = getpass.getpass("WeatherAPI.com key (hidden): ").strip()
    if not value:
        raise SystemExit("No key entered. Setup stopped.")
    (staging / "key").write_text(value + "\n")
