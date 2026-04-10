import os
import json

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from crewai import Agent, Task, Crew, Process

from prompts import get_continent_prompt, SYNTHESIZER_DIRECTOR_PROMPT

load_dotenv()

llm = ChatOpenAI(
    model="ZAI: GLM-5.1",
    base_url=os.getenv("GMI_ENDPOINT_URL"),
    api_key=os.getenv("GMI_API_KEY"),
)

CONTINENT_NAMES = [
    "North America",
    "South America",
    "Europe",
    "Africa",
    "Asia",
    "Oceania",
]

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
    llm=llm,
    verbose=False,
)


def run_simulation(user_scenario: str) -> dict:
    continent_tasks = []
    for name in CONTINENT_NAMES:
        task = Task(
            description=(
                f"The user has posed the following global 'What If' scenario:\n\n"
                f"\"{user_scenario}\"\n\n"
                f"As the {name} Regional Council, provide your region's reaction "
                f"in 2-3 paragraphs, explicitly citing how specific constituent "
                f"nations and their red lines influenced the consensus."
            ),
            expected_output=(
                f"A 2-3 paragraph reaction from the {name} Regional Council, "
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

    result = crew.kickoff()
    raw_output = result.raw

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
