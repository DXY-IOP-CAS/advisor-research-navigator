# H1: PostToolUse -- verify '## verification source' section exists
# Source: D07 K5 + synthesis-design-v0.1 §四 anchor
# Trigger: Write/Edit success
# Check: if file has external ref keywords but lacks '## verification source' section, warn
# Block: no (warn stderr only -- formal standard check, not a substitute for human review)

# Safe stdin read with 5s timeout
$stdinJson = $null
try {
    $task = [Console]::In.ReadToEndAsync()
    if ($task.Wait(5000)) {
        $stdinJson = $task.Result
    } else {
        exit 0
    }
} catch {
    exit 0
}

if ([string]::IsNullOrWhiteSpace($stdinJson)) {
    exit 0
}

$evt = $null
try {
    $evt = $stdinJson | ConvertFrom-Json -ErrorAction Stop
} catch {
    exit 0
}

# Defensive: tool_input may be nested or missing depending on event
$filePath = $null
if ($evt.tool_input -and $evt.tool_input.PSObject.Properties['file_path']) {
    $filePath = $evt.tool_input.file_path
}
if ([string]::IsNullOrWhiteSpace($filePath) -or -not (Test-Path -LiteralPath $filePath)) {
    exit 0
}

$content = Get-Content -LiteralPath $filePath -Raw -ErrorAction SilentlyContinue
if ([string]::IsNullOrWhiteSpace($content)) {
    exit 0
}

# External ref detection
$hasExternalRef = $content -match 'http[s]?://|arxiv\.org|doi\.org|references|bibliography|cited from'
$hasVerifySection = $content -match '##\s*verification source|##\s*验证来源'

if ($hasExternalRef -and -not $hasVerifySection) {
    [Console]::Error.WriteLine('WARN H1: file has external refs but no verification source section. CLAUDE.md R1 requires URL per external info.')
}

exit 0
