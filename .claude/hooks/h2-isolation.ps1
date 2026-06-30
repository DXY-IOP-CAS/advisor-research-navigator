# H2: PreToolUse -- isolation boundary (the ONLY real block)
# Source: CLAUDE.md R4 + handoff-doc section 6
# Trigger: Write/Edit before execution
# Check: write path with '..' (parent escape) -- exit 2 block
# Block: yes (CLAUDE.md R4's only hard physical block)

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

# Check 1: '..' parent escape (works for both relative and absolute paths)
if ($filePath -match '\.\.') {
    [Console]::Error.WriteLine("BLOCK H2: path '$filePath' contains '..' parent escape. CLAUDE.md R4 requires all writes inside pilot-test/ subtree.")
    exit 2
}

# Check 2: absolute path must be under CLAUDE_PROJECT_DIR
$projectDir = $env:CLAUDE_PROJECT_DIR
if ($filePath -match '^[a-zA-Z]:\\' -or $filePath -match '^/') {
    if (-not [string]::IsNullOrWhiteSpace($projectDir)) {
        $normalized = [System.IO.Path]::GetFullPath($filePath)
        $normalizedProject = [System.IO.Path]::GetFullPath($projectDir)
        if (-not $normalized.StartsWith($normalizedProject, [System.StringComparison]::OrdinalIgnoreCase)) {
            [Console]::Error.WriteLine("BLOCK H2: path '$filePath' not under project root '$normalizedProject'. CLAUDE.md R4 violation.")
            exit 2
        }
    }
}

exit 0
