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
st.write("Rank 1 to 6 (6 = Most Preferred, 1 = Least Preferred)")

default_data = {hol: [3]*6 for hol in HOLIDAYS}
df_prefs = pd.DataFrame(default_data, index=PROVIDERS)

edited_df = st.data_editor(df_prefs, use_container_width=True)

if st.button("🎲 Generate Full 6-Year Schedule", type="primary"):
    
    cum_points = {p: 0.0 for p in PROVIDERS}
    last_year_holiday = {p: "None" for p in PROVIDERS}
    results = []

    for year in range(1, 7):
        holidays_this_year = MAJOR_HOLIDAYS if year == 1 else HOLIDAYS
        available_providers = PROVIDERS.copy()
        year_assignments = {hol: "Not Assigned" for hol in HOLIDAYS}
        
        for hol in holidays_this_year:
            best_score = -1
            best_provider = None
            
            for p in available_providers:
                try:
                    pref = float(edited_df.loc[p, hol])
                except ValueError:
                    pref = 3.0
                
                rand_val = random.random()
                mult = 1.0 + (cum_points[p] * 0.15)
                fatigue_penalty = 0.01 if last_year_holiday[p] == hol else 1.0
                
                score = rand_val * pref * mult * fatigue_penalty
                
                if score > best_score:
                    best_score = score
                    best_provider = p
                    
            year_assignments[hol] = best_provider
            available_providers.remove(best_provider)
            
        for p in PROVIDERS:
            assigned_hol = "None"
            for h, prov in year_assignments.items():
                if prov == p:
                    assigned_hol = h
            
            pts_before = cum_points[p]
            mult_before = 1.0 + (pts_before * 0.15)
            
            if assigned_hol != "None":
                pref_val = int(edited_df.loc[p, assigned_hol])
                base_pts = 7 - pref_val 
                
                # Check if the holiday is one of the premium ones and apply its specific multiplier
                if assigned_hol in premium_weights:
                    multiplier_used = premium_weights[assigned_hol]
                    pts_earned = base_pts * multiplier_used
                    premium_text = f" (including the {multiplier_used}x {assigned_hol} bonus)" if multiplier_used > 1.0 else ""
                else:
                    pts_earned = float(base_pts)
                    premium_text = ""
                
                cum_points[p] += pts_earned
                last_year_holiday[p] = assigned_hol
                
                if year == 1:
                    exp = f"Year 1 baseline (0 points). Assigned {assigned_hol} (ranked a {pref_val}), adding {pts_earned}{premium_text} points to your fatigue score."
                else:
                    exp = f"Started year with {pts_before} pts (Multiplier: {mult_before:.2f}x). Assigned {assigned_hol} (ranked {pref_val}), earning {pts_earned} new points{premium_text}."
            else:
                pref_val = None
                pts_earned = 0
                last_year_holiday[p] = "None"
                
                if year == 1:
                    exp = "Year 1 baseline. You were not assigned a holiday this year. Fatigue score remains 0."
                else:
                    exp = f"Started year with {pts_before} pts (Multiplier: {mult_before:.2f}x). Not assigned a holiday this year."
            
            results.append({
                "Year": f"Year {year}",
                "Provider": p,
                "Assigned Holiday": assigned_hol,
                "Explanation": exp
            })
            
    st.session_state.master_schedule = pd.DataFrame(results)

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