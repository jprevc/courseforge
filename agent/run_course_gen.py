"""
Thin wrapper to run the course generator agent. Called by Django views.
Returns CourseContent or raises on failure.
"""

from agent.agent import CourseContent, get_agent


def run_course_generator_sync(topic: str) -> CourseContent:
    """Generate course content for the given topic. Blocks until done."""
    agent = get_agent()
    result = agent.run_sync(topic)
    if not result.output:
        raise RuntimeError("Agent returned no output")
    return result.output
