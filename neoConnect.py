from neo4j import GraphDatabase
import pandas as pd
import os
from dotenv import load_dotenv

df = pd.read_excel("ingredients.xlsx")

df = df[["Ingredient", "Harmful (Label)", "Reason", "Product Type"]]

# Convert 'Harmful (Label)' from 0/1 to meaningful labels
df["Harmful (Label)"] = df["Harmful (Label)"].map({0: "Safe", 1: "Harmful"})

print(df.head())



URI = os.getenv("URI")
USERNAME = os.getenv("NEOUSERNAME")
PASSWORD = os.getenv("PASSWORD")


# Connect to Neo4j Aura
driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def create_graph(tx, ingredient, harmful_label, reason, product_type):
    tx.run("""
        MERGE (i:Ingredient {name: $ingredient})
        MERGE (r:Risk {level: $harmful_label})
        MERGE (c:Category {name: $product_type})
        
        MERGE (i)-[:HAS_RISK]->(r)
        MERGE (i)-[:BELONGS_TO]->(c)
        
        FOREACH (_ IN CASE WHEN $reason <> "None" THEN [1] ELSE [] END |
            MERGE (e:Effect {description: $reason})
            MERGE (i)-[:CAUSES]->(e)
        )
    """, ingredient=ingredient, harmful_label=harmful_label, reason=reason, product_type=product_type)


with driver.session() as session:
    for _, row in df.iterrows():
        session.write_transaction(create_graph, row["Ingredient"], row["Harmful (Label)"], row["Reason"], row["Product Type"])

print("Data successfully imported into Neo4j!")
