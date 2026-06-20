import streamlit as st
import pandas as pd
import random

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Cardiology Holiday Scheduler", layout="wide")

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

# Initialize session state for the 6-year results
if 'master_schedule' not in st.session_state:
    st.session_state.master_schedule = None

# --- UI HEADER ---
st.title("🏥 Cardiology Group - 6-Year Holiday Coverage")

with st.expander("📖 System Rules & Fatigue Scoring"):
    st.write("""
    * **Preferences:** Rank the holidays from **1 to 6**. (6 = Most Preferred to Cover, 1 = Least Preferred).
    * **Fatigue Points:** If you are assigned a holiday, you earn points based on your dislike for it. Working a '1' earns you 6 points. Working a '6' earns you 1 point. 
    * **Multiplier:** Your points compound over the 6 years. The higher your fatigue score, the stronger your mathematical priority to get the holidays you actually want in upcoming years.
    * **Year 1 Rules:** Only Thanksgiving, Christmas, and New Year's are scheduled.
    * **Years 2-6 Rules:** All 6 holidays are scheduled. No double-booking in a single year, and heavy protection against working the same holiday two years in a row.
    """)

st.divider()

# --- INPUT SECTION ---
st.markdown("### Step 1: Input Group Preferences")
st.write("Rank 1 to 6 (6 = Most Preferred, 1 = Least Preferred)")

# Default preferences set to 3 for a neutral baseline
default_data = {hol: [3]*6 for hol in HOLIDAYS}
df_prefs = pd.DataFrame(default_data, index=PROVIDERS)

edited_df = st.data_editor(df_prefs, use_container_width=True)

if st.button("🎲 Generate Full 6-Year Schedule", type="primary"):
    
    # Tracking variables for the 6-year loop
    cum_points = {p: 0 for p in PROVIDERS}
    last_year_holiday = {p: "None" for p in PROVIDERS}
    results = []

    # Run the 6-year simulation
    for year in range(1, 7):
        holidays_this_year = ["Thanksgiving", "Christmas", "New Year"] if year == 1 else HOLIDAYS
        available_providers = PROVIDERS.copy()
        year_assignments = {hol: "Not Assigned" for hol in HOLIDAYS}
        
        # Assign each holiday
        for hol in holidays_this_year:
            best_score = -1
            best_provider = None
            
            for p in available_providers:
                try:
                    pref = float(edited_df.loc[p, hol])
                except ValueError:
                    pref = 3.0 # Fallback
                
                # Math logic
                rand_val = random.random()
                mult = 1.0 + (cum_points[p] * 0.15) # Multiplier increases by 0.15 per fatigue point
                fatigue_penalty = 0.01 if last_year_holiday[p] == hol else 1.0
                
                score = rand_val * pref * mult * fatigue_penalty
                
                if score > best_score:
                    best_score = score
                    best_provider = p
                    
            year_assignments[hol] = best_provider
            available_providers.remove(best_provider)
            
        # Log the results and update compounding scores for the next year
        for p in PROVIDERS:
            assigned_hol = "None"
            for h, prov in year_assignments.items():
                if prov == p:
                    assigned_hol = h
            
            pts_before = cum_points[p]
            mult_before = 1.0 + (pts_before * 0.15)
            
            if assigned_hol != "None":
                pref_val = int(edited_df.loc[p, assigned_hol])
                pts_earned = 7 - pref_val # 1->6pts, 6->1pt
                cum_points[p] += pts_earned
                last_year_holiday[p] = assigned_hol
                
                if year == 1:
                    exp = f"Year 1 baseline. You started with 0 fatigue points. You were assigned {assigned_hol} (which you ranked a {pref_val}), adding {pts_earned} points to your fatigue score for next year."
                else:
                    exp = f"Entering this year, your fatigue score was {pts_before}, giving you a priority multiplier of {mult_before:.2f}x. You were assigned {assigned_hol} (ranked {pref_val}), earning {pts_earned} new points."
            else:
                pref_val = None
                pts_earned = 0
                last_year_holiday[p] = "None"
                
                if year == 1:
                    exp = "Year 1 baseline. You were one of the providers not assigned a holiday this year. Your fatigue score remains 0."
                else:
                    exp = f"Entering this year, your fatigue score was {pts_before}, giving you a priority multiplier of {mult_before:.2f}x. You were not assigned a holiday this year."
            
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
        # Pivot the table to show Years as rows and Holidays as columns for the group
        group_df = st.session_state.master_schedule.copy()
        st.dataframe(group_df[["Year", "Provider", "Assigned Holiday"]], use_container_width=True, hide_index=True)
        
    with tab2:
        st.write("#### Personalized 6-Year View & Fatigue Tracking")
        selected_dr = st.selectbox("Select a Provider to view their profile:", PROVIDERS)
        
        dr_data = st.session_state.master_schedule[st.session_state.master_schedule["Provider"] == selected_dr]
        
        for index, row in dr_data.iterrows():
            with st.container():
                st.markdown(f"##### {row['Year']}")
                
                # Visual badge for the assignment
                if row['Assigned Holiday'] == "None":
                    st.info(f"**Assignment:** OFF")
                else:
                    st.error(f"**Assignment:** {row['Assigned Holiday']}")
                    
                st.write(f"> *{row['Explanation']}*")
                st.divider()