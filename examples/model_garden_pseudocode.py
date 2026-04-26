"""
model_garden_pseudocode.py
--------------------------
Self-Evolving Rule Promotion — pseudocode illustration.

This file demonstrates the Model Garden pattern: scanning logged mistakes
for recurring patterns and proposing promotions to the top-level harness
configuration when thresholds are met.

NOT production code. Replace paths, thresholds, and persistence logic
to fit your project.
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


# ── Thresholds ──────────────────────────────────────────────────────────
PROMOTION_MIN_COUNT = 30    # pattern must appear >= 30 times total (empirical)
PROMOTION_MIN_DOMAINS = 5   # across >= 5 distinct domains (empirical)
WATCH_MIN_COUNT = 10        # below this: watch list only, not proposed yet
CYCLE_SCAN_INTERVAL = 5     # run garden scan every N cycles (empirical)


# ── Keyword dictionary for pattern classification ───────────────────────
# Groups mistake log entries into semantic buckets.
# Extend this to cover your domain's recurring failure modes.
PATTERN_KEYWORDS: dict[str, list[str]] = {
    "silent_failure": [
        "silent", "return None", "invisible", "blank screen",
        "no log", "except.*pass", "swallowed",
    ],
    "type_guard_missing": [
        "isinstance", "AttributeError", "TypeError",
        "str object has no attribute", "'NoneType'",
    ],
    "parse_defense_missing": [
        "parse", "None check", "unclosed", "sanitize",
        "invalid structure", "malformed",
    ],
    "sync_missing": [
        "sync", "copy", "identical", "backup missed",
        "out of date", "stale",
    ],
    "audit_rubber_stamp": [
        "false pass", "false-pass", "FP-", "rubber stamp",
        "approved without", "screenshot missing",
    ],
    "hardcode": [
        "hardcode", "magic number", "literal", "API key in source",
        "credential",
    ],
}


@dataclass
class PatternEntry:
    name: str
    count: int = 0
    domains: set = field(default_factory=set)
    example_lines: list[str] = field(default_factory=list)

    @property
    def promotable(self) -> bool:
        return self.count >= PROMOTION_MIN_COUNT and len(self.domains) >= PROMOTION_MIN_DOMAINS

    @property
    def watchable(self) -> bool:
        return self.count >= WATCH_MIN_COUNT and not self.promotable


def load_mistake_log(mistakes_md_path: str) -> list[str]:
    """Read all comment-header lines from mistakes.md.

    Each entry is a <!-- M{N}: ... --> comment on one line.
    Returns list of raw entry strings for classification.
    """
    entries = []
    try:
        with open(mistakes_md_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("<!-- M") and "-->" in line:
                    entries.append(line)
    except FileNotFoundError:
        pass  # caller handles empty list
    return entries


def classify_entry(entry: str) -> Optional[str]:
    """Return the first matching pattern name, or None.

    Uses keyword matching. Replace with embedding similarity
    for semantic grouping across varied phrasings.
    """
    entry_lower = entry.lower()
    for pattern_name, keywords in PATTERN_KEYWORDS.items():
        for kw in keywords:
            if re.search(kw.lower(), entry_lower):
                return pattern_name
    return None


def extract_domain(entry: str) -> str:
    """Extract domain tag from mistake entry (e.g. worker module prefix).

    Looks for bracketed worker ID like [W_M{N}_DOMAIN_NAME].
    Falls back to 'unknown' if not found.
    """
    match = re.search(r"\[W_M\d+_([A-Z_]+)\]", entry)
    if match:
        # Take first two underscore-separated parts as domain key
        parts = match.group(1).split("_")
        return "_".join(parts[:2])
    return "unknown"


def collect_patterns(mistakes_md_path: str) -> dict[str, PatternEntry]:
    """Scan mistakes log and aggregate by pattern type.

    Returns mapping of pattern_name -> PatternEntry with accumulated stats.
    """
    patterns: dict[str, PatternEntry] = defaultdict(lambda: PatternEntry(name=""))
    entries = load_mistake_log(mistakes_md_path)

    for entry in entries:
        pattern_name = classify_entry(entry)
        if pattern_name is None:
            continue

        p = patterns[pattern_name]
        p.name = pattern_name
        p.count += 1
        p.domains.add(extract_domain(entry))
        if len(p.example_lines) < 3:  # keep up to 3 examples per pattern
            # Store only first 120 chars to avoid bloat
            p.example_lines.append(entry[:120])

    return dict(patterns)


def propose_rule_promotion(pattern: PatternEntry, config_path: str) -> str:
    """Generate a one-line rule proposal for the harness config.

    Does NOT write automatically. Returns the proposed text for human review
    or downstream hook to insert.
    """
    proposal = (
        f"# AUTO-PROPOSED by Model Garden\n"
        f"# Pattern: {pattern.name}\n"
        f"# Evidence: {pattern.count} occurrences across {len(pattern.domains)} domains\n"
        f"# Domains: {sorted(pattern.domains)}\n"
        f"# Example: {pattern.example_lines[0] if pattern.example_lines else 'n/a'}\n"
        f"RULE_{pattern.name.upper()}: enforce at Worker spawn + audit gate\n"
    )
    return proposal


def run_garden_scan(mistakes_md_path: str, config_path: str) -> dict:
    """Top-level entry point for one garden cycle.

    Returns a summary dict with promoted, watching, and skipped patterns.
    Suitable for logging or passing to a downstream report generator.
    """
    patterns = collect_patterns(mistakes_md_path)

    promoted = []
    watching = []
    skipped = []

    for name, p in patterns.items():
        if p.promotable:
            proposal = propose_rule_promotion(p, config_path)
            promoted.append({"name": name, "count": p.count, "domains": len(p.domains), "proposal": proposal})
        elif p.watchable:
            watching.append({"name": name, "count": p.count, "domains": len(p.domains)})
        else:
            skipped.append(name)

    return {
        "total_patterns_found": len(patterns),
        "promoted": promoted,
        "watching": watching,
        "skipped_count": len(skipped),
    }


# ── Example usage ────────────────────────────────────────────────────────
if __name__ == "__main__":
    result = run_garden_scan(
        mistakes_md_path="docs/ai/mistakes.md",
        config_path="CLAUDE.md",
    )
    print(f"Patterns found: {result['total_patterns_found']}")
    print(f"Ready for promotion: {len(result['promoted'])}")
    for p in result["promoted"]:
        print(f"  [{p['name']}] count={p['count']} domains={p['domains']}")
        print(f"  Proposal:\n{p['proposal']}")
    print(f"On watch list: {len(result['watching'])}")
