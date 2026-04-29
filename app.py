import streamlit as st
from apify_client import ApifyClient
import openai
import json

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
            prompt = f"""Act as a Senior Influencer Strategist & Competitor Analyst.
Analyze the following Instagram data:
Data: {json.dumps(data[:3], indent=2)}

Provide a "Competitor Intelligence Report" with these specific sections:

1. **The 'Hook' Strategy**: Analyze the top 5 captions. What is the recurring emotional hook (e.g., Fear of Missing Out, Educational, Aesthetic/Vibe)?
2. **Content Gap Opportunity**: What is this influencer NOT doing that a competitor could exploit? (e.g., "Lack of video tutorials," "No community Q&A").
3. **Engagement Quality Audit**:
   - Real vs. Bot feel of comments.
   - Saves/Shares potential (Does the content provide 'utility'?).
4. **Sponsorship Profile**:
   - Estimated Post Value based on followers and engagement.
   - Brand Fit: Which 3 industries would this influencer convert best for?
5. **Growth Velocity Prediction**: Based on recent activity, is this profile likely to 'Trend' or 'Stagnate' in the next 30 days?

Format the output using professional Markdown headers and bullet points. Use bolding for key metrics."""
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