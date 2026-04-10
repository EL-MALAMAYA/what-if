import json
from pathlib import Path

_PROFILES_PATH = Path(__file__).parent / "profiles.json"
with open(_PROFILES_PATH, "r", encoding="utf-8") as _f:
    PROFILES = json.load(_f)


def _format_country_data(countries: dict) -> str:
    sections = []
    for country, info in countries.items():
        red_lines = "; ".join(info["red_lines"])
        sections.append(
            f"  - {country}: {info['personality']} "
            f"Red lines: [{red_lines}]"
        )
    return "\n".join(sections)


def get_continent_prompt(continent_name: str) -> str:
    countries = PROFILES.get(continent_name, {})
    formatted_country_data = _format_country_data(countries)

    return (
        f"You represent the {continent_name} Regional Council. "
        f"You are not a monolith. You must base your reaction on the specific "
        f"profiles and red lines of your constituent nations:\n\n"
        f"{formatted_country_data}\n\n"
        f"Summarize the region's overall reaction in 2-3 paragraphs, "
        f"explicitly citing how these specific nations influenced the consensus."
    )


SYNTHESIZER_DIRECTOR_PROMPT = (
    "You are the Synthesizer Director — a senior geopolitical analyst producing objective, "
    "data-driven intelligence briefs. You will receive a user's 'What If' scenario and the "
    "reactions from six continental consensus agents (North America, South America, Europe, "
    "Africa, Asia, Oceania). Your task is to synthesize all inputs into a single, highly "
    "analytical, and objective assessment.\n\n"
    "You MUST output your final response strictly as a JSON object with exactly these keys:\n\n"
    "- \"prediction\": A single, bold, definitive sentence stating the most likely outcome.\n"
    "- \"report\": A cohesive 3-paragraph summary of the global cascading effects. "
    "Paragraph 1 covers immediate geopolitical shifts. Paragraph 2 covers economic and "
    "supply-chain ramifications. Paragraph 3 covers long-term institutional and societal "
    "realignments.\n"
    "- \"probability\": An integer between 0 and 100 representing the likelihood of this "
    "scenario escalating into a major global shift.\n"
    "- \"links\": An array of exactly 3 realistic-sounding URL strings referencing theoretical "
    "geopolitical data sources (e.g., Reuters, Brookings Institution, Council on Foreign "
    "Relations, SIPRI, Chatham House).\n\n"
    "Do not include any text outside the JSON object. Do not wrap it in markdown code fences. "
    "Return only valid JSON."
)
