#!/usr/bin/env python3
import fcntl
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import yaml

KEY_FILE = Path("/etc/supermon-node-weather.key")


def weather(zip_code):
    key = KEY_FILE.read_text().strip()
    if not key:
        raise ValueError("WeatherAPI key is empty")
    query = urlencode({"key": key, "q": zip_code})
    with urlopen("https://api.weatherapi.com/v1/current.json?" + query, timeout=8) as response:
        data = json.load(response)
    location, current = data["location"], data["current"]
    speed = current.get("wind_mph")
    direction = current.get("wind_dir")
    gust = current.get("gust_mph")
    wind_summary = ""
    if isinstance(speed, (int, float)):
        wind_summary = f", wind {speed:g} mph"
        if isinstance(direction, str) and direction.strip():
            wind_summary += f" {direction.strip()}"
        if isinstance(gust, (int, float)):
            wind_summary += f" (gust {gust:g})"
    return {
        "location": f"{location['name']}, {location['region']} {zip_code}",
        "conditions": (
            f"{current['temp_f']:g}°F, {current['temp_c']:g}°C, "
            f"{current['humidity']}% RH / {current['condition']['text']}"
            f"{wind_summary}"
        ),
    }


def skywarn(config_path):
    try:
        config = yaml.safe_load(Path(config_path).read_text())
        enabled = config["SKYWARNPLUS"]["Enable"]
        if enabled is False:
            return {"status": "Disabled"}
        if enabled is not True:
            return {"status": "Unavailable"}
    except (OSError, KeyError, TypeError, yaml.YAMLError):
        return {"status": "Unavailable"}

    try:
        directory = config.get("DEV", {}).get("TmpDir", "/tmp/SkywarnPlus")
        state = json.loads((Path(directory) / "data.json").read_text())
        alerts = state["last_alerts"]
        if not isinstance(alerts, list):
            raise ValueError("Invalid alert list")
        now = datetime.now(timezone.utc)
        active = {}
        for title, records in alerts:
            if not isinstance(title, str) or not isinstance(records, list) or not records:
                raise ValueError("Invalid alert entry")
            for record in records:
                end = datetime.fromisoformat(record["end_time_utc"].replace("Z", "+00:00"))
                if end > now:
                    active[title] = max(active.get(title, 0), end.timestamp())
        return {
            "status": "Enabled",
            "alerts": [{"title": title, "until": until} for title, until in active.items()],
        }
    except (OSError, KeyError, TypeError, ValueError, AttributeError):
        return {"status": "Enabled", "alerts": None}


def write_snapshot(destination, snapshot):
    with tempfile.NamedTemporaryFile(mode="w", dir=destination.parent, delete=False) as stream:
        temporary = Path(stream.name)
    try:
        with temporary.open("w") as stream:
            json.dump(snapshot, stream)
        temporary.chmod(0o644)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def collect(config_path, destination):
    config = json.loads(config_path.read_text())["nodes"]
    with destination.with_suffix(".lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        try:
            snapshot = json.loads(destination.read_text())
            previous = snapshot["weatherCache"] if snapshot.get("provider") == "WeatherAPI" else {}
        except (OSError, ValueError, KeyError):
            previous = {}
        site_cache = {}
        alert_cache = {}
        nodes = {}
        for node, settings in config.items():
            zip_code = settings["zip"]
            if not re.fullmatch(r"[0-9]+", node) or not re.fullmatch(r"[0-9]{5}", zip_code):
                raise ValueError(f"Invalid node ID or ZIP for {node!r}")
            if zip_code not in site_cache:
                entry = previous.get(zip_code, {})
                minute = int(time.time()) // 60
                if minute - entry.get("attempted", -3) >= 3:
                    try:
                        entry = {"report": weather(zip_code), "observed": int(time.time())}
                    except (OSError, ValueError, KeyError, IndexError, TypeError):
                        print(f"WeatherAPI request failed for ZIP {zip_code}.", file=sys.stderr)
                    entry["attempted"] = minute
                site_cache[zip_code] = entry
            entry = site_cache[zip_code]
            detail = {"zip": zip_code}
            if time.time() - entry.get("observed", 0) < 1800:
                detail.update(entry["report"], weatherUntil=entry["observed"] + 1800)
            if path := settings.get("skywarn_config"):
                if path not in alert_cache:
                    alert_cache[path] = skywarn(path)
                detail["skywarn"] = alert_cache[path]
            nodes[node] = detail
        write_snapshot(destination, {
            "provider": "WeatherAPI", "generated": int(time.time()), "nodes": nodes, "weatherCache": site_cache,
        })


if __name__ == "__main__":
    collect(Path(sys.argv[1]), Path(sys.argv[2]))
