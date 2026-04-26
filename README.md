# Recursive AI Harness — Self-Evolving Agent Framework

> A meta-system for Claude Code (and similar LLM agent frameworks) that turns mistakes into rules, enforces mandatory reading, and runs infinite verification cycles.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Built%20with-Claude%20Code-blue)](https://claude.ai/claude-code)

---

## The Problem

LLM agents forget across sessions. They repeat mistakes. They ignore long instruction files. They claim PASS when nothing was actually verified.

After 500+ iterations of building a desktop science application with Claude Code, four interlocking failure modes appeared again and again:

1. **Session amnesia**: A rule fixed in session 12 is broken again in session 30 because the agent starts fresh.
2. **Rubber-stamp audits**: A single cooperative auditor approves low-quality work. The next user interaction reveals the bug.
3. **Instruction bloat**: The more rules you add to a prompt file, the less any individual rule is followed. Eventually the whole file becomes wallpaper.
4. **Invisible failure**: An agent silently returns `None`, logs nothing, and the user sees a blank screen three steps later with no traceable cause.

These are not bugs in any one session. They are structural properties of stateless LLM agents operating on large codebases. Patching them one by one does not work. You need a harness.

---

## Four Interlocking Systems

After 500+ tracked changes across 50+ cycles, four patterns emerged that collectively address the structural failure modes above.

### 1. Model Garden — Self-Evolving Rules

The core idea: mistakes should cost less over time, not stay constant.

Each Worker agent logs failures to a shared `mistakes.md` file using a monotonic counter (M001, M002, ... M500+). A scanner reads all entries and classifies recurring patterns by domain and frequency. When a pattern accumulates enough occurrences across enough distinct domains, it auto-promotes to a top-level rule in the harness configuration.

```python
# Simplified: model_garden.py core logic
_PROMOTION_MIN_COUNT = 30    # pattern must appear >= 30 times
_PROMOTION_MIN_DOMAINS = 5   # across >= 5 distinct domains

def scan_audit_patterns(mistakes_dir):
    patterns = collect_patterns(mistakes_dir)
    for p in patterns:
        if p.count >= _PROMOTION_MIN_COUNT and p.domains >= _PROMOTION_MIN_DOMAINS:
            propose_rule_promotion(p, target="CLAUDE.md")
```

In practice, three rules promoted automatically after 34 cycles:

- **input validation defense** (L): 45 occurrences across 8 domains — mol is None check missed, causing invisible failures in structure rendering.
- **Silent failure prevention** (M): 35 occurrences — `except: pass` patterns, `None` returns without logging, blank UI states with no traceable error.
- **Type guard requirement** (N): 27 occurrences — external/AI data assumed to be `dict` when it was `str`, causing `AttributeError` in student-facing screens.

Cross-cycle mistake reduction for promoted rules: approximately 92% in the 10 cycles following promotion. The rules are short (one line each), positioned at the top of the instruction file, and referenced by code letter (L/M/N) in every Worker prompt.

The scanner also classifies patterns that are not yet ready for promotion (below threshold) and tracks their trajectory. This gives visibility into emerging failure modes before they become systemic.

---

### 2. Recursive Session Handoff

The core idea: a single file with 8 standardized sections should be enough for any new session to resume work without prompting.

A file called `NEXT_SESSION_PROMPT.md` is written at the end of every session. It contains:

```
Section 1: Cumulative Summary
  — last N M-numbers with one-line descriptions

Section 2: User Direct Quotes (verbatim)
  — exact words, not paraphrases, for alignment

Section 3: In-Progress Items
  — each with file path and current state

Section 4: Pending User Decisions
  — D-01, D-02 ... numbered, with status [waiting|approved|rejected]

Section 5: False-PASS Patterns
  — FP-XX registry: patterns where audit incorrectly returned PASS

Section 6: Citations
  — academic references for any technical claims made this session

Section 7: Termination Conditions
  — what "done" means for the current block

Section 8: Next 5 Actions
  — numbered, specific, enough to act on without reading anything else
```

The M-number counter is strictly monotonic. Every committed change gets a unique M-number. The `mistakes.md` header stores `LAST_M_NUMBER: M{N}` so any session can determine where it is immediately.

When a cycle archive exceeds a threshold size, older sessions compress into `cycle_history.md`. The active `mistakes.md` stays under 50KB. The `NEXT_SESSION_PROMPT.md` is always under 5KB.

In practice: sessions resume correctly without re-explanation approximately 95% of the time when this file is present and up to date.

---

### 3. Squirrel Cheek — Mandatory Reading Enforcement

The core idea: if reading is voluntary, it will be skipped. Make it structural.

Before any Worker agent takes action, it must read five specific files. This is called the Squirrel Cheek protocol (named for the compulsive hoarding behavior — you must collect before you act).

The five mandatory reads are:
1. `CLAUDE.md` compressed index (the short version, under 30 lines)
2. `mistakes.md` last 10 entries (recent failure patterns)
3. `FALSE_PASS_REGISTRY.md` (patterns where auditors incorrectly returned PASS)
4. `docs/ai/skills/INDEX.md` (skill file directory)
5. The domain-specific skill file for the current task

Output from any Worker that skips these reads is marked invalid. Two hooks enforce this:
- `PostToolUse`: checks that reads occurred before any `Edit` or `Write` call
- `SubagentStop`: verifies the read checklist was completed before the agent exits

The false-positive registry is particularly important. It catalogs patterns where the audit chain returned PASS but the output was actually wrong. Without this registry, the same false-PASS pattern repeats because auditors have no memory of previous approvals. With it, 18 distinct false-PASS patterns have been catalogued and 22 prevention rules derived.

---

### 4. Per-Deliverable 5-Reject Gate

The core idea: single-auditor approval is insufficient. Require independent confirmation at multiple checkpoints before a deliverable advances.

Each Worker output enters a four-stage verification chain:

**Stage 1 — 3 Parallel Auditors**
Three audit teams run concurrently: theory (correctness), gui (visual output), integration (cross-module consistency). All three must pass.

**Stage 2 — CT Second Review**
A control tower agent reviews the combined audit output and counts cumulative rejects per Worker ID. If the reject count for that Worker ID is below 5, two additional auditors spawn automatically.

**Stage 3 — 5-Pass Threshold**
Only when 5 independent audits all return PASS does the deliverable advance to the user.

**Stage 4 — Model Garden Scan**
After each verified deliverable, the garden scanner runs and checks whether the pattern of rejects from this cycle warrants a new rule proposal.

This prevents the most common failure mode in multi-agent systems: a Worker produces output, an auditor approves it because they share context and framing, and the defect only surfaces when a real user interacts with the system.

```python
# ct_2nd_review.py simplified
REJECT_THRESHOLD = 5  # minimum independent passes required

def evaluate_deliverable(worker_id, audit_results):
    reject_count = load_reject_count(worker_id)
    if reject_count < REJECT_THRESHOLD:
        spawn_additional_auditors(count=2)
        return "EXTRA_AUDIT_REQUIRED"
    recent_two = audit_results[-2:]
    if all(r.verdict == "PASS" for r in recent_two):
        return "APPROVED"
    return "PENDING"
```

---

## How the Four Systems Interlock

```
User Request
    |
    v
Worker agent
  [reads: CLAUDE.md + mistakes.md + FP registry + skills]
  [Squirrel Cheek hook verifies before first write]
    |
    v
3 Audit Teams (parallel: theory / gui / integration)
    |
    v
CT Second Review
  [counts rejects per Worker ID]
  [if < 5: spawn 2 more auditors]
    |
    v (5 independent PASS)
Model Garden scan
  [classify patterns from this cycle]
  [if threshold reached: propose CLAUDE.md update]
    |
    v
NEXT_SESSION_PROMPT.md written
  [8 sections, < 5KB, ready for next session]
    |
    v
Next cycle resumes (no re-explanation needed)
```

The four systems address the four failure modes directly:

| Failure Mode | System |
|---|---|
| Session amnesia | Recursive Session Handoff |
| Rubber-stamp audits | Per-Deliverable 5-Reject Gate |
| Instruction bloat | Model Garden (short promoted rules only) |
| Invisible failure | Squirrel Cheek (mandatory read of M rule: silent failure prevention) |

---

## Quantitative Results

The following figures are from a single project using this harness over approximately 50 cycles. Your numbers will differ.

| Metric | Value |
|---|---|
| Total tracked changes (M-numbers) | 500+ |
| Rules auto-promoted via Model Garden | 8 (from 12 candidates) |
| Cross-session continuity rate | ~95% |
| False-PASS patterns catalogued | 18 |
| False-PASS prevention rules derived | 22 |
| Mistake reduction after rule promotion | ~92% for promoted patterns |
| Average session startup time | < 2 minutes with handoff file |

---

## Limitations and Open Questions

**Pattern classification is keyword-based, not semantic.** The Model Garden scanner uses string matching against a keyword dictionary. Two semantically identical mistakes described in different words will not be grouped. Replacing this with embedding-based clustering is the most obvious improvement.

**The 5-reject threshold is empirical.** The value 5 was derived by observation, not from optimal stopping theory or a formal model of auditor reliability. Different projects with different auditor quality distributions will need different thresholds.

**Hooks still rely partly on prompt-level instruction.** The Squirrel Cheek `PostToolUse` hook checks that reads occurred, but the check itself is implemented as a Python script called by the hook, not as a hard constraint in the runtime. A sufficiently confused agent could bypass it.

**The handoff file degrades if sessions are very long.** The 8-section template assumes a session covers roughly 5-20 tracked changes. Sessions covering 50+ changes produce handoff files that are technically correct but cognitively overwhelming for the next session to process.

**Multi-project scope is untested.** This harness was developed in a single-project context. Applying it across multiple concurrent projects with shared `mistakes.md` state raises coordination questions that have not been fully resolved.

---

## Reference Implementation

This pattern was developed while building a complex desktop scientific application. The harness code is generic; the domain-specific parts are in separate modules that the harness does not touch.

The pseudocode examples in `examples/` illustrate each system independently. The `architecture.md` file contains the ASCII flow diagram.

To adapt to your project:
1. Create `CLAUDE.md` with a compressed index (under 30 lines)
2. Create `mistakes.md` with the M-number header format
3. Create `NEXT_SESSION_PROMPT.md` with the 8-section template
4. Implement the Model Garden scanner (see `examples/model_garden_pseudocode.py`)
5. Add the 5-reject gate to your audit flow (see `examples/ralph_loop_pseudocode.sh`)
6. Enforce mandatory reads at Worker spawn time (see `examples/squirrel_cheek_pseudocode.md`)

---

## License

MIT. See LICENSE file.

---

## Related

- [Claude Code documentation](https://claude.ai/claude-code)
- [Anthropic Agent SDK](https://github.com/anthropics/anthropic-sdk-python)
- Pattern: "Constitutional AI for agent harnesses" (Bai et al. 2022, generalized)
- Pattern: "Self-play improvement loops" (Silver et al. 2017, adapted for verification chains)

---

*Keywords: AI agent harness, self-evolving systems, Claude Code patterns, LLM verification cycles, session handoff, multi-agent auditing, mistake-driven rule promotion.*
