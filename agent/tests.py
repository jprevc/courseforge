"""Unit tests for the course generator agent (no Django, no LLM call)."""

import os

import pytest

from agent.agent import (
    CourseContent,
    get_course_generator_agent,
)


def test_course_content_model_parses_valid_output() -> None:
    """CourseContent and ExerciseItem parse valid structured data."""
    data = {
        "title": "Python list comprehensions",
        "overview": "You will learn how to write list comprehensions in Python.",
        "cheatsheet": "- [x for x in iterable]\n- Optional: [x for x in iterable if cond]",
        "exercises": [
            {
                "type": "multiple_choice",
                "multiple_choice": {
                    "question": "What is the result of [x*2 for x in [1,2,3]]?",
                    "options": ["[2,4,6]", "[1,2,3]", "[]", "Error"],
                    "correct_index": 0,
                },
                "matching": None,
            },
            {
                "type": "matching",
                "multiple_choice": None,
                "matching": {
                    "question": "Match construct to description.",
                    "pairs": [
                        {"left": "List comp", "right": "Single expression"},
                        {"left": "for loop", "right": "Multiple statements"},
                    ],
                },
            },
        ],
    }
    content = CourseContent.model_validate(data)
    assert content.title == "Python list comprehensions"
    assert len(content.exercises) == 2
    assert content.exercises[0].type == "multiple_choice"
    assert content.exercises[0].multiple_choice is not None
    assert content.exercises[0].multiple_choice.options[0] == "[2,4,6]"
    assert content.exercises[1].type == "matching"
    assert content.exercises[1].matching is not None
    assert len(content.exercises[1].matching.pairs) == 2


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set; skip agent build test",
)
def test_get_agent_returns_agent() -> None:
    """get_course_generator_agent returns an Agent with CourseContent output type."""
    agent = get_course_generator_agent(model="openai:gpt-4o-mini")
    assert agent is not None
    assert agent.output_type is CourseContent
