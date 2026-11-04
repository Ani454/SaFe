
import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from mistralai.client import Mistral
load_dotenv(); 
es = Elasticsearch(os.environ["ES_URL"], api_key=os.environ["ES_API_KEY"]); 
print("Elasticsearch connected:", es.info()["version"]["number"]); 
mistral = Mistral(api_key=os.environ["MISTRAL_API_KEY"]); 
print("Mistral connected:", len(mistral.models.list().data), "models available")


