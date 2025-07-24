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
from utils.helpers import clean_json_response, format_product_card

# Page configuration
st.set_page_config(
    page_title="🛒 AI Shopping Assistant",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS for better UI
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

/* Product Card Styling */
.product-card {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    padding: 20px;
    border-radius: 15px;
    margin: 15px 0;
    border: 1px solid #e0e6ed;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
}

.product-header {
    display: flex;
    align-items: center;
    margin-bottom: 15px;
}

.product-rank {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 8px 15px;
    border-radius: 25px;
    font-weight: bold;
    margin-right: 15px;
    font-size: 16px;
}

.product-title {
    color: #2c3e50;
    font-size: 20px;
    font-weight: 600;
    margin: 0;
    flex: 1;
}

.product-details {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 15px;
    margin: 15px 0;
}

.detail-item {
    text-align: center;
    padding: 10px;
    background: rgba(255, 255, 255, 0.7);
    border-radius: 10px;
}

.detail-label {
    font-size: 12px;
    color: #7f8c8d;
    font-weight: 500;
    margin-bottom: 5px;
}

.detail-value {
    font-size: 16px;
    font-weight: 600;
    color: #2c3e50;
}

.price-value {
    color: #e74c3c;
    font-size: 18px;
}

.rating-value {
    color: #f39c12;
}

.product-description {
    background: rgba(255, 255, 255, 0.8);
    padding: 12px;
    border-radius: 8px;
    margin: 10px 0;
    font-style: italic;
    color: #5d6d7e;
}

.buy-button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px 25px;
    border: none;
    border-radius: 25px;
    font-weight: 600;
    text-decoration: none;
    display: inline-block;
    margin-top: 10px;
    transition: transform 0.2s;
}

.buy-button:hover {
    transform: translateY(-2px);
    text-decoration: none;
    color: white;
}

/* Recommendation Cards */
.recommendation-card {
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
    padding: 20px;
    border-radius: 15px;
    margin: 10px 0;
    border-left: 5px solid #ff6b6b;
}

.recommendation-title {
    color: #d63031;
    font-weight: 600;
    font-size: 18px;
    margin-bottom: 8px;
}

.recommendation-text {
    color: #2d3436;
    line-height: 1.6;
}

/* Final Choice Card */
.final-choice {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    padding: 25px;
    border-radius: 20px;
    margin: 20px 0;
    border: 2px solid #00b894;
    text-align: center;
}

.final-choice h3 {
    color: #00b894;
    margin-bottom: 15px;
}

/* Section Headers */
.section-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 15px 20px;
    border-radius: 10px;
    margin: 20px 0 15px 0;
    font-size: 20px;
    font-weight: 600;
}
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

def display_product_card(product, index):
    """Display a beautifully formatted product card"""
    st.markdown(f"""
    <div class="product-card">
        <div class="product-header">
            <div class="product-rank">#{index + 1}</div>
            <h3 class="product-title">{product.get('title', product.get('Title', 'N/A'))}</h3>
        </div>
        
        <div class="product-details">
            <div class="detail-item">
                <div class="detail-label">💰 PRICE</div>
                <div class="detail-value price-value">{product.get('price', product.get('Price', 'N/A'))}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">⭐ RATING</div>
                <div class="detail-value rating-value">{product.get('rating', product.get('Rating', 'N/A'))}/5</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">🛒 AVAILABILITY</div>
                <div class="detail-value">In Stock</div>
            </div>
        </div>
        
        <div class="product-description">
            📝 {product.get('description', product.get('Brief description', 'No description available'))}
        </div>
        
        <a href="{product.get('buy_url', product.get('purchase_url', product.get('Purchase URL', '#')))}" 
           target="_blank" class="buy-button">
            🛒 Buy Now
        </a>
    </div>
    """, unsafe_allow_html=True)

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
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Parse and display results
            try:
                # Parse the result from the crew
                if hasattr(result, 'raw'):
                    result_data = json.loads(result.raw)
                elif isinstance(result, str):
                    result_data = json.loads(result)
                else:
                    result_data = result
                
                # Extract task outputs for better processing
                if hasattr(result, 'tasks_output') and result.tasks_output:
                    # Get products from research task
                    research_output = result.tasks_output[0]
                    if hasattr(research_output, 'raw'):
                        products_data = json.loads(research_output.raw)
                        products = products_data.get('products', [])
                    else:
                        products = []
                    
                    # Get recommendations from recommendation task
                    if len(result.tasks_output) > 2:
                        rec_output = result.tasks_output[2]
                        if hasattr(rec_output, 'raw'):
                            rec_data = json.loads(rec_output.raw)
                            recommendations = rec_data.get('recommendations', [])
                        else:
                            recommendations = []
                    else:
                        recommendations = []
                    
                    # Get final choice from purchase task
                    if len(result.tasks_output) > 3:
                        final_output = result.tasks_output[3]
                        if hasattr(final_output, 'raw'):
                            final_data = json.loads(final_output.raw)
                            best_choice = final_data.get('best_purchase_option', {})
                        else:
                            best_choice = {}
                    else:
                        best_choice = {}
                
                else:
                    # Fallback parsing
                    products = result_data.get('products', [])
                    recommendations = result_data.get('recommendations', [])
                    best_choice = result_data.get('best_purchase_option', {})
                
                # Display results with beautiful formatting
                if products:
                    st.markdown('<div class="section-header">🛍️ Product Search Results</div>', unsafe_allow_html=True)
                    
                    for idx, product in enumerate(products[:6]):  # Limit to 6 products
                        display_product_card(product, idx)
                
                # Display AI recommendations
                if recommendations:
                    st.markdown('<div class="section-header">💡 AI Recommendations</div>', unsafe_allow_html=True)
                    
                    for rec in recommendations:
                        st.markdown(f"""
                        <div class="recommendation-card">
                            <div class="recommendation-title">🎯 {rec.get('title', 'Recommendation')}</div>
                            <div class="recommendation-text">{rec.get('reasoning', rec.get('reason', 'No reasoning provided'))}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Display final choice
                if best_choice:
                    st.markdown('<div class="section-header">🏆 Best Choice Recommendation</div>', unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class="final-choice">
                        <h3>🎯 Our Top Pick: {best_choice.get('title', 'N/A')}</h3>
                        <p><strong>💰 Price:</strong> {best_choice.get('price', 'N/A')}</p>
                        <p><strong>⭐ Rating:</strong> {best_choice.get('rating', 'N/A')}/5</p>
                        <br>
                        <a href="{best_choice.get('purchase_url', '#')}" target="_blank" class="buy-button">
                            🛒 Buy This Product Now
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Success message
                st.success("🎉 Search completed successfully! Review the recommendations above.")
                
            except Exception as e:
                # Fallback: display raw result in a nice format
                st.markdown('<div class="section-header">📋 Search Results</div>', unsafe_allow_html=True)
                st.json(result.raw if hasattr(result, 'raw') else str(result))
                
        except Exception as e:
            st.error(f"❌ Error during search: {str(e)}")
            progress_bar.empty()
            status_text.empty()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "Built with ❤️ using [CrewAI](https://crewai.com), [Groq](https://groq.com), "
        "[RapidAPI](https://rapidapi.com), and [Streamlit](https://streamlit.io)"
    )

if __name__ == "__main__":
    main()