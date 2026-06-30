# H4: PostToolUse -- SKILL.md line count warning
# Source: CLAUDE.md R5 + handoff-doc section 8 (4-guide consensus: ideal < 100, target < 200)
# Trigger: Write/Edit SKILL.md success
# Check: SKILL.md line count > 200 -- warn
# Block: no (warn-first per 4-guide consensus)

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

# Only check SKILL.md
if ($filePath -notmatch '(?i)SKILL\.md$') {
    exit 0
}

if (-not (Test-Path -LiteralPath $filePath)) {
    exit 0
}

$lineCount = (Get-Content -LiteralPath $filePath).Count

if ($lineCount -gt 200) {
    [Console]::Error.WriteLine("WARN H4: SKILL.md has $lineCount lines (limit 200). CLAUDE.md R5 -- text guardrails are noise. Suggest moving detail to stageN_*/instructions.md.")
}

exit 0
