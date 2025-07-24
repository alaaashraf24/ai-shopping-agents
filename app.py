import streamlit as st
import os
from dotenv import load_dotenv
from crewai import Crew, Task
import json
import asyncio

# Load environment variables
load_dotenv()

# Import our custom modules
from tools.rapidapi_tool import RapidAPIShoppingTool
from agents.research_agent import create_research_agent
from agents.analysis_agent import create_analysis_agent  
from agents.recommendation_agent import create_recommendation_agent
from agents.purchase_agent import create_purchase_agent
from utils.helpers import clean_json_response, format_product_card

# Page configuration
st.set_page_config(
    page_title="🛒 AI Shopping Assistant",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    text-align: center;
    color: #1f77b4;
    margin-bottom: 2rem;
}
.agent-status {
    padding: 10px;
    border-radius: 5px;
    margin: 5px 0;
}
.working { background-color: #fff3cd; border-left: 5px solid #ffc107; }
.completed { background-color: #d4edda; border-left: 5px solid #28a745; }
.error { background-color: #f8d7da; border-left: 5px solid #dc3545; }
</style>
""", unsafe_allow_html=True)

def initialize_crew():
    """Initialize the CrewAI system with all agents"""
    if not os.getenv("GROQ_API_KEY"):
        st.error("🔑 Please set your GROQ_API_KEY in the .env file")
        return None, None
    
    # Initialize tool
    rapidapi_tool = RapidAPIShoppingTool()
    
    # Create agents
    research_agent = create_research_agent(rapidapi_tool)
    analysis_agent = create_analysis_agent()
    recommendation_agent = create_recommendation_agent()
    purchase_agent = create_purchase_agent()
    
    agents = [research_agent, analysis_agent, recommendation_agent, purchase_agent]
    
    return agents, rapidapi_tool

def create_tasks(agents, user_query):
    """Create tasks for each agent"""
    research_agent, analysis_agent, recommendation_agent, purchase_agent = agents
    
    # Task 1: Research products
    research_task = Task(
        description=f"""
        Search for products related to: "{user_query}"
        
        Use the Product Search Tool to find relevant products.
        Extract and structure the following information for each product:
        - Title
        - Price  
        - Rating
        - Image URL
        - Purchase URL
        - Brief description
        
        Return the results in JSON format with a 'products' array.
        """,
        agent=research_agent,
        expected_output="JSON with products array containing product details"
    )
    
    # Task 2: Analyze products
    analysis_task = Task(
        description=f"""
        Analyze the products found by the research agent for the query: "{user_query}"
        
        Compare products based on:
        - Price-to-value ratio
        - User ratings and reviews
        - Feature completeness
        - Brand reputation (if applicable)
        
        Rank the products from best to worst and provide reasoning.
        Return analysis in JSON format with ranked products and explanations.
        """,
        agent=analysis_agent,
        expected_output="JSON with ranked products and analysis reasoning"
    )
    
    # Task 3: Generate recommendations
    recommendation_task = Task(
        description=f"""
        Based on the analysis, provide personalized recommendations for: "{user_query}"
        
        Consider:
        - User's likely budget and needs
        - Best value options
        - Premium vs budget choices
        - Specific use cases
        
        Provide 2-3 top recommendations with clear explanations.
        Return in JSON format with recommendations and reasoning.
        """,
        agent=recommendation_agent,
        expected_output="JSON with top recommendations and explanations"
    )
    
    # Task 4: Purchase assistance
    purchase_task = Task(
        description=f"""
        From the recommendations, identify the single BEST purchase option for: "{user_query}"
        
        Highlight:
        - The #1 recommended product
        - Why it's the best choice
        - Next steps for purchase
        - Any important considerations
        
        Return in JSON format with the final recommendation and purchase guidance.
        """,
        agent=purchase_agent,
        expected_output="JSON with final purchase recommendation and guidance"
    )
    
    return [research_task, analysis_task, recommendation_task, purchase_task]

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown("<h1 class='main-header'>🛒 AI Shopping Assistant</h1>", unsafe_allow_html=True)
    st.markdown("**Powered by CrewAI + Groq + RapidAPI**")
    
    # Sidebar
    with st.sidebar:
        st.header("🤖 Agent Status")
        agent_status = st.empty()
        
        st.header("⚙️ Configuration")
        groq_status = "✅ Connected" if os.getenv("GROQ_API_KEY") else "❌ Missing API Key"
        rapidapi_status = "✅ Connected" if os.getenv("RAPIDAPI_KEY") else "❌ Missing API Key"
        
        st.write(f"**Groq API:** {groq_status}")
        st.write(f"**RapidAPI:** {rapidapi_status}")
        
        st.header("📊 System Info")
        st.write("**Research Agent:** Mixtral")
        st.write("**Analysis Agent:** LLaMA 3.1") 
        st.write("**Recommendation Agent:** Mixtral")
        st.write("**Purchase Agent:** LLaMA 3.1")
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔍 What are you looking for?")
        user_query = st.text_input(
            "Enter your search query:",
            placeholder="e.g., 'gaming laptop under $1000 with RTX 3060'",
            help="Be specific about your needs, budget, and preferences"
        )
        
        search_button = st.button("🚀 Search Products", type="primary")
    
    with col2:
        st.subheader("💡 Example Queries")
        example_queries = [
            "wireless headphones under $200",
            "ergonomic office chair",
            "gaming laptop RTX 4060",
            "smartphone with good camera",
            "running shoes for beginners"
        ]
        
        for query in example_queries:
            if st.button(f"🔍 {query}", key=query):
                user_query = query
                search_button = True
    
    # Process search
    if search_button and user_query:
        # Initialize crew
        agents, rapidapi_tool = initialize_crew()
        
        if not agents:
            st.stop()
        
        # Create progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Update status
            status_text.text("🔄 Initializing AI agents...")
            progress_bar.progress(10)
            
            # Validate API keys first
            if not os.getenv("GROQ_API_KEY"):
                st.error("❌ GROQ_API_KEY is required. Please add it to your .env file.")
                st.stop()
            
            if not os.getenv("RAPIDAPI_KEY"):
                st.error("❌ RAPIDAPI_KEY is required for real product search. Please add it to your .env file.")
                st.stop()
            
            # Create tasks
            tasks = create_tasks(agents, user_query)
            
            # Create and run crew
            crew = Crew(
                agents=agents,
                tasks=tasks,
                verbose=True,
                process="sequential"
            )
            
            status_text.text("🧠 AI agents are working...")
            progress_bar.progress(30)
            
            # Execute the crew
            result = crew.kickoff()
            
            progress_bar.progress(100)
            status_text.text("✅ Search completed!")
            
            # Display results
            st.success("🎉 Found products for you!")
            
            # Try to parse the final result
            try:
                if isinstance(result, str):
                    final_data = clean_json_response(result)
                else:
                    final_data = result
                
                # Check if we got valid products
                if not final_data.get('products') or len(final_data.get('products', [])) == 0:
                    if final_data.get('success') == False:
                        st.error(f"❌ Product search failed: {final_data.get('message', 'Unknown error')}")
                    else:
                        st.warning("⚠️ No products found for your query. Try a different search term.")
                    st.stop()
                
                # Display products
                st.subheader("🛍️ Product Results")
                
                for idx, product in enumerate(final_data['products']):
                    with st.container():
                        st.markdown(f"### #{idx + 1}")
                        format_product_card(product)
                        st.divider()
                
                # Display recommendations if available
                if final_data.get('recommendations'):
                    st.subheader("💡 AI Recommendations")
                    for rec in final_data['recommendations']:
                        st.info(f"**{rec.get('title', 'Recommendation')}:** {rec.get('reason', '')}")
                
                # Display final purchase advice
                if final_data.get('final_recommendation'):
                    st.subheader("🎯 Best Choice")
                    st.success(final_data['final_recommendation'])
                
            except Exception as e:
                # Fallback: display raw result
                st.subheader("📋 Results")
                st.write(result)
                
        except Exception as e:
            st.error(f"❌ Error during search: {str(e)}")
            progress_bar.progress(0)
            status_text.text("❌ Search failed")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "Built with ❤️ using [CrewAI](https://crewai.com), [Groq](https://groq.com), "
        "[RapidAPI](https://rapidapi.com), and [Streamlit](https://streamlit.io)"
    )

if __name__ == "__main__":
    main()