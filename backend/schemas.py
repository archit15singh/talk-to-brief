#!/usr/bin/env python3
"""
JSON schemas for structured outputs in the question generation pipeline
"""

from openai_client import SchemaBuilder

class QuestionPipelineSchemas:
    """Schemas for the 3-step question generation pipeline"""
    
    @staticmethod
    def summarization_schema():
        """Schema for Step 1: Summarization Layer"""
        return SchemaBuilder.object_schema(
            properties={
                "main_points": SchemaBuilder.array_property(
                    SchemaBuilder.string_property(),
                    "3-5 main arguments and claims"
                ),
                "evidence": SchemaBuilder.array_property(
                    SchemaBuilder.object_schema({
                        "point": SchemaBuilder.string_property("Main point this evidence supports"),
                        "evidence_items": SchemaBuilder.array_property(
                            SchemaBuilder.string_property(),
                            "1-2 supporting evidence items"
                        )
                    }),
                    "Supporting evidence for each main point"
                ),
                "assumptions": SchemaBuilder.array_property(
                    SchemaBuilder.string_property(),
                    "2-3 key assumptions or biases in reasoning"
                ),
                "open_loops": SchemaBuilder.array_property(
                    SchemaBuilder.string_property(),
                    "1-2 unanswered questions or ambiguities"
                )
            },
            required=["main_points", "evidence", "assumptions", "open_loops"]
        )
    
    @staticmethod
    def critical_thinking_schema():
        """Schema for Step 2: Critical Thinking Layer"""
        return SchemaBuilder.object_schema(
            properties={
                "weak_spots": SchemaBuilder.array_property(
                    SchemaBuilder.string_property(),
                    "3 claims with assumptions that could be probed"
                ),
                "contrarian_angles": SchemaBuilder.array_property(
                    SchemaBuilder.string_property(),
                    "3 'what if' scenarios or edge cases that break the argument"
                ),
                "future_implications": SchemaBuilder.array_property(
                    SchemaBuilder.string_property(),
                    "3 ways this intersects with tech, society, or economics in 2-5 years"
                ),
                "hooks": SchemaBuilder.array_property(
                    SchemaBuilder.string_property(),
                    "2 points connected to speaker's background or current work"
                )
            },
            required=["weak_spots", "contrarian_angles", "future_implications", "hooks"]
        )
    
    @staticmethod
    def question_generation_schema():
        """Schema for Step 3: Question Generation & Ranking"""
        return SchemaBuilder.object_schema(
            properties={
                "questions": SchemaBuilder.array_property(
                    SchemaBuilder.object_schema({
                        "rank": SchemaBuilder.number_property(1, 10, "Asymmetric return ranking (1-10)"),
                        "question": SchemaBuilder.string_property("The question (1-2 lines max)"),
                        "leverage_reason": SchemaBuilder.string_property("Why this creates leverage")
                    }),
                    "8-10 ranked questions with leverage reasoning"
                )
            },
            required=["questions"]
        )
    
    @staticmethod
    def final_questions_schema():
        """Schema for Final Merge: Top 5 Questions"""
        return SchemaBuilder.object_schema(
            properties={
                "top_questions": SchemaBuilder.array_property(
                    SchemaBuilder.object_schema({
                        "rank": SchemaBuilder.number_property(1, 5, "Final ranking (1-5)"),
                        "question": SchemaBuilder.string_property("The high-leverage question"),
                        "leverage_reason": SchemaBuilder.string_property("Reason for high leverage and audience value")
                    }),
                    "Top 5 highest-leverage questions"
                )
            },
            required=["top_questions"]
        )