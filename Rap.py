import streamlit as st
import requests
import json
from datetime import datetime

# 👇 Secure API key handling (Streamlit Secrets only)
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]

# App UI
st.set_page_config(page_title="AI Fitness Coach", layout="wide")
st.title("Sportify")
st.caption("Create your personalized training plan")

# User Inputs
with st.form("inputs"):
    col1, col2 = st.columns(2)
    with col1:
        sport = st.text_input("Sport", placeholder="e.g., Wheelchair Basketball", key="sport")
        difficulty = st.select_slider("Skill Level", ["Newbie", "Experienced", "Professional"])
    with col2:
        disability = st.text_input("Disabilities", placeholder="e.g., Amputee, Visual Impairment")
        equipment = st.text_input("Equipment Availability", placeholder="e.g., No equipment available, Access to equipment")
        culture = st.text_input("Cultural Preferences", placeholder="e.g., Halal, Kosher")
        diet = st.text_input("Diet Plan", placeholder="e.g., High-protein, Vegetarian")

    generate_btn = st.form_submit_button("Generate Plan", type="primary")

# API Call Function
def call_deepseek(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "Fitness Plan Generator"
    }

    payload = {
        "model": "deepseek/deepseek-r1:free",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1500
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=45
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        if hasattr(e, 'response') and e.response:
            st.error(f"Details: {e.response.text}")
        return None

# Generate Plan
if generate_btn and sport:
    if not OPENROUTER_API_KEY:
        st.error("API key not configured! Please set it in Streamlit Secrets.")
    else:
        with st.spinner("🧠 Designing your custom training plan..."):
            prompt = f"""Create a {difficulty} {sport} training plan for:
            - Physical needs: {disability if disability else "None"}
            - Cultural/religious: {culture if culture else "None"}
            - Equipment availability: {equipment if equipment else "None"}

            Include:
            1. Warm-up (dynamic exercises)
            2. Main workout (3-5 adapted exercises)
            3. Cooldown (static stretches)
            4. Safety precautions
            5. Equipment suggestions

            Format in markdown with bullet points."""

            result = call_deepseek(prompt)

            if result:
                plan = result["choices"][0]["message"]["content"]
                st.subheader(f"Your {sport} Plan ({difficulty})")
                st.markdown(plan)

                st.download_button(
                    label="Save Plan",
                    data=plan,
                    file_name=f"{sport.replace(' ', '_')}_plan.md",
                    mime="text/markdown"
                )
            else:
                st.error("Failed to generate plan. Please try again.")