import os

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.conversation import (
    Conversation,
    ConversationInitiationData,
)
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

load_dotenv()

AGENT_ID = os.getenv("AGENT_ID")
API_KEY = os.getenv("API_KEY")


user_name = "Dhruv"
schedule = "Class at 9:00 AM, Break at 4:00 PM, Lectures at 5:00PM, Projects at 7:00 PM, Dinner at 9:00 PM, Sleep at 11:00 PM"
prompt = f"You are a helpful assistant. Your interlocutor has the following schedule: {schedule}."
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

client = ElevenLabs(api_key=API_KEY)

conversation = Conversation(
    client,
    AGENT_ID,
    config=config,
    requires_auth=True,
    audio_interface=DefaultAudioInterface(),
)

def print_agent_response(response):
    print(f"Agent: {response}")

def print_interrupted_response(original, corrected):
    print(f"Agent interrupted, truncated response: {corrected}")

def print_user_transcript(transcript):
    print(f"User: {transcript}")


conversation = Conversation(
  client,
  AGENT_ID,
  config=config,
  requires_auth=True,
  audio_interface=DefaultAudioInterface(),
  callback_agent_response=print_agent_response,
  callback_agent_response_correction=print_interrupted_response,
  callback_user_transcript=print_user_transcript,
)

conversation.start_session()