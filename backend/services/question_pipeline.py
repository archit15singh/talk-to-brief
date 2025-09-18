#!/usr/bin/env python3
"""
3-step pipeline for generating high-leverage audience questions
"""

import time
from openai_client import OpenAIClient, ChatMessage, CompletionConfig, ModelType
from prompts import PromptTemplates
from schemas import QuestionPipelineSchemas
from utils.logger import Logger

# Global logger instance
log = Logger()

class QuestionGenerationPipeline:
    """3-step pipeline for generating high-leverage audience questions"""
    
    def __init__(self, client: OpenAIClient = None):
        self.client = client or OpenAIClient()
        self.config = CompletionConfig(model=ModelType.GPT_5_NANO)
        self.schemas = QuestionPipelineSchemas()
        self.prompts = PromptTemplates()
    
    def step1_summarization(self, chunk: str):
        """Step 1: Create structured summary with main points, evidence, assumptions, open loops"""
        messages = [
            ChatMessage("system", self.prompts.SUMMARIZATION_SYSTEM),
            ChatMessage("user", self.prompts.SUMMARIZATION_PROMPT.format(chunk=chunk))
        ]
        
        return self.client.structured_completion(
            messages=messages,
            schema=self.schemas.summarization_schema(),
            schema_name="SummarizationOutput",
            config=self.config
        )
    
    def step2_critical_thinking(self, summary):
        """Step 2: Identify weak spots, contrarian angles, future implications, hooks"""
        summary_text = self._format_summary_for_analysis(summary)
        
        messages = [
            ChatMessage("system", self.prompts.CRITICAL_THINKING_SYSTEM),
            ChatMessage("user", self.prompts.CRITICAL_THINKING_PROMPT.format(summary=summary_text))
        ]
        
        return self.client.structured_completion(
            messages=messages,
            schema=self.schemas.critical_thinking_schema(),
            schema_name="CriticalThinkingOutput",
            config=self.config
        )
    
    def step3_question_generation(self, critical_analysis):
        """Step 3: Generate and rank 8-10 high-leverage questions"""
        analysis_text = self._format_critical_analysis(critical_analysis)
        
        messages = [
            ChatMessage("system", self.prompts.QUESTION_GENERATION_SYSTEM),
            ChatMessage("user", self.prompts.QUESTION_GENERATION_PROMPT.format(critical_analysis=analysis_text))
        ]
        
        return self.client.structured_completion(
            messages=messages,
            schema=self.schemas.question_generation_schema(),
            schema_name="QuestionGenerationOutput",
            config=self.config
        )
    
    def merge_final_questions(self, all_question_sets):
        """Final step: Merge and deduplicate into top 5 questions"""
        questions_text = self._format_all_questions(all_question_sets)
        
        messages = [
            ChatMessage("system", self.prompts.MERGE_QUESTIONS_SYSTEM),
            ChatMessage("user", self.prompts.MERGE_QUESTIONS_PROMPT.format(all_questions=questions_text))
        ]
        
        return self.client.structured_completion(
            messages=messages,
            schema=self.schemas.final_questions_schema(),
            schema_name="FinalQuestionsOutput",
            config=self.config
        )
    
    def process_chunk(self, chunk: str, chunk_number: int):
        """Process a single chunk through all 3 steps"""
        start_time = time.time()
        
        log.info(f"Processing chunk {chunk_number} ({len(chunk):,} chars)", indent=1)
        
        try:
            # Step 1: Summarization
            step1_start = time.time()
            log.info("Step 1: Summarization Layer", indent=2)
            summary = self.step1_summarization(chunk)
            
            main_points = len(summary.get('main_points', []))
            assumptions = len(summary.get('assumptions', []))
            log.success(f"Extracted {main_points} main points, {assumptions} assumptions", indent=3)
            
            # Step 2: Critical Thinking
            step2_start = time.time()
            log.info("Step 2: Critical Thinking Layer", indent=2)
            critical_analysis = self.step2_critical_thinking(summary)
            
            weak_spots = len(critical_analysis.get('weak_spots', []))
            contrarian = len(critical_analysis.get('contrarian_angles', []))
            log.success(f"Identified {weak_spots} weak spots, {contrarian} contrarian angles", indent=3)
            
            # Step 3: Question Generation
            step3_start = time.time()
            log.info("Step 3: Question Generation & Ranking", indent=2)
            questions = self.step3_question_generation(critical_analysis)
            
            question_count = len(questions.get('questions', []))
            if question_count > 0:
                top_question = max(questions.get('questions', []), key=lambda x: x.get('rank', 0))
                top_rank = top_question.get('rank', 0)
                log.success(f"Generated {question_count} questions (top rank: {top_rank})", indent=3)
            
            total_time = time.time() - start_time
            log.processing_time(start_time, f"Chunk {chunk_number}")
            
            return {
                'chunk_number': chunk_number,
                'original_text': chunk,
                'summary': summary,
                'critical_analysis': critical_analysis,
                'questions': questions,
                'char_count': len(chunk),
                'processing_time': total_time
            }
            
        except Exception as e:
            log.error(f"Chunk {chunk_number} failed: {str(e)}", indent=2)
            return {
                'chunk_number': chunk_number,
                'original_text': chunk,
                'error': str(e),
                'char_count': len(chunk)
            }
    
    def _format_summary_for_analysis(self, summary):
        """Format summary data for critical thinking step"""
        formatted = "STRUCTURED SUMMARY:\n\n"
        
        formatted += "Main Points:\n"
        for point in summary.get('main_points', []):
            formatted += f"• {point}\n"
        
        formatted += "\nEvidence:\n"
        for evidence_group in summary.get('evidence', []):
            formatted += f"• {evidence_group.get('point', 'Unknown point')}:\n"
            for item in evidence_group.get('evidence_items', []):
                formatted += f"  - {item}\n"
        
        formatted += "\nAssumptions:\n"
        for assumption in summary.get('assumptions', []):
            formatted += f"• {assumption}\n"
        
        formatted += "\nOpen Loops:\n"
        for loop in summary.get('open_loops', []):
            formatted += f"• {loop}\n"
        
        return formatted
    
    def _format_critical_analysis(self, analysis):
        """Format critical analysis for question generation"""
        formatted = "CRITICAL ANALYSIS:\n\n"
        
        formatted += "Weak Spots:\n"
        for spot in analysis.get('weak_spots', []):
            formatted += f"• {spot}\n"
        
        formatted += "\nContrarian Angles:\n"
        for angle in analysis.get('contrarian_angles', []):
            formatted += f"• {angle}\n"
        
        formatted += "\nFuture Implications:\n"
        for implication in analysis.get('future_implications', []):
            formatted += f"• {implication}\n"
        
        formatted += "\nHooks:\n"
        for hook in analysis.get('hooks', []):
            formatted += f"• {hook}\n"
        
        return formatted
    
    def _format_all_questions(self, question_sets):
        """Format all question sets for final merging"""
        formatted = "ALL QUESTION SETS:\n\n"
        
        for q_set in question_sets:
            if 'error' in q_set:
                continue
                
            formatted += f"Chunk {q_set['chunk_number']} Questions:\n"
            questions = q_set.get('questions', {}).get('questions', [])
            
            for q in questions:
                rank = q.get('rank', 0)
                question = q.get('question', 'No question')
                reason = q.get('leverage_reason', 'No reason')
                formatted += f"[{rank}] {question} → {reason}\n"
            
            formatted += "\n"
        
        return formatted