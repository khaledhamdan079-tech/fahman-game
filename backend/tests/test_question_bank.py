from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIRECTORY = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIRECTORY))

from arabic_question_relations_extra import EXTRA_RELATION_CATEGORIES  # noqa: E402
from build_arabic_question_bank import (  # noqa: E402
    OPTION_DEPENDENT_PHRASES,
    build_payload,
)


def test_generated_question_bank_is_balanced_and_standalone() -> None:
    items = build_payload()["items"]

    assert len(items) == 2448
    assert len({item["category_name_ar"] for item in items}) == 51
    tier_counts = Counter((item["category_name_ar"], item["points"]) for item in items)
    assert set(tier_counts.values()) == {16}
    assert not [
        item["prompt_ar"]
        for item in items
        if any(phrase in item["prompt_ar"] for phrase in OPTION_DEPENDENT_PHRASES)
    ]


def test_expansion_adds_1008_questions_in_well_sized_categories() -> None:
    items = build_payload()["items"]
    extra_counts = Counter(
        item["category_name_ar"]
        for item in items
        if item["category_name_ar"] in EXTRA_RELATION_CATEGORIES
    )

    assert len(extra_counts) == 21
    assert sum(extra_counts.values()) == 1008
    assert set(extra_counts.values()) == {48}


def test_every_question_has_one_matching_correct_option() -> None:
    for item in build_payload()["items"]:
        correct = [option for option in item["options"] if option["is_correct"]]
        assert len(correct) == 1
        assert correct[0]["text_ar"] == item["answer_ar"]
