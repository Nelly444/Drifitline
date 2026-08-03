import re
from collections import Counter

from rapidfuzz import fuzz

_SUFFIX_PATTERN = re.compile(r"(\.COM|\sINC|\*SUBSCRIPTION)$")


def _strip_suffix(name: str) -> str:
    return _SUFFIX_PATTERN.sub("", name.upper()).strip()


def normalize_merchants(raw_names: list[str], threshold: float = 87.0) -> dict[str, str]:
    counts = Counter(raw_names)
    unique_names = list(counts.keys())

    groups: list[list[str]] = []
    group_keys: list[str] = []

    for name in unique_names:
        key = _strip_suffix(name)
        best_group_index = None
        best_score = 0.0

        for i, group_key in enumerate(group_keys):
            score = fuzz.WRatio(key, group_key)
            if score >= threshold and score > best_score:
                best_group_index = i
                best_score = score

        if best_group_index is not None:
            groups[best_group_index].append(name)
        else:
            groups.append([name])
            group_keys.append(key)

    mapping: dict[str, str] = {}
    for group in groups:
        canonical = max(group, key=lambda n: (counts[n], -len(n)))
        for name in group:
            mapping[name] = canonical

    return mapping
