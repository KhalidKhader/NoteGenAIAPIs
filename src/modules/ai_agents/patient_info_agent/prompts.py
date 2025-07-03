from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import List
from src.core.settings.logging import logger


def get_patient_info_prompt_en() -> ChatPromptTemplate:
    """
    Create a ChatPromptTemplate for patient information extraction with agent_scratchpad support.
    
    Returns:
        Configured ChatPromptTemplate object
    """
    template = """
You are a medical information extraction specialist. Your task is to extract specific patient demographic information from a medical conversation transcript.

EXTRACT THE FOLLOWING INFORMATION:
1. First name
2. Last name
3. Date of birth (format: YYYY-MM-DD, or null if not mentioned)
4. Gender (MALE/FEMALE/OTHER/null if not mentioned)

INSTRUCTIONS:
- Only extract information that is explicitly mentioned in the conversation
- Use null for any field that is not clearly stated
- Be very careful with dates - only extract if clearly stated
- For names, extract exactly as spoken (don't make assumptions)

EXAMPLES:

Example 1:
Doctor: "Good morning, Mrs. Sarah Johnson. I see you're here for your annual checkup."
Patient: "Yes, that's right. And yes, I'm okay with you recording this session."
Doctor: "Thank you. Can you confirm your date of birth for our records?"
Patient: "March 15th, 1985."

Response:
{{
  "firstName": "Sarah",
  "lastName": "Johnson", 
  "dateOfBirth": "1985-03-15",
  "gender": "FEMALE"
}}

Example 2:
Doctor: "Hello Mr. Robert Smith, how are you feeling today?"
Patient: "I'm doing well, doctor."
Doctor: "I need to record our session today, is that alright?"
Patient: "No, I'd prefer not to be recorded."

Response:
{{
  "firstName": "Robert",
  "lastName": "Smith",
  "dateOfBirth": null,
  "gender": "MALE"
}}

CONVERSATION TRANSCRIPT:
{transcript}

RESPONSE (JSON only, no explanation):
"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert AI assistant specializing in extracting structured patient demographic information from medical transcripts. Your task is to accurately identify and extract the requested information and format it as a JSON object. Adhere strictly to the requested fields and format. If information for a field is not present, use null."),
        ("human", template),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    
    logger.debug("Created ChatPromptTemplate for patient info extraction")
    return prompt


def get_prompt(language: str = "en") -> ChatPromptTemplate:
    """
    Get the appropriate prompt based on language.
    
    Args:
        language: Language code ('en' or 'fr')
        
    Returns:
        Configured ChatPromptTemplate object
    """
    if language.lower() == "fr":
        return get_patient_info_prompt_fr()
    else:
        return get_patient_info_prompt_en()


def get_patient_info_prompt_fr() -> ChatPromptTemplate:
    """
    Create a ChatPromptTemplate for patient information extraction in French with agent_scratchpad support.
    
    Returns:
        Configured ChatPromptTemplate object
    """
    template = """
Vous êtes un spécialiste de l'extraction d'informations médicales. Votre tâche est d'extraire des informations démographiques spécifiques du patient à partir d'une transcription de conversation médicale.

EXTRAIRE LES INFORMATIONS SUIVANTES:
1. Prénom
2. Nom de famille
3. Date de naissance (format: YYYY-MM-DD, ou null si non mentionné)
4. Sexe (MALE/FEMALE/OTHER/null si non mentionné)

INSTRUCTIONS:
- Extraire seulement les informations explicitement mentionnées dans la conversation
- Utiliser null pour tout champ qui n'est pas clairement énoncé
- Être très prudent avec les dates - extraire seulement si clairement énoncé
- Pour les noms, extraire exactement comme prononcé (ne pas faire d'hypothèses)

EXEMPLES:

Exemple 1:
Docteur: "Bonjour Madame Sarah Johnson. Je vois que vous êtes ici pour votre examen annuel."
Patient: "Oui, c'est exact. Et oui, je suis d'accord pour que vous enregistriez cette session."
Docteur: "Merci. Pouvez-vous confirmer votre date de naissance pour nos dossiers?"
Patient: "Le 15 mars 1985."

Réponse:
{{
  "firstName": "Sarah",
  "lastName": "Johnson",
  "dateOfBirth": "1985-03-15", 
  "gender": "FEMALE"
}}

Exemple 2:
Docteur: "Bonjour Monsieur Robert Smith, comment vous sentez-vous aujourd'hui?"
Patient: "Je vais bien, docteur."
Docteur: "Je dois enregistrer notre session aujourd'hui, est-ce que ça va?"
Patient: "Non, je préférerais ne pas être enregistré."

Réponse:
{{
  "firstName": "Robert",
  "lastName": "Smith",
  "dateOfBirth": null,
  "gender": "MALE"
}}

TRANSCRIPTION DE CONVERSATION:
{transcript}

RÉPONSE (JSON seulement, pas d'explication):
"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Vous êtes un assistant IA expert spécialisé dans l'extraction d'informations démographiques structurées des patients à partir de transcriptions médicales. Votre tâche est d'identifier et d'extraire avec précision les informations demandées et de les formater en tant qu'objet JSON. Respectez strictement les champs et le format demandés. Si l'information pour un champ n'est pas présente, utilisez null."),
        ("human", template),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    
    logger.debug("Created ChatPromptTemplate for patient info extraction (French)")
    return prompt


# Legacy support - keeping for backward compatibility
PATIENT_INFO_SYSTEM_PROMPT_TEXT = (
    "You are an expert AI assistant specializing in extracting structured "
    "patient demographic information from medical transcripts. Your task is "
    "to accurately identify and extract the requested information and format "
    "it as a JSON object. Adhere strictly to the requested fields and format. "
    "If information for a field is not present, use null."
)

PATIENT_INFO_SYSTEM_PROMPT = PATIENT_INFO_SYSTEM_PROMPT_TEXT

PATIENT_INFO_EXTRACTION_PROMPTS = {
    "en": get_patient_info_prompt_en(),
    "fr": get_patient_info_prompt_fr(),
} 