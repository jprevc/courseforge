"""
Course generator agent: takes a topic string and returns structured CourseContent
(overview, cheatsheet, exercises) using pydantic-ai with structured output.
"""

from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai import Agent


class MultipleChoiceExercise(BaseModel):
    """One multiple-choice question: 4 options and the index of the correct one."""

    question: str
    options: list[str] = Field(..., min_length=4, max_length=4)
    correct_index: int = Field(..., ge=0, le=3)
    explanation: str  # Why the correct answer is right


class MatchingPair(BaseModel):
    """One pair of items to be matched (e.g. term and definition)."""

    left: str
    right: str


class MatchingExercise(BaseModel):
    """One matching exercise: a list of pairs to connect."""

    question: str
    pairs: list[MatchingPair] = Field(..., min_length=2)


class ExerciseItem(BaseModel):
    """Discriminated union: either a multiple_choice or a matching exercise."""

    type: Literal["multiple_choice", "matching"]
    multiple_choice: MultipleChoiceExercise | None = None
    matching: MatchingExercise | None = None


class CourseContent(BaseModel):
    """Full course content as returned by the agent: title, overview, cheatsheet, and exercises."""

    title: str
    overview: str
    cheatsheet: str
    exercises: list[ExerciseItem] = Field(..., min_length=1)


COURSE_GENERATOR_INSTRUCTIONS = """You are an educational content designer. You will receive a structured request containing:
- Topic: the subject of the course
- Difficulty: Beginner, Intermediate, or Advanced — adapt vocabulary, depth of explanation, and exercise difficulty to this level (Beginner = simpler terms and easier questions; Advanced = more technical and challenging)
- Optional additional instructions: free-form guidance (e.g. "focus on async/await", "use real-world examples", "avoid math-heavy explanations") — follow these carefully when provided
- Optional number of exercises: if specified, produce exactly that many exercises; otherwise use between 5 and 8

Produce a short course with:
1. A clear title (short, based on the topic).
2. One overview paragraph (2-4 sentences) explaining what the learner will learn.
3. A cheatsheet with key facts, formulas, or definitions written in valid Markdown. Use ### headings for category titles (e.g. "### Basic Verbs") and bullet list items only for the entries beneath each heading. Never put a category title inside a bullet point.
4. The requested number of exercises (or 5–8 if not specified). Mix multiple choice and matching exercises.
- Multiple choice: exactly 4 options, one correct. Set correct_index to 0, 1, 2, or 3 for the correct option. Always include an explanation: a short sentence explaining why the correct answer is right.
- Matching: 4 to 6 pairs of (left, right) items that belong together (e.g. term-definition, question-answer).
Keep explanations clear and concise. Make exercises fun and instructive. Always respect the difficulty level and any additional instructions."""


def get_course_generator_agent(model: str = "openai:gpt-4o-mini") -> Agent:
    """Build the course generator agent with the given model string (e.g. openai:gpt-4o-mini)."""
    return Agent(
        model,
        output_type=CourseContent,
        instructions=COURSE_GENERATOR_INSTRUCTIONS,
    )


# Default agent instance (model can be overridden via env in run_course_gen)
_course_agent = None


def get_agent() -> Agent:
    """Return the default course generator agent (lazy init, model from env or default)."""
    global _course_agent
    if _course_agent is None:
        import os

        model = os.environ.get("COURSEFORGE_LLM_MODEL", "openai:gpt-4o-mini")
        _course_agent = get_course_generator_agent(model=model)
    return _course_agent
