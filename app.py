import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
import os

# Get configuration from environment variables
SPEECH_KEY = os.getenv('AZURE_SPEECH_KEY', st.secrets["azure"]["speech_key"])
SPEECH_REGION = os.getenv('AZURE_SPEECH_REGION', st.secrets["azure"]["speech_region"])
FUNCTION_URL = os.getenv('AZURE_FUNCTION_URL', st.secrets["azure"]["function_url"])

# Initialize speech configuration
def init_speech_config():
    try:
        speech_config = speechsdk.SpeechConfig(
            subscription=SPEECH_KEY, 
            region=SPEECH_REGION
        )
        return speechsdk.SpeechRecognizer(speech_config=speech_config)
    except Exception as e:
        st.error(f"Failed to initialize speech configuration: {str(e)}")
        return None

# Main application
def main():
    st.set_page_config(
        page_title="Auto Service Analytics", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("Auto Service Analytics Dashboard")
    
    # Sidebar
    with st.sidebar:
        st.header("Voice Commands")
        if st.button("🎤 Start Voice Command"):
            recognizer = init_speech_config()
            if recognizer:
                with st.spinner("Listening..."):
                    result = recognizer.recognize_once()
                    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                        query_text = result.text
                        st.success(f"Recognized: {query_text}")
                        process_query(query_text)
                    else:
                        st.error("Sorry, I couldn't understand that. Please try again.")
        
        st.markdown("---")
        st.markdown("""
        ### Sample Commands:
        - "Show total revenue for last month"
        - "Display vehicle types as pie chart"
        - "Show technician performance"
        """)

def process_query(query_text):
    try:
        with st.spinner("Processing query..."):
            response = requests.post(
                FUNCTION_URL,
                json={"query": query_text},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                display_results(data)
            else:
                st.error(f"Error: {response.status_code}")
    except Exception as e:
        st.error(f"Failed to process query: {str(e)}")

def display_results(data):
    if not data or 'data' not in data:
        st.warning("No data available")
        return
        
    viz_type = data.get('visualizationType', 'table')
    
    if viz_type == 'bar':
        fig = px.bar(data['data'], x='name', y='value', title=data.get('title', ''))
        st.plotly_chart(fig, use_container_width=True)
    
    elif viz_type == 'pie':
        fig = px.pie(data['data'], names='name', values='value', title=data.get('title', ''))
        st.plotly_chart(fig, use_container_width=True)
    
    elif viz_type == 'line':
        fig = px.line(data['data'], x='name', y='value', title=data.get('title', ''))
        st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.write(data['data'])

if __name__ == "__main__":
    main()
