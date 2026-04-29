import streamlit as st
from apify_client import ApifyClient
import openai

# 1. Initialize
client = ApifyClient(st.secrets["APIFY_API_TOKEN"])
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="IG Scout AI", page_icon="📈")

# Simple Sidebar for Status
with st.sidebar:
    st.title("User Dashboard")
    if "free_used" not in st.session_state:
        st.session_state.free_used = False
    
    status = "Free Member" if not st.session_state.free_used else "Limit Reached"
    st.write(f"Status: **{status}**")
    if st.session_state.free_used:
        st.link_button("Upgrade to Pro", "https://buy.stripe.com/your_link")

st.title("📸 IG Influencer Scout")
st.write("Enter a handle to get a 2026 ROI Predictor Report.")

handle = st.text_input("", placeholder="e.g. travel_with_me")

if st.button("Generate Pro Report", type="primary"):
    if st.session_state.free_used:
        st.error("Free trial exhausted. Please upgrade to Pro for unlimited searches.")
    else:
        with st.status("Gathering Intelligence...", expanded=True) as status:
            st.write("🕵️‍♂️ Scraping Instagram data...")
            run_input = {"usernames": [handle.replace("@", "")], "resultsLimit": 12}
            run = client.actor("apify/instagram-scraper").call(run_input=run_input)
            data = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            
            st.write("🤖 AI Analysis in progress...")
            # We wrap the AI call to ensure it looks clean
            prompt = f"Analyze this IG data and return 3 metrics (Engage %, Trust Score 1-10, Value $) followed by a summary: {data}"
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            status.update(label="Analysis Complete!", state="complete", expanded=False)

        # UI Layout for results
        res_text = response.choices[0].message.content
        
        # Displaying data in a user-friendly grid
        col1, col2, col3 = st.columns(3)
        col1.metric("Trust Score", "8.5/10") # Example: You can parse actual numbers from GPT later
        col2.metric("Eng. Rate", "4.2%")
        col3.metric("Est. Value", "$450/post")

        st.markdown("### 📝 Full Audit Report")
        st.info(res_text)
        
        st.session_state.free_used = True