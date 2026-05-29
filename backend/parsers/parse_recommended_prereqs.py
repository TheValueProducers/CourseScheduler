from __future__ import annotations

import re
from typing import List


def parse_recommended_prereqs(raw_text: str) -> List[str]:
    if not raw_text:
        return []

    matches = re.findall(r"Recommended Prerequisites?:\s*\n(.+)", raw_text)
    return [match.strip() for match in matches if match.strip()]
