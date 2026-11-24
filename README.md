# Supermon Node Weather

WeatherAPI.com conditions and optional SkywarnPlus status and alerts in the **Node Information** table for each configured node in Supermon 8 on Debian ASL3.

## Requirements

- AllStarLink 3 with Supermon 8 installed at `/var/www/html/supermon`
- PHP CLI, an active cron service, and `sudo` access on the ASL3 node
- A WeatherAPI.com API key and a five-digit U.S. ZIP code for each node you configure

The installer installs `python3-yaml` if needed. SkywarnPlus is optional. When it is installed locally, the add-on can show its status and active alerts. Current conditions are fetched every three minutes per ZIP, and the add-on checks SkywarnPlus status once a minute.

## Install

Sign in to GitHub if prompted, open the installer ZIP, and click **Download raw file**. Copy the ZIP to your ASL3 node if you downloaded it on another computer. [Installer ZIP](https://github.com/KD5FMU/Weather-Node-Information/blob/main/downloads/supermon-node-weather-1.0.0.zip) · [SHA-256 checksum](https://github.com/KD5FMU/Weather-Node-Information/blob/main/downloads/supermon-node-weather-1.0.0.zip.sha256)

On the ASL3 node, open a terminal in the directory containing the ZIP and run:

```sh
unzip supermon-node-weather-1.0.0.zip -d supermon-weather-1.0.0 &&
cd supermon-weather-1.0.0/supermon-node-weather &&
sudo sh install.sh
```

1. Choose one node by ID or all local Supermon nodes. The all-local option selects numeric node entries in `allmon.ini` that use a loopback address.
2. Enter a five-digit ZIP for each selected node. If a standard local SkywarnPlus installation is detected, choose whether to show its status.
3. Choose automatic sizing or a fixed width shared by all node tables. With fixed width, long text wraps and rows grow vertically.
4. Paste your WeatherAPI.com key at the hidden prompt and press Return. One key covers all configured nodes.
5. Refresh Supermon.

The installer reuses saved settings and the API key on upgrades. To revisit node and ZIP choices, run `sudo sh install.sh --configure` from the extracted installer folder. If a Supermon update replaces `link.php`, rerun `sudo sh install.sh` to restore the add-on.

## Change the table width

On the ASL3 node, run:

```sh
sudo supermon-node-weather-width
```

The command shows your current setting. Enter a width from **640 to 2000 pixels**, such as `900`. Enter `auto` to restore automatic sizing, or press Return on a blank line to cancel. Refresh Supermon after saving. Your node choices, ZIP codes, and API key are preserved.

## Uninstall

On the ASL3 node, run:

```sh
sudo supermon-node-weather-uninstall
```

This removes the add-on’s changes from `link.php`, its dashboard files, and its scheduled collector. It keeps your settings and API key for a reinstall. To remove those as well, use the following command **in place of** the standard uninstall command:

```sh
sudo supermon-node-weather-uninstall --purge
```

Refresh Supermon after removal. Backups are stored in `/var/backups/supermon-node-weather/`.

## License

The Supermon Node Weather add-on is licensed under the MIT License. Supermon and SkywarnPlus are separate projects distributed under their own licenses. [MIT License](LICENSE)
