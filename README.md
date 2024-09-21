# Customer Service Chatbot

## Description

This application is a customer service chatbot designed to assist users with their reservations. It utilizes the OpenAI API for generating responses based on user queries, along with a set of frequently asked questions (FAQs) for context. The app allows users to validate their reservation and engage in a chat with the assistant.

## Features

- Validate reservations using a unique reservation ID.
- Chat interface for interacting with the assistant.
- Contextual responses based on user reservation details and relevant FAQs.
- Logging for monitoring application performance and errors.

## Getting Started

### Prerequisites

- Python 3.x
- Flask
- OpenAI API key
- Additional libraries (listed below)

### Installation

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/repository.git
   cd repository
   ```

2. Install the required packages:

   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables in a `.env` file:

   ```
   FLASK_SECRET_KEY=your_secret_key
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_ASSISTANT_ID=your_assistant_id
   ```

4. Make sure the necessary data files (`faq_embeddings.npy`, `faiss_index.index`, `extracted_qa_pairs.json`, and `updated_reservations_with_customer_name.json`) are present in the project directory.

### Running the Application Locally

To run the application locally, execute the following command:

```
python app.py
```

Note : Before running the app locally, you need to make the following changes in the app.py

1) In the last line of the code
   ```
   app.run(debug=True, host='0.0.0.0', port=8080)
```

The application will be accessible at `http://localhost:8080`.


## Technologies Used

- **Flask**: Web framework for building the application.
- **OpenAI API**: For handling user queries and generating responses.
- **Sentence Transformers**: For embedding FAQ questions and finding similarities.
- **FAISS**: For efficient similarity search and clustering of dense vectors.
- **NumPy**: For handling numerical data and array operations.
- **Python-dotenv**: For loading environment variables from a `.env` file.
- **Flask-CORS**: For handling Cross-Origin Resource Sharing.

## Configuration

### Environment Variables

Make sure to set the following environment variables in a `.env` file:

```
FLASK_SECRET_KEY=your_secret_key
OPENAI_API_KEY=your_openai_api_key
OPENAI_ASSISTANT_ID=your_assistant_id
```

Replace `your_secret_key`, `your_openai_api_key`, and `your_assistant_id` with your actual keys.

## File Structure

```
├── app.py                      # Main application file
├── faq_embeddings.npy          # Numpy file containing FAQ embeddings
├── faiss_index.index           # FAISS index file
├── extracted_qa_pairs.json     # JSON file with QA pairs
├── updated_reservations_with_customer_name.json  # JSON file with reservation data
├── templates                   # Folder for HTML templates
│   ├── landing.html            # Landing page template
│   └── chat.html               # Chat interface template
├── static                      # Folder for CSS & JS
│   ├── chat.js                 # JS code for the chat page
│   └── styles.css              # CSS file for the app
└── .env                        # Environment variables
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any improvements or bug fixes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```

