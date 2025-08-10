# app.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
from pathlib import Path
from PIL import Image
import io
import matplotlib.pyplot as plt
import os
import textwrap

# Optional: if you want to use actual LLM polishing for the recommendations,
# set OPENAI_API_KEY in secrets and install openai. This app will still work
# perfectly well without OpenAI.
try:
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

# ---------------- Page config ----------------
st.set_page_config(page_title="🌱 PlantCareAI", page_icon="🌿", layout="wide")

# ---------------- Paths ----------------
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
PLANTS_CSV = DATA_DIR / "plants.csv"
GROWTH_CSV = DATA_DIR / "growth_logs.csv"
IMAGES_DIR = DATA_DIR / "images"
IMAGES_DIR.mkdir(exist_ok=True)

# ---------------- Built-in plant "encyclopedia" ----------------
# This is a small starter dataset. You can extend with more species.
PLANT_DB = {
    "Tomato": {
        "type": "Vegetable",
        "water_interval_days": 2,
        "sunlight_hours_min": 6,
        "sunlight_hours_max": 8,
        "soil": "Loamy, well-draining",
        "temp_c_min": 18,
        "temp_c_max": 27,
        "fertilizer": "Balanced NPK every 2 weeks during growing season"
    },
    "Rose": {
        "type": "Flower",
        "water_interval_days": 3,
        "sunlight_hours_min": 5,
        "sunlight_hours_max": 8,
        "soil": "Loamy, slightly acidic",
        "temp_c_min": 10,
        "temp_c_max": 25,
        "fertilizer": "High-P potassium fertilizer once a month during bloom"
    },
    "Snake Plant": {
        "type": "Indoor - Low Light",
        "water_interval_days": 21,
        "sunlight_hours_min": 1,
        "sunlight_hours_max": 4,
        "soil": "Sandy, well-draining",
        "temp_c_min": 15,
        "temp_c_max": 30,
        "fertilizer": "Very light during spring"
    },
    "Aloe Vera": {
        "type": "Succulent",
        "water_interval_days": 21,
        "sunlight_hours_min": 3,
        "sunlight_hours_max": 6,
        "soil": "Cactus mix, excellent drainage",
        "temp_c_min": 15,
        "temp_c_max": 30,
        "fertilizer": "Light succulent fertilizer in spring"
    },
    "Basil": {
        "type": "Herb",
        "water_interval_days": 3,
        "sunlight_hours_min": 4,
        "sunlight_hours_max": 8,
        "soil": "Moist, well-draining",
        "temp_c_min": 18,
        "temp_c_max": 30,
        "fertilizer": "Every 3-4 weeks with balanced fertilizer"
    }
}

# ---------------- Utility helpers ----------------
def load_df(path, columns):
    if path.exists():
        return pd.read_csv(path)
    else:
        return pd.DataFrame(columns=columns)

def save_df(df, path):
    df.to_csv(path, index=False)

def days_since(d):
    """given a string or date, return integer days since that date"""
    if pd.isna(d) or d == "":
        return None
    if isinstance(d, str):
        try:
            dt = datetime.strptime(d, "%Y-%m-%d").date()
        except Exception:
            # fallback for datelike objects saved differently
            dt = pd.to_datetime(d).date()
    elif isinstance(d, (date, datetime)):
        dt = d if isinstance(d, date) else d.date()
    else:
        dt = pd.to_datetime(d).date()
    return (datetime.today().date() - dt).days

def save_uploaded_image(uploaded_file, plant_name):
    if uploaded_file is None:
        return None
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    ext = Path(uploaded_file.name).suffix or ".png"
    filename = f"{plant_name}_{ts}{ext}"
    out_path = IMAGES_DIR / filename
    img = Image.open(uploaded_file)
    img.save(out_path)
    return str(out_path)

def pretty_recs_block(recs):
    """Return markdown block for list of recs with icons and badges."""
    out = ""
    for r in recs:
        out += f"- {r}\n"
    return out

def llm_polish(text):
    """Optional: if OpenAI is available and key is set via Streamlit secrets, call the API.
       Otherwise return the base text."""
    if not OPENAI_AVAILABLE:
        return text
    try:
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        prompt = ("You are a friendly plant-care assistant. Polish and expand the "
                  "following care instructions into a concise, helpful paragraph "
                  "with specific actionable steps and short reasons.\n\nInstructions:\n")
        prompt += textwrap.fill(text, width=100)
        prompt += "\n\nPolish:"
        resp = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            temperature=0.6,
            max_tokens=200
        )
        polished = resp.choices[0].text.strip()
        return polished
    except Exception as e:
        # if OpenAI fails, return original text
        return text

# ---------------- Load data ----------------
plants_columns = ["id", "name", "species", "type", "last_watered", "last_fertilized",
                  "sunlight_hours", "temp_c", "humidity_percent", "notes", "image_path", "added_on"]
plants_df = load_df(PLANTS_CSV, plants_columns)

growth_columns = ["plant_id", "date", "height_cm", "notes"]
growth_df = load_df(GROWTH_CSV, growth_columns)

# ---------------- Styling (dark UI) ----------------
st.markdown("""
<style>
body, .stApp { background-color: #000000; color: #ffffff; }
.card {
  background: #0f1720;
  border-radius: 12px;
  padding: 18px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.6);
  margin-bottom: 16px;
}
.small-muted { color: #9aa4b2; font-size:12px }
.badge {
  display:inline-block;
  padding:4px 8px;
  border-radius:8px;
  margin-right:6px;
  font-weight:600;
  font-size:13px;
}
.badge-warn { background:#ffcc00; color:#111}
.badge-danger { background:#ff5c5c; color:#111}
.badge-ok { background:#1bbf7b; color:#011 }
</style>
""", unsafe_allow_html=True)

# ---------------- Header ----------------
st.title("🌱 PlantCareAI — Smart Plant Growth Tracker")
st.markdown("Add plants, log growth, upload photos, and get *smart, actionable care recommendations*.")

# ---------------- Left column: Add plant ----------------
with st.container():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("➕ Add / Update Plant")
    c1, c2 = st.columns((1,1))
    with c1:
        name = st.text_input("Plant name (e.g., 'Balcony Tomato')")
        species = st.selectbox("Species (choose)", options=["Tomato", "Rose", "Snake Plant", "Aloe Vera", "Basil", "Other"])
        if species == "Other":
            species = st.text_input("Enter species name")
        type_field = PLANT_DB.get(species, {}).get("type", st.selectbox("Type", ["Flower","Vegetable","Succulent","Herb","Indoor - Low Light","Fruit"]))
        last_watered = st.date_input("Last watered on", value=datetime.today())
        last_fertilized = st.date_input("Last fertilized on", value=datetime.today())
    with c2:
        sunlight_hours = st.slider("Sunlight per day (hours)", min_value=0, max_value=14, value=6)
        temp_c = st.number_input("Current temperature (°C)", value=25.0, step=0.5)
        humidity = st.slider("Current humidity (%)", 0, 100, 50)
        notes = st.text_area("Notes (pests, leaf color, drooping etc.)", max_chars=500)
        uploaded = st.file_uploader("Upload plant photo", type=["png","jpg","jpeg"])
    if st.button("💾 Save / Add Plant"):
        if not name or not species:
            st.error("Please provide at least a name and a species.")
        else:
            image_path = save_uploaded_image(uploaded, name) if uploaded else ""
            pid = int(datetime.now().timestamp())  # simple id
            new_row = {
                "id": pid,
                "name": name,
                "species": species,
                "type": type_field,
                "last_watered": last_watered.strftime("%Y-%m-%d"),
                "last_fertilized": last_fertilized.strftime("%Y-%m-%d"),
                "sunlight_hours": sunlight_hours,
                "temp_c": temp_c,
                "humidity_percent": humidity,
                "notes": notes,
                "image_path": image_path,
                "added_on": datetime.now().strftime("%Y-%m-%d")
            }
            plants_df = pd.concat([plants_df, pd.DataFrame([new_row])], ignore_index=True)
            save_df(plants_df, PLANTS_CSV)
            st.success(f"Saved plant '{name}' ✅")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Middle column: Quick AI form & actions ----------------
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("🤖 Quick AI Input — Describe your plant in plain English")
ai_text = st.text_area("E.g. 'My rose has yellowing leaves on lower branches, it's been 5 days since watering, gets 3 hours sun', or paste a care note.")

if st.button("🧠 Analyze & Recommend (AI-enhanced)"):
    if not ai_text.strip():
        st.warning("Please describe your plant.")
    else:
        # Basic rule-based extraction (improved)
        text = ai_text.lower()
        recs = []
        # Water-related heuristics
        if "dry" in text or "wilting" in text or "droop" in text or "wilt" in text or "5 days" in text or "not watered" in text:
            recs.append("💧 Water now — soil seems dry or plant wilted.")
        if "yellow" in text and ("leaves" in text or "leaf" in text):
            recs.append("🧪 Yellow leaves may indicate nutrient deficiency (nitrogen) or overwatering — check soil moisture and fertilize if dry.")
        if "brown tip" in text or "brown" in text:
            recs.append("🔥 Brown tips often mean low humidity or salt build-up — flush soil and increase humidity.")
        if "pests" in text or "aphid" in text or "mealy" in text:
            recs.append("🕵️ Inspect for pests and treat with insecticidal soap or neem oil.")
        if "no sun" in text or "3 hours" in text or "too little sun" in text:
            recs.append("☀ Increase sunlight — move closer to an east/west window for morning/afternoon sun.")
        if not recs:
            recs.append("✅ No urgent issue detected. Keep a consistent watering schedule and monitor leaves.")
        base = "\n".join(recs)
        polished = llm_polish(base)
        st.markdown("*Recommendations:*")
        st.info(polished)
st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Right column: Plant list and recommendations ----------------
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("📋 Your Plants & Smart Recommendations")

if plants_df.empty:
    st.info("No plants added yet — add one from the form above.")
else:
    # show each plant with computed badges and recs
    for idx, row in plants_df.sort_values("added_on", ascending=False).iterrows():
        st.markdown("---")
        c1, c2 = st.columns((1,2))
        with c1:
            if row.get("image_path"):
                try:
                    img = Image.open(row["image_path"])
                    st.image(img, use_column_width=True)
                except Exception:
                    st.write("📷 image unavailable")
            else:
                st.write("📷 No image")
        with c2:
            st.markdown(f"### {row['name']} — {row['species']}")
            st.markdown(f"<div class='small-muted'>Added on {row.get('added_on')}</div>", unsafe_allow_html=True)

            # compute conditions
            days_water = days_since(row.get("last_watered"))
            days_fert = days_since(row.get("last_fertilized"))
            current_sun = float(row.get("sunlight_hours") or 0)
            current_temp = float(row.get("temp_c") or 0)
            humidity = float(row.get("humidity_percent") or 0)

            # get ideal from DB if exists
            db = PLANT_DB.get(row["species"], {})
            ideal_interval = db.get("water_interval_days", 3)
            sun_min = db.get("sunlight_hours_min", 3)
            sun_max = db.get("sunlight_hours_max", 8)
            tmin = db.get("temp_c_min", 10)
            tmax = db.get("temp_c_max", 30)
            fert_note = db.get("fertilizer", "Follow package instructions")

            # badges logic
            badges = []
            recs = []
            # Water checks
            if days_water is None:
                recs.append("💧 Last watering date unknown — set it in the plant profile.")
            else:
                if days_water >= ideal_interval + 1:
                    badges.append(("<span class='badge badge-danger'>Needs Water</span>"))
                    recs.append(f"💧 It has been {days_water} days since last watering — recommended every {ideal_interval} days.")
                elif days_water <= max(1, ideal_interval//2):
                    # potentially over-watered (if just watered very recently)
                    recs.append("⚠ You watered very recently — avoid frequent shallow watering to prevent root rot.")
                else:
                    badges.append(("<span class='badge badge-ok'>Hydrated</span>"))
                    recs.append("💧 Hydration looks okay.")

            # Fertilizer checks
            if days_fert is None:
                recs.append("🌿 Fertilizer history missing — track last fertilized date.")
            else:
                if days_fert >= 14:
                    badges.append(("<span class='badge badge-warn'>Fertilize</span>"))
                    recs.append(f"🌿 Last fertilized {days_fert} days ago — {fert_note}.")
                else:
                    recs.append("🌿 Fertilizer schedule OK.")

            # Sunlight checks
            if current_sun < sun_min:
                badges.append(("<span class='badge badge-warn'>Low Light</span>"))
                recs.append(f"☀ Current sunlight {current_sun}h < ideal {sun_min}h — move to brighter spot (east/west window).")
            elif current_sun > sun_max:
                badges.append(("<span class='badge badge-warn'>Too Much Sun</span>"))
                recs.append(f"🌤 Current sunlight {current_sun}h > safe {sun_max}h — provide shade or move slightly away from direct noon sun.")
            else:
                recs.append("☀ Sunlight is within recommended range.")

            # Temperature & humidity checks
            if current_temp < tmin:
                badges.append(("<span class='badge badge-warn'>Too Cold</span>"))
                recs.append(f"🌡 Temp {current_temp}°C below ideal {tmin}°C — protect from chill.")
            elif current_temp > tmax:
                badges.append(("<span class='badge badge-warn'>Too Hot</span>"))
                recs.append(f"🌡 Temp {current_temp}°C above ideal {tmax}°C — improve ventilation and shade.")

            if humidity < 30:
                recs.append("💦 Low humidity — consider misting or a humidity tray for tropical species.")
            if humidity > 85:
                recs.append("💨 Very high humidity — ensure good airflow to avoid fungal issues.")

            # Compose recommendations & display
            # badges html
            if badges:
                st.markdown("".join(badges), unsafe_allow_html=True)
            # recommendations polished (optionally via LLM)
            base_recs = "\n".join(recs)
            polished = llm_polish(base_recs)
            st.markdown(pretty_recs_block(recs))

            st.markdown(f"*Species tips:* {fert_note}")
            st.markdown(f"<div class='small-muted'>Ideal temp: {tmin}°C–{tmax}°C • Ideal sun: {sun_min}h–{sun_max}h • Soil: {db.get('soil','—')}</div>", unsafe_allow_html=True)

            # action buttons for logging growth or watering done
            a1, a2, a3 = st.columns(3)
            with a1:
                if st.button(f"💧 Mark Watered — {row['name']}", key=f"water_{row['id']}"):
                    plants_df.loc[plants_df['id'] == row['id'], 'last_watered'] = datetime.today().strftime("%Y-%m-%d")
                    save_df(plants_df, PLANTS_CSV)
                    st.experimental_rerun()
            with a2:
                if st.button(f"🌿 Mark Fertilized — {row['name']}", key=f"fert_{row['id']}"):
                    plants_df.loc[plants_df['id'] == row['id'], 'last_fertilized'] = datetime.today().strftime("%Y-%m-%d")
                    save_df(plants_df, PLANTS_CSV)
                    st.experimental_rerun()
            with a3:
                if st.button(f"📈 Log Growth — {row['name']}", key=f"grow_{row['id']}"):
                    # show modal-ish inputs
                    h = st.number_input("Height / size now (cm)", min_value=0.0, step=0.1, key=f"height_input_{row['id']}")
                    note_g = st.text_input("Growth note (optional)", key=f"growth_note_{row['id']}")
                    if st.button("Save growth", key=f"save_growth_{row['id']}"):
                        growth_df = load_df(GROWTH_CSV, growth_columns)
                        growth_df = pd.concat([growth_df, pd.DataFrame([{"plant_id": row['id'], "date": datetime.today().strftime("%Y-%m-%d"), "height_cm": h, "notes": note_g}])], ignore_index=True)
                        save_df(growth_df, GROWTH_CSV)
                        st.success("Growth logged.")
                        st.experimental_rerun()

st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Growth charts viewer ----------------
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("📈 Growth Charts")

if growth_df.empty:
    st.info("No growth logs yet — use 'Log Growth' to add height/time points.")
else:
    # allow user to pick plant and show plot
    plant_choices = plants_df.set_index('id')['name'].to_dict()
    selected_pid = st.selectbox("Select plant to view growth chart", options=list(plant_choices.keys()), format_func=lambda x: plant_choices[x])
    logs = growth_df[growth_df['plant_id'] == int(selected_pid)].sort_values('date')
    if logs.empty:
        st.info("No growth logs for this plant yet.")
    else:
        dates = pd.to_datetime(logs['date'])
        heights = logs['height_cm'].astype(float)
        plt.figure(figsize=(8,3.5))
        plt.plot(dates, heights, marker='o')
        plt.title(f"Growth of {plant_choices[int(selected_pid)]}")
        plt.xlabel("Date")
        plt.ylabel("Height (cm)")
        plt.grid(alpha=0.2)
        st.pyplot(plt)
st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Footer ----------------
st.markdown("---")
st.markdown("<div class='small-muted'>Made with ❤️ by Savan, Akash and Athul — PlantCareAI</div>", unsafe_allow_html=True)
