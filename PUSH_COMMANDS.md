# Push Commands — Recursive AI Harness

## Prerequisites

1. Create a new GitHub repository at https://github.com/new
   - Repository name: `recursive-ai-harness`
   - Visibility: Public
   - Do NOT initialize with README (this repo already has one)

2. Authenticate GitHub CLI (one time only):

```bash
gh auth login
```

Follow the prompts. Choose GitHub.com, HTTPS, and authenticate via browser.

---

## One-Block Push

Copy and run this entire block after completing steps 1 and 2 above.
Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username.

```bash
cd /path/to/recursive-ai-harness && \
git init && \
git add . && \
git commit -m "feat: recursive AI harness — self-evolving agent framework" && \
git branch -M main && \
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/recursive-ai-harness.git && \
git push -u origin main
```

---

## After Push: Improve Discoverability (Optional)

### Topics (GitHub web UI)
Go to your repo > gear icon next to "About" > add topics:
```
claude-code  ai-agent  llm  self-evolving  agent-harness  verification  claude
```

### Description (GitHub web UI)
```
Self-evolving Claude Code harness: turns repeated mistakes into rules, enforces mandatory reading, runs infinite verification cycles.
```

### Social sharing to reach trending

**Hacker News:**
Title: `Show HN: Self-evolving Claude Code harness — 500+ iterations, patterns auto-promote to rules`
URL: your repo URL
Text: brief description of the 4 systems

**Reddit r/ClaudeAI:**
Title: `Built a self-evolving harness for Claude Code after 500+ iterations — sharing the patterns`

**Anthropic Claude Code Discussions:**
File an issue or discussion at: https://github.com/anthropics/anthropic-sdk-python
Link your repo and describe how the harness adapts the SDK's Agent tool.

---

## File List

```
recursive-ai-harness/
  README.md                              — main overview (1500 words)
  architecture.md                        — ASCII flow diagrams
  examples/
    model_garden_pseudocode.py           — self-evolving rule promotion
    ralph_loop_pseudocode.sh             — recursive verification loop
    squirrel_ball_pseudocode.md          — mandatory reading enforcement
  PUSH_COMMANDS.md                       — this file
  .gitignore                             — standard Python + Node ignores
  LICENSE                                — MIT
```
