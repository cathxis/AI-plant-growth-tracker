import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import random

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="🌱 AI Plant Growth Tracker",
    page_icon="🌿",
    layout="wide"
)

# Custom CSS for attractive UI
st.markdown("""
<style>
.stApp {
    background: linear-gradient(120deg, #e0f7e9, #f0fff4);
}
.card {
    padding: 20px;
    border-radius: 15px;
    background: white;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ----------------- TITLE -----------------
st.title("🌱 AI-Powered Plant Growth Tracker")
st.markdown("Track your plants, get *smart AI recommendations*, and keep them thriving! 🌿")

# Data storage
DATA_FILE = "plants.csv"
try:
    plants_df = pd.read_csv(DATA_FILE)
except FileNotFoundError:
    plants_df = pd.DataFrame(columns=["Name", "Type", "Last Watered", "Sunlight Hours", "Season", "Notes", "Image"])

# ----------------- ADD PLANT FORM -----------------
with st.container():
    st.subheader("➕ Add / Update Plant Info")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Plant Name")
        plant_type = st.selectbox("Plant Type", ["Flower", "Vegetable", "Fruit", "Succulent", "Herb"])
        last_watered = st.date_input("Last Watered", datetime.today())
        sunlight_hours = st.slider("Sunlight per day (hours)", 0, 12, 6)
    with col2:
        season = st.selectbox("Current Season", ["Spring", "Summer", "Autumn", "Winter"])
        notes = st.text_area("Additional Notes")
        uploaded_image = st.file_uploader("Upload Plant Photo", type=["jpg", "jpeg", "png"])
        img_path = uploaded_image.name if uploaded_image else None

    if st.button("💾 Save Plant Info"):
        new_data = pd.DataFrame([[name, plant_type, last_watered, sunlight_hours, season, notes, img_path]],
                                columns=plants_df.columns)
        plants_df = pd.concat([plants_df, new_data], ignore_index=True)
        plants_df.to_csv(DATA_FILE, index=False)
        st.success(f"✅ {name} saved!")

# ----------------- AI TEXT FORM -----------------
st.subheader("🤖 AI Quick Input")
ai_text = st.text_area("Describe your plant’s condition (e.g., 'My tomato plant has yellow leaves, gets 3 hours of sun, and was watered 5 days ago.')")

if st.button("🧠 Get AI Recommendation"):
    if ai_text.strip():
        # Fake AI logic (replace with real model if you have API key)
        keywords = ["yellow", "dry", "drooping", "no sun"]
        recs = []
        if "yellow" in ai_text.lower():
            recs.append("🌿 Leaves yellow — consider adding balanced fertilizer.")
        if "dry" in ai_text.lower() or "5 days" in ai_text.lower():
            recs.append("💧 Water your plant now.")
        if "no sun" in ai_text.lower() or "3 hours" in ai_text.lower():
            recs.append("☀ Move to a sunnier location.")
        if not recs:
            recs.append("✅ Your plant seems fine! Keep regular care.")
        st.markdown("*AI Recommendations:*\n- " + "\n- ".join(recs))
    else:
        st.warning("Please describe your plant's condition.")

# ----------------- DISPLAY PLANTS -----------------
st.subheader("📋 Your Plants")
if not plants_df.empty:
    for idx, row in plants_df.iterrows():
        with st.container():
            st.markdown(f"<div class='card'>*{row['Name']}* ({row['Type']})", unsafe_allow_html=True)
            cols = st.columns([1, 2])
            with cols[0]:
                if row["Image"]:
                    try:
                        img = Image.open(row["Image"])
                        st.image(img, use_container_width=True)
                    except:
                        st.write("📷 No image available")
                else:
                    st.write("📷 No image uploaded")
            with cols[1]:
                days_since_watered = (datetime.today().date() - datetime.strptime(str(row["Last Watered"]), "%Y-%m-%d").date()).days
                recs = []
                if row["Type"] in ["Flower", "Vegetable", "Fruit"]:
                    recs.append("💧 Water now" if days_since_watered >= 3 else "💧 Water in a few days")
                elif row["Type"] == "Succulent":
                    recs.append("💧 Water now" if days_since_watered >= 10 else "💧 Wait before watering")
                if row["Season"] in ["Spring", "Summer"]:
                    recs.append("🌿 Add fertilizer every 2 weeks")
                else:
                    recs.append("❄ Reduce fertilizer — plant resting")
                if row["Sunlight Hours"] < 4:
                    recs.append("☀ Move to a sunnier spot")
                elif row["Sunlight Hours"] > 10:
                    recs.append("🌤 Reduce sunlight exposure")
                st.markdown("*Care Recommendations:*\n- " + "\n- ".join(recs))
            st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No plants added yet.")
