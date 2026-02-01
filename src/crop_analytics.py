# File: src/crop_analytics.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def render_crop_analytics(user_data=None):
    default_crop = "Rice"
    default_soil = "Clay"
    
    if user_data:
        default_crop = user_data.get('crop_type', 'Rice')
        default_soil = user_data.get('soil_type', 'Clay')

    st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    div[data-testid="stMetric"] { background-color: #1f2937; border: 1px solid #374151; }
    </style>
    """, unsafe_allow_html=True)

    st.title("Crop Analytics")
    
    with st.expander("Update Crop Data", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            crop_name = st.text_input("Active Crop", value=default_crop)
            current_stage = st.selectbox("Growth Stage", ["Seedling", "Vegetative", "Flowering", "Ripening"], index=2)
        with col2:
            days_in_stage = st.number_input("Days in Stage", value=12)
            water_level = st.slider("Water Level (cm)", 0, 15, 7)

    st.subheader(f"Analysis for: {crop_name}")
    
    stages = ["Seedling", "Vegetative", "Flowering", "Ripening"]
    try:
        progress = (stages.index(current_stage) + 1) / 4
    except:
        progress = 0.5
    st.progress(progress)
    st.caption(f"Current Stage: {current_stage} | Soil Context: {default_soil}")

    m1, m2, m3 = st.columns(3)
    m1.metric("Days in Stage", f"{days_in_stage} Days")
    m2.metric("Water Level", f"{water_level} cm", delta="-2cm (Target 5cm)")
    m3.metric("Soil Type", default_soil)

    st.subheader("Growth Trend")
    chart_data = pd.DataFrame({
        'Week': [1, 2, 3, 4, 5],
        'Growth': [2, 4, 6, 8, 10]
    })
    st.line_chart(chart_data.set_index('Week'))
