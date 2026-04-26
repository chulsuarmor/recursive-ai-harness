# Architecture — Recursive AI Harness

## Full System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Request                            │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Worker Agent (spawn)                         │
│  Task: create one deliverable (code change / output / report)   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Squirrel Cheek Hook                            │
│  PostToolUse check — before first Edit/Write:                   │
│    [1] CLAUDE.md (compressed index < 30 lines)                  │
│    [2] mistakes.md last 10 entries                              │
│    [3] FALSE_PASS_REGISTRY.md (18 FP patterns)                  │
│    [4] skills/INDEX.md                                          │
│    [5] skills/{domain}.md                                       │
│                                                                 │
│  SubagentStop check — at exit: all 5 boxes checked?            │
│  Missing read → BLOCK (output invalidated)                      │
└──────────────────────┬──────────────────────────────────────────┘
                       │  (all reads confirmed)
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│             3 Parallel Audit Teams                              │
│                                                                 │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│   │   Theory    │  │     GUI     │  │    Integration      │   │
│   │ correctness │  │  visual     │  │  cross-module       │   │
│   │ accuracy    │  │  output     │  │  consistency        │   │
│   │             │  │  screenshot │  │                     │   │
│   └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘   │
│          │                │                     │              │
└──────────┼────────────────┼─────────────────────┼──────────────┘
           │ PASS           │ PASS                │ PASS
           └────────────────┼─────────────────────┘
                            │ (all 3 PASS)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CT Second Review                               │
│  Count cumulative passes per Worker ID                          │
│                                                                 │
│  reject_count < 5?                                              │
│       │ YES                      │ NO (>= 5 independent PASS)  │
│       ▼                          ▼                              │
│  Spawn 2 extra          Deliverable APPROVED                    │
│  auditors               → advance to Model Garden              │
│  re-enter loop                                                  │
└─────────────────────────────────────────────────────────────────┘
                            │ (5 PASS reached)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Model Garden                                │
│                                                                 │
│  scan_audit_patterns(mistakes.md)                               │
│    → collect entries by M-number                                │
│    → classify by keyword buckets                                │
│    → aggregate count + domains per pattern                      │
│                                                                 │
│  for each pattern p:                                            │
│    if p.count >= 30 and p.domains >= 5:                         │
│       propose_rule_promotion(p, target="CLAUDE.md")             │
│    elif p.count >= 10:                                          │
│       add to watch list                                         │
│                                                                 │
│  Write proposals to model_garden_proposals.md                   │
│  (human reviews and approves/rejects each proposal)             │
└──────────────────────┬──────────────────────────────────────────┘
                       │ (promoted rules written to CLAUDE.md)
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│             Recursive Session Handoff                           │
│                                                                 │
│  Write NEXT_SESSION_PROMPT.md (< 5 KB):                         │
│                                                                 │
│   Section 1: Cumulative Summary (last N M-numbers)             │
│   Section 2: User Direct Quotes (verbatim)                      │
│   Section 3: In-Progress Items (file + state)                   │
│   Section 4: Pending Decisions (D-01, D-02 ...)                 │
│   Section 5: False-PASS Patterns (FP registry delta)           │
│   Section 6: Citations                                          │
│   Section 7: Termination Conditions                             │
│   Section 8: Next 5 Actions                                     │
│                                                                 │
│  Update mistakes.md header:                                     │
│    LAST_M_NUMBER: M{N}                                          │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Next Cycle (t+1)                              │
│                                                                 │
│  New Worker session starts fresh.                               │
│  First action: read NEXT_SESSION_PROMPT.md                      │
│  Resume at Section 8, Action 1.                                 │
│  No re-explanation needed.                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Failure Mode Map

Each failure mode (left column) is addressed by one or more systems:

```
Failure Mode                 │ System(s) That Address It
─────────────────────────────┼──────────────────────────────────────
Session amnesia              │ Recursive Session Handoff
  Agent forgets rules from   │   — NEXT_SESSION_PROMPT.md injected
  previous sessions          │     at every spawn
                             │
Rubber-stamp audits          │ Per-Deliverable 5-Reject Gate
  Single auditor approves    │   — 5 independent PASS required
  low-quality output         │   — extra auditors auto-spawned
                             │
Instruction bloat            │ Model Garden
  Long rule file ignored     │   — short promoted rules only
  entirely                   │   — CLAUDE.md kept < 30 lines
                             │
Invisible failure            │ Squirrel Cheek (M rule enforcement)
  Silent None returns,       │   — mandatory read of silent failure
  blank screens, no logs     │     prevention rule before every write
```

---

## State Files

| File | Owner | Updated By | Read By |
|---|---|---|---|
| `CLAUDE.md` | Harness | Model Garden (proposals) | All agents |
| `mistakes.md` | Project | Every Worker (at end) | All agents (Squirrel Cheek) |
| `NEXT_SESSION_PROMPT.md` | Project | Handoff step | Next session only |
| `FALSE_PASS_REGISTRY.md` | Audit teams | After each false PASS | All agents (Squirrel Cheek) |
| `model_garden_proposals.md` | Model Garden | Garden scan | Human reviewer |
| `counts/{worker_id}.count` | CT review | CT second review step | CT second review step |

---

## Cycle Timing (Approximate)

```
Spawn Worker        →  0:00
Squirrel Cheek check →  0:01
3 Parallel auditors →  0:03 — 0:06
CT second review    →  0:06 — 0:07
Model Garden scan   →  0:07 — 0:08
Handoff update      →  0:08 — 0:09
Next cycle ready    →  0:09
```

Total per cycle: approximately 8-10 minutes for a single deliverable.
Varies with task complexity and number of extra auditors spawned.
