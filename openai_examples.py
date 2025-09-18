#!/usr/bin/env python3
"""
OpenAI Client Library - Usage Examples
Demonstrates various use cases for the generalized OpenAI interface
"""

import json
from openai_client import (
    OpenAIClient, 
    ChatMessage, 
    CompletionConfig, 
    ModelType,
    SchemaBuilder,
    CommonSchemas,
    validate_api_key
)


def example_article_summary():
    """Example: Generate article summary with structured output"""
    print("=== Article Summary Example ===")
    
    client = OpenAIClient()
    
    messages = [
        ChatMessage("user", "Summarize 'Machine Learning in Finance' with title, summary, and 3 tags")
    ]
    
    schema = CommonSchemas.article_summary()
    
    try:
        result = client.structured_completion(messages, schema, "ArticleSummary")
        
        print(f"Title: {result['title']}")
        print(f"Summary: {result['summary']}")
        print(f"Tags: {', '.join(result['tags'])}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_sentiment_analysis():
    """Example: Analyze sentiment with structured output"""
    print("\n=== Sentiment Analysis Example ===")
    
    client = OpenAIClient()
    
    text_to_analyze = "The new product launch exceeded all expectations! Customers are thrilled."
    
    messages = [
        ChatMessage("system", "You are a sentiment analysis expert."),
        ChatMessage("user", f"Analyze the sentiment of this text: '{text_to_analyze}'")
    ]
    
    schema = CommonSchemas.sentiment_analysis()
    
    try:
        result = client.structured_completion(messages, schema, "SentimentAnalysis")
        
        print(f"Text: {text_to_analyze}")
        print(f"Sentiment: {result['sentiment']}")
        print(f"Confidence: {result['confidence']:.2f}")
        if 'emotions' in result:
            print(f"Emotions: {', '.join(result['emotions'])}")
            
    except Exception as e:
        print(f"Error: {e}")


def example_custom_schema():
    """Example: Create and use custom schema"""
    print("\n=== Custom Schema Example ===")
    
    client = OpenAIClient()
    
    # Build custom schema for product review analysis
    schema = SchemaBuilder.object_schema(
        properties={
            "product_name": SchemaBuilder.string_property("Name of the product"),
            "rating": SchemaBuilder.number_property(1, 5, "Rating out of 5"),
            "pros": SchemaBuilder.array_property(
                SchemaBuilder.string_property(),
                "Positive aspects"
            ),
            "cons": SchemaBuilder.array_property(
                SchemaBuilder.string_property(),
                "Negative aspects"
            ),
            "recommended": SchemaBuilder.boolean_property("Whether product is recommended")
        },
        required=["product_name", "rating", "recommended"]
    )
    
    review_text = """
    I bought the UltraBook Pro laptop last month. The battery life is amazing - lasts 12 hours easily.
    The screen is crisp and bright. However, it gets quite hot during intensive tasks and the keyboard
    feels a bit cramped. Overall, it's a solid choice for productivity work.
    """
    
    messages = [
        ChatMessage("user", f"Analyze this product review and extract key information: {review_text}")
    ]
    
    try:
        result = client.structured_completion(messages, schema, "ProductReview")
        
        print(f"Product: {result['product_name']}")
        print(f"Rating: {result['rating']}/5")
        print(f"Recommended: {result['recommended']}")
        
        if 'pros' in result and result['pros']:
            print(f"Pros: {', '.join(result['pros'])}")
        if 'cons' in result and result['cons']:
            print(f"Cons: {', '.join(result['cons'])}")
            
    except Exception as e:
        print(f"Error: {e}")


def example_simple_chat():
    """Example: Simple chat completion"""
    print("\n=== Simple Chat Example ===")
    
    client = OpenAIClient()
    
    # Configure for creative writing (use model defaults for temperature)
    config = CompletionConfig(
        model=ModelType.GPT_5_MINI,
        max_tokens=200
    )
    
    try:
        response = client.simple_prompt(
            "Write a haiku about artificial intelligence",
            system_message="You are a creative poet.",
            config=config
        )
        
        print("Haiku:")
        print(response)
        
    except Exception as e:
        print(f"Error: {e}")


def example_code_review():
    """Example: Code review with structured output"""
    print("\n=== Code Review Example ===")
    
    client = OpenAIClient()
    
    code_snippet = '''
def calculate_average(numbers):
    total = 0
    for i in range(len(numbers)):
        total = total + numbers[i]
    return total / len(numbers)
    '''
    
    messages = [
        ChatMessage("system", "You are an expert code reviewer. Analyze code for quality, issues, and improvements."),
        ChatMessage("user", f"Review this Python function:\n\n{code_snippet}")
    ]
    
    schema = CommonSchemas.code_review()
    
    try:
        result = client.structured_completion(messages, schema, "CodeReview")
        
        print(f"Overall Rating: {result['overall_rating']}/10")
        
        if result['issues']:
            print("\nIssues Found:")
            for issue in result['issues']:
                print(f"  - {issue['type']}: {issue['description']} (Severity: {issue['severity']})")
        
        if result['suggestions']:
            print("\nSuggestions:")
            for suggestion in result['suggestions']:
                print(f"  - {suggestion}")
                
    except Exception as e:
        print(f"Error: {e}")


def example_batch_processing():
    """Example: Process multiple items efficiently"""
    print("\n=== Batch Processing Example ===")
    
    client = OpenAIClient()
    
    topics = [
        "Quantum Computing",
        "Blockchain Technology", 
        "Renewable Energy"
    ]
    
    schema = CommonSchemas.article_summary()
    
    print("Processing multiple topics...")
    
    for topic in topics:
        try:
            messages = [ChatMessage("user", f"Create a brief summary for '{topic}'")]
            result = client.structured_completion(messages, schema, "ArticleSummary")
            
            print(f"\n{topic}:")
            print(f"  Title: {result['title']}")
            print(f"  Tags: {', '.join(result['tags'])}")
            
        except Exception as e:
            print(f"  Error processing {topic}: {e}")


def main():
    """Run all examples"""
    if not validate_api_key():
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY='your-key-here'")
        return
    
    print("🚀 OpenAI Client Library Examples\n")
    
    try:
        example_article_summary()
        example_sentiment_analysis()
        example_custom_schema()
        example_simple_chat()
        example_code_review()
        example_batch_processing()
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")


if __name__ == "__main__":
    main()