# H3: PreToolUse -- stage gate (warn, do not block)
# Source: 计划书.md 2.1 + user-review-gate design
# Trigger: Write tool before execution
# Check: writing '00_身份验证卡.md' without phase-0 prereqs; or '01_基础画像.md' without phase-0 card
# Block: no (warn only; user decides)
#
# Note: Updated 2026-07-01 for new file paths (项目/导师/<姓名>/00_*.md instead of output/stageN_*.md)

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

$filePath = $null
if ($evt.tool_input -and $evt.tool_input.PSObject.Properties['file_path']) {
    $filePath = $evt.tool_input.file_path
}
if ([string]::IsNullOrWhiteSpace($filePath)) {
    exit 0
}

$leaf = Split-Path -Leaf $filePath

# Check 1: writing 01_基础画像.md without 00_身份验证卡.md in same directory
if ($leaf -eq '01_基础画像.md') {
    $parentDir = Split-Path -Parent $filePath
    $cardPath = Join-Path $parentDir '00_身份验证卡.md'
    if (-not (Test-Path -LiteralPath $cardPath)) {
        [Console]::Error.WriteLine("WARN H3: writing 01_基础画像.md but 00_身份验证卡.md not found in same directory. Phase 0 (identity verification) must complete first per 计划书.md 2.2.")
    }
    exit 0
}

# Check 2: writing 02_领域脉络.md without 01_基础画像.md in same directory
if ($leaf -match '^02_') {
    $parentDir = Split-Path -Parent $filePath
    $profilePath = Join-Path $parentDir '01_基础画像.md'
    if (-not (Test-Path -LiteralPath $profilePath)) {
        [Console]::Error.WriteLine("WARN H3: writing $leaf but 01_基础画像.md not found. Phase 1 must complete first.")
    }
    exit 0
}

exit 0
