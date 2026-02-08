import json
import pymongo
import os
# Import AzureChatOpenAI instead of ChatOpenAI
from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- Azure OpenAI Configuration ---
# You can set these in your environment variables or replace them here
AZURE_OPENAI_API_KEY = "your_azure_api_key"
AZURE_OPENAI_ENDPOINT = "https://your-resource-name.openai.azure.com/"
AZURE_DEPLOYMENT_NAME = "your_deployment_name" # The name of your model deployment
API_VERSION = "2023-05-15" # Check Azure docs for the latest version

# --- MongoDB Configuration ---
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "your_database_name"
COLLECTION_NAME = "your_collection_name"

# 1. Initialize MongoDB Connection
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# 2. Get Schema Context
def get_schema_context(coll):
    """
    Retrieves a sample document to provide context to the LLM.
    """
    sample_doc = coll.find_one()
    if sample_doc:
        sample_doc.pop('_id', None)
        return json.dumps(sample_doc, indent=2, default=str)
    return "Collection is empty."

# 3. Initialize Azure Chat OpenAI
# This is the core change for Azure integration
llm = AzureChatOpenAI(
    azure_deployment=AZURE_DEPLOYMENT_NAME,
    openai_api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=API_VERSION,
    temperature=0
)

# 4. Define English Prompt Template
prompt_template = ChatPromptTemplate.from_messages([
    ("system", """
    You are a MongoDB expert. Given the schema below, generate a valid MongoDB Query (JSON).
    
    SCHEMA:
    {schema}
    
    RULES:
    1. Return ONLY the JSON query object for the .find() method.
    2. Do not explain. Do not use markdown backticks like ```json.
    3. Ensure field names match the schema provided.
    """),
    ("human", "{user_input}")
])

# 5. Execution Logic
def run_azure_query(user_question):
    schema = get_schema_context(collection)
    
    # Building the chain
    chain = prompt_template | llm | StrOutputParser()
    
    print(f"--- User Question: {user_question} ---")
    
    try:
        # Get raw response from Azure
        raw_query = chain.invoke({
            "schema": schema,
            "user_input": user_question
        })
        
        # Parse and clean query
        clean_query = raw_query.strip().replace("```json", "").replace("```", "")
        query_dict = json.loads(clean_query)
        
        print(f"Generated MQL: {query_dict}")
        
        # Execute query
        results = list(collection.find(query_dict).limit(5))
        return results

    except Exception as e:
        return f"Process failed: {str(e)}"

# --- Run Test ---
if __name__ == "__main__":
    # Example: "Find items with price greater than 100"
    question = "Tìm sản phẩm có giá lớn hơn 100"
    print(run_azure_query(question))