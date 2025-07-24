from crewai import Agent
from groq import Groq
import os

def create_recommendation_agent():
    """Create the Recommendation Agent using Mixtral"""
    
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    return Agent(
        role='Personal Shopping Advisor',
        goal='Provide personalized product recommendations with clear reasoning',
        backstory="""You are a friendly and knowledgeable shopping advisor who understands 
        consumer needs and preferences. You excel at translating technical product 
        comparisons into easy-to-understand recommendations that match user requirements 
        and budget constraints.""",
        verbose=True,
        allow_delegation=False,
        llm=groq_client,
        max_iter=2
    )