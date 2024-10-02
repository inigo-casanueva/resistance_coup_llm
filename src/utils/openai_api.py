import os

from openai import OpenAI
from src.models.players.llm_agent.params import llm_model

openai_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=openai_key)


def generate_text(system_prompt: str, user_prompt: str, model: str = llm_model) -> str:
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    return completion.choices[0].message.content