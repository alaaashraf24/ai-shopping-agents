from crewai import Agent
from groq import Groq
import os

def create_purchase_agent():
    """Create the Purchase Assistant Agent using LLaMA 3.1"""
    
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    return Agent(
        role='Purchase Decision Assistant',
        goal='Highlight the best purchase option and provide clear buying guidance',
        backstory="""You are a decisive purchase assistant who helps users make final 
        buying decisions. You excel at identifying the single best option from a list 
        of recommendations and providing clear, actionable next steps for purchase.""",
        verbose=True,
        allow_delegation=False,
        llm=groq_client,
        max_iter=1
    )