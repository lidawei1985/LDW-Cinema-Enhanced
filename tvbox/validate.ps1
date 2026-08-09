param(
    [string]$ConfigPath = (Join-Path $PSScriptRoot 'config.json')
)

$ErrorActionPreference = 'Stop'
$raw = Get-Content -LiteralPath $ConfigPath -Raw
$config = $raw | ConvertFrom-Json
$errors = [System.Collections.Generic.List[string]]::new()

foreach ($required in 'sites', 'lives', 'parses') {
    if ($null -eq $config.$required) {
        $errors.Add("Missing required array: $required")
    }
}

$urlPattern = 'https?://[^\s"''<>]+'
foreach ($match in [regex]::Matches($raw, $urlPattern)) {
    $url = $match.Value
    if (-not $url.StartsWith('https://', [StringComparison]::OrdinalIgnoreCase)) {
        $errors.Add("Non-HTTPS URL: $url")
    }
    if ($url -match '(?i)\.jar(?:\?|$)') {
        $errors.Add("Remote JAR is not allowed: $url")
    }
    if ($url -match '(?i)(?:/|[?&])(jx|jiexi|vip|parse)(?:/|=|\?|&|$)') {
        $errors.Add("Possible bypass parser URL: $url")
    }
}

if ($errors.Count) {
    $errors | Sort-Object -Unique | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Host "TVBox config is valid: $ConfigPath"
