from typing import List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from src.core.settings.logging import logger


def get_prompt() -> ChatPromptTemplate:
    """
    Create a ChatPromptTemplate for medical terms extraction with agent_scratchpad support.
    
    Returns:
        Configured ChatPromptTemplate object
    """
    template = """
From the following text, which is a snippet from a doctor-patient conversation, please extract all potential medical terms.
Be comprehensive. Include specific diagnoses, symptoms (even if described in layperson's terms), medications (brand and generic), medical tests, procedures, and anatomical references.
If a patient says 'my stomach hurts,' extract 'stomach pain'. If they mention feeling 'sad', extract 'sadness' or 'depressed mood'.

Return the terms as a JSON list of strings. For example: ["hypertension", "Lisinopril", "CBC", "headache", "abdominal pain"].
Do not include any explanation or surrounding text. Your output must be ONLY the JSON list.
The text is in {language}. The extracted terms should also be in {language}.

Text:
---
{text}
---
"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert medical terminologist. Your task is to identify and extract all potential medical terms, symptoms, diagnoses, medications, and procedures from the provided text."),
        ("human", template),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    
    logger.debug("Created ChatPromptTemplate for medical terms extraction")
    return prompt


# Legacy support - keeping for backward compatibility
MEDICAL_TERM_EXTRACTION_SYSTEM_PROMPT = "You are an expert medical terminologist. Your task is to identify and extract all potential medical terms, symptoms, diagnoses, medications, and procedures from the provided text."

