from crewai import Agent
import os

def create_research_agent(rapidapi_tool):
    """Create the Research Agent using Mixtral - Free Version"""
    
    return Agent(
        role='Product Research Specialist',
        goal='Find and gather comprehensive product information based on user queries',
        backstory="""You are an expert product researcher with deep knowledge of e-commerce 
        and consumer goods. You excel at finding relevant products and extracting key 
        information like pricing, ratings, and specifications from search results.""",
        verbose=True,
        allow_delegation=False,
        tools=[rapidapi_tool],
        # Use current available Groq model
        llm="groq/llama-3.3-70b-versatile",
        max_iter=3
    )