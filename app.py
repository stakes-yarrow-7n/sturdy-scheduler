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
HOLIDAYS = ["Memorial Day", "4th of July", "Labor Day", "Thanksgiving", "Christmas", "New Year"]
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
    
    # Store these in a dictionary for easy lookup later
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

# Create a place to paste the Google Sheet link
sheet_url = st.text_input("https://docs.google.com/spreadsheets/d/1dewvDOk7_dzEH06DyeXKGr6p4kiBO_6_49zvpnL9xfM/edit?/export?format=csv") 

if sheet_url:
    try:
        # Read the live Google Sheet
        survey_data = pd.read_csv(sheet_url)
        st.success("Successfully connected to Google Form responses!")
        
        # NOTE: You may need to adjust the column names in the brackets below 
        # to match exactly what you typed as questions in your Google Form.
        # Example: if your form question is "Thanksgiving Preference", change the text below to match.
        
        # Build the table from the survey data
        imported_data = {
            "Memorial Day": survey_data["Memorial Day"].tolist(),
            "July 4th": survey_data["4th of July"].tolist(),
            "Labor Day": survey_data["Labor Day"].tolist(),
            "Thanksgiving": survey_data["Thanksgiving"].tolist(),
            "Christmas": survey_data["Christmas"].tolist(),
            "New Year": survey_data["New Year"].tolist()
        }
        
        # Use the names from the form
        provider_names = survey_data["Doctor Name"].tolist()
        df_prefs = pd.DataFrame(imported_data, index=provider_names)
        
    except Exception as e:
        st.error(f"Could not read the Google Sheet. Please check the link format. Error: {e}")
        # Fallback to default
        default_data = {hol: [3]*6 for hol in HOLIDAYS}
        df_prefs = pd.DataFrame(default_data, index=PROVIDERS)
else:
    st.write("Rank 1 to 6 (6 = Most Preferred, 1 = Least Preferred)")
    default_data = {hol: [3]*6 for hol in HOLIDAYS}
    df_prefs = pd.DataFrame(default_data, index=PROVIDERS)

# Show the data table (it will auto-fill if the link is used!)
edited_df = st.data_editor(df_prefs, use_container_width=True)

# --- DISPLAY TABS ---
if st.session_state.master_schedule is not None:
    st.markdown("### Step 2: Review Schedules")
    
    tab1, tab2 = st.tabs(["📊 Master Group Schedule", "👤 Individual Physician Profiles"])
    
    with tab1:
        st.write("#### Full 6-Year Master Roster")
        group_df = st.session_state.master_schedule.copy()
        st.dataframe(group_df[["Year", "Provider", "Assigned Holiday"]], use_container_width=True, hide_index=True)
        
    with tab2:
        st.write("#### Personalized 6-Year View & Fatigue Tracking")
        selected_dr = st.selectbox("Select a Provider to view their profile:", PROVIDERS)
        
        dr_data = st.session_state.master_schedule[st.session_state.master_schedule["Provider"] == selected_dr]
        
        for index, row in dr_data.iterrows():
            with st.container():
                st.markdown(f"##### {row['Year']}")
                
                if row['Assigned Holiday'] == "None":
                    st.info(f"**Assignment:** OFF")
                else:
                    st.error(f"**Assignment:** {row['Assigned Holiday']}")
                    
                st.write(f"> *{row['Explanation']}*")
                st.divider()