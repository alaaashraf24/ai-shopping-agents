import requests
import os
import json  # Added missing json import
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
                 
        # Using Real-Time Product Search API (example endpoint)
        url = "https://real-time-product-search.p.rapidapi.com/search"
                 
        headers = {
            "X-RapidAPI-Key": rapidapi_key,
            "X-RapidAPI-Host": "real-time-product-search.p.rapidapi.com"
        }
                 
        params = {
            "q": query,
            "country": "us",
            "language": "en",
            "limit": "10"
        }
                 
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
                         
            if response.status_code == 200:
                data = response.json()
                                 
                # Format the response for agents
                products = []
                for item in data.get('data', [])[:8]:  # Limit to 8 products
                    product = {
                        'title': item.get('product_title', ''),
                        'price': item.get('offer', {}).get('price', 'N/A'),
                        'rating': item.get('product_rating', 'N/A'),
                        'image_url': item.get('product_photos', [{}])[0].get('link', ''),
                        'buy_url': item.get('offer', {}).get('offer_page_url', ''),
                        'description': item.get('product_description', '')[:200] + '...' if item.get('product_description') else ''
                    }
                    products.append(product)
                                 
                return json.dumps({
                    "success": True,
                    "products": products,
                    "total_found": len(products)
                })
            else:
                return json.dumps({
                    "success": False,
                    "error": f"API request failed with status {response.status_code}",
                    "message": "Unable to fetch products. Please check your RapidAPI key and try again.",
                    "products": []
                })
                         
        except requests.exceptions.Timeout:
            return json.dumps({
                "success": False,
                "error": "Request timeout",
                "message": "The API request timed out. Please try again later.",
                "products": []
            })
        except requests.exceptions.ConnectionError:
            return json.dumps({
                "success": False,
                "error": "Connection error",
                "message": "Unable to connect to the API. Please check your internet connection.",
                "products": []
            })
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "message": "An unexpected error occurred while fetching products.",
                "products": []
            })