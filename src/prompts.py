#!/usr/bin/env python3
"""
Prompt templates for the 3-step question generation pipeline
"""

class PromptTemplates:
    """Structured prompts for the question generation pipeline"""
    
    # Step 1: Summarization Layer
    SUMMARIZATION_PROMPT = """You are an expert note-taker and strategist. Given the following transcript chunk, produce a structured summary:

1. Main arguments and claims
2. Supporting evidence/examples  
3. Unanswered questions or ambiguities
4. Key assumptions or biases in reasoning

Keep it concise. Use short, clear sentences. No extra commentary.

Transcript: {chunk}

Format your response as:
Main Points → 3–5 bullets
Evidence → 1–2 bullets per point
Assumptions → 2–3 bullets
Open Loops → 1–2 bullets"""

    SUMMARIZATION_SYSTEM = "You are an expert note-taker and strategist who creates structured, analytical summaries."

    # Step 2: Critical Thinking Layer  
    CRITICAL_THINKING_PROMPT = """You are an expert in critical thinking and intellectual sparring. Given this summary, identify:

1. Weak spots: Claims with assumptions that could be probed
2. Contrarian angles: Where a "what if" or edge case breaks the argument
3. Future implications: How this topic intersects with tech, society, or economics in 2–5 years
4. Personalization hooks: Points connected to the speaker's background or current work

Keep it structured as 3–5 bullets per category.

Summary: {summary}

Format your response as:
Weak Spots → 3 bullets
Contrarian Angles → 3 bullets  
Future Implications → 3 bullets
Hooks → 2 bullets"""

    CRITICAL_THINKING_SYSTEM = "You are an expert in critical thinking and intellectual sparring who identifies leverage points for deeper inquiry."

    # Step 3: Question Generation & Ranking
    QUESTION_GENERATION_PROMPT = """You are designing high-leverage audience questions. Given the weak spots, contrarian angles, future implications, and hooks:

- Generate 8–10 questions
- Rank them from 1–10 by "Asymmetric Return" potential:
  - Does it expose deep thinking?
  - Does it open doors for a follow-up conversation?  
  - Does it create value for the audience?

Format: [Rank] Question (1–2 lines max) → Reason why it creates leverage.

Inputs: {critical_analysis}

Format your response as numbered questions with rankings and reasoning."""

    QUESTION_GENERATION_SYSTEM = "You are an expert at designing high-leverage audience questions that create asymmetric value."

    # Final Merge Prompt
    MERGE_QUESTIONS_PROMPT = """Here are multiple question sets from different chunks. Merge and deduplicate them into the top 5 highest-leverage questions overall. 

Rank them by asymmetry potential and connection value.

Question Sets: {all_questions}

Format your response as:
1. [Question] → [Reason for high leverage]
2. [Question] → [Reason for high leverage]
...
5. [Question] → [Reason for high leverage]"""

    MERGE_QUESTIONS_SYSTEM = "You are an expert at synthesizing and ranking questions for maximum audience value."