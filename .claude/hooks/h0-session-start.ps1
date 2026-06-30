# H0: SessionStart -- inject read-chuzhong reminder
# Source: CLAUDE.md section 0 + chuzhong/02 + Why Prompt Guardrails Fail
# Behavior: emit JSON to stdout; Claude Code parses additionalContext into session.
# Note: SessionStart does NOT pass tool_input via stdin.

$ctx = '[pilot-seed] Read these 4 files before your first reply: chuzhong/01_why_seed.md, chuzhong/02_seed_essence.md, chuzhong/03_usage_principles.md, chuzhong/04_clone_and_grow.md. Skip = violate CLAUDE.md R5/R6/R8.'

$obj = @{
    hookSpecificOutput = @{
        hookEventName     = 'SessionStart'
        additionalContext = $ctx
    }
}

$json = $obj | ConvertTo-Json -Compress
[Console]::Out.WriteLine($json)
exit 0
