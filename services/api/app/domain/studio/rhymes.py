"""Rhyme detection for lyrics."""

import re

_ENDING_LEN = 3


def _last_syllable_ending(word: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z\u0430-\u044f\u0451\u0400-\u04FF]", "", word.lower())
    if len(cleaned) <= _ENDING_LEN:
        return cleaned
    return cleaned[-_ENDING_LEN:]


def _line_ending(line: str) -> str | None:
    words = line.strip().split()
    if not words:
        return None
    return _last_syllable_ending(words[-1])


def analyze_rhymes(text: str) -> dict:
    lines = text.splitlines() or [text]
    endings: list[dict] = []
    for idx, line in enumerate(lines):
        ending = _line_ending(line)
        if ending:
            endings.append({"line_number": idx + 1, "text": line.strip(), "ending": ending})

    groups: dict[str, list[int]] = {}
    for item in endings:
        groups.setdefault(item["ending"], []).append(item["line_number"])

    rhyme_groups = [
        {"ending": ending, "line_numbers": sorted(nums)}
        for ending, nums in groups.items()
        if len(nums) >= 2
    ]
    rhyme_groups.sort(key=lambda g: (-len(g["line_numbers"]), g["ending"]))

    rhyme_map = {item["line_number"]: item["ending"] for item in endings}

    return {
        "rhyme_group_count": len(rhyme_groups),
        "rhyme_groups": rhyme_groups,
        "line_endings": rhyme_map,
        "unrhymed_lines": [
            item["line_number"]
            for item in endings
            if len(groups.get(item["ending"], [])) < 2
        ],
    }


def lines_share_rhyme(line_a: str, line_b: str) -> bool:
    a = _line_ending(line_a)
    b = _line_ending(line_b)
    return a is not None and a == b
