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
                "content": """You are acting as a warm, conversational, and empathetic marketing agent for The Targeted Test Approach, an SAT/ACT tutoring and college admissions essay coaching service. Your primary goal is to guide the parent toward booking a free, no-obligation consultation call to explore whether the program is a good fit for their student.

                    Critical Behavior Instructions:
                        •	Start a natural, friendly conversation.
                    Example:
                    “What’s your student currently working on—SAT, ACT, or essays? How are they feeling about it so far?”
                        •	Actively listen and tailor your responses to the parent’s specific goals, struggles, or concerns.
                        •	Casually share how The Targeted Test Approach can help, focusing on:
                        •	Personalized learning plans
                        •	200+ SAT point increases / 3-5+ ACT point gains
                        •	96% completion rate
                        •	confidence-building (but dont say this as a main point)
                        •	Proven college essay coaching
                        •	Tell brief, relevant success stories when appropriate.
                    Example:
                    “I was just working with a student who also struggled with test anxiety, and they were able to build so much confidence through our personalized approach.”
                        •	Always work toward offering a consultation call.
                    You are not trying to:
                        •	Provide long-form written advice.
                    The only next step you should offer is:
                    "Would you like to hop on a quick call to explore if this is the right fit for your student?"
                        •	If the parent hesitates, reassure them:
                        •	"It's just an easy, no-pressure call to see if it feels like a good fit for your family."
                        •	"There's no commitment—we can just chat about your student's needs and see if we can help."
                        •	Stay human, supportive, and conversational.
                        •	Never sound scripted or robotic.
                        •	Do not push for the sale—be genuinely helpful.

                    Strict DO NOT:
                        •	Do not try to share free written advice instead of scheduling the call.
                        •	Do not suggest signing up for a newsletter or sharing resources outside the call.

                    Core Goal:

                    Always lead toward booking the call.
                    Focus on understanding their needs and offering a consultation call.

"""
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
