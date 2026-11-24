#!/bin/sh
set -eu
cd "$(dirname "$0")"
dashboard=/var/www/html/supermon
support=/usr/local/lib/supermon-node-weather
settings=/etc/supermon-node-weather.json
state=/var/lib/supermon-node-weather
key=/etc/supermon-node-weather.key

if [ "$(id -u)" != 0 ]; then
    echo "Run the installer with sudo." >&2
    exit 1
fi
id asterisk >/dev/null
command -v php >/dev/null
if ! python3 -c 'import yaml' 2>/dev/null; then
    apt-get update
    apt-get install -y python3-yaml
fi
if ! systemctl is-active --quiet cron; then
    echo "Start the cron service before installing." >&2
    exit 1
fi
python3 patch.py "$dashboard/link.php" --check
php -l node-weather.php
staging=$(mktemp -d)
trap 'rm -f "$staging/key" "$staging/settings"; rmdir "$staging"' EXIT
umask 077
python3 setup.py "$settings" "$key" "$staging" "$dashboard" "$@"
group=$(id -gn asterisk)
if [ -f "$staging/key" ]; then
    install -m 0640 -o root -g "$group" "$staging/key" "$key"
fi
if [ -f "$staging/settings" ]; then
    install -m 0644 "$staging/settings" "$settings"
fi
install -d -m 0755 "$support"
install -d -m 0755 -o asterisk -g "$(id -gn asterisk)" "$state"
install -m 0644 collect.py patch.py "$support/"
install -m 0755 uninstall.sh /usr/local/sbin/supermon-node-weather-uninstall
install -m 0755 set-width.py /usr/local/sbin/supermon-node-weather-width
install -m 0644 node-weather.js node-weather.php "$dashboard/"
python3 patch.py "$dashboard/link.php"
install -m 0644 supermon-node-weather.cron /etc/cron.d/supermon-node-weather
if ! runuser -u asterisk -- python3 "$support/collect.py" "$settings" "$state/snapshot.json"; then
    echo "Initial snapshot failed. Check $settings and collector output." >&2
    exit 1
fi
echo "Installed. Reload the Supermon node page."
