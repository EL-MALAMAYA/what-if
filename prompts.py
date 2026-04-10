import json
from pathlib import Path

_PROFILES_PATH = Path(__file__).parent / "profiles.json"
with open(_PROFILES_PATH, "r", encoding="utf-8") as _f:
    _DATA = json.load(_f)

COUNTRIES = _DATA["countries"]
RELATIONS = _DATA["relations"]

_COUNTRIES_BY_REGION: dict[str, list[dict]] = {}
for _c in COUNTRIES:
    _COUNTRIES_BY_REGION.setdefault(_c["region"], []).append(_c)


def _format_country_profile(country: dict) -> str:
    leader = country["leader"]
    red_lines = "; ".join(country["red_lines"])
    core = "; ".join(country["core_interests"])
    events = " | ".join(
        f"{e['event']} ({e['type']}, impact: {e['impact']})"
        for e in country["recent_events"]
    )
    statements = " | ".join(country["official_statements"])

    return (
        f"  {country['country']} — Leader: {leader['name']} ({leader['title']})\n"
        f"    Core interests: {core}\n"
        f"    Red lines: [{red_lines}]\n"
        f"    Recent events: {events}\n"
        f"    Official stance: {statements}\n"
        f"    Decision style: {country['decision_style']}"
    )


def _format_relations(region_countries: list[dict]) -> str:
    names = {c["country"] for c in region_countries}
    relevant = [
        r for r in RELATIONS
        if r["from"] in names or r["to"] in names
    ]
    if not relevant:
        return "  (No mapped relations)"
    return "\n".join(
        f"  {r['from']} → {r['to']}: {r['type']}"
        for r in relevant
    )


def get_continent_prompt(continent_name: str) -> str:
    region_countries = _COUNTRIES_BY_REGION.get(continent_name, [])

    profiles_block = "\n\n".join(
        _format_country_profile(c) for c in region_countries
    )
    relations_block = _format_relations(region_countries)

    return (
        f"You represent the {continent_name} Regional Council. "
        f"Base your reaction on the following rich profiles and relationship "
        f"dynamics of your constituent nations:\n\n"
        f"=== NATION PROFILES ===\n{profiles_block}\n\n"
        f"=== KEY RELATIONS ===\n{relations_block}\n\n"
        f"Explicitly weigh their recent events, core interests, and active "
        f"alliances/hostilities when forming the region's consensus. "
        f"Summarize the region's overall reaction in 2-3 paragraphs, "
        f"citing how specific nations influenced the outcome."
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
