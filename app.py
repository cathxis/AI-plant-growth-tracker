import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Title
st.title("🌱 Plant Growth Tracker")
st.write("Track your plant's growth and get care recommendations.")

# Data storage
DATA_FILE = "plants.csv"

# Load existing data
try:
    plants_df = pd.read_csv(DATA_FILE)
except FileNotFoundError:
    plants_df = pd.DataFrame(columns=["Name", "Type", "Last Watered", "Sunlight Hours", "Season", "Notes"])

# Add new plant
st.subheader("Add / Update Plant Info")
name = st.text_input("Plant Name")
plant_type = st.selectbox("Plant Type", ["Flower", "Vegetable", "Fruit", "Succulent", "Herb"])
last_watered = st.date_input("Last Watered", datetime.today())
sunlight_hours = st.slider("Sunlight per day (hours)", 0, 12, 6)
season = st.selectbox("Current Season", ["Spring", "Summer", "Autumn", "Winter"])
notes = st.text_area("Additional Notes")

if st.button("Save Plant Info"):
    new_data = pd.DataFrame([[name, plant_type, last_watered, sunlight_hours, season, notes]],
                            columns=plants_df.columns)
    plants_df = pd.concat([plants_df, new_data], ignore_index=True)
    plants_df.to_csv(DATA_FILE, index=False)
    st.success("✅ Plant info saved!")

# Show plant list
st.subheader("Your Plants")
st.dataframe(plants_df)

# Recommendations
st.subheader("Care Recommendations")
for idx, row in plants_df.iterrows():
    recs = []

    # Watering advice
    days_since_watered = (datetime.today().date() - datetime.strptime(row["Last Watered"], "%Y-%m-%d").date()).days
    if row["Type"] in ["Flower", "Vegetable", "Fruit"]:
        if days_since_watered >= 3:
            recs.append("💧 Water now")
        else:
            recs.append("💧 Water in a few days")
    elif row["Type"] == "Succulent":
        if days_since_watered >= 10:
            recs.append("💧 Water now")
        else:
            recs.append("💧 Succulents need less water — wait")

    # Fertilizer advice
    if row["Season"] in ["Spring", "Summer"]:
        recs.append("🌿 Add fertilizer every 2 weeks")
    else:
        recs.append("❄ Reduce fertilizer — plant resting")

    # Sunlight advice
    if row["Sunlight Hours"] < 4:
        recs.append("☀ Move to a sunnier spot")
    elif row["Sunlight Hours"] > 10:
        recs.append("🌤 Reduce sunlight exposure")

    st.markdown(f"*{row['Name']}* ({row['Type']}): " + " | ".join(recs))
