import os
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from openai import OpenAI
from flask_cors import CORS
from dotenv import load_dotenv
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

ASSISTANT_ID = os.environ.get('OPENAI_ASSISTANT_ID')
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Load configuration
class Config:
    EMBEDDINGS_FILE = 'faq_embeddings.npy'
    INDEX_FILE = 'faiss_index.index'
    QA_FILE = 'extracted_qa_pairs.json'
    RESERVATIONS_FILE = 'updated_reservations_with_customer_name.json'

# Load data
def load_data():
    with open(Config.RESERVATIONS_FILE, 'r', encoding='utf-8') as f:
        reservation_data = json.load(f)
    
    embeddings = np.load(Config.EMBEDDINGS_FILE)
    index = faiss.read_index(Config.INDEX_FILE)
    
    with open(Config.QA_FILE, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    return reservation_data, embeddings, index, dataset

reservation_data, embeddings, index, dataset = load_data()
model = SentenceTransformer('all-MiniLM-L6-v2')

def send_initial_context(thread_id: str, reservation: Dict):
    context_message = f"""
    Context about the customer's reservation:
    Reservation ID: {reservation['reservation_id']}
    Trip Start: {reservation['trip_start']}
    Trip End: {reservation['trip_end']}
    Trip Duration: {reservation['trip_duration']}
    Delivery Location: {reservation.get('delivery_location', '')}
    Vehicle Type: {reservation.get('vehicle_type', '')}
    Delivery Location Category: {reservation.get('delivery_location_category', '')}
    Car Product Type: {reservation.get('Car Product Type', '')}
    Customer Type: {reservation.get('Customer Type', '')}
    Customer Name: {reservation.get('customer_name', '')}
    """

    messages = reservation.get('messages', [])
    if messages:
        context_message += "\n\nPrevious conversation with the customer:\n"
        for message in messages[-10:]:  # Only include the last N messages
            context_message += f"{message['author']} ({message['created']}): {message['text']}\n"

    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=context_message
    )
    logger.info(f"Sent initial context for reservation {reservation['reservation_id']} to thread {thread_id}")

def create_new_thread(reservation: Dict) -> str:
    thread = client.beta.threads.create()
    thread_id = thread.id
    logger.info(f"Created new thread with ID: {thread_id} for reservation {reservation['reservation_id']}")
    send_initial_context(thread_id, reservation)
    return thread_id

def retrieve_faq(query: str, metadata_filters: Optional[Dict] = None, k: int = 10, similarity_threshold: float = 0.3) -> List[Dict]:
    query_embedding = model.encode([query])
    distances, indices = index.search(query_embedding, k)
    results = []

    strict_filters = [] #You can Specify Strict Filters here later
    
    for i, idx in enumerate(indices[0]):
        similarity_score = 1 - distances[0][i]
        if similarity_score > similarity_threshold:
            matched_entry = dataset[idx]
            matched_metadata = matched_entry['metadata']

            if metadata_filters and all(matched_metadata.get(field) == metadata_filters[field] for field in strict_filters):
                results.append({
                    'question': matched_entry['question'],
                    'answer': matched_entry['answer'],
                    'metadata': matched_metadata,
                    'similarity_score': similarity_score
                })

    if not results or not metadata_filters:
        return results

    filter_fields = [field for field in metadata_filters.keys() if field not in strict_filters]

    for num_filters in range(len(filter_fields), 0, -1):
        filtered_results = [
            result for result in results
            if all(result['metadata'].get(field) == metadata_filters[field] for field in filter_fields[:num_filters])
        ]
        if filtered_results:
            return filtered_results

    return results

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/validate_reservation', methods=['POST'])
def validate_reservation():
    reservation_id = request.form.get('reservation_id')
    reservation = next((r for r in reservation_data if r['reservation_id'] == int(reservation_id)), None)
    
    if reservation:
        session['reservation'] = reservation
        thread_id = create_new_thread(reservation)
        session['thread_id'] = thread_id
        return redirect(url_for('chat'))
    else:
        return render_template('landing.html', error="Invalid reservation ID")

@app.route('/chat')
def chat():
    if 'reservation' not in session or 'thread_id' not in session:
        return redirect(url_for('landing'))
    return render_template('chat.html', reservation=session['reservation'])

@app.route('/api/chat', methods=['POST'])
def chat_api():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "No message provided"}), 400

        user_message = data['message']
        reservation = session.get('reservation')
        thread_id = session.get('thread_id')

        if not reservation or not thread_id:
            return jsonify({"error": "No active reservation or thread. Please start a new conversation."}), 400

        logger.info(f"Processing chat request. Thread ID: {thread_id}, User message: {user_message}")

        metadata_filters = {
            "Customer Type": reservation.get('Customer Type', ''),
            "vehicle_type": reservation.get('vehicle_type', ''),
            "delivery_location": reservation.get('delivery_location', ''),
            "delivery_location_category": reservation.get('delivery_location_category', ''),
            "Car Product Type": reservation.get('Car Product Type', '')
        }
        retrieved_faqs = retrieve_faq(user_message, metadata_filters=metadata_filters, k=5, similarity_threshold=0.3)

        rag_context = "Related Questions from customers :\n" + "\n\n".join(f"Question: {faq['question']}\nAnswer: {faq['answer']}" for faq in retrieved_faqs)

        combined_message = f"User Query: {user_message}\n\n{rag_context}\n\nGenerate a response as a customer service rep to the User's Query based on their reservation details and the provided Related FAQ context (if relevant)."

        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=combined_message
        )
        
        run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=ASSISTANT_ID)
        logger.info(f"Created run with ID: {run.id}")

        while True:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            if run.status == "completed":
                break
            elif run.status in ["failed", "cancelled", "expired"]:
                raise Exception(f"Run failed with status: {run.status}")
            time.sleep(1)

        messages = client.beta.threads.messages.list(thread_id=thread_id, order="desc", limit=1)
        
        if not messages.data:
            raise ValueError("No messages found in the thread.")

        latest_message = messages.data[0]
        assistant_response = next((content.text.value for content in latest_message.content if content.type == 'text'), None)

        if assistant_response is None:
            raise ValueError("No text content found in the latest message")

        logger.info(f"Assistant response: {assistant_response}")

        return jsonify({
            "thread_id": thread_id,
            "reply": assistant_response
        })

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred while processing your request"}), 500

@app.template_filter('formatdate')
def format_date(value):
    date = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    return date.strftime("%B %d, %Y at %I:%M %p")

@app.route('/exit', methods=['POST'])
def exit_chat():
    session.clear()
    return redirect(url_for('landing'))

if __name__ == '____main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
