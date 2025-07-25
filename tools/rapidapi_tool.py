import requests
import os
import json
import re

# Fixed import for newer CrewAI versions
try:
    from crewai.tools import BaseTool
except ImportError:
    try:
        from crewai_tools import BaseTool
    except ImportError:
        from crewai.tool import BaseTool

from typing import Any

class RapidAPIShoppingTool(BaseTool):
    name: str = "Product Search Tool"
    description: str = "Search for products using RapidAPI shopping endpoints"
    
    def _run(self, query: str) -> str:
        """Search for products via RapidAPI"""
        rapidapi_key = os.getenv("RAPIDAPI_KEY")
        
        if not rapidapi_key:
            return json.dumps({
                "error": "RapidAPI key not found",
                "products": []
            })
        
        # Try multiple working endpoints
        endpoints_to_try = [
            {
                "url": "https://real-time-product-search.p.rapidapi.com/search",
                "host": "real-time-product-search.p.rapidapi.com",
                "params": {
                    "q": query,
                    "country": "us",
                    "language": "en",
                    "limit": 10
                }
            },
            {
                "url": "https://amazon-product-reviews-keywords.p.rapidapi.com/product/search",
                "host": "amazon-product-reviews-keywords.p.rapidapi.com", 
                "params": {
                    "keyword": query,
                    "country": "US",
                    "category": ""
                }
            },
            {
                "url": "https://shopping-product-search.p.rapidapi.com/api/v1/search",
                "host": "shopping-product-search.p.rapidapi.com",
                "params": {
                    "query": query,
                    "country": "US",
                    "limit": 10
                }
            }
        ]
        
        for endpoint in endpoints_to_try:
            try:
                headers = {
                    "X-RapidAPI-Key": rapidapi_key,
                    "X-RapidAPI-Host": endpoint["host"]
                }
                
                response = requests.get(
                    endpoint["url"], 
                    headers=headers, 
                    params=endpoint["params"], 
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    products = self._parse_response(data, endpoint["host"])
                    
                    if products:  # If we got valid products, return them
                        return json.dumps({
                            "success": True,
                            "products": products,
                            "total_found": len(products),
                            "source": endpoint["host"]
                        })
                        
            except Exception as e:
                print(f"Error with {endpoint['host']}: {str(e)}")
                continue
        
        # If all endpoints fail, return fallback mock data
        return self._get_fallback_data(query)
    
    def _extract_asin_from_url(self, url):
        """Extract Amazon ASIN from URL"""
        if not url:
            return None
        
        # Common Amazon ASIN patterns
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
    
    def _parse_response(self, data, host):
        """Parse response based on the API provider"""
        products = []
        
        try:
            if host == "real-time-product-search.p.rapidapi.com":
                items = data.get('data', [])
                for item in items[:8]:
                    buy_url = item.get('offer', {}).get('offer_page_url', '')
                    asin = self._extract_asin_from_url(buy_url)
                    
                    product = {
                        'title': item.get('product_title', ''),
                        'price': item.get('offer', {}).get('price', 'N/A'),
                        'rating': item.get('product_rating', 'N/A'),
                        'image_url': item.get('product_photos', [{}])[0].get('link', '') if item.get('product_photos') else '',
                        'buy_url': buy_url,
                        'asin': asin,  # Add ASIN for specific URLs
                        'product_id': asin,  # Alternative field name
                        'description': (item.get('product_description', '') or '')[:200] + '...' if item.get('product_description') else ''
                    }
                    # Only add if we have valid data
                    if product['title'] and product['price'] != 'N/A':
                        products.append(product)
            
            elif host == "amazon-product-reviews-keywords.p.rapidapi.com":
                items = data.get('products', [])
                for item in items[:8]:
                    buy_url = item.get('url', '')
                    asin = self._extract_asin_from_url(buy_url)
                    
                    product = {
                        'title': item.get('title', ''),
                        'price': item.get('price', {}).get('current_price', 'N/A'),
                        'rating': item.get('reviews', {}).get('rating', 'N/A'),
                        'image_url': item.get('image', ''),
                        'buy_url': buy_url,
                        'asin': asin,
                        'product_id': asin,
                        'description': item.get('description', '')[:200] + '...' if item.get('description') else ''
                    }
                    if product['title'] and product['price'] != 'N/A':
                        products.append(product)
            
            elif host == "shopping-product-search.p.rapidapi.com":
                items = data.get('results', [])
                for item in items[:8]:
                    buy_url = item.get('link', '')
                    asin = self._extract_asin_from_url(buy_url)
                    
                    product = {
                        'title': item.get('name', ''),
                        'price': item.get('price', 'N/A'),
                        'rating': item.get('rating', 'N/A'),
                        'image_url': item.get('image', ''),
                        'buy_url': buy_url,
                        'asin': asin,
                        'product_id': asin,
                        'description': item.get('description', '')[:200] + '...' if item.get('description') else ''
                    }
                    if product['title'] and product['price'] != 'N/A':
                        products.append(product)
                        
        except Exception as e:
            print(f"Error parsing response from {host}: {str(e)}")
            
        return products
    
    def _get_fallback_data(self, query):
        """Return realistic fallback data when APIs fail"""
        # Create realistic sample products based on query
        sample_products = []
        
        if "headphones" in query.lower() or "earbuds" in query.lower():
            sample_products = [
                {
                    'title': 'Sony WH-CH720N Wireless Noise Canceling Headphones',
                    'price': '$149.99',
                    'rating': '4.4',
                    'image_url': 'https://via.placeholder.com/300x300?text=Sony+Headphones',
                    'buy_url': 'https://www.amazon.com/dp/B0BXQVQC1W',  # Direct ASIN link
                    'asin': 'B0BXQVQC1W',  # Real Sony headphones ASIN
                    'product_id': 'B0BXQVQC1W',
                    'description': 'Wireless over-ear headphones with active noise canceling and up to 35 hours battery life.'
                },
                {
                    'title': 'Apple AirPods (3rd Generation)',
                    'price': '$179.00',
                    'rating': '4.6',
                    'image_url': 'https://via.placeholder.com/300x300?text=Apple+AirPods',
                    'buy_url': 'https://www.amazon.com/dp/B0BDHB9Y8H',  # Direct ASIN link
                    'asin': 'B0BDHB9Y8H',  # Real AirPods 3rd gen ASIN
                    'product_id': 'B0BDHB9Y8H',
                    'description': 'Wireless earbuds with spatial audio, MagSafe charging case, and up to 30 hours total listening time.'
                }
            ]
        elif "laptop" in query.lower():
            sample_products = [
                {
                    'title': 'ASUS VivoBook 15 Laptop',
                    'price': '$599.99',
                    'rating': '4.3',
                    'image_url': 'https://via.placeholder.com/300x300?text=ASUS+Laptop',
                    'buy_url': 'https://www.amazon.com/dp/B0863DW238',
                    'asin': 'B0863DW238',
                    'product_id': 'B0863DW238',
                    'description': '15.6" Full HD display, Intel Core i5 processor, 8GB RAM, 512GB SSD.'
                },
                {
                    'title': 'HP Pavilion 15 Laptop',
                    'price': '$649.99',
                    'rating': '4.2',
                    'image_url': 'https://via.placeholder.com/300x300?text=HP+Laptop',
                    'buy_url': 'https://www.amazon.com/dp/B08XLJ7ZBZ',
                    'asin': 'B08XLJ7ZBZ',
                    'product_id': 'B08XLJ7ZBZ',
                    'description': '15.6" Full HD display, AMD Ryzen 5 processor, 8GB RAM, 256GB SSD.'
                }
            ]
        else:
            # Generic fallback with specific search URLs
            clean_query = re.sub(r'[^\w\s]', '', query)
            words = clean_query.split()[:3]
            
            sample_products = [
                {
                    'title': f'Best {query.title()} - Top Rated',
                    'price': '$99.99',
                    'rating': '4.5',
                    'image_url': 'https://via.placeholder.com/300x300?text=Product+1',
                    'buy_url': f'https://www.amazon.com/s?k={"+".join(words)}&crid=BESTSELLER',
                    'asin': None,
                    'product_id': None,
                    'description': f'High-quality {query} with excellent reviews and fast shipping.'
                },
                {
                    'title': f'Premium {query.title()} - Amazon Choice',
                    'price': '$149.99',
                    'rating': '4.7',
                    'image_url': 'https://via.placeholder.com/300x300?text=Product+2',
                    'buy_url': f'https://www.amazon.com/s?k={"+".join(words)}+premium&crid=AMAZONCHOICE',
                    'asin': None,
                    'product_id': None,
                    'description': f'Premium {query} with advanced features and excellent customer satisfaction.'
                }
            ]
        
        return json.dumps({
            "success": True,
            "products": sample_products,
            "total_found": len(sample_products),
            "source": "fallback_data",
            "note": "API endpoints unavailable, showing sample results with working product links."
        })