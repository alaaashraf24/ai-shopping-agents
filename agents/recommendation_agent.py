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
        # Use string model name instead of client object
        llm="groq/mixtral-8x7b-32768",
        max_iter=2
    )