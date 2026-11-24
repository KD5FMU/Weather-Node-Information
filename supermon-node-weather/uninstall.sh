#!/bin/sh
set -eu
mode=${1:-}
case "$mode" in
    ""|--purge) ;;
    *) echo "Usage: supermon-node-weather-uninstall [--purge]" >&2; exit 2 ;;
esac
[ "$(id -u)" = 0 ] || { echo "Run with sudo." >&2; exit 1; }
dashboard=/var/www/html/supermon
support=/usr/local/lib/supermon-node-weather
state=/var/lib/supermon-node-weather

if [ -f "$dashboard/link.php" ]; then
    python3 "$support/patch.py" "$dashboard/link.php" --remove
fi
rm -f /etc/cron.d/supermon-node-weather
rm -f "$dashboard/node-weather.js" "$dashboard/node-weather.php"
rm -f "$support/collect.py" "$support/patch.py"
rm -f "$state/snapshot.json" "$state/snapshot.lock"
rmdir "$support" "$state" 2>/dev/null || true
if [ "$mode" = --purge ]; then
    rm -f /etc/supermon-node-weather.json /etc/supermon-node-weather.key
fi
rm -f /usr/local/sbin/supermon-node-weather-uninstall /usr/local/sbin/supermon-node-weather-width
echo "Supermon Node Weather removed. Reload the dashboard."
