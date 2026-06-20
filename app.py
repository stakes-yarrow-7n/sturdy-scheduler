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
HOLIDAYS = ["Memorial Day", "July 4th", "Labor Day", "Thanksgiving", "Christmas", "New Year"]
MAJOR_HOLIDAYS = ["Thanksgiving", "Christmas", "New Year"]

if 'master_schedule' not in st.session_state:
    st.session_state.master_schedule = None

# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("⚙️ Group Settings")
    st.markdown("Adjust system rules here before generating the schedule.")
    
    st.markdown("### Premium Holiday Weights")
    weight_thanksgiving = st.slider("🦃 Thanksgiving Multiplier", min_value=1.0, max_value=3.0, value=1.5, step=0.1)
    weight_christmas = st.slider("🎄 Christmas Multiplier", min_value=1.0, max_value=3.0, value=2.0, step=0.1)
    weight_new_year = st.slider("🎆 New Year Multiplier", min_value=1.0, max_value=3.0, value=1.5, step=0.1)
    
    premium_weights = {
        "Thanksgiving": weight_thanksgiving,
        "Christmas": weight_christmas,
        "New Year": weight_new_year
    }
    st.divider()

# --- UI HEADER ---
st.title("🏥 Cardiology Group - 6-Year Holiday Coverage")

with st.expander("📖 System Rules & Fatigue Scoring"):
    st.write("""
    * **Preferences:** Rank the holidays from **1 to 6**. (6 = Most Preferred to Cover, 1 = Least Preferred).
    * **Standard Fatigue Points:** Working a '1' earns you 6 points. Working a '6' earns you 1 point. 
    * **The Major Holiday Premium:** Working Thanksgiving, Christmas, or New Year's applies a custom multiplier to reward the extra sacrifice.
    * **Priority Odds:** Your points compound over the 6 years. The higher your fatigue score, the stronger your mathematical priority in upcoming years.
    * **Rules:** No double-booking in a single year, and heavy protection against working the same holiday two years in a row.
    """)

st.divider()

# --- INPUT SECTION ---
st.markdown("### Step 1: Input Group Preferences")

my_sheet_url = "https://docs.google.com/spreadsheets/d/1dewvDOk7_dzEH06DyeXKGr6p4kiBO_6_49zvpnL9xfM/export?format=csv"
sheet_url = st.text_input("🔗 Google Sheets CSV Link", value=my_sheet_url) 

# Start by creating the complete default table (all 6 doctors, all 3s)
default_data = {hol: [3]*len(PROVIDERS) for hol in HOLIDAYS}
df_prefs = pd.DataFrame(default_data, index=PROVIDERS)

if sheet_url:
    try:
        # Read the live Google Sheet
        survey_data = pd.read_csv(sheet_url)
        
        # Clean the Google Sheet column names (make lowercase, remove spaces)
        survey_data.columns = [str(c).strip().lower() for c in survey_data.columns]
        
        count = 0
        for index, row in survey_data.iterrows():
            # Find the name column (even if it's slightly misspelled)
            raw_name = ""
            for col in survey_data.columns:
                if "doctor" in col or "name" in col:
                    raw_name = str(row[col]).strip().lower()
                    break
                    
            # FUZZY MATCH: Check if the doctor's real base name is inside the form name
            matched_provider = None
            for p in PROVIDERS:
                base_name = p.split(",")[0].strip().lower() # Turns "Ross Pollack, MD" into "ross pollack"
                if base_name in raw_name:
                    matched_provider = p
                    break
            
            # If we found a match, fill in their holidays
            if matched_provider:
                for hol in HOLIDAYS:
                    hol_lower = hol.lower()
                    # Find the matching column in Google Sheets
                    for col in survey_data.columns:
                        if hol_lower in col or (hol_lower == "july 4th" and "4th" in col):
                            try:
                                df_prefs.loc[matched_provider, hol] = int(float(row[col]))
                            except ValueError:
                                pass # Skip if they left it blank or typed a word
                            break
                count += 1
        
        if count > 0:
            st.success(f"Successfully loaded responses for {count} provider(s)!")
        else:
            st.info("Connected to Google Sheets. Waiting for form submissions (or names didn't match).")
            
        # Developer tool to see exactly what Google is sending
        with st.expander("🛠️ Developer View (Raw Google Data)"):
            st.write("If names aren't matching, check what Google is actually sending below:")
            st.dataframe(survey_data)
            
    except Exception as e:
        st.error(f"Could not connect to sheet. Defaulting to 3s. (Error: {e})")

# Show the data table
edited_df = st.data_editor(df_prefs, use_container_width=True)


# --- SCHEDULING LOGIC ---
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
                    if p in edited_df.index:
                        pref = float(edited_df.loc[p, hol])
                    else:
                        pref = 3.0
                except (ValueError, KeyError):
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
                if p in edited_df.index:
                    pref_val = int(edited_df.loc[p, assigned_hol])
                else:
                    pref_val = 3
                    
                base_pts = 7 - pref_val 
                
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