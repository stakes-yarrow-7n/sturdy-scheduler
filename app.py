import streamlit as st
import pandas as pd
import random

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Cardiology Holiday Scheduler", layout="wide", initial_sidebar_state="expanded")

# --- CONSTANTS ---
PROVIDERS = [
    "Ross Pollack, MD", 
    "Richard Hayes, MD", 
    "Ronald Pigeon, MD", 
    "Rabah Alreshq, MD", 
    "George Waters, MD", 
    "Petro Gjini, MD"
]
# Updated to exactly match your Google Form
HOLIDAYS = ["Memorial Day", "July 4th", "Labor Day", "Thanksgiving", "Christmas", "New Year"]
MAJOR_HOLIDAYS = ["Thanksgiving", "Christmas", "New Year"]

if 'master_schedule' not in st.session_state:
    st.session_state.master_schedule = None

# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("⚙️ Group Settings")
    st.markdown("Adjust system rules here before generating the schedule. You do not need to edit code to change these.")
    
    st.markdown("### Premium Holiday Weights")
    st.markdown("Thanksgiving, Christmas, and New Year's are universally valued. Use the sliders below to determine how much *more* each specific holiday contributes to a provider's fatigue score.")
    
    weight_thanksgiving = st.slider("🦃 Thanksgiving Multiplier", min_value=1.0, max_value=3.0, value=1.5, step=0.1)
    weight_christmas = st.slider("🎄 Christmas Multiplier", min_value=1.0, max_value=3.0, value=2.0, step=0.1)
    weight_new_year = st.slider("🎆 New Year Multiplier", min_value=1.0, max_value=3.0, value=1.5, step=0.1)
    
    premium_weights = {
        "Thanksgiving": weight_thanksgiving,
        "Christmas": weight_christmas,
        "New Year": weight_new_year
    }
    
    st.divider()
    st.caption("Settings adjustments apply immediately upon generating a new schedule.")

# --- UI HEADER ---
st.title("🏥 Cardiology Group - 6-Year Holiday Coverage")

with st.expander("📖 System Rules & Fatigue Scoring"):
    st.write("""
    * **Preferences:** Rank the holidays from **1 to 6**. (6 = Most Preferred to Cover, 1 = Least Preferred).
    * **Standard Fatigue Points:** Working a '1' earns you 6 points. Working a '6' earns you 1 point. 
    * **The Major Holiday Premium:** Working Thanksgiving, Christmas, or New Year's applies a custom multiplier (set in the sidebar) to your points to reward the extra sacrifice.
    * **Priority Odds:** Your points compound over the 6 years. The higher your fatigue score, the stronger your mathematical priority to get the holidays you actually want in upcoming years.
    * **Rules:** No double-booking in a single year, and heavy protection against working the same holiday two years in a row.
    """)

st.divider()

# --- INPUT SECTION ---
st.markdown("### Step 1: Input Group Preferences")

# Google Sheets Link
my_sheet_url = "