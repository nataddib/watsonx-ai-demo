from dotenv import load_dotenv
from ibm_watsonx_ai.client import APIClient
from elasticsearch import Elasticsearch, helpers
from ibm_watsonx_ai.foundation_models import Model
from datetime import datetime
import ssl
import os

# Load environment variables
load_dotenv()
es_endpoint = os.environ["es_endpoint"]
es_cert_path = os.environ["es_cert_path"]
emb_ibm_cloud_url=os.environ["emb_ibm_cloud_url"]
emb_api_key = os.environ["emb_api_key"]
emb_space_id = os.environ["emb_space_id"]
deployment_id = os.environ["deployment_id"]
api_key = os.environ["WATSONX_APIKEY"]
project_id = os.environ["WATSONX_PROJECT_ID"]
ibm_cloud_url = os.environ["IBM_CLOUD_URL"]


emb_creds = {
    "url": emb_ibm_cloud_url,
    "apikey": emb_api_key 
}

LLM_model_id =  "meta-llama/llama-3-70b-instruct"
creds = {
        "url": ibm_cloud_url,
        "apikey": api_key
    }

def connect_watsonx_llm(model_id_llm):
    model = Model(
	model_id = model_id_llm,
	params = {
        'decoding_method': "greedy",
        'min_new_tokens': 1,
        'max_new_tokens': 400,
        'temperature': 0.0,
        'repetition_penalty': 1
    },
	credentials=creds,
    project_id=project_id)
    return model

client = APIClient(credentials=emb_creds, space_id=emb_space_id)
# Connect to the Elasticsearch server

context = ssl.create_default_context(cafile=es_cert_path)
es = Elasticsearch([es_endpoint], ssl_context=context)
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


def semantic_search(search_term, top_k = 3, index_name="hr-policy-index"):
    """
    Perform a semantic search on the specified Elasticsearch index using the given search term.

    Args:
    search_term (str): The search term for the semantic search.
    top_k (int, optional) : The number of document want to retrieve from the elastic database
    index_name (str, optional): The name of the Elasticsearch index to search. Default is "hr-policy-index".
    Returns:
    dict: A dictionary with different relevant sources

    Example usage:
    >>> results = semantic_search('leave policy')
    >>> print(results)

    Note:
    Ensure the Elasticsearch index is configured for vector searches and the `scoring_embedder` function is available.
    """
    print("\nSemantic search\n")
    # Semantic search
    semantic_query = {
        "field": "vector_en",
        "query_vector": scoring_embedder(search_term),
        "k": top_k,
        "num_candidates": 20
    }

    results = {}
    i = 1
    semantic_resp_en = es.search(index=index_name, knn=semantic_query)
    for hit in semantic_resp_en['hits']['hits']:
        # print(hit['_score'])
        # print(hit['_source']['content'])
        results[f"doc{i}"] = hit['_source']['content']
        i+=1
        # results.append(hit['_source']['content'])
    return results

def send_to_watsonxai(model,
                    prompts
                    ):
    assert not any(map(lambda prompt: len(prompt) < 1, prompts)), "make sure none of the prompts in the inputs prompts are empty"
    output = []
    for prompt in prompts:
        o = model.generate_text(prompt)
        output.append(o)
    return output

def get_leave_days():
    """
    Display the number of leave days from the taken and the number of leave days left from the user that asked the question.
    This does not apply to generic workdays.

    Returns:
    dict: A dictionary containing the leave days information.
    """
    try:
        # Hardcoded values for demonstration purposes
        casual_leave_taken = 2
        casual_leave_left = 10
        earned_leave_taken = 5
        earned_leave_left = 15
        
        return {
            'casual_leave_taken': f'{casual_leave_taken} days taken',
            'casual_leave_left': f'{casual_leave_left} days left',
            'earned_leave_taken': f'{earned_leave_taken} days taken',
            'earned_leave_left': f'{earned_leave_left} days left'
        }

    except Exception as e:
        return {"error": str(e)}
    
def get_upcoming_holidays():
    """
    Retrieve a list of upcoming holidays.

    Returns:
    list: A list of dictionaries, each containing the name and date of an upcoming holiday.

    Instructions:
    1. Call the function without any arguments to get a list of upcoming holidays.
    2. The function returns a list of dictionaries, each with the holiday name and date.
    3. The holiday date is returned as a string in the format 'YYYY-MM-DD'.

    Example usage:
    >>> holidays = get_upcoming_holidays()
    >>> print(holidays)

    Note:
    This example uses a predefined list of holidays. In a real-world scenario, consider integrating with an API or a database.
    """
    # Predefined list of holidays
    holidays = [
        {"name": "New Year's Day", "date": "2024-01-01"},
        {"name": "Independence Day", "date": "2024-07-04"},
        {"name": "Thanksgiving Day", "date": "2024-11-28"},
        {"name": "Christmas Day", "date": "2024-12-25"},
        {"name": "New Year's Day", "date": "2025-01-01"},
        {"name": "Independence Day", "date": "2025-07-04"},
        {"name": "Thanksgiving Day", "date": "2025-11-27"},  # Adjusted to the correct date for 2025
        {"name": "Christmas Day", "date": "2025-12-25"},
        {"name": "New Year's Day", "date": "2026-01-01"},
        {"name": "Independence Day", "date": "2026-07-04"},
        {"name": "Thanksgiving Day", "date": "2026-11-26"},  # Adjusted to the correct date for 2026
        {"name": "Christmas Day", "date": "2026-12-25"}
    ]

    # Get today's date
    today = datetime.today().date()

    # Filter upcoming holidays
    upcoming_holidays = [holiday for holiday in holidays if datetime.strptime(holiday['date'], "%Y-%m-%d").date() > today]

    return upcoming_holidays

def extract_request_data_stream():
    try:
        request_data = request.json
        if request_data is None:
            raise ValueError("Invalid or missing JSON in request")
        return {
            'input': request_data.get('input', ''),
        }
    except Exception as e:
        app.logger.error(f"Error in extract_request_data: {e}")
        app.logger.error(traceback.format_exc())
        return None