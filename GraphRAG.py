from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("URI")
USERNAME = os.getenv("NEOUSERNAME")
PASSWORD = os.getenv("PASSWORD")


driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

#fetching multiple ingredient at once
def fetch_ingredient_info(ingredient_list):
    """Fetches ingredient data in bulk from Neo4j, filtering by the provided list."""
    with driver.session() as session:
        result = session.run("""
            MATCH (i:Ingredient)
            WHERE i.name IN $ingredients
            OPTIONAL MATCH (i)-[:HAS_RISK]->(r:Risk)
            OPTIONAL MATCH (i)-[:CAUSES]->(e:Effect)
            OPTIONAL MATCH (i)-[:BELONGS_TO]->(c:Category)
            RETURN i.name AS Ingredient, r.level AS Risk, 
                   COLLECT(DISTINCT e.description) AS Health_Effects, 
                   c.name AS Product_Type;
        """, ingredients=ingredient_list)
        return [record for record in result]  
