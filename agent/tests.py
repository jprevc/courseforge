"""Unit tests for the course generator agent (no Django, no LLM call)."""

import os
import unittest

from agent.agent import (
    CourseContent,
    ExerciseItem,
    MatchingExercise,
    MatchingPair,
    MultipleChoiceExercise,
    get_course_generator_agent,
)


class TestCourseContentModel(unittest.TestCase):
    def test_course_content_model_parses_valid_output(self):
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
        self.assertEqual(content.title, "Python list comprehensions")
        self.assertEqual(len(content.exercises), 2)
        self.assertEqual(content.exercises[0].type, "multiple_choice")
        self.assertEqual(content.exercises[0].multiple_choice.options[0], "[2,4,6]")
        self.assertEqual(content.exercises[1].type, "matching")
        self.assertEqual(len(content.exercises[1].matching.pairs), 2)


@unittest.skipIf(
    not os.environ.get("OPENAI_API_KEY"),
    "OPENAI_API_KEY not set; skip agent build test",
)
class TestAgentBuilder(unittest.TestCase):
    def test_get_agent_returns_agent(self):
        """get_course_generator_agent returns an Agent with CourseContent output type."""
        agent = get_course_generator_agent(model="openai:gpt-4o-mini")
        self.assertIsNotNone(agent)
        self.assertIs(agent.output_type, CourseContent)
