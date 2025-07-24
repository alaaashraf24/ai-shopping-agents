from crewai import Agent
from groq import Groq
import os

def create_analysis_agent():
    """Create the Analysis Agent using LLaMA 3.1"""
    
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    return Agent(
        role='Product Analysis Expert',
        goal='Analyze and compare products based on price, features, ratings, and value',
        backstory="""You are a meticulous analyst who excels at comparing products 
        objectively. You can quickly identify the best value propositions, highlight 
        pros and cons, and rank products based on various criteria like price-to-performance 
        ratio, user ratings, and feature completeness.""",
        verbose=True,
        allow_delegation=False,
        llm=groq_client,
        max_iter=2
    )