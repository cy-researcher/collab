import streamlit as st
import json
import requests
import time

# --- Configuration ---
# You must set your API Key in Streamlit Secrets manager under the key 'GEMINI_API_KEY'
# DO NOT include a hardcoded key here.
API_KEY = st.secrets.get("GEMINI_API_KEY", "")
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"

# --- Helper Functions ---

def call_gemini_api(prompt, system_instruction, max_retries=3):
    """Handles the API call with exponential backoff."""
    if not API_KEY:
        st.error("API Key not found. Please set 'GEMINI_API_KEY' in Streamlit secrets.")
        return None

    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(f"{API_URL}?key={API_KEY}", headers=headers, json=payload, timeout=30)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            result = response.json()
            if result.get("candidates") and result["candidates"][0]["content"]["parts"][0].get("text"):
                return result["candidates"][0]["content"]["parts"][0]["text"]
            else:
                st.error("AI response was empty or malformed.")
                return None
        except requests.exceptions.RequestException as e:
            st.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                sleep_time = 2 ** attempt
                time.sleep(sleep_time)
            else:
                st.error("Failed to get a response from the AI after multiple retries.")
                return None
        except json.JSONDecodeError:
            st.error("Failed to decode JSON response from AI.")
            return None

    return None

# --- Application UI and Logic ---

def main():
    st.set_page_config(
        page_title="The Idea Forge: HI + GenAI Collaboration",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("💡 The Idea Forge: Collaborative Prompt Engineering")
    st.markdown("---")

    # Phase 1: Human Intelligence Initiation
    st.header("1. Human Input: The Seed Idea")
    raw_idea = st.text_area(
        "Start with a vague or simple concept:",
        "A detective story set in the future.",
        height=100,
        key="raw_idea"
    )

    if st.button("Generate AI Suggestions", key="suggest_button"):
        if raw_idea:
            with st.spinner("GenAI is brainstorming refinements..."):
                system_prompt_suggestions = (
                    "You are a creative brainstorming partner. The user is providing a rough story idea. "
                    "Your task is to provide 3 distinct, structured creative elements to refine this idea. "
                    "Format your response strictly using this structure: "
                    "**GENRE VARIANT:** [A specific sub-genre suggestion]\n\n"
                    "**KEY CONFLICT:** [A high-stakes, specific conflict idea]\n\n"
                    "**ATMOSPHERE/TONE:** [A unique tone or style suggestion]\n\n"
                    "Keep all suggestions concise (under 10 words each) and impactful. Do not add any introductory or concluding text."
                )

                ai_suggestions = call_gemini_api(
                    f"Rough Idea: {raw_idea}",
                    system_prompt_suggestions
                )

                if ai_suggestions:
                    st.session_state['ai_suggestions'] = ai_suggestions
                    # Pre-populate the refinement area with the AI's output for editing
                    st.session_state['refined_prompt'] = f"Seed Idea: {raw_idea}\n\nAI Suggestions:\n{ai_suggestions}"
                else:
                    st.error("Could not generate suggestions.")

    st.markdown("---")

    # Phase 2: Human Intelligence Refinement (The Collaboration)
    st.header("2. HI + GenAI Collaboration: Refine the Prompt")

    if 'ai_suggestions' in st.session_state:
        st.markdown("**AI Suggestions for refinement (for reference):**")
        st.info(st.session_state['ai_suggestions'])

        st.markdown("Use your judgment to edit, combine, and select the best elements below to create the final, polished prompt.")
        final_prompt_text = st.text_area(
            "Final, Collaboratively Engineered Prompt:",
            value=st.session_state.get('refined_prompt', ''),
            height=250,
            key="final_prompt_text"
        )

        # Phase 3: GenAI Execution
        st.header("3. GenAI Execution: Final Output")
        if st.button("Generate Final Story Summary", key="execute_button"):
            if final_prompt_text:
                with st.spinner("Generating final content based on the perfected prompt..."):
                    system_prompt_execution = (
                        "You are a master storyteller. Your task is to write a compelling, concise (150-word maximum) "
                        "plot summary based EXACTLY on the refined prompt provided by the user. "
                        "Do not add any additional analysis or commentary."
                    )
                    final_summary = call_gemini_api(
                        final_prompt_text,
                        system_prompt_execution
                    )

                    if final_summary:
                        st.subheader("🎉 Generated Story Summary")
                        st.balloons()
                        st.markdown(final_summary)
                    else:
                        st.error("Could not generate the final summary.")

            else:
                st.warning("Please finalize the prompt before executing generation.")
    else:
        st.info("Start by entering your seed idea and pressing 'Generate AI Suggestions' above.")

if __name__ == "__main__":
    main()
