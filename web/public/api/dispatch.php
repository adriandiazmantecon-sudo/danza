<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *'); 
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Configuración de Seguridad
$ADMIN_PASSWORD = "Pueblo30dan&&";
$GITHUB_TOKEN = "TU_TOKEN_DE_GITHUB_AQUI";
$GITHUB_REPO = "adriandiazmantecon-sudo/danza";

// Manejo de preflight (CORS)
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

// Solo aceptamos POST
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(["status" => "error", "message" => "Método no permitido"]);
    exit;
}

// Leer datos del cuerpo de la petición (JSON)
$input = json_decode(file_get_contents('php://input'), true);
$received_password = $input['password'] ?? '';
$venues = $input['venues'] ?? '';

// 1. Validar Contraseña
if ($received_password !== $ADMIN_PASSWORD) {
    http_response_code(401);
    echo json_encode(["status" => "error", "message" => "Contraseña incorrecta"]);
    exit;
}

// 2. Preparar llamada a GitHub
$url = "https://api.github.com/repos/$GITHUB_REPO/dispatches";
$payload = json_encode([
    "event_type" => "trigger-scrape",
    "client_payload" => [
        "venues" => $venues
    ]
]);

$ch = curl_init($url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    "Authorization: Bearer $GITHUB_TOKEN",
    "Accept: application/vnd.github+json",
    "Content-Type: application/json",
    "User-Agent: Madrid-Dance-Backend"
]);

$result = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

// 3. Responder al frontend
if ($http_code >= 200 && $http_code < 300) {
    echo json_encode(["status" => "success", "message" => "Acción lanzada con éxito en GitHub"]);
} else {
    http_response_code($http_code);
    echo json_encode([
        "status" => "error", 
        "message" => "Error al conectar con GitHub",
        "github_response" => json_decode($result, true)
    ]);
}
?>
