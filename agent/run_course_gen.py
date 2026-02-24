"""
Thin wrapper to run the course generator agent. Called by Django views.
Returns (CourseContent, model_name) or raises on failure.
"""

from agent.agent import CourseContent, get_agent, get_agent_model


def run_course_generator_sync(
    topic: str,
    difficulty: str = "beginner",
    additional_instructions: str | None = None,
    include_questions: bool = True,
    num_exercises: int | None = None,
    include_flashcards: bool = False,
    num_flashcards: int | None = None,
) -> tuple[CourseContent, str]:
    """Generate course content for the given topic and options. Blocks until done. Returns (content, model_used)."""
    parts = [f"Topic: {topic.strip()}", f"Difficulty: {difficulty.strip().capitalize()}"]
    if additional_instructions and additional_instructions.strip():
        parts.append(f"Additional instructions: {additional_instructions.strip()}")
    content_bits: list[str] = []
    if include_questions:
        if num_exercises is not None:
            content_bits.append(f"Questions ({num_exercises})")
        else:
            content_bits.append("Questions")
    if include_flashcards:
        if num_flashcards is not None:
            content_bits.append(f"Flashcards ({num_flashcards})")
        else:
            content_bits.append("Flashcards")
    if content_bits:
        parts.append(f"Content to generate: {", ".join(content_bits)}")
    prompt = "\n\n".join(parts)
    agent = get_agent()
    result = agent.run_sync(prompt)
    output = result.output
    if not output:
        raise RuntimeError("Agent returned no output")
    return output, get_agent_model()
