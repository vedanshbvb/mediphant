from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
import os

from agents.script_agent import ScriptAgent
from agents.identify_characters_agent import IdentifyCharactersAgent
from agents.voice_agent import VoiceAgent
from agents.video_agent import VideoAgent
from agents.publish_agent import PublishAgent
from agents.analytics_agent import AnalyticsAgent

RootAgent = LlmAgent(
    name="root_agent",
    model=os.environ.get("AGENT_MODEL", "gemini-2.0-flash"),
    description="Agent that greets the user.",
    instruction="""
    You are an agent who has to greet the user. For each user prompt, you must do the following thing:

    Say "Hello, I am your medical assistant. Please fill the form on your screen."
    """,

)
