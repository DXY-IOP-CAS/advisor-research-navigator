# H0: SessionStart -- inject project context reminder
# Source: CLAUDE.md section 0
# Behavior: emit JSON to stdout; Claude Code parses additionalContext into session.
# Note: SessionStart does NOT pass tool_input via stdin.

$ctx = '[pilot-seed] Read 计划/计划书.md (v3.0) and 计划/上下文交接.md (v2.0) before first reply.'

$obj = @{
    hookSpecificOutput = @{
        hookEventName     = 'SessionStart'
        additionalContext = $ctx
    }
}

$json = $obj | ConvertTo-Json -Compress
[Console]::Out.WriteLine($json)
exit 0
