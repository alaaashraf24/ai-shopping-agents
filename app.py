# SQLite3 compatibility fix
import sys
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import os
os.environ["CREWAI_DISABLE_MEMORY"] = "true"

import streamlit as st
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
from utils.helpers import clean_json_response, format_product_card, validate_url, create_search_fallback_url

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
        st.write("**Research Agent:** LLaMA 3.3 70B")
        st.write("**Analysis Agent:** LLaMA 3.1 8B") 
        st.write("**Recommendation Agent:** LLaMA 3.3 70B")
        st.write("**Purchase Agent:** LLaMA 3.1 8B")
    
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
            
            # Parse the crew results
            try:
                # Get all task outputs
                all_outputs = []
                if hasattr(result, 'tasks_output'):
                    all_outputs = result.tasks_output
                elif isinstance(result, dict) and 'tasks_output' in result:
                    all_outputs = result['tasks_output']
                
                # Extract products from research task (first task output)
                products_data = None
                if all_outputs and len(all_outputs) > 0:
                    research_output = all_outputs[0]
                    if hasattr(research_output, 'raw'):
                        research_raw = research_output.raw
                    elif isinstance(research_output, dict):
                        research_raw = research_output.get('raw', str(research_output))
                    else:
                        research_raw = str(research_output)
                    
                    products_data = clean_json_response(research_raw)
                
                # Fallback: try to parse the main result
                if not products_data or not products_data.get('products'):
                    if isinstance(result, str):
                        products_data = clean_json_response(result)
                    elif hasattr(result, 'raw'):
                        products_data = clean_json_response(result.raw)
                    else:
                        products_data = result if isinstance(result, dict) else {}
                
                # Display all products
                if products_data and products_data.get('products'):
                    st.subheader("🛍️ All Products Found")
                    
                    products = products_data['products']
                    for idx, product in enumerate(products):
                        with st.container():
                            st.markdown(f"### #{idx + 1} - {product.get('title', product.get('Title', 'Unknown Product'))}")
                            format_product_card(product)
                            st.divider()
                    
                    # Display source info
                    if products_data.get('source'):
                        st.caption(f"📡 Data source: {products_data['source']}")
                    if products_data.get('note'):
                        st.info(products_data['note'])
                
                # Display AI recommendation from final task
                final_recommendation = None
                if all_outputs and len(all_outputs) >= 4:
                    final_output = all_outputs[3]  # Purchase agent output
                    if hasattr(final_output, 'raw'):
                        final_raw = final_output.raw
                    elif isinstance(final_output, dict):
                        final_raw = final_output.get('raw', str(final_output))
                    else:
                        final_raw = str(final_output)
                    
                    final_recommendation = clean_json_response(final_raw)
                
                # Display the AI's top recommendation
                if final_recommendation and final_recommendation.get('best_purchase_option'):
                    st.subheader("🎯 AI's Top Recommendation")
                    
                    best_product = final_recommendation['best_purchase_option']
                    why_best = final_recommendation.get("why_it's_the_best_choice", {})
                    
                    # Display the recommended product
                    st.markdown(f"**🏆 Recommended Product:** {best_product.get('title', 'N/A')}")
                    
                    # Create columns for the recommendation
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        img_url = best_product.get('image_url', '')
                        if img_url and img_url.strip():
                            try:
                                st.image(img_url, width=200)
                            except:
                                st.markdown("🖼️ *Image not available*")
                        else:
                            st.markdown("🖼️ *No image available*")
                    
                    with col2:
                        st.markdown(f"**💰 Price:** {best_product.get('price', 'N/A')}")
                        st.markdown(f"**⭐ Rating:** {best_product.get('rating', 'N/A')}")
                        
                        if why_best.get('reasoning'):
                            st.success(f"**Why it's the best:** {why_best['reasoning']}")
                        
                        # Purchase button
                        purchase_url = best_product.get('purchase_url', '')
                        if purchase_url and validate_url(purchase_url):
                            st.link_button("🛒 Buy This Top Pick", purchase_url, type="primary")
                        else:
                            # Fallback search
                            search_url = create_search_fallback_url(best_product.get('title', ''))
                            st.link_button("🔍 Search for This Product", search_url, type="primary")
                    
                    # Display next steps
                    if final_recommendation.get('next_steps_for_purchase'):
                        st.subheader("📋 Next Steps")
                        next_steps = final_recommendation['next_steps_for_purchase']
                        if next_steps.get('recommended_action'):
                            st.info(next_steps['recommended_action'])
                        if next_steps.get('considerations'):
                            st.warning(f"**Consider:** {next_steps['considerations']}")
                
                # If no products found
                if not products_data or not products_data.get('products'):
                    st.warning("⚠️ No products found for your query. Try a different search term or check your API configuration.")
                    
            except Exception as e:
                st.error(f"Error parsing results: {str(e)}")
                st.subheader("🔍 Raw Results")
                st.write("Here's what the AI agents returned:")
                st.code(str(result), language="json")
                
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