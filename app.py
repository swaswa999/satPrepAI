from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_session import Session
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
import os
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True  # Requires HTTPS in production
Session(app)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def initialize_conversation():
    # Initialize conversation history in session if it doesn't exist
    if 'conversation' not in session:
        session['conversation'] = [
            {
                "role": "system", 
                "content": """You are an expert SAT/ACT test prep advisor. Your goal is to engage students in conversation about test-taking strategies and encourage them to sign up for SMS updates. Keep responses concise and focused on test prep strategies. 
                
                Key points to emphasize:
                - Most students miss points due to not knowing specific test-taking strategies
                - The tests are designed to be beaten with the right approach
                - We offer free tips and strategies via SMS
                
                Your main goal is to get their phone number to sign them up for SMS tips. After 2-3 messages, guide the conversation towards asking for their phone number to receive free test-taking strategies.
                
                If they ask about pricing or services, explain that the first tips are free and they'll get more information after signing up."""
            }
        ]
        session.modified = True

@app.route('/')
def home():
    initialize_conversation()
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        initialize_conversation()
        data = request.json
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Add user message to conversation history
        session['conversation'].append({"role": "user", "content": user_message})
        
        # Get response from OpenAI
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=session['conversation'],
                temperature=0.7,
                max_tokens=500
            )
        except Exception as e:
            print(f"OpenAI API Error: {str(e)}")
            return jsonify({'error': 'Sorry, I encountered an error. Please try again.'}), 500
        
        assistant_message = response.choices[0].message.content
        
        # Add assistant's response to conversation history
        session['conversation'].append({"role": "assistant", "content": assistant_message})
        
        # Save the session
        session.modified = True
        
        # Add booking link to the response
        booking_link = "https://calendly.com/your-booking-link"  # Replace with your actual booking link
        
        # Format the response with the booking link
        formatted_response = f"""{assistant_message}

        <div style="margin-top: 20px; padding: 15px; background-color: #f0f7ff; border-radius: 8px; border-left: 4px solid #3b82f6;">
            <p style="margin: 0 0 10px 0; font-weight: 500;">Ready to take the next step?</p>
            <a href="{booking_link}" target="_blank" style="display: inline-block; padding: 8px 16px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 4px; font-weight: 500;">
                Book Your Free Consultation Now
            </a>
        </div>"""
        
        return jsonify({
            'response': formatted_response,
            'conversation': session['conversation']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear', methods=['POST'])
def clear_conversation():
    try:
        initialize_conversation()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs('instance', exist_ok=True)  # Create instance folder for session storage
    app.run(debug=True)
