# H3: PreToolUse -- stage gate (warn, do not block)
# Source: SKILL.md section 2 + D07 K5
# Trigger: Write tool before execution
# Check: writing 'output/stageN_xxx.md' (N=2/3/4) -- check stage N-1 product exists
# Block: no (warn + ask user; CLAUDE.md R3 lets user decide whether to roll back)

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

# Match pattern: output/stageN_xxx.md where N=2/3/4 (stage 1 is entry, no gate)
if ($filePath -match '(?i)output[/\\]stage([2-4])_') {
    $stageNum = [int]$matches[1]
    $prevStage = $stageNum - 1

    $projectDir = $env:CLAUDE_PROJECT_DIR
    if ([string]::IsNullOrWhiteSpace($projectDir)) {
        $projectDir = (Get-Location).Path
    }
    $outputDir = Join-Path $projectDir 'output'

    if (-not (Test-Path -LiteralPath $outputDir)) {
        # output/ doesn't exist yet -- no previous stage product possible, but still warn
        [Console]::Error.WriteLine("WARN H3: writing stage${stageNum} product but output/ directory not yet created. SKILL.md stage 1 product missing.")
        exit 0
    }

    $pattern = "stage${prevStage}_*.md"
    $prevFiles = Get-ChildItem -Path $outputDir -Filter $pattern -ErrorAction SilentlyContinue

    if (-not $prevFiles -or $prevFiles.Count -eq 0) {
        $leaf = Split-Path -Leaf $filePath
        [Console]::Error.WriteLine("WARN H3: writing stage${stageNum} ($leaf), but stage${prevStage} product (output/stage${prevStage}_*.md) missing. SKILL.md section 2 requires user confirmation before stage switch.")
    }
}

exit 0
