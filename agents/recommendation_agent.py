from crewai import Agent
import os

def create_recommendation_agent():
    """Create the Recommendation Agent using Mixtral - Free Version"""
    
    return Agent(
        role='Personal Shopping Advisor',
        goal='Provide personalized product recommendations with clear reasoning',
        backstory="""You are a friendly and knowledgeable shopping advisor who understands 
        consumer needs and preferences. You excel at translating technical product 
        comparisons into easy-to-understand recommendations that match user requirements 
        and budget constraints.""",
        verbose=True,
        allow_delegation=False,
        # Use current available Groq model
        llm="groq/llama-3.3-70b-versatile",
        max_iter=2
    )