$ErrorActionPreference = 'Stop'

$path = Join-Path (Split-Path -Parent $PSScriptRoot) 'TVBox多仓线路汇总.json'
$text = Get-Content -LiteralPath $path -Raw -Encoding UTF8

# JSON supports \uXXXX, but not Python-style \UXXXXXXXX escapes.
$text = [regex]::Replace($text, '\\U([0-9a-fA-F]{8})', {
    param($match)
    [char]::ConvertFromUtf32([Convert]::ToInt32($match.Groups[1].Value, 16))
})

# Repair accidental physical newlines embedded in quoted values.
$builder = [Text.StringBuilder]::new()
$quoted = $false
$escaped = $false
foreach ($char in $text.ToCharArray()) {
    if ($quoted -and ($char -eq "`r" -or $char -eq "`n")) { continue }
    [void]$builder.Append($char)
    if ($escaped) { $escaped = $false; continue }
    if ($char -eq '\') { $escaped = $true; continue }
    if ($char -eq '"') { $quoted = -not $quoted }
}

$json = $builder.ToString() | ConvertFrom-Json
$json | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $path -Encoding UTF8
Write-Output "Repaired $($json.urls.Count) entries: $path"

