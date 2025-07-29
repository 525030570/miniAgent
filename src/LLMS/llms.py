import os
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
load_dotenv()



llm = ChatOpenAI(
    model=os.getenv("online_chat_model_name"), 
    temperature=0.0,
    api_key=os.getenv("online_model_API_KEY"),
    base_url=os.getenv("online_model_API_URL"),
)



embeddings = OpenAIEmbeddings(
    model=os.getenv("online_embedding_model_name"),
    api_key=os.getenv("online_embedding_model_API_KEY"),
    base_url=os.getenv("online_embedding_model_API_URL"),
)
