# Squirrel Cheek — Mandatory Reading Enforcement

## Overview

The Squirrel Cheek protocol enforces that every spawned Worker agent reads
a specific set of files before taking any write action. Named for the
compulsive pre-action collection behavior: you must gather before you act.

Without enforcement, agents skip long instruction files. With enforcement,
the most recent failure patterns are always in context.

---

## The Five Mandatory Reads

Every Worker prompt must include (or reference) these five files:

```
1. CLAUDE.md              — compressed rule index (< 30 lines)
2. mistakes.md            — last 10 entries only
3. FALSE_PASS_REGISTRY.md — patterns where audit incorrectly returned PASS
4. docs/ai/skills/INDEX.md — skill file directory
5. docs/ai/skills/{domain}.md — domain-specific skill for current task
```

The domain is determined by the task type (e.g., `rendering` for visual
output tasks, `session_handoff` for state-preservation tasks).

---

## Worker Spawn Template (pseudocode)

```python
def spawn_worker(task: dict) -> str:
    """Build a Worker prompt with mandatory reads pre-injected."""

    domain = detect_domain(task)  # e.g. "rendering", "parsing", "audit"

    mandatory_reads = [
        read_file("CLAUDE.md"),
        read_last_n_lines("docs/ai/mistakes.md", n=40),   # ~10 entries
        read_file("docs/ai/FALSE_PASS_REGISTRY.md"),
        read_file("docs/ai/skills/INDEX.md"),
        read_file(f"docs/ai/skills/{domain}.md"),
    ]

    checklist = "\n".join([
        "## SQUIRREL BALL CHECKLIST",
        "You must confirm each item before your first Edit/Write:",
        "[ ] Read CLAUDE.md — note the rule code letters (A-Z)",
        "[ ] Read mistakes.md last 10 — note any entry matching your task",
        "[ ] Read FALSE_PASS_REGISTRY.md — note FP codes for your domain",
        "[ ] Read skills/INDEX.md — confirm domain file path",
        f"[ ] Read skills/{domain}.md — note patterns for this task type",
        "",
        "Failure to check all boxes before first write = output invalidated.",
    ])

    prompt = "\n\n".join([
        checklist,
        *mandatory_reads,
        format_task(task),
    ])

    return prompt
```

---

## Hook Implementation (PostToolUse)

The `PostToolUse` hook verifies reads occurred before any write:

```python
# .claude/hooks/squirrel_cheek_check.py
# Called by PostToolUse hook after every tool invocation.

import json
import sys

REQUIRED_READS = [
    "CLAUDE.md",
    "mistakes.md",
    "FALSE_PASS_REGISTRY.md",
    "skills/INDEX.md",
]

def check(hook_input: dict) -> dict:
    tool_name = hook_input.get("tool_name", "")
    if tool_name not in ("Edit", "Write"):
        return {"action": "continue"}

    # Read the current session's tool call history
    tool_history = hook_input.get("tool_history", [])
    read_files = [
        t.get("params", {}).get("file_path", "")
        for t in tool_history
        if t.get("tool_name") == "Read"
    ]

    missing = []
    for required in REQUIRED_READS:
        if not any(required in f for f in read_files):
            missing.append(required)

    if missing:
        return {
            "action": "block",
            "reason": f"Squirrel Cheek FAIL: mandatory reads missing: {missing}. "
                      f"Read these files before any Edit/Write.",
        }

    return {"action": "continue"}
```

---

## SubagentStop Hook

At agent exit, verify the checklist was confirmed:

```python
# .claude/hooks/squirrel_cheek_exit_check.py
# Called by SubagentStop hook when a sub-agent finishes.

def check(hook_input: dict) -> dict:
    output_text = hook_input.get("agent_output", "")

    # Require explicit checklist confirmation in the agent's output
    if "SQUIRREL BALL CHECKLIST" not in output_text:
        return {
            "action": "warn",
            "reason": "Agent exited without confirming Squirrel Cheek checklist. "
                      "Output may be invalid.",
        }

    unchecked = output_text.count("[ ]")   # unchecked boxes remaining
    if unchecked > 0:
        return {
            "action": "warn",
            "reason": f"Squirrel Cheek: {unchecked} checklist items not confirmed.",
        }

    return {"action": "continue"}
```

---

## Why This Works

The key insight is that agents are not lazy — they are stateless. Every new
agent spawn starts with no knowledge of previous failures. The Squirrel Cheek
protocol ensures the most recent failure patterns are always injected into
context before the agent can act. The hooks ensure the injection actually
happened rather than being skipped.

The false-positive registry is the most important of the five reads. Without
it, auditors have no memory of previously-approved-but-wrong outputs, and
the same false approval pattern repeats indefinitely.

---

## Adapting to Your Project

Replace the five mandatory reads with files relevant to your domain.
The critical properties are:

- **Short enough to read quickly**: CLAUDE.md should be < 30 lines.
  Use a compressed index with references to detailed files.
- **Recently updated**: mistakes.md must be updated at the end of every
  session. Stale mistakes files defeat the purpose.
- **Domain-specific**: The fifth read should vary by task type.
  A rendering task reads the rendering skill file;
  an API integration task reads the integration skill file.
