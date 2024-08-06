from function import scoring_embedder, semantic_search, connect_watsonx_llm, get_upcoming_holidays, get_leave_days
from prompt_template import prompt_gen
import traceback
from flask import Flask, request, Response, jsonify, make_response
import json
import time

app = Flask(__name__)
model_id_llm='meta-llama/llama-3-70b-instruct'
model_llm = connect_watsonx_llm(model_id_llm)

@app.route('/get_upcoming_holidays', methods=['POST'])
def query_upcoming_holidays():
    results = {"results": get_upcoming_holidays()}
    return results

@app.route('/get_leave_days', methods=['POST'])
def query_leave_days():
    results = {"results": get_leave_days()}
    return results

@app.route('/finding_documents', methods=['POST'])
def finding_documents():
    data = request.json
    question = data["user_query"]
    relevant_documents = semantic_search(question, 5, "hr-policy-index")
    prompt = prompt_gen(question, relevant_documents)
    print(prompt)
    start_time = time.time()
    print("THE TIME TAKEN", time.time() - start_time)
    results = {"prompt": prompt, "relevant_docs": relevant_documents}
    response = make_response(json.dumps(results, ensure_ascii=False))
    response.headers['Content-Type'] = 'application/json'
    return response


def generate_stream(input, model_llm=model_llm):
    print("INPUT", input)
    try:
        for response in model_llm.generate_text_stream(input):
            if response:
                yield f'data: {json.dumps({"results": [{"generated_text": response}]})}\n\n'
            else:
                print("ERROR: Received empty or unexpected response:", response)
    except Exception as e:
        error_message = {"error": "Exception occurred", "details": str(e)}
        print("ERROR: ", error_message)
        yield f'data: {json.dumps(error_message)}\n\n'

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


# Main route
@app.route('/generation_stream', methods=['POST'])
def stream():
    data = extract_request_data_stream()
    print("DATA,", data)
    if data is None:
        return jsonify({"error": "Error processing request data"}), 400

    return Response(generate_stream(**data), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, port=8001, host="0.0.0.0")
