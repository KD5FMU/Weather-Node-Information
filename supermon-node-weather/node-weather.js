(function () {
    "use strict";

    let reports = {};
    let lastSuccess = 0;
    let widthStyle;

    function setTableWidth(width) {
        if (!Number.isInteger(width) || width < 640 || width > 2000) {
            widthStyle?.remove();
            widthStyle = undefined;
            document.querySelectorAll(".supermon-fixed-columns").forEach(columns => columns.remove());
            return;
        }
        if (!widthStyle) {
            widthStyle = document.createElement("style");
            document.head.appendChild(widthStyle);
        }
        document.querySelectorAll('table.gridtable[id^="table_"]').forEach(table => {
            if (table.querySelector("colgroup")) return;
            const columns = document.createElement("colgroup");
            columns.className = "supermon-fixed-columns";
            for (let index = 0; index < 7; index++) {
                const column = document.createElement("col");
                columns.appendChild(column);
            }
            table.prepend(columns);
        });
        widthStyle.textContent = `
            table.gridtable[id^="table_"] {
                table-layout: fixed;
                width: ${width}px;
                min-width: ${width}px;
                max-width: ${width}px;
            }
            table.gridtable[id^="table_"] > colgroup > col:nth-child(1) { width: 8%; }
            table.gridtable[id^="table_"] > colgroup > col:nth-child(2) { width: 40%; }
            table.gridtable[id^="table_"] > colgroup > col:nth-child(3) { width: 10%; }
            table.gridtable[id^="table_"] > colgroup > col:nth-child(4) { width: 10%; }
            table.gridtable[id^="table_"] > colgroup > col:nth-child(5) { width: 10%; }
            table.gridtable[id^="table_"] > colgroup > col:nth-child(6) { width: 12%; }
            table.gridtable[id^="table_"] > colgroup > col:nth-child(7) { width: 10%; }
            table.gridtable[id^="table_"] th,
            table.gridtable[id^="table_"] td {
                white-space: normal;
                overflow-wrap: anywhere;
            }`;
    }

    function line(parent, message, color, fontSize) {
        const item = document.createElement("div");
        item.textContent = message;
        if (color) item.style.color = color;
        if (fontSize) item.style.fontSize = fontSize;
        parent.appendChild(item);
    }

    function render(node, body) {
        const cell = body?.rows[0]?.cells[1];
        if (!cell) return;

        let box = cell.querySelector(".supermon-node-weather");
        let status = cell.querySelector(".supermon-skywarn-status");
        const report = reports[node];
        if (!report) {
            box?.remove();
            status?.remove();
            return;
        }

        if (!box) {
            box = document.createElement("div");
            box.className = "supermon-node-weather";
            box.style.fontSize = "0.9em";
            cell.appendChild(box);
        }
        if (report.skywarn && !status) {
            status = document.createElement("div");
            status.className = "supermon-skywarn-status";
            cell.prepend(status);
        }
        if (!report.skywarn) status?.remove();
        else status.style.fontSize = "";
        box.replaceChildren();
        const now = Date.now() / 1000;
        if (now - lastSuccess > 120) {
            if (report.skywarn) {
                status.textContent = "SkywarnPlus Unavailable";
                status.style.color = "";
            }
            line(box, "Weather unavailable");
            return;
        }

        line(box, report.weatherUntil > now
            ? report.location + " · " + report.conditions
            : "Weather unavailable for " + report.zip);

        if (report.skywarn) {
            const skywarn = report.skywarn;
            status.textContent = "SkywarnPlus " + skywarn.status;
            const colors = { Enabled: "#006400", Disabled: "#a00000" };
            status.style.color = colors[skywarn.status] || "";
            if (skywarn.status === "Enabled") {
                if (!Array.isArray(skywarn.alerts)) {
                    line(box, "Alert status unavailable");
                } else {
                    const alerts = skywarn.alerts.filter(alert => alert.until > now);
                    if (alerts.length) {
                        alerts.forEach(alert => {
                            const title = alert.title;
                            let color = "firebrick";
                            if (/\bwatch\b/i.test(title)) color = "#a00000";
                            if (/\bwarning\b/i.test(title)) color = "#9a4100";
                            const fontSize = /\b(?:watch|warning)\b/i.test(title)
                                ? "calc(1em + 2pt)" : undefined;
                            if (fontSize) status.style.fontSize = "calc(0.9em + 2pt)";
                            line(box, title, color, fontSize);
                        });
                    } else {
                        line(box, "No active alerts in SkywarnPlus state");
                    }
                }
            }
        }
    }

    function redraw() {
        document.querySelectorAll('table[id^="table_"]').forEach(table => {
            render(table.id.slice(6), table.tBodies[0]);
        });
    }

    async function refresh() {
        try {
            const response = await fetch("node-weather.php", {
                cache: "no-store",
                signal: AbortSignal.timeout(8000)
            });
            setTableWidth(Number(response.headers.get("X-Supermon-Table-Width")));
            if (response.ok) {
                reports = await response.json();
                const testNode = new URLSearchParams(location.search).get("testAlerts");
                if (/^[0-9]+$/.test(testNode) && reports[testNode]?.skywarn?.status === "Enabled") {
                    const until = Date.now() / 1000 + 120;
                    reports[testNode].skywarn.alerts = [
                        { title: "TEST — Tornado Watch", until },
                        { title: "TEST — Severe Thunderstorm Warning", until }
                    ];
                }
                lastSuccess = Date.now() / 1000;
            } else {
                lastSuccess = 0;
            }
        } catch {
            // Let a transient network failure use the previous snapshot briefly.
        }
        redraw();
        setTimeout(refresh, 60000);
    }

    window.supermonNodeWeather = render;
    document.addEventListener("DOMContentLoaded", refresh);
}());
