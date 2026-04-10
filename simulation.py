import os
import json

from dotenv import load_dotenv

from prompts import get_continent_prompt, SYNTHESIZER_DIRECTOR_PROMPT

load_dotenv()

CONTINENT_NAMES = [
    "North America",
    "South America",
    "Europe",
    "Africa",
    "Asia",
    "Oceania",
]

_crew_cache: dict = {}


def _clean_secret(value: str | None) -> str:
    """Normalize env/ui secrets to avoid hidden formatting issues."""
    if not value:
        return ""
    # Strip whitespace and optional wrapping quotes copied from dashboards.
    return value.strip().strip("'").strip('"')


def _crew_config_key(provider: str, claude_api_key: str | None = None) -> tuple:
    """Invalidate cached Crew when provider/config changes."""
    if provider == "claude":
        return (
            provider,
            _clean_secret(claude_api_key or os.getenv("CLAUDE_API_KEY", "")),
            os.getenv("CLAUDE_MODEL", ""),
            os.getenv("GMI_TIMEOUT", ""),
            os.getenv("GMI_MAX_RETRIES", ""),
            os.getenv("GMI_MAX_TOKENS", ""),
            os.getenv("GMI_TEMPERATURE", ""),
        )
    return (
        provider,
        os.getenv("GMI_API_KEY", ""),
        os.getenv("GMI_ENDPOINT_URL", ""),
        os.getenv("GMI_MODEL", ""),
        os.getenv("GMI_USE_JSON_RESPONSE_FORMAT", "").lower(),
        os.getenv("GMI_TIMEOUT", ""),
        os.getenv("GMI_MAX_RETRIES", ""),
        os.getenv("GMI_MAX_TOKENS", ""),
        os.getenv("GMI_TEMPERATURE", ""),
    )


def _llm_client_kwargs() -> dict:
    """Longer timeout + more retries for slow reasoning models (e.g. DeepSeek-R1) and flaky gateways."""
    try:
        timeout = float(os.getenv("GMI_TIMEOUT", "180"))
    except ValueError:
        timeout = 180.0
    try:
        max_retries = int(os.getenv("GMI_MAX_RETRIES", "6"))
    except ValueError:
        max_retries = 6
    return {"timeout": timeout, "max_retries": max(0, max_retries)}


def _llm_generation_kwargs() -> dict:
    """Keep generation compact to reduce long-running websocket sessions."""
    try:
        max_tokens = int(os.getenv("GMI_MAX_TOKENS", "700"))
    except ValueError:
        max_tokens = 700
    try:
        temperature = float(os.getenv("GMI_TEMPERATURE", "0.2"))
    except ValueError:
        temperature = 0.2
    return {
        "max_tokens": max(128, max_tokens),
        "temperature": min(1.0, max(0.0, temperature)),
    }


def _get_missing_vars(provider: str = "gmi", claude_api_key: str | None = None) -> list[str]:
    missing = []
    if provider == "claude":
        if not _clean_secret(claude_api_key or os.getenv("CLAUDE_API_KEY")):
            missing.append("CLAUDE_API_KEY")
        return missing
    if not os.getenv("GMI_API_KEY"):
        missing.append("GMI_API_KEY")
    if not os.getenv("GMI_ENDPOINT_URL"):
        missing.append("GMI_ENDPOINT_URL")
    return missing


def _build_crew(provider: str = "gmi", claude_api_key: str | None = None):
    cfg = _crew_config_key(provider, claude_api_key)
    if _crew_cache.get("config_key") == cfg and "continent_agents" in _crew_cache:
        return _crew_cache["continent_agents"], _crew_cache["director_agent"]

    from crewai import Agent, LLM

    _client = _llm_client_kwargs()
    _gen = _llm_generation_kwargs()

    if provider == "claude":
        _api_key = _clean_secret(claude_api_key or os.getenv("CLAUDE_API_KEY", ""))
        _model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest")
        llm = LLM(
            model=_model,
            provider="anthropic",
            api_key=_api_key,
            **_client,
            **_gen,
        )
        director_llm = LLM(
            model=_model,
            provider="anthropic",
            api_key=_api_key,
            **_client,
            **_gen,
        )
    else:
        _api_key = os.getenv("GMI_API_KEY", "")
        _base_url = os.getenv("GMI_ENDPOINT_URL", "")
        # Must match the model id from GET {GMI_ENDPOINT_URL}/models.
        _model = os.getenv("GMI_MODEL", "deepseek-ai/DeepSeek-R1")
        _json_mode = os.getenv("GMI_USE_JSON_RESPONSE_FORMAT", "").lower() in (
            "1",
            "true",
            "yes",
        )
        llm = LLM(
            model=_model,
            provider="openai",
            base_url=_base_url,
            api_key=_api_key,
            **_client,
            **_gen,
        )
        director_kwargs = {
            "model": _model,
            "provider": "openai",
            "base_url": _base_url,
            "api_key": _api_key,
            **_client,
            **_gen,
        }
        if _json_mode:
            director_kwargs["response_format"] = {"type": "json_object"}
        director_llm = LLM(**director_kwargs)

    continent_agents = {
        name: Agent(
            role=f"{name} Regional Council",
            goal=f"React to global scenarios as the unified voice of {name}, citing constituent nations.",
            backstory=get_continent_prompt(name),
            llm=llm,
            verbose=False,
        )
        for name in CONTINENT_NAMES
    }

    director_agent = Agent(
        role="Synthesizer Director",
        goal="Synthesize all continental reactions into a single analytical JSON brief.",
        backstory=SYNTHESIZER_DIRECTOR_PROMPT,
        llm=director_llm,
        verbose=False,
    )

    _crew_cache["config_key"] = cfg
    _crew_cache["continent_agents"] = continent_agents
    _crew_cache["director_agent"] = director_agent
    return continent_agents, director_agent


def run_simulation(
    user_scenario: str,
    provider: str = "gmi",
    claude_api_key: str | None = None,
) -> dict:
    from crewai import Task, Crew, Process

    provider = (provider or "gmi").lower().strip()
    if provider not in ("gmi", "claude"):
        provider = "gmi"

    missing = _get_missing_vars(provider=provider, claude_api_key=claude_api_key)
    if missing:
        return {
            "prediction": "Simulation unavailable — missing environment variables.",
            "report": f"The following variables are not set: {', '.join(missing)}. "
                      "Please configure them in your hosting dashboard or .env file.",
            "probability": 0,
            "links": [],
        }

    continent_agents, director_agent = _build_crew(
        provider=provider,
        claude_api_key=claude_api_key,
    )

    continent_tasks = []
    for name in CONTINENT_NAMES:
        task = Task(
            description=(
                f"The user has posed the following global 'What If' scenario:\n\n"
                f"\"{user_scenario}\"\n\n"
                f"As the {name} Regional Council, provide your region's reaction "
                f"in 2-3 short sentences, explicitly citing how specific constituent "
                f"nations and their red lines influenced the consensus."
            ),
            expected_output=(
                f"A concise 2-3 sentence reaction from the {name} Regional Council, "
                f"referencing specific nations and their red lines."
            ),
            agent=continent_agents[name],
        )
        continent_tasks.append(task)

    director_task = Task(
        description=(
            f"The user's 'What If' scenario is:\n\n"
            f"\"{user_scenario}\"\n\n"
            "You have received reactions from all six continental analysts above. "
            "Synthesize them into a single JSON object with the keys: "
            "prediction, report, probability, links."
        ),
        expected_output=(
            "A valid JSON object with keys: prediction (string), report (string), "
            "probability (integer 0-100), links (array of 3 URL strings)."
        ),
        agent=director_agent,
    )

    crew = Crew(
        agents=list(continent_agents.values()) + [director_agent],
        tasks=continent_tasks + [director_task],
        process=Process.sequential,
        verbose=False,
    )

    try:
        result = crew.kickoff()
        raw_output = result.raw
    except Exception as e:
        err = str(e)
        if provider == "claude":
            auth_hint = ""
            if "authentication_error" in err.lower() or "invalid authentication credentials" in err.lower():
                auth_hint = (
                    " Your Claude key appears invalid/revoked for this deployment environment. "
                    "Generate a new Anthropic API key, update CLAUDE_API_KEY in Railway/hosting variables, "
                    "then redeploy."
                )
            hint = (
                " Confirm CLAUDE_API_KEY is valid and CLAUDE_MODEL is supported by your Anthropic account. "
                "You can also try a different model (e.g. claude-3-5-sonnet-latest). "
                "If the error mentions 'Anthropic native provider not available', install Anthropic extras "
                "for CrewAI (e.g. `pip install \"crewai[anthropic]\"`), then redeploy."
                f"{auth_hint}"
            )
        else:
            hint = (
                " Confirm GMI_MODEL matches an id from GET /v1/models. "
                "Leave GMI_USE_JSON_RESPONSE_FORMAT unset unless your model supports JSON mode. "
                "If you see max_retries_exceeded or status 523, the upstream model may be overloaded or too slow: "
                "raise GMI_TIMEOUT (e.g. 300) and GMI_MAX_RETRIES (e.g. 8), or switch to a faster model "
                "such as deepseek-ai/DeepSeek-V3."
            )
        return {
            "prediction": "Simulation failed — LLM request was rejected.",
            "report": f"{err}\n\n{hint}",
            "probability": 0,
            "links": [],
        }

    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        start = raw_output.find("{")
        end = raw_output.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(raw_output[start:end])
        return {
            "prediction": "Unable to parse Director output.",
            "report": raw_output,
            "probability": 0,
            "links": [],
        }
