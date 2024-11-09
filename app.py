from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
from pymongo import MongoClient
from cryptography.fernet import Fernet
import base64

app = Flask(__name__)
CORS(app)

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

@app.route('/predict', methods=['POST'])
def predict():
    try:
        request_data = request.get_json()

        # Validate request data
        if 'data' not in request_data or 'mode' not in request_data:
            return jsonify({'error': 'Missing data or mode in the request'}), 400

        data = request_data['data']
        mode = request_data['mode']

        # Use the email model and vectorizer for both Email and SMS modes
        transformed_data = email_vectorizer.transform([data])
        prediction = email_model.predict(transformed_data)

        # Convert prediction to a label
        prediction_label = "Safe" if prediction[0] == 0 else "Phishing"

        # Encrypt the data
        encrypted_code = cipher_suite.encrypt(data.encode('utf-8'))

        # Prepare data to insert into MongoDB
        message_data = {
            'message': encrypted_code.decode('utf-8'),
            'mode': mode,  # Store the mode (Email or SMS) as provided by the frontend
            'prediction': prediction_label
        }
        collection.insert_one(message_data)

        # Return the response
        return jsonify({
            'transcription': data,
            'prediction': prediction_label
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
