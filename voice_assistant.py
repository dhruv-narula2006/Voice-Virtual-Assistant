import os

from dotenv import load_dotenv
from ddgs import DDGS
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.conversation import (
    ClientTools,
    Conversation,
    ConversationInitiationData,
)
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

load_dotenv()

AGENT_ID = os.getenv("AGENT_ID")
API_KEY = os.getenv("API_KEY")

# ---------------------------------------------------------
# 1. Agent person/ context 
# ---------------------------------------------------------

user_name = "Dhruv"
schedule = "Class at 9:00 AM, Break at 4:00 PM, Lectures at 5:00PM, Projects at 7:00 PM, Dinner at 9:00 PM, Sleep at 11:00 PM"
prompt =(
     f"You are a helpful, multipurpose assistant. Your interlocutor is {user_name},"
     f"who has the following daily schedule: {schedule}."
     "You have access to a 'web_search' tool - use it whenever the user asks about"
     "current events, facts you're unsure of, or anything that could have changed "
     "recently. Keep spoken answers concise, since this is a voice conversation."
)
first_message = f"Hello {user_name}, how can I help you today?"

conversation_override = {
    "agent": {
        "prompt": {
            "prompt": prompt,
        },
        "first_message": first_message,
    },
}

config = ConversationInitiationData(
    conversation_config_override=conversation_override,
    extra_body ={},
    dynamic_variables={},
)

# ---------------------------------------------------------
# 2. Client tool implementation
# ---------------------------------------------------------
def web_search(parameters: dict) -> str:
    query = parameters.get("query", "")
    if not query:
        return "No search query provided."
    
    try:
        results = DDGS().text(query, max_results=4)
    except Exception as e:
        return f"Seach failed: {e}"

    if not results:
        return f"no results found for the query '{query}'."

    # Keep it short - this gets read back to the agent, and eventually spoken aloud.
    summary_lines = []
    for r in results:
        title = r.get("title", "")
        body = r.get("body", "")
        summary_lines.append(f"{title}: {body}")

    return " | ".join(summary_lines)[:1500]   #cap length for latency/cost
        
client_tools = ClientTools()
client_tools.register("web_search", web_search)

# ---------------------------------------------------------
# 3. Callbacks (unchanged)
# ---------------------------------------------------------
def print_agent_response(response):
    print(f"Agent: {response}")

def print_interrupted_response(original, corrected):
    print(f"Agent interrupted, truncated response: {corrected}")

def print_user_transcript(transcript):
    print(f"User: {transcript}")

# ---------------------------------------------------------
#  4. Build and start the conversation
# ---------------------------------------------------------
client = ElevenLabs(api_key=API_KEY)

conversation = Conversation(
    client,
    AGENT_ID,
    config=config,
    requires_auth=True,
    audio_interface=DefaultAudioInterface(),
    client_tools = client_tools,
    callback_agent_response=print_agent_response,
    callback_agent_response_correction=print_interrupted_response,
    callback_user_transcript=print_user_transcript
)

conversation.start_session()