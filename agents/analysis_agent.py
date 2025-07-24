from crewai import Agent
import os

def create_analysis_agent():
    """Create the Analysis Agent using LLaMA 3.1 - Free Version"""
    
    return Agent(
        role='Product Analysis Expert',
        goal='Analyze and compare products based on price, features, ratings, and value',
        backstory="""You are a meticulous analyst who excels at comparing products 
        objectively. You can quickly identify the best value propositions, highlight 
        pros and cons, and rank products based on various criteria like price-to-performance 
        ratio, user ratings, and feature completeness.""",
        verbose=True,
        allow_delegation=False,
        # Use string model name instead of client object
        llm="groq/llama-3.1-70b-versatile",
        max_iter=2
    )