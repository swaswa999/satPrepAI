from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
from dotenv import load_dotenv
import openai
import os
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
Session(app)

# Initialize OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Initialize conversation history in session if it doesn't exist
if 'conversation' not in session:
    session['conversation'] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Add user message to conversation history
        session['conversation'].append({"role": "user", "content": user_message})
        
        # Get response from OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=session['conversation']
        )
        
        assistant_message = response.choices[0].message['content']
        
        # Add assistant's response to conversation history
        session['conversation'].append({"role": "assistant", "content": assistant_message})
        
        # Save the session
        session.modified = True
        
        return jsonify({
            'response': assistant_message,
            'conversation': session['conversation']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear', methods=['POST'])
def clear_conversation():
    try:
        session['conversation'] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]
        session.modified = True
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs('instance', exist_ok=True)  # Create instance folder for session storage
    app.run(debug=True)
