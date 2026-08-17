# 🎙️ Voice Virtual Assistant

A Python-based voice virtual assistant built using **ElevenLabs Conversational AI**.

The assistant can have real-time voice conversations with the user and can be personalized with information such as the user's name, schedule, system prompt, and first message. It's also equipped with live tools for web search, sports scores, and breaking news — each with source cross-referencing to catch discrepancies before they're spoken aloud.

## ✨ Features

- 🎤 Real-time voice conversations
- 🧠 Personalized AI system prompt
- 👋 Custom first message
- 📅 Schedule-aware assistance
- 🔎 **Web search** — live lookups for current events and facts the model can't answer from memory
- 🏀 **Live sports scores** — pulls from ESPN's scoreboard feed, cross-checked against an independent web search
- 📰 **Breaking news** — headlines via DuckDuckGo News, optionally cross-referenced against NewsAPI.org if a key is provided
- ⚖️ **Discrepancy flagging** — when two sources disagree, the assistant says so instead of silently picking one
- ❓ **Clarifying questions** — asks before acting on ambiguous requests (e.g. "the score" with no team named) instead of guessing
- 🔐 Secure API key management using `.env`
- 🐍 Python implementation
- 🎧 Microphone and speaker interaction

## 🛠️ Tech Stack

- **Python 3.11+**
- **ElevenLabs Conversational AI**
- **ElevenLabs Python SDK**
- **PyAudio**
- **python-dotenv**
- **requests** — sports data (ESPN scoreboard API) and optional NewsAPI calls
- **ddgs** — key-free web and news search (DuckDuckGo)

## 🧰 Tools

The assistant calls out to three **client-side tools**, executed locally and registered with the ElevenLabs agent via `ClientTools`. Each must also be registered as a **Client tool** in the ElevenLabs dashboard (Agent → Tools) with a matching name and parameters:

| Tool | Parameters | What it does |
|---|---|---|
| `web_search` | `query` (string, required) | General-purpose web search for current info the model isn't confident about. |
| `get_sports_score` | `query` (string, required), `sport` (string, optional), `league` (string, optional) | Fetches a live/recent score from ESPN's scoreboard feed and cross-checks it against a web search. Flags the result if the two sources disagree. |
| `get_breaking_news` | `topic` (string, optional) | Pulls recent headlines via DuckDuckGo News. If `NEWSAPI_KEY` is set, also queries NewsAPI.org and notes whether the two sources corroborate each other. |

## 📁 Project Structure

```text
Voice_Virtual_Assistant/
│
├── voice_assistant.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
└── README.md
```

## ⚙️ Environment Variables

| Variable | Required | Description |
|---|---|---|
| `AGENT_ID` | Yes | Your ElevenLabs agent ID |
| `API_KEY` | Yes | Your ElevenLabs API key |
| `NEWSAPI_KEY` | No | Free key from [newsapi.org](https://newsapi.org) — enables cross-referenced news headlines. Without it, `get_breaking_news` still works using DuckDuckGo News alone. |

## 🚀 Setup

1. Clone the repo and create a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in `AGENT_ID` and `API_KEY` (and optionally `NEWSAPI_KEY`).
4. In the ElevenLabs dashboard, add the three Client tools listed above under your agent's **Tools** tab, matching names and parameters exactly.
5. Run the assistant:
   ```bash
   python voice_assistant.py
   ```

## 🧠 Notes on Accuracy & Context

- Conversation history is retained natively by ElevenLabs for the duration of a session — no extra setup needed for context within a single call.
- Persistent memory *across* separate sessions isn't included by default; ElevenLabs supports a Mem0 integration for that if needed later.
- ESPN's scoreboard endpoint is unofficial/undocumented and could change without notice — the web-search cross-check is there as a fallback if it fails.