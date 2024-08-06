from dotenv import load_dotenv

from ibm_watsonx_ai.client import APIClient
from elasticsearch import Elasticsearch, helpers
import os
from elasticsearch import Elasticsearch, helpers
import ssl

# Load environment variables
load_dotenv()
es_endpoint = os.environ["es_endpoint"]
es_cert_path = os.environ["es_cert_path"]
emb_ibm_cloud_url=os.environ["emb_ibm_cloud_url"]
emb_api_key = os.environ["emb_api_key"]
emb_space_id = os.environ["emb_space_id"]
deployment_id = os.environ["deployment_id"]

emb_creds = {
    "url": emb_ibm_cloud_url,
    "apikey": emb_api_key 
}

client = APIClient(credentials=emb_creds, space_id=emb_space_id)

context = ssl.create_default_context(cafile=es_cert_path)

# Connect to the Elasticsearch server
es = Elasticsearch([es_endpoint], ssl_context=context)


def creating_index_body(index_name, dimension=768):
    # Create index with mapping for embeddings
    # index_name = "test-index-2"
    create_index_body = {
        "settings": {
            "index": {
            "analysis": {
                "analyzer": {
                "analyzer_shingle": {
                    "tokenizer": "icu_tokenizer",
                    "filter": [
                    "filter_shingle"
                    ]
                }
                },
                "filter": {
                "filter_shingle": {
                    "type": "shingle",
                    "max_shingle_size": 3,
                    "min_shingle_size": 2,
                    "output_unigrams": "true"
                }
                }
            }
            }
        },  
        "mappings": {
            "properties": {
                "en_character": {"type": "text"},
                "en_character_description": {"type": "text", "analyzer": "analyzer_shingle"},
                "vector_en": {
                    "type": "dense_vector",
                    "dims": dimension,
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
    }
    if not es.indices.exists(index=index_name):
        print(f"Index '{index_name}' does not exist. Creating a new one")
    else:
        response = es.indices.delete(index=index_name)
        print(f"Index '{index_name}' deleted successfully.")
    es.indices.create(index=index_name, body=create_index_body)

def scoring_embedder(sentence):
    payload = {
        'input_data': [
            {
                'values': [
                    [sentence]
                ]
            }
        ]
    }

    return client.deployments.score(deployment_id, payload)["predictions"][0]["values"][0][1]

def ingestion_data_to_elastic(index_name, dataframe):
    # Index the documents with semantic embeddings and raw text
    for i in range(len(dataframe)):
        # Generate embeddings
        title = dataframe.iloc[i]["title"]
        page_number = dataframe.iloc[i]["page_number"]
        chunk_content = dataframe.iloc[i]["chunk_content"]
        embedding = scoring_embedder(chunk_content)

        # Index document with both raw text and embeddings
        res = es.index(index=index_name, id=i, body={
            'title': title,
            'content': chunk_content,
            'timestamp': page_number,
            'vector_en': embedding  # Store embedding
        })
        print(f"Document {i} indexing result: {res['result']}")


## Search

def get_all(index_name):
    # Get all data
    resp = es.search(index=index_name, query={"match_all":{}})
    for hit in resp['hits']['hits']:
        # print("HIT")
        print(hit['_source']["content"])

def fuzzy_search(index_name, search_term):
    # search_term = "Elasticsearch?"  # Intentionally misspelled for demonstration

    print("\nFuzzy search\n")
    # Fuzzy search
    fuzzy_query = {
        "query": {
            "fuzzy": {
                "en_character": {
                    "value": search_term,
                    "fuzziness": "AUTO"  # You can adjust the fuzziness level
                }
            }
        }
    }

    res = es.search(index=index_name, body=fuzzy_query)
    print(f"Got {res['hits']['total']['value']} Hits:")
    for hit in res['hits']['hits']:
        print(f"Document: {hit['_source']['content']}")

def semantic_search(index_name, search_term):
    print("\nSemantic search\n")
    # Semantic search
    semantic_query_en = {
        "field": "vector_en",
        "query_vector": scoring_embedder(search_term),
        "k": 4,
        "num_candidates": 20
    }


    semantic_resp_en = es.search(index=index_name, knn=semantic_query_en)
    for hit in semantic_resp_en['hits']['hits']:
        print(hit['_score'])
        print(hit['_source']['content'])