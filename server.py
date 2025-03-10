from flask import Flask, request, jsonify
from groq import Groq
import os
from dotenv import load_dotenv
from GraphRAG import fetch_ingredient_info
import re


load_dotenv()


app = Flask(__name__)


api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

def extract_ingredients(text):
    """Extracts ingredients from OCR text, handling capitalization properly."""
    text = re.sub(r"\s+", " ", text.strip())
    match = re.search(r"(?i)ingredients:\s*(.*)", text)
    if match:
        text = match.group(1)
    ingredients = re.split(r",\s*", text)
    final_ingredients = []
    for item in ingredients:
        final_ingredients.extend(item.split(" & "))
    def format_ingredient(ing):
        ing = ing.lower().rstrip(".")  
        words = ing.split()
        return " ".join(word.capitalize() for word in words) if words else ""

    return [format_ingredient(i) for i in final_ingredients if i.strip()]


@app.route('/process_ingredients', methods=['POST'])
def process_ingredients():
    try:
        data = request.json
        sendtextAI = data.get('sendtextAI', '')
        health_conditions = data.get('healthConditions', ["", "", ""])

        ingredient_list = extract_ingredients(sendtextAI)
        found_ingredients = fetch_ingredient_info(ingredient_list)


        if found_ingredients:
            graph_context = "\n".join(
                [
                    f"Ingredient: {i['Ingredient']}\nRisk Level: {i['Risk']}\nHealth Effects: {', '.join(i['Health_Effects'])}\nProduct Type: {i['Product_Type']}\n"
                    for i in found_ingredients
                ]
            )
        else:
            graph_context = "No pre-existing knowledge found for the provided ingredients."



        system_instruction = f'''
        You are an Ingredient Validator. Only analyze and summarize ingredient lists from packaged food. Use the If the text does not clearly contain ingredients, respond only with: "The provided text is not an ingredient list," and do not provide any further interpretation or summary:

        1. The primary task is to generate a summary of ingredients from the text extracted from an ingredient list on packaged foods.

        2. The summary should:
            - Include a brief list of key ingredients and their summary.
            - Specifically highlight any substances that might not be healthy for user found in the ingredients, if present.
        3. Text provided is extracted via OCR, so there may be spelling or recognition errors. Based on context, accurately predict ingredient names and correct obvious misspellings wherever possible.

        4. Communicate directly to the user in clear and formal language, maintaining abstraction by avoiding overly technical or informal explanations.

        5. Do not use Markdown, as the app cannot render it. But please give new lines for different lines and format it as much as you can without using markdown to make it look good. Give 2 new lines to separate different lines. Give response as points not in a single paragraph.

        6. If the text provided does not appear to contain an ingredient list, clarify to the user that no relevant ingredients were found and refrain from further comments.

        7. MOST IMPORTANT: If the text is not related to ingredient list, say it directly to the user and do not give any other input at all cost. Do not give any comment if the given text is not about product ingredient. No other text than ingredient summarization and guidance on that, DO NOT summarize any other thing. Instead, respond with exactly: "The provided text is not an ingredient list."

        8. Consider the patient's history when crafting your response. Personalize the guidance based on the specific health conditions provided (if these some values are false or empty then ignore these conditions):
            - Diabetic Status: {health_conditions[0]}
            - Hypertensive Status: {health_conditions[1]}
            - Custom Condition: {health_conditions[2]}
            This ensures that the recommendations are relevant, beneficial, and tailored to the individual's health profile. If some ingredient may cause problems with these particular symptoms, then call it out.

        9. The following pre-existing knowledge is available about some ingredients:
            {graph_context}
        10. If external information for any ingredient in {ingredient_list} is not in {graph_context} then generate with your general knowledge.
        '''

        
        message = ", ".join(ingredient_list) + f"  Health conditions: {health_conditions[0]}, {health_conditions[1]}, {health_conditions[2]}: [Personalize response based on these]"

        # Call Groq API
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": message}
            ],
            temperature=0,
            max_tokens=8000,
            top_p=0.95,
            stream=False,
            stop=None,
        )

        # Extract response
        response_text = completion.choices[0].message.content

        # Return the response
        return jsonify({"response": response_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
