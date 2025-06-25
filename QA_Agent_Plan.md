# QA Agent Implementation Plan

## Overview

This document outlines the phased engineering plan for building an internal **Validator Agent (QA Agent)**. The agent's function is to be an integral part of the note generation pipeline, ensuring the quality, accuracy, and safety of all AI-generated medical documentation through a series of internal service checks.

This agent will not expose new API endpoints. Instead, it will be invoked internally after content generation and before the result is returned to the calling service (NestJS).

## Phased Implementation Strategy

The implementation is broken into four distinct phases. Each phase enhances the validation capabilities of the core pipeline. Estimated times assume focused development using an AI assistant.

---

### Phase 1: Foundational Validation - Automated Grounding and Integrity Checks

- **Estimated Implementation Time:** **1 - 2 hours**

**Objective:** Integrate a baseline, automated validation step into the generation pipeline to catch critical grounding and integrity errors.

**Implementation Steps:**

1.  **Create the `ValidatorService` Module:**
    - Develop a new service module: `src/services/validator_service.py`.
    - This service will contain all QA logic and will be designed to be called directly from other services.

2.  **Integrate Validator into the Main Pipeline:**
    - Modify the main encounter processing logic (likely within `src/services/section_generator.py` or a coordinating service).
    - After a section's content is generated, and before it is finalized, invoke `validator_service.validate_section(...)`.
    - The `validate_section` method will take the generated section data and the original encounter data as input.

3.  **Implement Traceability Validation (Content Grounding):**
    - The `ValidatorService` will perform these checks:
        - **Existence Check:** Verify that every `line_number` in the `line_references` exists in the original transcript.
        - **Content Match:** Verify that the `text` in each reference is a plausible substring of the content at the corresponding line number.
    - *Outcome:* Prevents hallucinations by ensuring all generated content is traceable to its source.

4.  **Implement Medical Term Grounding:**
    - The `ValidatorService` will verify that medical concepts in the `content` have corresponding entries in the `snomed_mappings` list.
    - *Outcome:* Ensures the AI isn't inventing medical terms that weren't validated by the SNOMED RAG.

5.  **Implement Structural Integrity Checks:**
    - **Model Validation:** Ensure the generated output conforms to the Pydantic model.
    - **Completeness Check:** Ensure all requested sections in the template were generated.

**Result of Phase 1:** A fast, reliable, automated QA layer that catches major defects like fabricated content and structural errors before they leave the service.

---

### Phase 2: Semantic Validation - AI-Powered Consistency and Correctness

- **Estimated Implementation Time:** **2 - 4 hours**

**Objective:** Enhance the `ValidatorService` with "LLM-as-a-Judge" capabilities to assess the clinical and logical coherence of the generated notes.

**Implementation Steps:**

1.  **Formalize the "LLM-as-a-Judge" Pattern:**
    - Within the `ValidatorService`, create a dedicated method (e.g., `get_semantic_validation_score()`).
    - This method will use a separate, dedicated prompt template designed for evaluation (e.g., the "5 Cs" framework).

2.  **Implement Factual Consistency Scoring:**
    - The `ValidatorService` will pass the generated `content` and its source `context_chunks` to the LLM judge for a consistency score.

3.  **Implement Cross-Section Coherence Validation:**
    - After a full template (e.g., SOAP note) is generated, the `ValidatorService` will perform coherence checks between related sections:
        - **S-A Link:** "Is the `Assessment` a reasonable conclusion based on the `Subjective` section?"
        - **A-P Link:** "Is the `Plan` an appropriate course of action for the diagnoses in the `Assessment`?"
    - This involves internal calls to the LLM judge with pairs of sections.

**Result of Phase 2:** An advanced QA agent that can flag subtle errors in clinical reasoning and logical flow internally.

---

### Phase 3: Human-in-the-Loop - Learning from Physician Feedback

- **Estimated Implementation Time:** **4 - 6 hours**

**Objective:** To create a feedback loop where the system learns from corrections made by physicians, directly improving the quality of future generations.

**Implementation Steps:**

1.  **Establish "Golden Note" Benchmark (Offline):**
    - For internal testing, create a small, curated set of "perfect" reference notes for specific encounters.
    - The `ValidatorService` can be run against these rubrics to measure and improve completeness and conciseness scores.

2.  **Integrate Physician Feedback into Pattern Learning:**
    - **Assumption:** The main application will provide a mechanism to log physician edits (original text vs. modified text) to a persistent store.
    - The `PatternLearningService` (`src/services/pattern_learning.py`) will be enhanced to consume this data.
    - **Action:** A new method within `PatternLearningService` will periodically (or on-demand) process the logged edits, refining the doctor's preference dictionary. This makes the system smarter and more personalized with every correction.

**Result of Phase 3:** A data-driven QA system that continuously improves by learning from its end-users, directly enhancing the existing `PatternLearningService`.

---

### Phase 4: Proactive Safety and Ethics Auditing

- **Estimated Implementation Time:** **3 - 5 hours (for initial setup)**

**Objective:** To integrate proactive, internal checks for critical safety issues and potential biases.

**Implementation Steps:**

1.  **Implement Drug Interaction and Allergy Checking:**
    - The `ValidatorService` will extract prescribed medications from the generated `Plan` section.
    - It will then make an internal, server-to-server call to a third-party API (e.g., RxNorm, OpenFDA) to check for potential drug-drug or drug-allergy interactions.

2.  **Develop an Offline Bias Auditing Pipeline:**
    - This is an offline process, not part of the real-time generation pipeline.
    - Create scripts to periodically analyze a large, anonymized dataset of generated notes.
    - The scripts will check for statistical disparities in diagnoses or treatments based on available demographic data.

**Result of Phase 4:** A mature, production-grade QA system that proactively monitors for critical safety and ethical issues, making the system trustworthy for clinical use. 