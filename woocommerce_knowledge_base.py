# woocommerce_knowledge_base.py

import httpx
import json
from typing import List, Dict
import asyncio
from datetime import datetime

class WooCommerceKnowledgeBase:
    def __init__(self, woo_url: str, woo_key: str, woo_secret: str):
        self.woo_url = woo_url.rstrip('/')
        self.woo_key = woo_key
        self.woo_secret = woo_secret
        self.products = []
        self.categories = []
        self.orders = []
        self.pages = []
    
    async def fetch_all_products(self) -> List[Dict]:
        """Fetch ALL products from WooCommerce"""
        print("📦 Fetching products from WooCommerce...")
        
        all_products = []
        page = 1
        
        async with httpx.AsyncClient(
            auth=(self.woo_key, self.woo_secret),
            timeout=30
        ) as client:
            while True:
                response = await client.get(
                    f"{self.woo_url}/wp-json/wc/v3/products",
                    params={
                        "per_page": 100,
                        "page": page,
                        "orderby": "date"
                    }
                )
                
                products = response.json()
                
                if not products:
                    break
                
                # Process each product
                for product in products:
                    processed = {
                        "id": product["id"],
                        "name": product["name"],
                        "description": product.get("description", ""),
                        "price": product.get("price", "0"),
                        "regular_price": product.get("regular_price"),
                        "sale_price": product.get("sale_price"),
                        "stock_quantity": product.get("stock_quantity"),
                        "in_stock": product.get("in_stock"),
                        "categories": [cat.get("name") for cat in product.get("categories", [])],
                        "tags": [tag.get("name") for tag in product.get("tags", [])],
                        "sku": product.get("sku"),
                        "images": [img.get("src") for img in product.get("images", [])],
                        "attributes": product.get("attributes", []),
                        "related_ids": product.get("related_ids", []),
                        "short_description": product.get("short_description", ""),
                        "rating": product.get("average_rating", 0),
                        "review_count": product.get("review_count", 0)
                    }
                    
                    all_products.append(processed)
                
                print(f"  ✓ Fetched {len(all_products)} products...")
                page += 1
        
        self.products = all_products
        print(f"✅ Total products loaded: {len(all_products)}")
        return all_products
    
    async def fetch_categories(self) -> List[Dict]:
        """Fetch product categories"""
        print("📂 Fetching categories...")
        
        async with httpx.AsyncClient(
            auth=(self.woo_key, self.woo_secret),
            timeout=30
        ) as client:
            response = await client.get(
                f"{self.woo_url}/wp-json/wc/v3/products/categories",
                params={"per_page": 100}
            )
            
            self.categories = response.json()
            print(f"✅ Loaded {len(self.categories)} categories")
            return self.categories
    
    async def fetch_recent_orders(self, limit: int = 100) -> List[Dict]:
        """Fetch recent orders for context"""
        print(f"📋 Fetching {limit} recent orders...")
        
        async with httpx.AsyncClient(
            auth=(self.woo_key, self.woo_secret),
            timeout=30
        ) as client:
            response = await client.get(
                f"{self.woo_url}/wp-json/wc/v3/orders",
                params={
                    "per_page": limit,
                    "orderby": "date",
                    "order": "desc"
                }
            )
            
            self.orders = response.json()
            print(f"✅ Loaded {len(self.orders)} recent orders")
            return self.orders
            
    async def fetch_pages(self) -> List[Dict]:
        """Fetch WordPress pages (for custom info like FAQs, Policies)"""
        print("📄 Fetching store pages...")
        import re
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(
                    f"{self.woo_url}/wp-json/wp/v2/pages",
                    params={"per_page": 100}
                )
                if response.status_code == 200:
                    pages = response.json()
                    self.pages = []
                    for page in pages:
                        # Strip HTML
                        raw_content = page.get("content", {}).get("rendered", "")
                        clean_content = re.sub(r'<[^>]+>', ' ', raw_content).strip()
                        clean_content = re.sub(r'\s+', ' ', clean_content)
                        
                        self.pages.append({
                            "id": page["id"],
                            "title": page.get("title", {}).get("rendered", ""),
                            "content": clean_content,
                            "link": page.get("link", "")
                        })
                    print(f"✅ Loaded {len(self.pages)} pages")
                    return self.pages
                else:
                    print(f"⚠️ Failed to load pages: {response.status_code}")
                    self.pages = []
                    return []
            except Exception as e:
                print(f"⚠️ Error fetching pages: {e}")
                self.pages = []
                return []
    
    def create_knowledge_documents(self) -> List[Dict]:
        """Create knowledge documents from WooCommerce data"""
        print("📚 Creating knowledge base documents...")
        
        documents = []
        
        # Create documents for each product
        for product in self.products:
            doc = {
                "type": "product",
                "id": product["id"],
                "title": product["name"],
                "content": self._create_product_text(product),
                "metadata": {
                    "price": product["price"],
                    "in_stock": product["in_stock"],
                    "categories": product["categories"],
                    "rating": product["rating"],
                    "sku": product["sku"]
                }
            }
            documents.append(doc)
        
        # Create category documents
        for category in self.categories:
            doc = {
                "type": "category",
                "id": category["id"],
                "title": category["name"],
                "content": category.get("description", f"Category: {category['name']}"),
                "metadata": {
                    "category_id": category["id"]
                }
            }
            documents.append(doc)
        
        # Create summary document
        summary = {
            "type": "inventory_summary",
            "id": "summary",
            "title": "DeenCommerce Inventory Summary",
            "content": self._create_inventory_summary(),
            "metadata": {
                "total_products": len(self.products),
                "total_categories": len(self.categories)
            }
        }
        documents.append(summary)
        
        print(f"✅ Created {len(documents)} knowledge documents")
        return documents
    
    def _create_product_text(self, product: Dict) -> str:
        """Create searchable text for a product"""
        
        text = f"""Product: {product['name']}
SKU: {product['sku']}
Price: ৳{product['price']}
Stock: {product['stock_quantity'] or 'N/A'} items
Status: {'In Stock' if product['in_stock'] else 'Out of Stock'}

Description:
{product['short_description'] or product['description'][:500]}

Categories: {', '.join(product['categories'])}
Tags: {', '.join(product.get('tags', []))}

Rating: {product['rating']}/5 ({product['review_count']} reviews)
"""
        
        return text
    
    def _create_inventory_summary(self) -> str:
        """Create inventory summary document"""
        
        in_stock_count = sum(1 for p in self.products if p['in_stock'])
        out_of_stock_count = len(self.products) - in_stock_count
        total_value = sum(float(p['price'] or 0) for p in self.products)
        
        text = f"""
DeenCommerce Inventory Status
Last Updated: {datetime.now().isoformat()}

Total Products: {len(self.products)}
In Stock: {in_stock_count}
Out of Stock: {out_of_stock_count}
Total Inventory Value: ৳{total_value:,.0f}

Categories: {len(self.categories)}
Most Popular Categories: {', '.join([c['name'] for c in self.categories[:5]])}

Stock Levels:
- High Stock (100+): {sum(1 for p in self.products if p.get('stock_quantity', 0) >= 100)}
- Medium Stock (10-99): {sum(1 for p in self.products if 10 <= p.get('stock_quantity', 0) < 100)}
- Low Stock (1-9): {sum(1 for p in self.products if 1 <= p.get('stock_quantity', 0) < 10)}
- No Stock: {sum(1 for p in self.products if not p['in_stock'])}
"""
        
        return text
    
    def save_to_file(self, filename: str = "woo_knowledge_base.json"):
        """Save processed data to file"""
        data = {
            "products": self.products,
            "categories": self.categories,
            "pages": self.pages,
            "metadata": {
                "total_products": len(self.products),
                "total_categories": len(self.categories),
                "last_updated": datetime.now().isoformat(),
                "store_url": self.woo_url
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Knowledge base saved to {filename}")

# Usage
async def setup_knowledge_base(woo_url: str, woo_key: str, woo_secret: str, output_file: str = "woo_knowledge_base.json"):
    """Setup WooCommerce knowledge base"""
    
    kb = WooCommerceKnowledgeBase(
        woo_url=woo_url,
        woo_key=woo_key,
        woo_secret=woo_secret
    )
    
    # Fetch all data
    await kb.fetch_all_products()
    await kb.fetch_categories()
    await kb.fetch_pages()
    await kb.fetch_recent_orders(limit=50)
    
    # Create knowledge documents
    documents = kb.create_knowledge_documents()
    
    # Save
    kb.save_to_file(output_file)
    
    return kb, documents