import streamlit as st
import json
from typing import Dict, List, Any
import re

def clean_json_response(response: str) -> Dict[str, Any]:
    """Clean and parse JSON response from agents"""
    try:
        # Remove markdown formatting
        cleaned = re.sub(r'```json\n?', '', response)
        cleaned = re.sub(r'```\n?', '', cleaned)
        cleaned = cleaned.strip()
        
        # Try to parse JSON
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: extract JSON-like content
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        # Final fallback: return structured error
        return {
            "products": [],
            "message": "Failed to parse response",
            "raw_response": response
        }

def format_product_card(product: Dict[str, Any]) -> None:
    """Display product card in Streamlit"""
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if product.get('image_url'):
            try:
                st.image(product['image_url'], width=150)
            except:
                st.text("🖼️ Image unavailable")
        else:
            st.text("🖼️ No image")
    
    with col2:
        st.subheader(product.get('title', 'Unknown Product'))
        st.write(f"💰 **Price:** {product.get('price', 'N/A')}")
        st.write(f"⭐ **Rating:** {product.get('rating', 'N/A')}")
        
        if product.get('buy_url'):
            st.link_button("🛒 Buy Now", product['buy_url'])
        
        if product.get('description'):
            with st.expander("📝 Details"):
                st.write(product['description'])