# product_embeddings.py

import json
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from db import supabase
import logging

logger = logging.getLogger(__name__)

class ProductVectorStore:
    def __init__(self):
        """Initialize product vector store"""
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.has_connection = supabase is not None
        
    def create_from_knowledge_base(self, knowledge_base_file: str = "woo_knowledge_base.json"):
        """Create embeddings for all products and save to Supabase"""
        if not self.has_connection:
            logger.error("❌ No Supabase connection available. Cannot save embeddings.")
            return

        with open(knowledge_base_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        products = data['products']
        logger.info(f"🧠 Creating and saving embeddings for {len(products)} products to Supabase...")
        
        batch_size = 50
        records = []
        for i, product in enumerate(products):
            # Create searchable text for product
            text = f"""
{product['name']}
{product.get('short_description', '')}
{product.get('description', '')}
Categories: {', '.join(product.get('categories', []))}
Tags: {', '.join(product.get('tags', []))}
Price: ৳{product['price']}
SKU: {product['sku']}
"""
            
            # Create embedding
            embedding = self.model.encode(text, convert_to_tensor=False).tolist()
            
            records.append({
                "id": product['id'],
                "content": text,
                "metadata": product,
                "embedding": embedding
            })
            
            if len(records) >= batch_size or i == len(products) - 1:
                try:
                    supabase.table("product_embeddings").upsert(records).execute()
                    records = []
                    logger.info(f"  ✓ Processed and uploaded {i + 1} products...")
                except Exception as e:
                    logger.error(f"  ❌ Failed to upload batch: {e}")
        
        logger.info("✅ Embeddings saved to Supabase successfully!")
    
    def search_products(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search products using semantic similarity via Supabase pgvector"""
        if not self.has_connection:
            return []
            
        # Create embedding for query
        query_embedding = self.model.encode(query, convert_to_tensor=False).tolist()
        
        try:
            response = supabase.rpc(
                "match_products",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": 0.2,
                    "match_count": top_k
                }
            ).execute()
            
            results = []
            if response.data:
                for row in response.data:
                    results.append({
                        "product": row["metadata"],
                        "similarity_score": row["similarity"],
                        "search_text": row["content"][:500]
                    })
            return results
        except Exception as e:
            logger.error(f"❌ Supabase semantic search error: {e}")
            return []