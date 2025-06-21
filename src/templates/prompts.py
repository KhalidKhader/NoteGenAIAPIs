"""
SOAP Generation Prompt Templates - Medical Best Practices Implementation

This module implements the comprehensive prompt patterns for SOAP note generation
following medical best practices and the system architecture requirements:

1. Section-specific prompt patterns (Subjective, Objective, Assessment, Plan)
2. Multi-language support (English/French)
3. Doctor preference integration
4. SNOMED Canadian edition alignment
5. Hallucination prevention through strict referencing
6. Line-number and substring tracking requirements
"""

from typing import Dict, List, Optional, Any
from enum import Enum

class PromptLanguage(str, Enum):
    """Supported languages for prompt generation."""
    ENGLISH = "en"
    FRENCH = "fr"

class SOAPSectionType(str, Enum):
    """SOAP section types for targeted prompt generation."""
    SUBJECTIVE = "subjective"
    OBJECTIVE = "objective"
    ASSESSMENT = "assessment"
    PLAN = "plan"
    KEYWORDS = "keywords"

# =============================================================================
# Base SOAP Prompt Template Structure
# =============================================================================

SOAP_BASE_TEMPLATE = """
You are a medical documentation specialist creating the {section} section of a SOAP note.

MEDICAL CONTEXT:
- Language: {language} ({language_full})
- Medical Standards: SNOMED Canadian Edition
- Specialty Focus: {specialty}
- Doctor ID: {doctor_id}

CONVERSATION EXCERPT (with line numbers):
{relevant_conversation_chunks}

PREVIOUS SOAP SECTIONS:
{previous_sections}

DOCTOR-SPECIFIC PREFERENCES:
{doctor_patterns}

SNOMED MAPPINGS AVAILABLE:
{snomed_mappings}

INSTRUCTIONS:
Generate the {section} section following these medical documentation standards:
1. Use medical terminology appropriate for {specialty}
2. Apply SNOMED codes where clinically relevant
3. Follow doctor's preferred terminology patterns
4. Maintain professional medical language standards
5. Include relevant measurements and clinical observations
6. CRITICAL: Reference exact line numbers where information was extracted
7. CRITICAL: Avoid hallucinations - only use information from provided conversation
8. CRITICAL: Generate in {language_full} language

REFERENCE REQUIREMENTS:
- Every clinical statement must reference source line numbers
- Use format: "Patient reports chest pain (Line 23-25)"
- Include direct quotes where appropriate: "Patient states 'sharp stabbing pain' (Line 24)"

{section_specific_instructions}

OUTPUT FORMAT:
{section_format}

QUALITY CHECKS:
- All information must be traceable to specific conversation lines
- Medical terms must align with provided SNOMED mappings
- Content must be in {language_full} language
- Apply doctor preference patterns consistently
"""

# =============================================================================
# Section-Specific Instructions
# =============================================================================

SUBJECTIVE_INSTRUCTIONS = {
    "en": """
SUBJECTIVE SECTION FOCUS:
Extract the patient's subjective experience including:
- Chief complaint and history of present illness
- Review of systems (ROS) 
- Past medical history relevant to current visit
- Social history and family history if mentioned
- Patient's own words and descriptions
- Symptoms as described by the patient

CRITICAL: Focus ONLY on what the patient reports, not clinical observations.
Include direct patient quotes where possible with line references.

Example Output:
"Chief Complaint: Patient presents with chest pain x 3 days (Line 12). 
Patient describes pain as 'sharp and stabbing, worse with movement' (Line 15-16).
Associated symptoms include shortness of breath (Line 18) and nausea (Line 20)."
""",
    "fr": """
FOCUS SECTION SUBJECTIVE:
Extraire l'expérience subjective du patient incluant:
- Plainte principale et histoire de la maladie actuelle
- Revue des systèmes (RDS)
- Antécédents médicaux pertinents à la consultation actuelle
- Histoire sociale et familiale si mentionnée
- Mots et descriptions du patient
- Symptômes tels que décrits par le patient

CRITIQUE: Se concentrer SEULEMENT sur ce que le patient rapporte, pas les observations cliniques.
Inclure des citations directes du patient avec références de ligne quand possible.

Exemple de sortie:
"Plainte principale: Patient se présente avec douleur thoracique x 3 jours (Ligne 12).
Patient décrit la douleur comme 'aiguë et lancinante, pire avec le mouvement' (Ligne 15-16).
Symptômes associés incluent essoufflement (Ligne 18) et nausée (Ligne 20)."
"""
}

OBJECTIVE_INSTRUCTIONS = {
    "en": """
OBJECTIVE SECTION FOCUS:
Extract objective clinical findings including:
- Vital signs and measurements (BP, HR, Temp, Weight, Height, O2 Sat)
- Physical examination findings by body system
- Laboratory results mentioned during encounter
- Diagnostic test results discussed
- Clinical observations by healthcare provider
- Imaging findings if discussed

CRITICAL: Focus ONLY on measurable, observable data and clinical findings.
Exclude patient's subjective reports.

Example Output:
"Vital Signs: BP 140/90 mmHg (Line 45), HR 82 bpm (Line 46), Temp 37.2°C (Line 47)
Physical Exam: Cardiovascular - Regular rate and rhythm, no murmurs detected (Line 52-53)
Respiratory - Clear to auscultation bilaterally (Line 55)"
""",
    "fr": """
FOCUS SECTION OBJECTIVE:
Extraire les trouvailles cliniques objectives incluant:
- Signes vitaux et mesures (TA, FC, Temp, Poids, Taille, Sat O2)
- Trouvailles d'examen physique par système corporel
- Résultats de laboratoire mentionnés durant la rencontre
- Résultats de tests diagnostiques discutés
- Observations cliniques par le fournisseur de soins
- Trouvailles d'imagerie si discutées

CRITIQUE: Se concentrer SEULEMENT sur données mesurables, observables et trouvailles cliniques.
Exclure les rapports subjectifs du patient.

Exemple de sortie:
"Signes vitaux: TA 140/90 mmHg (Ligne 45), FC 82 bpm (Ligne 46), Temp 37.2°C (Ligne 47)
Examen physique: Cardiovasculaire - Rythme et fréquence réguliers, aucun souffle détecté (Ligne 52-53)
Respiratoire - Clair à l'auscultation bilatéralement (Ligne 55)"
"""
}

ASSESSMENT_INSTRUCTIONS = {
    "en": """
ASSESSMENT SECTION FOCUS:
Extract clinical assessment including:
- Primary diagnosis with appropriate SNOMED codes
- Secondary diagnoses if mentioned
- Clinical impressions and differential diagnoses
- Assessment of symptom severity and progression
- Risk stratification if discussed
- Clinical reasoning provided by healthcare provider

CRITICAL: Include SNOMED codes for all diagnoses when available.
Focus on provider's clinical judgment and diagnostic reasoning.

Example Output:
"Primary Diagnosis: 
1. Hypertension, uncontrolled (SNOMED: 38341003) - Based on BP readings 140/90 mmHg (Line 45) and patient history (Line 12-15)

Secondary Diagnoses:
2. Chest pain, unspecified (SNOMED: 29857009) - Requires further evaluation given atypical presentation (Line 60-62)"
""",
    "fr": """
FOCUS SECTION ÉVALUATION:
Extraire l'évaluation clinique incluant:
- Diagnostic primaire avec codes SNOMED appropriés
- Diagnostics secondaires si mentionnés
- Impressions cliniques et diagnostics différentiels
- Évaluation de la sévérité et progression des symptômes
- Stratification du risque si discutée
- Raisonnement clinique fourni par le fournisseur de soins

CRITIQUE: Inclure les codes SNOMED pour tous diagnostics quand disponibles.
Se concentrer sur le jugement clinique et raisonnement diagnostique du fournisseur.

Exemple de sortie:
"Diagnostic primaire:
1. Hypertension, non contrôlée (SNOMED: 38341003) - Basé sur lectures TA 140/90 mmHg (Ligne 45) et histoire du patient (Ligne 12-15)

Diagnostics secondaires:
2. Douleur thoracique, non spécifiée (SNOMED: 29857009) - Nécessite évaluation supplémentaire donnée présentation atypique (Ligne 60-62)"
"""
}

PLAN_INSTRUCTIONS = {
    "en": """
PLAN SECTION FOCUS:
Extract treatment plan including:
- Medications prescribed or adjusted (name, dosage, frequency, duration)
- Procedures recommended or performed
- Follow-up appointments scheduled
- Patient education provided
- Lifestyle modifications discussed
- Referrals to specialists
- Additional testing ordered

CRITICAL: Include specific dosages, frequencies, and instructions.
Capture all actionable items discussed.

Example Output:
"Medications:
1. Lisinopril 10mg PO daily - Start immediately for hypertension management (Line 78-79)
2. ASA 81mg PO daily - Cardioprotective, discussed benefits/risks (Line 82)

Follow-up:
- Return visit in 2 weeks to reassess BP control (Line 85)
- Laboratory: Basic metabolic panel in 1 week (Line 87)

Patient Education:
- Dietary sodium restriction <2g daily discussed (Line 90)
- Home BP monitoring technique demonstrated (Line 92-93)"
""",
    "fr": """
FOCUS SECTION PLAN:
Extraire le plan de traitement incluant:
- Médicaments prescrits ou ajustés (nom, dosage, fréquence, durée)
- Procédures recommandées ou effectuées
- Rendez-vous de suivi planifiés
- Éducation patient fournie
- Modifications de style de vie discutées
- Références aux spécialistes
- Tests additionnels ordonnés

CRITIQUE: Inclure dosages spécifiques, fréquences et instructions.
Capturer tous les éléments d'action discutés.

Exemple de sortie:
"Médicaments:
1. Lisinopril 10mg PO quotidien - Commencer immédiatement pour gestion hypertension (Ligne 78-79)
2. AAS 81mg PO quotidien - Cardioprotecteur, bénéfices/risques discutés (Ligne 82)

Suivi:
- Visite de retour dans 2 semaines pour réévaluer contrôle TA (Ligne 85)
- Laboratoire: Panel métabolique de base dans 1 semaine (Ligne 87)

Éducation patient:
- Restriction sodium alimentaire <2g quotidien discutée (Ligne 90)
- Technique monitoring TA domicile démontrée (Ligne 92-93)"
"""
}

KEYWORDS_INSTRUCTIONS = {
    "en": """
KEYWORDS/MEASUREMENTS SECTION FOCUS:
Extract key medical terms and measurements including:
- Primary medical conditions and diagnoses
- Vital signs and measurements
- Medications mentioned
- Procedures discussed
- Key symptoms and findings
- SNOMED codes for major conditions

CRITICAL: Provide structured keyword extraction with categories.

Example Output:
"Medical Conditions: Hypertension (SNOMED: 38341003), Chest pain (SNOMED: 29857009)
Vital Signs: BP 140/90 mmHg, HR 82 bpm, Temp 37.2°C
Medications: Lisinopril 10mg daily, ASA 81mg daily
Symptoms: Chest pain, Shortness of breath, Nausea
Procedures: Blood pressure monitoring, Physical examination"
""",
    "fr": """
FOCUS SECTION MOTS-CLÉS/MESURES:
Extraire termes médicaux clés et mesures incluant:
- Conditions médicales primaires et diagnostics
- Signes vitaux et mesures
- Médicaments mentionnés
- Procédures discutées
- Symptômes et trouvailles clés
- Codes SNOMED pour conditions majeures

CRITIQUE: Fournir extraction de mots-clés structurée avec catégories.

Exemple de sortie:
"Conditions médicales: Hypertension (SNOMED: 38341003), Douleur thoracique (SNOMED: 29857009)
Signes vitaux: TA 140/90 mmHg, FC 82 bpm, Temp 37.2°C
Médicaments: Lisinopril 10mg quotidien, AAS 81mg quotidien
Symptômes: Douleur thoracique, Essoufflement, Nausée
Procédures: Monitoring pression artérielle, Examen physique"
"""
}

# =============================================================================
# Output Format Templates
# =============================================================================

SECTION_OUTPUT_FORMATS = {
    "subjective": {
        "en": """**SUBJECTIVE SECTION**
Chief Complaint: [Patient's primary concern with line reference]
History of Present Illness: [Detailed patient narrative with line references]  
Review of Systems: [Relevant positive/negative findings with line references]
Past Medical History: [Relevant past conditions with line references]
Medications: [Current medications mentioned by patient with line references]
Allergies: [Known allergies with line references]
Social History: [Relevant social factors with line references]""",
        
        "fr": """**SECTION SUBJECTIVE**
Plainte principale: [Préoccupation primaire du patient avec référence de ligne]
Histoire de la maladie actuelle: [Narrative détaillée du patient avec références de ligne]
Revue des systèmes: [Trouvailles positives/négatives pertinentes avec références de ligne]
Antécédents médicaux: [Conditions passées pertinentes avec références de ligne]
Médicaments: [Médicaments actuels mentionnés par patient avec références de ligne]
Allergies: [Allergies connues avec références de ligne]
Histoire sociale: [Facteurs sociaux pertinents avec références de ligne]"""
    },
    
    "objective": {
        "en": """**OBJECTIVE SECTION**
Vital Signs: [All measurements with line references]
General Appearance: [Overall patient presentation with line references]
Physical Examination:
  - Cardiovascular: [Heart exam findings with line references]
  - Respiratory: [Lung exam findings with line references]
  - HEENT: [Head, eye, ear, nose, throat findings with line references]
  - Abdomen: [Abdominal exam findings with line references]
  - Extremities: [Extremity findings with line references]
  - Neurological: [Neuro exam findings with line references]
Laboratory/Diagnostic Results: [Test results discussed with line references]""",
        
        "fr": """**SECTION OBJECTIVE**
Signes vitaux: [Toutes mesures avec références de ligne]
Apparence générale: [Présentation globale du patient avec références de ligne]
Examen physique:
  - Cardiovasculaire: [Trouvailles examen cardiaque avec références de ligne]
  - Respiratoire: [Trouvailles examen pulmonaire avec références de ligne]
  - HEENT: [Trouvailles tête, œil, oreille, nez, gorge avec références de ligne]
  - Abdomen: [Trouvailles examen abdominal avec références de ligne]
  - Extrémités: [Trouvailles extrémités avec références de ligne]
  - Neurologique: [Trouvailles examen neuro avec références de ligne]
Résultats laboratoire/diagnostique: [Résultats tests discutés avec références de ligne]"""
    },
    
    "assessment": {
        "en": """**ASSESSMENT SECTION**
Primary Diagnosis:
1. [Diagnosis name] (SNOMED: [code]) - [Clinical reasoning with line references]

Secondary Diagnoses:
2. [Diagnosis name] (SNOMED: [code]) - [Clinical reasoning with line references]
3. [Additional diagnoses as needed]

Clinical Impression: [Overall clinical assessment with line references]
Risk Stratification: [Risk assessment if applicable with line references]""",
        
        "fr": """**SECTION ÉVALUATION**
Diagnostic primaire:
1. [Nom diagnostic] (SNOMED: [code]) - [Raisonnement clinique avec références de ligne]

Diagnostics secondaires:
2. [Nom diagnostic] (SNOMED: [code]) - [Raisonnement clinique avec références de ligne]
3. [Diagnostics additionnels au besoin]

Impression clinique: [Évaluation clinique globale avec références de ligne]
Stratification du risque: [Évaluation risque si applicable avec références de ligne]"""
    },
    
    "plan": {
        "en": """**PLAN SECTION**
Medications:
1. [Medication name] [dose] [route] [frequency] - [Indication with line references]
2. [Additional medications as needed]

Procedures/Interventions:
- [Procedure/intervention recommended with line references]

Follow-up:
- [Follow-up appointments/timeline with line references]

Monitoring:
- [Monitoring requirements with line references]

Patient Education:
- [Education provided with line references]

Additional Testing:
- [Tests ordered with line references]

Referrals:
- [Specialist referrals with line references]""",
        
        "fr": """**SECTION PLAN**
Médicaments:
1. [Nom médicament] [dose] [voie] [fréquence] - [Indication avec références de ligne]
2. [Médicaments additionnels au besoin]

Procédures/Interventions:
- [Procédure/intervention recommandée avec références de ligne]

Suivi:
- [Rendez-vous de suivi/chronologie avec références de ligne]

Monitoring:
- [Exigences de monitoring avec références de ligne]

Éducation patient:
- [Éducation fournie avec références de ligne]

Tests additionnels:
- [Tests ordonnés avec références de ligne]

Références:
- [Références spécialistes avec références de ligne]"""
    },
    
    "keywords": {
        "en": """**KEYWORDS/MEASUREMENTS SECTION**
Primary Conditions: [Main diagnoses with SNOMED codes]
Vital Signs: [All measurements taken]
Medications: [All medications discussed]
Symptoms: [Key symptoms mentioned]
Procedures: [Procedures performed/discussed]
Laboratory: [Lab tests mentioned]
Follow-up: [Key follow-up items]""",
        
        "fr": """**SECTION MOTS-CLÉS/MESURES**
Conditions primaires: [Diagnostics principaux avec codes SNOMED]
Signes vitaux: [Toutes mesures prises]
Médicaments: [Tous médicaments discutés]
Symptômes: [Symptômes clés mentionnés]
Procédures: [Procédures effectuées/discutées]
Laboratoire: [Tests labo mentionnés]
Suivi: [Éléments de suivi clés]"""
    }
}

# =============================================================================
# Multi-Language Support
# =============================================================================

LANGUAGE_MAPPINGS = {
    "en": "English",
    "fr": "French (Français)"
}

# =============================================================================
# Prompt Generation Functions
# =============================================================================

def generate_soap_section_prompt(
    section_type: SOAPSectionType,
    language: PromptLanguage = PromptLanguage.ENGLISH,
    specialty: str = "General Medicine",
    doctor_id: str = "unknown",
    relevant_chunks: List[str] = None,
    previous_sections: Dict[str, str] = None,
    doctor_preferences: Dict[str, str] = None,
    snomed_mappings: List[Dict[str, Any]] = None
) -> str:
    """
    Generate section-specific SOAP prompt with all context.
    
    Args:
        section_type: Type of SOAP section to generate
        language: Target language for generation
        specialty: Medical specialty context
        doctor_id: Doctor identifier for preference application
        relevant_chunks: Conversation chunks with line numbers
        previous_sections: Previously generated SOAP sections
        doctor_preferences: Doctor's terminology preferences
        snomed_mappings: Available SNOMED code mappings
    
    Returns:
        Complete prompt string for section generation
    """
    # Get section-specific instructions
    if section_type == SOAPSectionType.SUBJECTIVE:
        section_instructions = SUBJECTIVE_INSTRUCTIONS.get(language, SUBJECTIVE_INSTRUCTIONS["en"])
    elif section_type == SOAPSectionType.OBJECTIVE:
        section_instructions = OBJECTIVE_INSTRUCTIONS.get(language, OBJECTIVE_INSTRUCTIONS["en"])
    elif section_type == SOAPSectionType.ASSESSMENT:
        section_instructions = ASSESSMENT_INSTRUCTIONS.get(language, ASSESSMENT_INSTRUCTIONS["en"])
    elif section_type == SOAPSectionType.PLAN:
        section_instructions = PLAN_INSTRUCTIONS.get(language, PLAN_INSTRUCTIONS["en"])
    else:  # keywords
        section_instructions = KEYWORDS_INSTRUCTIONS.get(language, KEYWORDS_INSTRUCTIONS["en"])
    
    # Get output format
    section_format = SECTION_OUTPUT_FORMATS.get(section_type.value, {}).get(language, "")
    
    # Format conversation chunks
    chunks_text = "\n".join(relevant_chunks or ["No relevant conversation chunks available"])
    
    # Format previous sections
    previous_text = ""
    if previous_sections:
        previous_text = "\n".join([f"{k.upper()}: {v}" for k, v in previous_sections.items()])
    else:
        previous_text = "No previous sections available"
    
    # Format doctor preferences
    preferences_text = ""
    if doctor_preferences:
        preference_mappings = "\n".join([
            f"- Use '{preferred}' instead of '{original}'"
            for original, preferred in doctor_preferences.items()
        ])
        preferences_text = DOCTOR_PREFERENCE_TEMPLATE.format(
            preference_mappings=preference_mappings,
            hypertension_preference=doctor_preferences.get("hypertension", "hypertension")
        )
    else:
        preferences_text = "No specific preferences for this doctor"
    
    # Format SNOMED mappings
    snomed_text = ""
    if snomed_mappings:
        snomed_text = "\n".join([
            f"- {mapping.get('term', 'Unknown')}: SNOMED {mapping.get('code', 'N/A')} - {mapping.get('preferred_term', 'N/A')}"
            for mapping in snomed_mappings
        ])
    else:
        snomed_text = "No SNOMED mappings available - use clinical judgment"
    
    # Generate complete prompt
    prompt = SOAP_BASE_TEMPLATE.format(
        section=section_type.value.upper(),
        language=language,
        language_full=LANGUAGE_MAPPINGS.get(language, "English"),
        specialty=specialty,
        doctor_id=doctor_id,
        relevant_conversation_chunks=chunks_text,
        previous_sections=previous_text,
        doctor_patterns=preferences_text,
        snomed_mappings=snomed_text,
        section_specific_instructions=section_instructions,
        section_format=section_format
    )
    
    return prompt

def generate_multi_template_prompt(
    template_type: str,
    section_type: str,
    base_prompt: str,
    language: PromptLanguage = PromptLanguage.ENGLISH,
    doctor_preferences: Dict[str, str] = None
) -> str:
    """
    Generate prompt for non-SOAP templates (Visit Summary, Referral, Custom).
    
    Args:
        template_type: Type of template (visit_summary, referral, custom)
        section_type: Section within template
        base_prompt: Base prompt from NestJS
        language: Target language
        doctor_preferences: Doctor preferences to apply
    
    Returns:
        Enhanced prompt for template generation
    """
    template_enhancement = f"""
TEMPLATE TYPE: {template_type.upper()}
SECTION: {section_type.upper()}
LANGUAGE: {LANGUAGE_MAPPINGS.get(language, "English")}

MEDICAL REQUIREMENTS:
- Follow medical documentation standards
- Include precise line number references
- Apply SNOMED codes where appropriate
- Use professional medical terminology
- Generate in {LANGUAGE_MAPPINGS.get(language, "English")} language

DOCTOR PREFERENCES:
{_format_preferences(doctor_preferences)}

BASE PROMPT:
{base_prompt}

CRITICAL REQUIREMENTS:
1. Every statement must reference source line numbers
2. Use format: "Patient reports X (Line N)" or "Clinical finding Y (Lines N-M)"
3. No hallucinations - only use provided conversation content
4. Apply doctor preferences consistently
5. Include relevant SNOMED codes for medical terms
"""
    
    return template_enhancement

def _format_preferences(preferences: Dict[str, str] = None) -> str:
    """Format doctor preferences for prompt inclusion."""
    if not preferences:
        return "No specific preferences for this doctor"
    
    return "\n".join([
        f"- Use '{preferred}' instead of '{original}'"
        for original, preferred in preferences.items()
    ])

# =============================================================================
# Validation and Quality Assurance Prompts
# =============================================================================

FACTUAL_CONSISTENCY_VALIDATION_PROMPT = """
You are a meticulous clinical fact-checker AI. Your task is to validate the factual consistency of a generated medical note section against the original conversation transcript.

**Generated Content:**
---
{generated_content}
---

**Source Transcript Chunks:**
---
{source_chunks}
---

**Validation Instructions:**
1.  **Verify Every Claim:** Each statement in the "Generated Content" MUST be directly supported by evidence in the "Source Transcript Chunks".
2.  **Check Line References:** If line numbers are cited, confirm they are accurate.
3.  **Identify Unsupported Information:** Flag any information present in the generated content that is NOT supported by the source transcript. This is a hallucination.

**Response Format (JSON object only):**
You MUST provide your response as a single JSON object. Do not include any other text or markdown formatting.

{{
  "factualConsistencyScore": <A score from 1 (completely fabricated) to 10 (perfectly consistent)>,
  "hallucinationRisk": "<LOW, MEDIUM, or HIGH>",
  "issuesFound": [
    {{
      "statement": "<The specific statement in the generated content that has an issue>",
      "issue": "<A brief description of the issue (e.g., 'Not supported by transcript', 'Incorrect line reference', 'Contradicts source')>"
    }}
  ],
  "justification": "<A brief summary of your reasoning for the score and risk assessment>"
}}
"""

SNOMED_VALIDATION_PROMPT = """
Validate SNOMED code usage in the following medical content:

MEDICAL CONTENT:
{content}

AVAILABLE SNOMED MAPPINGS:
{snomed_mappings}

VALIDATION REQUIREMENTS:
1. All SNOMED codes must be from Canadian edition
2. Codes must accurately represent the medical concepts
3. Preferred terms should be used when available
4. Both English and French terms should be supported

Provide validation results and corrections if needed.
"""

SECTION_GENERATION_SYSTEM_PROMPT_TEMPLATE = """
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
"""

SECTION_GENERATION_USER_PROMPT_TEMPLATE = """
**Generate the '{section_name}' section.**

**User Prompt for this section:**
{section_prompt}

---

**Context:**

**1. Conversation Transcript (with line numbers):**
{conversation_context_text}

---

**Your Output (JSON object only):**
"""

# =============================================================================
# Export All Templates
# =============================================================================

MEDICAL_TERM_EXTRACTION_SYSTEM_PROMPT = "You are an expert medical terminologist. Your task is to identify and extract all potential medical terms, symptoms, diagnoses, medications, and procedures from the provided text."

MEDICAL_TERM_EXTRACTION_USER_PROMPT_TEMPLATE = """
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

__all__ = [
    "PromptLanguage",
    "SOAPSectionType", 
    "generate_soap_section_prompt",
    "SOAP_BASE_TEMPLATE",
    "SUBJECTIVE_INSTRUCTIONS",
    "OBJECTIVE_INSTRUCTIONS", 
    "ASSESSMENT_INSTRUCTIONS",
    "PLAN_INSTRUCTIONS",
    "KEYWORDS_INSTRUCTIONS",
    "SECTION_OUTPUT_FORMATS",
    "MEDICAL_TERM_EXTRACTION_SYSTEM_PROMPT",
    "MEDICAL_TERM_EXTRACTION_USER_PROMPT_TEMPLATE",
    "FACTUAL_CONSISTENCY_VALIDATION_PROMPT",
    "SECTION_GENERATION_SYSTEM_PROMPT_TEMPLATE",
    "SECTION_GENERATION_USER_PROMPT_TEMPLATE",
]
