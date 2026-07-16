"""Syllable counting and rhythm analysis for lyrics."""

import re

_VOWEL_GROUPS = re.compile(
    r"[aeiouy\u0430\u0435\u0451\u0438\u043e\u0443\u044b\u044d\u044e\u044f\u0430\u0435\u0438\u043e\u0443]+",
    re.IGNORECASE,
)


def count_syllables_in_word(word: str) -> int:
    cleaned = re.sub(r"[^a-zA-Z\u0430-\u044f\u0451\u0400-\u04FF]", "", word)
    if not cleaned:
        return 0
    groups = _VOWEL_GROUPS.findall(cleaned)
    return max(1, len(groups))


def count_syllables_in_line(line: str) -> int:
    words = line.split()
    if not words:
        return 0
    return sum(count_syllables_in_word(w) for w in words)


def analyze_syllables(text: str) -> dict:
    lines = text.splitlines() or [text]
    line_counts = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            line_counts.append({"line_number": idx + 1, "text": line, "syllables": 0})
            continue
        line_counts.append(
            {
                "line_number": idx + 1,
                "text": line,
                "syllables": count_syllables_in_line(stripped),
            }
        )

    non_empty = [lc["syllables"] for lc in line_counts if lc["syllables"] > 0]
    total = sum(non_empty)
    avg = round(total / len(non_empty), 2) if non_empty else 0.0

    return {
        "total_syllables": total,
        "line_count": len(lines),
        "average_syllables_per_line": avg,
        "lines": line_counts,
    }
