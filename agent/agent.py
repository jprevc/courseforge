"""
Course generator agent: takes a topic string and returns structured CourseContent
(overview, cheatsheet, exercises) using pydantic-ai with structured output.
"""

import functools
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai import Agent


class MultipleChoiceExercise(BaseModel):
    """One multiple-choice question: 4 options and the index of the correct one."""

    question: str
    options: list[str] = Field(..., min_length=4, max_length=4, description="Exactly 4 answer choices")
    correct_index: int = Field(..., ge=0, le=3, description="Index (0–3) of the correct option")
    explanation: str = Field(..., description="Short sentence explaining why the correct answer is right")


class MatchingPair(BaseModel):
    """One pair of items to be matched (e.g. term and definition)."""

    left: str
    right: str


class MatchingExercise(BaseModel):
    """One matching exercise: a list of pairs to connect."""

    question: str
    pairs: list[MatchingPair] = Field(
        ..., min_length=4, max_length=6, description="4 to 6 term-definition or concept-answer pairs"
    )


class ExerciseItem(BaseModel):
    """Discriminated union: either a multiple_choice or a matching exercise."""

    type: Literal["multiple_choice", "matching"]
    multiple_choice: MultipleChoiceExercise | None = None
    matching: MatchingExercise | None = None


class FlashcardItem(BaseModel):
    """One flashcard: short front (prompt) and short back (answer, max ~3 words each)."""

    front: str = Field(..., description="Very short key term, concept name, or brief question (at most 3 words)")
    back: str = Field(..., description="Very short answer or definition (at most 3 words, not a full sentence)")


class CourseContent(BaseModel):
    """Full course content as returned by the agent: title, overview, cheatsheet, exercises, and flashcards."""

    title: str = Field(..., description="Short course title based on the topic")
    overview: str = Field(..., description="One paragraph (2–4 sentences) explaining what the learner will learn")
    cheatsheet: str = Field(
        ...,
        description="Key facts/formulas/definitions in valid Markdown. Use ### headings for category titles and bullet list items for entries beneath each heading. Never put a category title inside a bullet point.",
    )
    exercises: list[ExerciseItem] = Field(
        default_factory=list,
        description="Mix of multiple_choice and matching exercises. Generate exactly the requested count, or 5–8 if not specified.",
    )
    flashcards: list[FlashcardItem] = Field(
        default_factory=list, description="Generate exactly the requested count, or 5–10 if not specified."
    )


COURSE_GENERATOR_INSTRUCTIONS = """You are an educational content designer. You will receive a structured request containing:
- Topic: the subject of the course
- Difficulty: Beginner, Intermediate, or Advanced — adapt vocabulary, depth of explanation, and exercise difficulty to this level (Beginner = simpler terms and easier questions; Advanced = more technical and challenging)
- Optional additional instructions: free-form guidance (e.g. "focus on async/await", "use real-world examples", "avoid math-heavy explanations") — follow these carefully when provided
- Optional number of exercises: if specified, produce exactly that many exercises; otherwise use between 5 and 8
- Optional number of flashcards: if specified, produce exactly that many flashcards; otherwise use between 5 and 10
- A line indicating which content to generate (for example: "Content to generate: Questions (5), Flashcards (8)"). Only generate the types of content explicitly requested on that line.

Keep explanations clear and concise. Make exercises fun and instructive. Always respect the difficulty level and any additional instructions."""


def get_course_generator_agent(model: str = "openai:gpt-5-mini") -> Agent[None, CourseContent]:
    """Build the course generator agent with the given model string (e.g. openai:gpt-5-mini)."""
    return Agent(
        model,
        output_type=CourseContent,
        instructions=COURSE_GENERATOR_INSTRUCTIONS,
        output_retries=3,
    )


def get_agent_model() -> str:
    """Return the model string used for course generation (env or default). Same as used by get_agent()."""
    import os

    return os.environ.get("COURSEFORGE_LLM_MODEL", "openai:gpt-5-mini")


@functools.cache
def get_agent() -> Agent[None, CourseContent]:
    """Return the default course generator agent (lazy init, model from env or default)."""
    return get_course_generator_agent(model=get_agent_model())
