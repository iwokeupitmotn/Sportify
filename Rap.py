import streamlit as st
import requests
import time
import os
from itertools import cycle

# ANIMATION CONTROLS
PROGRESS_SHIMMER_SPEED = "2"  # "0.5s" for faster, "3s" for slower shimmer
PROGRESS_FILL_SPEED = 0.2  # 0.05 for faster, 0.2 for slower filling
LOADING_ANIMATION_SPEED = 0.3  # Time between animation frames

# Secure API key handling (Streamlit Secrets only)
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]

# Set page config
st.set_page_config(page_title="Sportify AI - Your AI Fitness Coach", layout="wide")

# Custom CSS with adjustable animation
st.markdown(f"""
<style>
    /* Cursor styles */
    div[data-baseweb="select"] div,
    div[data-baseweb="select"] div[role="button"],
    div[role="listbox"] div,
    button {{
        cursor: pointer !important;
    }}

    /* Progress bar animation */
    .stProgress > div > div > div > div {{
        background-image: linear-gradient(
            to right,
            #4CAF50,
            #8BC34A,
            #4CAF50
        );
        background-size: 200% 100%;
        animation: progressAnimation {PROGRESS_SHIMMER_SPEED} linear infinite;
    }}

    @keyframes progressAnimation {{
        0% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}
    
    /* Button container styling */
    .button-container {{
        display: flex;
        gap: 10px;
        margin-top: 20px;
    }}
    
    /* Loading animation */
    .loading-text {{
        font-size: 1.1rem;
        margin-bottom: 1rem;
    }}
</style>
""", unsafe_allow_html=True)

# Language dictionary
translations = {
    "English": {
        "title": "Sportify",
        "subtitle": "Create your personalized training plan",
        "sport": "Sport",
        "sport_placeholder": "e.g., Football, Soccer",
        "skill_level": "Skill Level",
        "skill_levels": ["Beginner", "Intermediate", "Advanced", "Professional"],
        "duration": "Training duration",
        "disabilities": "Disabilities",
        "disabilities_placeholder": "e.g., Amputee, Visual Impairment",
        "equipment": "Equipment Availability",
        "equipment_placeholder": "e.g., No equipment available, Access to equipment",
        "culture": "Cultural Preferences",
        "culture_placeholder": "e.g., Halal, Kosher",
        "diet": "Diet Plan",
        "diet_placeholder": "e.g., High protein, Vegetarian",
        "generate_btn": "Generate Plan",
        "loading_text": "🧠 Designing your custom training plan",
        "api_warning": "Please add your OpenRouter API key in the code!",
        "plan_title": "Your {} Plan ({})",
        "save_btn": "Save Plan",
        "translate_btn": "Translate Plan",
        "error_message": "Failed to generate plan. Check your API key and try again.",
        "prompt_instruction": "Respond in English.",
        "translation_loading": "Translating your plan..."
    },
    "Русский": {
        "title": "Sportify",
        "subtitle": "Создайте свой персональный план тренировок",
        "sport": "Спорт",
        "sport_placeholder": "напр., Футбол, Волейбол",
        "skill_level": "Уровень подготовки",
        "skill_levels": ["Новичок", "Любитель", "Опытный", "Профессионал"],
        "duration": "Продолжительность обучения",
        "disabilities": "Ограничения",
        "disabilities_placeholder": "напр., Ампутация, Нарушение зрения",
        "equipment": "Доступное оборудование",
        "equipment_placeholder": "напр., Нет оборудования, Есть доступ к оборудованию",
        "culture": "Культурные/религиозные предпочтения",
        "culture_placeholder": "напр., Халяль, Кошер",
        "diet": "План питания",
        "diet_placeholder": "напр., Высокобелковая, Вегетарианская",
        "generate_btn": "Создать план",
        "loading_text": "🧠 Создаем ваш индивидуальный план тренировок",
        "api_warning": "Пожалуйста, добавьте ваш API ключ в код!",
        "plan_title": "Ваш план по {} ({})",
        "save_btn": "Сохранить план",
        "translate_btn": "Перевести план",
        "error_message": "Не удалось создать план. Проверьте API ключ и попробуйте снова.",
        "prompt_instruction": "Отвечайте на русском языке.",
        "translation_loading": "Перевод вашего плана..."
    },
    "O`zbek": {
        "title": "Sportify",
        "subtitle": "Shaxsiy mashq rejangizni yarating",
        "sport": "Sport",
        "sport_placeholder": "masalan, Futbol, Voleybol",
        "skill_level": "Mahorat darajasi",
        "skill_levels": ["Boshlang'ich", "O'rta", "Yuqori", "Professional"],
        "duration": "Mashg`ulotlar davomiyligi",
        "disabilities": "Nogironliklar",
        "disabilities_placeholder": "masalan, amputatsiya, ko'rish qiyinchiligi",
        "equipment": "Mavjud jihozlar",
        "equipment_placeholder": "masalan, Jihozlar mavjud emas, Jihozlar yetarli",
        "culture": "Madaniy/diniy afzalliklar",
        "culture_placeholder": "masalan, Halol, Kosher",
        "diet": "Ovqatlanish rejasi",
        "diet_placeholder": "masalan, Oqsilli, Vegetarian",
        "generate_btn": "Reja yaratish",
        "loading_text": "🧠 Siz uchun maxsus mashq rejasi tayyorlanmoqda",
        "api_warning": "Iltimos, kodga OpenRouter API kalitingizni qo`shing!",
        "plan_title": "Sizning {} rejangiz ({})",
        "save_btn": "Rejani saqlash",
        "translate_btn": "Rejani tarjima qilish",
        "error_message": "Reja yaratib bo`lmadi. API kalitingizni tekshirib, qayta urinib ko`ring.",
        "prompt_instruction": "Javobni o'zbek tilida bering.",
        "translation_loading": "Rejangiz tarjima qilinmoqda..."
    }
}

# Animation frames
loading_frames = ["", ".", "..", "...", "...."]

# Initialize session state
if 'original_plan' not in st.session_state:
    st.session_state.original_plan = None
if 'current_plan' not in st.session_state:
    st.session_state.current_plan = None
if 'current_language' not in st.session_state:
    st.session_state.current_language = "English"
if 'translation_in_progress' not in st.session_state:
    st.session_state.translation_in_progress = False
if 'generation_in_progress' not in st.session_state:
    st.session_state.generation_in_progress = False

# Language selection
with st.sidebar:
    language = st.selectbox("Language | Til | Язык", ["English", "O`zbek", "Русский"])
lang = translations[language]

# App UI
st.title(lang["title"])
st.caption(lang["subtitle"])

# User Inputs
with st.form("inputs"):
    col1, col2 = st.columns(2)
    with col1:
        sport = st.text_input(lang["sport"], placeholder=lang["sport_placeholder"])
        difficulty = st.select_slider(lang["skill_level"], lang["skill_levels"])
        duration = st.slider(lang["duration"], min_value=1, max_value=30, value=7)
    with col2:
        disability = st.text_input(lang["disabilities"], placeholder=lang["disabilities_placeholder"])
        equipment = st.text_input(lang["equipment"], placeholder=lang["equipment_placeholder"])
        culture = st.text_input(lang["culture"], placeholder=lang["culture_placeholder"])
        diet = st.text_input(lang["diet"], placeholder=lang["diet_placeholder"])
    generate_btn = st.form_submit_button(lang["generate_btn"], type="primary")

# Animated loading text function
def show_loading_animation(text, key):
    loading_placeholder = st.empty()
    for frame in cycle(loading_frames):
        if not st.session_state.get(key, False):
            break
        loading_placeholder.markdown(f"<div class='loading-text'>{text}{frame}</div>", unsafe_allow_html=True)
        time.sleep(LOADING_ANIMATION_SPEED)
    loading_placeholder.empty()

# API Call Function
def call_deepseek(prompt):
    st.session_state.generation_in_progress = True
    progress_bar = st.progress(0)
    
    # Start loading animation in a separate thread
    import threading
    animation_thread = threading.Thread(
        target=show_loading_animation,
        args=(lang["loading_text"], "generation_in_progress")
    )
    animation_thread.start()

    try:
        # Initial progress
        for i in range(10, 31, 5):
            progress_bar.progress(i)
            time.sleep(PROGRESS_FILL_SPEED)

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

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=45
        )

        # Main progress
        for i in range(35, 81, 5):
            progress_bar.progress(i)
            time.sleep(PROGRESS_FILL_SPEED)

        response.raise_for_status()
        result = response.json()

        time.sleep(3)

        # Final progress
        for i in range(85, 101, 3):
            progress_bar.progress(i)
            time.sleep(PROGRESS_FILL_SPEED * 0.6)  # Slightly faster finish

        return result
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None
    finally:
        st.session_state.generation_in_progress = False
        progress_bar.empty()
        animation_thread.join()

# Translation Function
def translate_plan(plan_text, target_language):
    st.session_state.translation_in_progress = True
    
    # Start loading animation in a separate thread
    import threading
    animation_thread = threading.Thread(
        target=show_loading_animation,
        args=(translations[st.session_state.current_language]["translation_loading"], "translation_in_progress")
    )
    animation_thread.start()
    
    try:
        prompt = f"Translate this fitness plan to {target_language}. Keep all markdown formatting exactly the same, only translate the text:\n\n{plan_text}"
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "Fitness Plan Translator"
        }

        payload = {
            "model": "deepseek/deepseek-r1:free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 2000
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )

        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        st.error(f"Translation Error: {str(e)}")
        return None
    finally:
        st.session_state.translation_in_progress = False
        animation_thread.join()

# Generate Plan
if generate_btn and sport:
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "your_api_key_here":
        st.warning(lang["api_warning"])
    else:
        prompt = f"""{lang['prompt_instruction']}
        Create a {difficulty} level {duration}-day {sport} training plan for:
        - Physical needs: {disability if disability else "None"}
        - Cultural/religious: {culture if culture else "None"}
        - Equipment availability: {equipment if equipment else "None"}
        - Diet types: {diet if diet else "None"}

        Include:
        1. Warm-up (dynamic exercises)
        2. Main workout (3-5 adapted exercises)
        3. Cooldown (static stretches)
        4. Safety precautions
        5. Equipment suggestions

        Format in markdown with bullet points (with •).
        Make the plan for {duration} days with different plans for everyday.
        You can group days (like day 5-8) if the training is for a long period"""

        result = call_deepseek(prompt)

        if result:
            plan = result["choices"][0]["message"]["content"]
            st.session_state.original_plan = plan
            st.session_state.current_plan = plan
            st.session_state.current_language = language

# Display Plan
if st.session_state.current_plan:
    st.subheader(translations[st.session_state.current_language]["plan_title"].format(sport, difficulty))
    
    with st.container(border=True):
        st.markdown(st.session_state.current_plan)
    
    # Translation options - exclude current language
    translate_options = [lang for lang in translations.keys() if lang != st.session_state.current_language]
    selected_translation = st.selectbox(lang["translate_btn"], translate_options)
    
    col1, col2 = st.columns(2)
    with col1:
        # Download as TXT file
        st.download_button(
            label=translations[st.session_state.current_language]["save_btn"],
            data=st.session_state.current_plan,
            file_name=f"{sport.replace(' ', '_')}_plan_{st.session_state.current_language}.txt",
            mime="text/plain"
        )
    with col2:
        if st.button(translations[st.session_state.current_language]["translate_btn"]):
            if not st.session_state.translation_in_progress:
                translated_plan = translate_plan(st.session_state.original_plan, selected_translation)
                if translated_plan:
                    st.session_state.current_plan = translated_plan
                    st.session_state.current_language = selected_translation
                    st.rerun()

if generate_btn and sport and not st.session_state.current_plan:
    st.error(lang["error_message"])