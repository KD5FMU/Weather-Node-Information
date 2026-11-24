<?php
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

$settings = @file_get_contents('/etc/supermon-node-weather.json');
$config = $settings === false ? null : json_decode($settings, true);
$width = $config['table_width'] ?? null;
if (is_int($width) && $width >= 640 && $width <= 2000) {
    header('X-Supermon-Table-Width: ' . $width);
}

$payload = @file_get_contents('/var/lib/supermon-node-weather/snapshot.json', false, null, 0, 1048576);
$data = $payload === false ? null : json_decode($payload, true);
if (!isset($data['generated'], $data['nodes']) || time() - $data['generated'] > 300) {
    http_response_code(503);
    echo '{}';
    exit;
}
echo json_encode((object) $data['nodes'], JSON_INVALID_UTF8_SUBSTITUTE);
