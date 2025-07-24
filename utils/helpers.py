import json
import re
import streamlit as st

def clean_json_response(response_text):
    """Clean and parse JSON response from agents"""
    try:
        # If it's already a dict, return it
        if isinstance(response_text, dict):
            return response_text
        
        # Remove markdown code blocks
        cleaned = re.sub(r'```json\s*', '', response_text)
        cleaned = re.sub(r'```\s*$', '', cleaned)
        
        # Remove any leading/trailing whitespace
        cleaned = cleaned.strip()
        
        # Try to find JSON in the text
        json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        
        # If no JSON found, try parsing the whole thing
        return json.loads(cleaned)
        
    except json.JSONDecodeError as e:
        st.error(f"JSON parsing error: {e}")
        return {"error": "Could not parse response", "products": []}
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return {"error": str(e), "products": []}

def format_product_card(product):
    """Format product information in a nice card layout"""
    try:
        # Get product details with fallbacks
        title = product.get('title', product.get('Title', 'Unknown Product'))
        price = product.get('price', product.get('Price', 'N/A'))
        rating = product.get('rating', product.get('Rating', 'N/A'))
        description = product.get('description', product.get('Brief description', product.get('description', 'No description available')))
        image_url = product.get('image_url', product.get('Image URL', ''))
        buy_url = product.get('buy_url', product.get('purchase_url', product.get('Purchase URL', '')))
        
        # Clean up rating format (remove extra /5/5)
        if isinstance(rating, str) and '/5/5' in rating:
            rating = rating.replace('/5/5', '/5')
        
        # Create two columns for layout
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Display product image
            if image_url and image_url.strip() and not any(x in image_url.lower() for x in ['placeholder', 'example.com', 'amazon.com/gp']):
                try:
                    st.image(image_url, width=200, caption=title)
                except Exception:
                    st.markdown("🖼️ *Image not available*")
            else:
                st.markdown("🖼️ *No image available*")
        
        with col2:
            # Product details
            st.markdown(f"**💰 Price:** {price}")
            st.markdown(f"**⭐ Rating:** {rating}")
            
            if description and description != 'No description available':
                st.markdown(f"**📝 Description:** {description}")
            else:
                st.markdown("**📝 Description:** *No description available*")
            
            # Buy button
            if buy_url and buy_url.strip() and buy_url != 'N/A':
                # Check if it's a working URL
                if buy_url.startswith('http'):
                    st.link_button("🛒 View Product", buy_url, help="Click to view this product")
                else:
                    st.markdown("🔗 *Purchase link not available*")
            else:
                # Create a search link as fallback
                search_query = title.replace(' ', '+')
                search_url = f"https://www.amazon.com/s?k={search_query}"
                st.link_button("🔍 Search on Amazon", search_url, help="Search for this product on Amazon")
    
    except Exception as e:
        st.error(f"Error displaying product: {e}")
        st.write("**Product data:**", product)

def validate_url(url):
    """Simple URL validation"""
    if not url or url == 'N/A':
        return False
    
    # Check for common invalid patterns
    invalid_patterns = [
        'example.com',
        'placeholder',
        'amazon.com/gp/help',
        'localhost',
        '127.0.0.1'
    ]
    
    for pattern in invalid_patterns:
        if pattern in url.lower():
            return False
    
    return url.startswith(('http://', 'https://'))

def create_search_fallback_url(product_title):
    """Create a search URL as fallback when direct links don't work"""
    clean_title = re.sub(r'[^\w\s]', '', product_title)  # Remove special characters
    search_query = clean_title.replace(' ', '+')
    return f"https://www.amazon.com/s?k={search_query}"