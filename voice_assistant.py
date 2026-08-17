import os

import requests
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
    f"You are a helpful, multipurpose assistant. Your interlocutor is {user_name}, "
    f"who has the following daily schedule: {schedule}. "
    "\n\nTOOLS: You have three tools available:\n"
    "- `web_search`: general current-events or fact lookups.\n"
    "- `get_sports_score`: live/recent scores for a specific team or matchup. "
    "Requires a team or matchup name — if the user just says 'what's the score', "
    "ask them which team or game they mean before calling it.\n"
    "- `get_breaking_news`: recent news on a topic. If the user just says "
    "'what's happening in the news', ask whether they want a specific topic "
    "(e.g. tech, politics, their local area) or general top headlines before calling it.\n"
    "\nAMBIGUITY: If a request could reasonably mean more than one thing "
    "(unclear team name, unclear time frame like 'recent', unclear pronoun "
    "referring to something earlier in the conversation), ask one short "
    "clarifying question rather than guessing. Don't ask for clarification "
    "on requests that are already clear enough to act on.\n"
    "\nACCURACY: If a tool result looks internally inconsistent (e.g. flags "
    "a discrepancy between sources), say so out loud rather than picking one "
    "version silently — e.g. 'One source says X, another says Y, here's what "
    "I'd trust and why.'\n"
    "\nKeep spoken answers concise, since this is a voice conversation."
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

def get_sports_score(parameters: dict) -> str:
    query = parameters.get("query", "")
    league = parameters.get("league", "").lower().strip()
    sport = parameters.get("sport", "").lower().strip()

    if not query:
        return "No team or matchup provided."

    espn_result = None
    if sport and league:
        try:
            url =  f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard"
            resp = requests.get(url, timeout =6)
            resp.raise_for_status()
            data = resp.json()
            events = data.get("events", [])      
            matches = [
                e for e in events
                if query.lower() in e.get("name", "").lower()
            ]
            if matches:
                e = matches[0]
                comp = e["competitions"][0]
                status = comp["status"]["type"]["description"]
                teams = [
                    f"{c['team']['displayName']} {c.get('score', '?')}"
                    for c in comp["competitors"]
                ]
                espn_result = f"{status}: {' vs '.join(teams)}"

        except Exception:
            espn_result = None

    # Independent cross-check via web search
    web_result = None
    try:
        hits = DDGS().text(f"{query} score", max_results=2)
        if hits:
            web_result = hits[0].get("body", "")[:300]
    except Exception:
        pass

    if espn_result and web_result:
        return (
            f"ESPN data: {espn_result}. Web cross-check: {web_result}."
            "If these disagree on the score, mention both to the user."
        )
    if espn_result:
        return f"ESPN data: {espn_result} (no independent check available)."
    if web_result:
        return f"Web search result: {web_result} (structured sports feed unavailable - pass 'sport' and 'league' parameters for a direct box score next time)."
    return f"Couldn't find current score information for '{query}'"

def get_breaking_news(parameters: dict) -> str:
    topic = parameters.get("topic", "").strip()
    if not topic:
        topic = "top world news"

    ddgs_headlines = []
    try:
        results = DDGS().news(topic, max_results=4)
        ddgs_headlines = [r.get("title", "") for r in results if r.get("title")]
    except Exception:
        pass

    newsapi_headline = []
    newsapi_key = os.getenv("NEWSAPI_KEY")
    if newsapi_key:
        try:
            resp = requests.get(
                "https://newsapi.org/v2/everything",
                params={"q": topic, "sortBy": "publishedAt", "pageSize": 4, "apiKey": newsapi_key},
                timeout=6,
            )
            resp.raise_for_status()
            articles = resp.json().get("articles", [])
            newsapi_headlines = [a.get("title", "") for a in articles if a.get("title")]
        except Exception:
            pass

    if not ddgs_headlines and not newsapi_headlines:
        return f"No recent news found for '{topic}'"
    if ddgs_headlines and newsapi_headlines:
        overlap = any(
            _headline_overlap(h1,h2)
            for h1 in ddgs_headlines for h2 in newsapi_headlines
        )
        confidence = "corroborated by two independent sources" if overlap  else "sources cover this differently - treat with more causion"
        combined = ddgs_headlines[:3] + newsapi_headlines[:3]
        return f"({confidence}) Headlines: " + " | ".join(combined)[:1500]

    single_source = ddgs_headlines or newsapi_headlines
    return "Headlines (single source): " + " | ".join(single_source)[:1500]

def _headline_overlap(a: str, b: str) -> bool:
    a_words = set(a.lower().split())
    b_words = set(b.lower().split())
    if not a_words or not b_words:
        return False
    overlap_ratio = len(a_words & b_words) / min(len(a_words), len(b_words))
    return overlap_ratio > 0.3
        

client_tools = ClientTools()
client_tools.register("web_search", web_search)
client_tools.register("get_sports_score", get_sports_score)
client_tools.register("get_breaking_news", get_breaking_news)


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