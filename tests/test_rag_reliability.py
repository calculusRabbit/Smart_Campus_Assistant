"""Regression tests for campus RAG retrieval and response validation."""

from services.rag import pipeline


def test_wulug_abbreviation_prioritizes_official_club():
    selected = pipeline.prioritize_campus_documents(
        "What is WuLUG?",
        [],
        [],
    )

    assert selected
    first_index, _ = selected[0]

    assert pipeline.chunks[first_index]["url"].endswith("/organization/wulug")


def test_shockersync_prioritizes_platform_sources():
    selected = pipeline.prioritize_campus_documents(
        "What is the purpose of ShockerSync?",
        [],
        [],
    )

    urls = [
        pipeline.chunks[index]["url"]
        for index, _ in selected
    ]

    assert urls[0].endswith("/organization/seb")
    assert urls[1].endswith("/engage/organizations")


def test_unknown_question_preserves_semantic_retrieval():
    selected = pipeline.prioritize_campus_documents(
        "Tell me about the campus library",
        [5, 8, 12],
        [0.75, 0.60, 0.50],
    )

    assert [index for index, _ in selected] == [5, 8, 12]


def test_duplicate_retrieval_results_are_removed():
    club_index = next(
        index
        for index, chunk in enumerate(pipeline.chunks)
        if chunk.get("url", "").endswith("/organization/wulug")
    )

    selected = pipeline.prioritize_campus_documents(
        "What is WuLUG?",
        [club_index, club_index, 5],
        [0.80, 0.80, 0.40],
    )

    indices = [index for index, _ in selected]

    assert indices.count(club_index) == 1


def test_bad_generation_rejects_empty_or_reasoning():
    assert pipeline.is_bad_generation("") is True
    assert pipeline.is_bad_generation("Let me think about this.") is True
    assert pipeline.is_bad_generation("<think>analysis") is True


def test_bad_generation_accepts_normal_answer():
    answer = (
        "WuLUG is a computing club at Wichita State University. "
        "It organizes workshops and learning activities."
    )

    assert pipeline.is_bad_generation(answer) is False
