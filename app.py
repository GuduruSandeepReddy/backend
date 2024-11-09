from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
from pymongo import MongoClient
from cryptography.fernet import Fernet
import base64

app = Flask(__name__)
CORS(app, origins=["*"])  # Allow all origins for testing


# Encryption key setup
key = b"abcdefghijabcdefghijabcdefghij12"
key = base64.urlsafe_b64encode(key)
cipher_suite = Fernet(key)

# Load the email model and vectorizer (used for both Email and SMS)
email_model = joblib.load('EmailModel.pkl')
email_vectorizer = joblib.load('EmailVectorizer.pkl')

# Connect to MongoDB Atlas
client = MongoClient("mongodb+srv://yashwanth0110:uLtgeEmyZPyqTfp4@projectml.9omii.mongodb.net/?retryWrites=true&w=majority&appName=projectml")
db = client['projectml']
collection = db['ml']

# Home route
@app.route('/')
def home():
    return "Welcome to the Flask API!"

@app.route('/predict', methods=['POST'])
def predict():
    try:
        request_data = request.get_json()
        
        # Log incoming data
        print(f"Received request data: {request_data}")
        
        # Validate request data
        if 'data' not in request_data or 'mode' not in request_data:
            return jsonify({'error': 'Missing data or mode in the request'}), 400

        data = request_data['data']
        mode = request_data['mode']

        # Log data and mode
        print(f"Data: {data}, Mode: {mode}")

        # Use the email model and vectorizer
        transformed_data = email_vectorizer.transform([data])
        prediction = email_model.predict(transformed_data)

        prediction_label = "Safe" if prediction[0] == 0 else "Phishing"

        # Encrypt the data
        encrypted_code = cipher_suite.encrypt(data.encode('utf-8'))

        # Prepare data to insert into MongoDB
        message_data = {
            'message': encrypted_code.decode('utf-8'),
            'mode': mode,
            'prediction': prediction_label
        }
        collection.insert_one(message_data)

        # Log prediction result
        print(f"Prediction: {prediction_label}")

        return jsonify({
            'transcription': data,
            'prediction': prediction_label
        })
    except Exception as e:
        # Log the exception
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
