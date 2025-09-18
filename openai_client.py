#!/usr/bin/env python3
"""
OpenAI Client Library - Generalized Interface for Organization Use
Provides structured output, chat completions, and utility functions
"""

import json
import os
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
from openai import OpenAI


class ModelType(Enum):
    """Available OpenAI models"""
    GPT_5_MINI = "gpt-5-mini"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo"


@dataclass
class ChatMessage:
    """Structured chat message"""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class CompletionConfig:
    """Configuration for OpenAI completions"""
    model: ModelType = ModelType.GPT_5_MINI
    temperature: Optional[float] = None  # Use model default
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None  # Use model default
    frequency_penalty: Optional[float] = None  # Use model default
    presence_penalty: Optional[float] = None  # Use model default


class OpenAIClient:
    """
    Generalized OpenAI client for organization-wide use
    Handles structured outputs, chat completions, and common patterns
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = OpenAI()  # Uses OPENAI_API_KEY env var
    
    def structured_completion(
        self,
        messages: List[Union[ChatMessage, Dict[str, str]]],
        schema: Dict[str, Any],
        schema_name: str,
        config: Optional[CompletionConfig] = None
    ) -> Dict[str, Any]:
        """
        Generate structured output using JSON schema validation
        
        Args:
            messages: List of chat messages
            schema: JSON schema for structured output
            schema_name: Name for the schema
            config: Completion configuration
            
        Returns:
            Parsed JSON response matching the schema
            
        Raises:
            ValueError: If JSON parsing fails
            RuntimeError: If API call fails
        """
        if config is None:
            config = CompletionConfig()
        
        # Convert ChatMessage objects to dicts
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, ChatMessage):
                formatted_messages.append({"role": msg.role, "content": msg.content})
            else:
                formatted_messages.append(msg)
        
        try:
            # Build parameters, excluding None values
            params = {
                "model": config.model.value,
                "messages": formatted_messages,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema_name,
                        "schema": schema
                    }
                }
            }
            
            # Add optional parameters only if specified
            if config.temperature is not None:
                params["temperature"] = config.temperature
            if config.top_p is not None:
                params["top_p"] = config.top_p
            if config.frequency_penalty is not None:
                params["frequency_penalty"] = config.frequency_penalty
            if config.presence_penalty is not None:
                params["presence_penalty"] = config.presence_penalty
            if config.max_tokens is not None:
                params["max_completion_tokens"] = config.max_tokens
            
            response = self.client.chat.completions.create(**params)
            
            json_text = response.choices[0].message.content
            return json.loads(json_text)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON returned from API: {e}")
        except Exception as e:
            raise RuntimeError(f"API call failed: {e}")
    
    def chat_completion(
        self,
        messages: List[Union[ChatMessage, Dict[str, str]]],
        config: Optional[CompletionConfig] = None
    ) -> str:
        """
        Generate standard chat completion
        
        Args:
            messages: List of chat messages
            config: Completion configuration
            
        Returns:
            Response content as string
        """
        if config is None:
            config = CompletionConfig()
        
        # Convert ChatMessage objects to dicts
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, ChatMessage):
                formatted_messages.append({"role": msg.role, "content": msg.content})
            else:
                formatted_messages.append(msg)
        
        try:
            # Build parameters, excluding None values
            params = {
                "model": config.model.value,
                "messages": formatted_messages
            }
            
            # Add optional parameters only if specified
            if config.temperature is not None:
                params["temperature"] = config.temperature
            if config.top_p is not None:
                params["top_p"] = config.top_p
            if config.frequency_penalty is not None:
                params["frequency_penalty"] = config.frequency_penalty
            if config.presence_penalty is not None:
                params["presence_penalty"] = config.presence_penalty
            if config.max_tokens is not None:
                params["max_completion_tokens"] = config.max_tokens
            
            response = self.client.chat.completions.create(**params)
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise RuntimeError(f"API call failed: {e}")
    
    def simple_prompt(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        config: Optional[CompletionConfig] = None
    ) -> str:
        """
        Simple prompt interface for quick queries
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            config: Completion configuration
            
        Returns:
            Response content as string
        """
        messages = []
        if system_message:
            messages.append(ChatMessage("system", system_message))
        messages.append(ChatMessage("user", prompt))
        
        return self.chat_completion(messages, config)


class SchemaBuilder:
    """Helper class for building JSON schemas"""
    
    @staticmethod
    def object_schema(
        properties: Dict[str, Dict[str, Any]],
        required: Optional[List[str]] = None,
        additional_properties: bool = False
    ) -> Dict[str, Any]:
        """
        Build object schema
        
        Args:
            properties: Property definitions
            required: Required property names
            additional_properties: Allow additional properties
            
        Returns:
            JSON schema for object
        """
        schema = {
            "type": "object",
            "properties": properties,
            "additionalProperties": additional_properties
        }
        
        if required:
            schema["required"] = required
            
        return schema
    
    @staticmethod
    def string_property(description: Optional[str] = None) -> Dict[str, Any]:
        """Create string property"""
        prop = {"type": "string"}
        if description:
            prop["description"] = description
        return prop
    
    @staticmethod
    def array_property(
        items: Dict[str, Any],
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create array property"""
        prop = {
            "type": "array",
            "items": items
        }
        if description:
            prop["description"] = description
        return prop
    
    @staticmethod
    def number_property(
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create number property"""
        prop = {"type": "number"}
        if minimum is not None:
            prop["minimum"] = minimum
        if maximum is not None:
            prop["maximum"] = maximum
        if description:
            prop["description"] = description
        return prop
    
    @staticmethod
    def boolean_property(description: Optional[str] = None) -> Dict[str, Any]:
        """Create boolean property"""
        prop = {"type": "boolean"}
        if description:
            prop["description"] = description
        return prop


# Common schema templates
class CommonSchemas:
    """Pre-built schemas for common use cases"""
    
    @staticmethod
    def article_summary() -> Dict[str, Any]:
        """Schema for article summaries"""
        return SchemaBuilder.object_schema(
            properties={
                "title": SchemaBuilder.string_property("Article title"),
                "summary": SchemaBuilder.string_property("Brief summary"),
                "tags": SchemaBuilder.array_property(
                    SchemaBuilder.string_property(),
                    "Relevant tags"
                )
            },
            required=["title", "summary", "tags"]
        )
    
    @staticmethod
    def sentiment_analysis() -> Dict[str, Any]:
        """Schema for sentiment analysis"""
        return SchemaBuilder.object_schema(
            properties={
                "sentiment": SchemaBuilder.string_property("Overall sentiment"),
                "confidence": SchemaBuilder.number_property(0.0, 1.0, "Confidence score"),
                "emotions": SchemaBuilder.array_property(
                    SchemaBuilder.string_property(),
                    "Detected emotions"
                )
            },
            required=["sentiment", "confidence"]
        )
    
    @staticmethod
    def code_review() -> Dict[str, Any]:
        """Schema for code review"""
        return SchemaBuilder.object_schema(
            properties={
                "overall_rating": SchemaBuilder.number_property(1, 10, "Overall code quality"),
                "issues": SchemaBuilder.array_property(
                    SchemaBuilder.object_schema({
                        "type": SchemaBuilder.string_property("Issue type"),
                        "description": SchemaBuilder.string_property("Issue description"),
                        "severity": SchemaBuilder.string_property("Severity level")
                    }),
                    "Code issues found"
                ),
                "suggestions": SchemaBuilder.array_property(
                    SchemaBuilder.string_property(),
                    "Improvement suggestions"
                )
            },
            required=["overall_rating", "issues", "suggestions"]
        )


def validate_api_key() -> bool:
    """Check if OpenAI API key is available"""
    return bool(os.getenv("OPENAI_API_KEY"))


if __name__ == "__main__":
    # Example usage
    if not validate_api_key():
        print("❌ OPENAI_API_KEY not found in environment")
        exit(1)
    
    client = OpenAIClient()
    
    # Test structured output
    messages = [ChatMessage("user", "Analyze the sentiment of: 'I love this new feature!'")]
    schema = CommonSchemas.sentiment_analysis()
    
    try:
        result = client.structured_completion(messages, schema, "SentimentAnalysis")
        print("Structured Output:", json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")