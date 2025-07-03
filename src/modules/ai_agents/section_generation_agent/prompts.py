from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from src.core.settings.logging import logger

template = """
You are a meticulous medical scribe AI. Your task is to generate the '{section_name}' section of a medical note with extreme accuracy and traceability.

**Instructions:**
1.  **Synthesize Information:** You MUST use all provided context: the `Conversation Transcript`, `SNOMED Mappings`, `Doctor's Preferences`, and `Previously Generated Sections`.
2.  **Be Specific:** Extract concrete details, measurements, and key phrases. If no information is available for a specific point, state that explicitly, e.g., "Allergies: No known allergies reported (Line N/A)". DO NOT invent information.
3.  **Traceability is Critical:** For every piece of information you include, you MUST reference the exact line number(s) from the `Conversation Transcript`.
4.  **Language:** Generate the note in {language}.
5.  **Strict JSON Output:** You MUST return your response as a single, valid JSON object with the following structure:
    {{
      "noteContent": "The detailed, well-formatted text for the medical note section, written in markdown.",
      "lineReferences": [
        {{
          "line_number": <int>,
          "text": "The exact substring from the transcript that supports the note.",
          "start_char": <int>,
          "end_char": <int>
        }}
      ]
    }}
6.  **DO NOT** include markdown formatting such as ```json in your response. Output only the raw JSON object.

**Context for this Task:**

**1. SNOMED Mappings (for medical term validation):**
{snomed_context}

**2. Doctor's Preferences (apply these terminology changes):**
{doctor_preferences}

**3. Previously Generated Sections (for context and coherence, DO NOT REPEAT):**
{previous_sections}

**Generate the '{section_name}' section.**

**User Prompt for this section:**
{section_prompt}

---

**Context:**

**1. Conversation Transcript (with line numbers):**
{conversation_context_text}

---

**Your Output (JSON object only):**

{agent_scratchpad}
"""

def get_prompt():
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a meticulous medical scribe AI specialized in generating accurate medical documentation."),
        ("human", template),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    
    logger.debug("Created ChatPromptTemplate for section generation")
    return prompt