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
        
        # IMPROVED: Try multiple URL fields and use product ID for specific URLs
        buy_url = product.get('buy_url', product.get('purchase_url', product.get('Purchase URL', product.get('url', ''))))
        product_id = product.get('asin', product.get('product_id', product.get('id', '')))
        
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
            
            # IMPROVED: Better URL handling with specific product links
            if buy_url and buy_url.strip() and buy_url != 'N/A' and validate_url(buy_url):
                # Use the specific product URL
                st.link_button("🛒 View Product", buy_url, help="Click to view this product")
            elif product_id:
                # Create specific Amazon product URL using ASIN/Product ID
                specific_url = f"https://www.amazon.com/dp/{product_id}"
                st.link_button("🛒 View Product", specific_url, help="Click to view this specific product")
            else:
                # Create a more specific search as fallback
                search_url = create_specific_search_url(title, price)
                st.link_button("🔍 Find This Product", search_url, help="Search for this specific product")
    
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

def create_specific_search_url(title, price):
    """Create a more specific search URL using title and price"""
    # Clean the title and add price range if available
    clean_title = re.sub(r'[^\w\s]', '', title)
    search_query = clean_title.replace(' ', '+')
    
    # Try to extract price number for better search
    if price and price != 'N/A':
        price_match = re.search(r'\d+', str(price))
        if price_match:
            price_num = int(price_match.group())
            # Add price range to search
            search_query += f"+under+{price_num + 50}"
    
    return f"https://www.amazon.com/s?k={search_query}&ref=sr_st_price-asc-rank"

def extract_product_id_from_url(url):
    """Extract Amazon ASIN or product ID from URL"""
    if not url:
        return None
    
    # Try to extract ASIN from Amazon URLs
    asin_patterns = [
        r'/dp/([A-Z0-9]{10})',
        r'/product/([A-Z0-9]{10})',
        r'asin=([A-Z0-9]{10})',
        r'/([A-Z0-9]{10})(?:/|$)'
    ]
    
    for pattern in asin_patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None