import streamlit as st
from apify_client import ApifyClient
from openai import OpenAI
import concurrent.futures

# 1. Setup & Secrets
client = ApifyClient(st.secrets["APIFY_API_TOKEN"])
ai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
STRIPE_LINK = "https://buy.stripe.com/your_link_id" # Ensure https:// is here!

st.set_page_config(page_title="IG Scout Pro", page_icon="📈", layout="wide")

if "free_used" not in st.session_state:
    st.session_state.free_used = False

# --- SIDEBAR (Fixed Scroller) ---
with st.sidebar:
    st.title("🛡️ Dashboard")
    
    if st.session_state.free_used:
        st.error("Free trial exhausted.")
        # FIX: Ensure this button is independent and has a full URL
        st.link_button("🚀 Unlock Full Access ($10)", STRIPE_LINK, type="primary", use_container_width=True)
    else:
        st.info("Status: **Free Member**")
        st.caption("1 free report remaining")

    # Use a simple spacer to push to bottom without scroller
    st.markdown("<div style='height: 60vh;'></div>", unsafe_allow_html=True)
    st.divider()
    st.caption("📈 Total Visitors")
    st.markdown("![Visitors](https://hits.sh/ig-analyzer.streamlit.app.svg?label=Visitors&color=ff4b4b)")

# Main UI Header
st.markdown("<h1 style='text-align: center;'>📷 Influencer ROI Intelligence</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Professional competitor deep-dives in seconds.</p>", unsafe_allow_html=True)

handle = st.text_input("Enter Instagram Handle (without @)", placeholder="wanderingwithpaint")

if st.button("Generate Intelligence Report", type="primary", use_container_width=True):
    if not handle:
        st.warning("Please enter a username.")
    elif st.session_state.free_used:
        st.error("Free trial exhausted. Use the link in the sidebar to upgrade.")
    else:
        with st.status("🔍 Deep-Scraping Profile...", expanded=True) as status:
            clean_handle = handle.replace("@", "").strip()

            def get_profile():
                profile_input = {"usernames": [clean_handle], "sessionID": st.secrets.get("IG_SESSION_ID", "")}
                run = client.actor("apify/instagram-profile-scraper").call(run_input=profile_input)
                return list(client.dataset(run["defaultDatasetId"]).iterate_items())

            def get_posts():
                post_input = {"username": [clean_handle], "resultsLimit": 20, "sessionID": st.secrets.get("IG_SESSION_ID", "")}
                run = client.actor("apify/instagram-post-scraper").call(run_input=post_input)
                return list(client.dataset(run["defaultDatasetId"]).iterate_items())

            with concurrent.futures.ThreadPoolExecutor() as executor:
                f_profile = executor.submit(get_profile)
                f_posts = executor.submit(get_posts)
                profile_items, post_items = f_profile.result(), f_posts.result()

            if not profile_items or not post_items:
                status.update(label="Scraping Failed", state="error")
                st.error("Authentication failed. Check your IG_SESSION_ID in secrets.")
            else:
                prof = profile_items[0]
                follower_count = prof.get("followersCount") or prof.get("followers_count") or 0
                
                # --- CALC APPROX EARNINGS ---
                low_end = (follower_count / 1000) * 5
                high_end = (follower_count / 1000) * 15
                
                # --- GREEDY VIEW HUNTING ---
                videos = []
                for i in post_items:
                    # Check every possible view/play count key used in 2026
                    possible_keys = [
                        "playCount", "viewCount", "videoPlayCount", "videoViewCount", 
                        "video_view_count", "plays_count", "video_play_count"
                    ]
                    # Find the first one that exists and is a number
                    v_val = 0
                    for key in possible_keys:
                        val = i.get(key)
                        if val and isinstance(val, (int, float)) and val > 0:
                            v_val = val
                            break
                    
                    if v_val > 0:
                        i["final_views"] = v_val
                        videos.append(i)
                
                trending = sorted(videos, key=lambda x: x.get("final_views", 0), reverse=True)[:2]
                
                st.write("🤖 AI Strategy Audit...")
                summary_data = {
                    "handle": handle,
                    "followers": follower_count,
                    "est_earnings": f"${low_end:,.0f} - ${high_end:,.0f}",
                    "trending_metrics": [{"views": v.get("final_views"), "caption": v.get("caption", "")[:30]} for v in trending]
                }
                
                response = ai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": "You are a professional Influencer Agent. Provide clean, bulleted analysis."},
                              {"role": "user", "content": f"Analyze: {summary_data}"}]
                )
                
                status.update(label="Intelligence Gathered!", state="complete", expanded=False)

                # --- RESULTS DISPLAY ---
                st.divider()
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Followers", f"{follower_count:,}")
                col_b.metric("Est. Earnings / Post", f"${low_end:,.0f} - ${high_end:,.0f}", delta="USD")
                col_c.metric("Account Tier", "Elite" if follower_count > 100000 else "Pro")
                
                st.markdown("### 🔥 Trending Content Benchmarks")
                if not trending:
                    st.warning("Play counts are hidden by Instagram. Try refreshing your Session ID.")
                else:
                    v_col1, v_col2 = st.columns(2)
                    for idx, v in enumerate(trending):
                        with (v_col1 if idx == 0 else v_col2):
                            st.image(v.get("displayUrl") or v.get("thumbnailUrl"), use_container_width=True)
                            st.metric("Video Views", f"{v.get('final_views', 0):,}")

                # --- SOOTHING AGENCY REPORT ---
                st.markdown("### 📝 Agency Strategic Report")
                report_html = response.choices[0].message.content.replace("\n", "<br>")
                st.markdown(
                    f"""
                    <div style="
                        background-color: #1e293b; 
                        color: #e2e8f0; 
                        padding: 30px; 
                        border-radius: 15px; 
                        border-left: 6px solid #3b82f6;
                        line-height: 1.7;
                        font-family: 'Inter', sans-serif;
                    ">
                        {report_html}
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
                st.session_state.free_used = True
                st.balloons()