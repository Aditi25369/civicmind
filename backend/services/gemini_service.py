"""
Gemini service using new google-genai SDK (supports AQ. auth keys)
"""
import os
import json
from typing import Optional
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY)

DOMAIN_PROMPTS = {
    "transport": "Focus on: traffic flow, public transit performance, route optimization, commute times, accident hotspots, and infrastructure needs.",
    "health":    "Focus on: healthcare access, disease prevalence, clinic utilization, wellness program reach, and community health indicators.",
    "education": "Focus on: enrollment trends, literacy rates, school resource allocation, workforce development, and economic mobility.",
    "community": "Focus on: citizen satisfaction, service accessibility, feedback sentiment, inclusivity metrics, and public engagement.",
    "general":   "Address any smart city topic across all domains.",
}

SYSTEM_INSTRUCTION = """You are CivicMind, an AI Decision Intelligence assistant
for Smart City operations. You help city officials, planners, and community
members make data-driven decisions about transport, health, education, and
community services.
Always:
- Give clear, actionable recommendations
- Cite data when available
- Flag anomalies or urgent issues prominently
- Suggest follow-up questions to deepen analysis
- Keep answers concise but complete"""


async def query_gemini(
    message: str,
    domain: str,
    history: list,
    rag_context: Optional[str] = None,
) -> dict:
    domain_ctx = DOMAIN_PROMPTS.get(domain, DOMAIN_PROMPTS["general"])

    rag_section = ""
    if rag_context:
        rag_section = f"\n\nRelevant documents:\n{rag_context}\n"

    full_prompt = f"""{SYSTEM_INSTRUCTION}

Domain context: {domain_ctx}
{rag_section}
User question: {message}

Respond with a JSON object:
{{
  "answer": "<your detailed answer>",
  "suggested_actions": ["<action1>", "<action2>"],
  "follow_up_questions": ["<q1>", "<q2>", "<q3>"]
}}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=full_prompt,
    )

    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = {
            "answer": response.text,
            "suggested_actions": [],
            "follow_up_questions": [],
        }

    return parsed


async def search_documents(query: str, domain: str) -> tuple:
    return "", []


async def generate_insights(domain: str, data_summary: str) -> dict:
    prompt = f"""Analyze this {domain} data summary and generate insights:

{data_summary}

Respond with JSON:
{{
  "insights": [
    {{
      "title": "<short title>",
      "description": "<2-3 sentence explanation>",
      "severity": "info|warning|critical",
      "metric": "<metric name or null>",
      "value": <number or null>,
      "trend": "up|down|stable|null"
    }}
  ],
  "summary": "<1 paragraph executive summary>"
}}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    return json.loads(text)