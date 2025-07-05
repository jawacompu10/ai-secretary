from agents import Agent

from config import settings


agent = Agent(
    name="Secretary",
    handoff_description="Specialist agent for managing tasks and schedules",
    instructions=f"""
        You are a Personal Secretary to {settings.user_name}
        """,
)
