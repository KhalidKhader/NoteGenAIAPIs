from typing import List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from src.core.settings.logging import logger


def get_prompt() -> ChatPromptTemplate:
    """
    Create a ChatPromptTemplate for recording consent detection with agent_scratchpad support.
    
    Returns:
        Configured ChatPromptTemplate object
    """
    template = """
Analyze the following text from a patient:
"{patient_text}"

Does this text contain a clear statement of consent to be recorded?

Example 1:
Patient text: "Yes, that's fine."
Your response: CONSENT

Example 2:
Patient text: "I have a sore throat."
Your response: NO_CONSENT

Example 3:
Patient text: "je suis d'accord pour l'enregistrement"
Your response: CONSENT
"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an AI assistant specialized in analyzing medical conversations. Your task is to determine if a patient is giving explicit consent to record the conversation. Respond with only 'CONSENT' if they do, and 'NO_CONSENT' if they do not."),
        ("human", template),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    
    logger.debug("Created ChatPromptTemplate for recording consent detection")
    return prompt


# Legacy support - keeping for backward compatibility
RECORDING_CONSENT_SYSTEM_PROMPT_TEXT = (
    "You are an AI assistant specialized in analyzing medical conversations. "
    "Your task is to determine if a patient is giving explicit consent to "
    "record the conversation. Respond with only 'CONSENT' if they do, and "
    "'NO_CONSENT' if they do not."
)