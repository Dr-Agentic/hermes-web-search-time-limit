# hermes-web-search-time-limit

**Live:** https://github.com/Dr-Agentic/hermes-web-search-time-limit

Time-filtered web search plugin for [Hermes Agent](https://github.com/NousResearch/hermes-agent) — powered by DuckDuckGo, no API key required.

## What it does

Adds `web_search_timed` to Hermes Agent's tool list:

```
web_search_timed(query: string, time_range: "d"|"w"|"m"|"y", limit?: int)
```

| `time_range` | Meaning |
|---|---|
| `d` | Past 24 hours |
| `w` | Past week |
| `m` | Past month |
| `y` | Past year |

## Installation — Two Options

### Option A: pip install (recommended)

```bash
pip install hermes-web-search-time-limit
```

Hermes auto-discovers it via the `hermes.plugins` entry point. Restart Hermes to load.

### Option B: Clone into plugins directory

```bash
git clone https://github.com/YOUR_HANDLE/hermes-web-search-time-limit.git ~/.hermes/plugins/hermes-web-search-time-limit
```

Then restart Hermes.

## Usage

Once installed, the LLM sees `web_search_timed` alongside `web_search`. Example prompts:

- *"Search for AI agent news from the past 24 hours"*
- *"Find climate tech funding from the past week using web_search_timed"*
- *"Research the latest developments in AI agents — past month"*

## Dependencies

- Python ≥ 3.10
- `ddgs` (installed automatically with pip)

## License

Apache 2.0
