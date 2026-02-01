import streamlit as st
import random
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from src.ai_logic import get_chat_response

def show_farmer_dashboard():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');
        
        * {
            font-family: 'Outfit', sans-serif;
        }
        
        .main {
            background-color: #0e1117;
            color: #ffffff;
        }
        
        .stButton>button {
            border-radius: 12px;
            background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%);
            color: white;
            border: none;
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 114, 255, 0.3);
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 114, 255, 0.4);
        }
        
        .glass-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: transform 0.3s ease;
        }
        
        .glass-card:hover {
            border: 1px solid rgba(255, 255, 255, 0.1);
            background: rgba(255, 255, 255, 0.05);
        }
        
        .stat-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #00c6ff;
        }
        
        .stat-label {
            font-size: 0.9rem;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        [data-testid="stSidebar"] {
            background-color: #0a0c10;
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .header-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 2rem;
        }
        
        .badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .badge-green { background: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid #10b981; }
        .badge-yellow { background: rgba(245, 158, 11, 0.1); color: #f59e0b; border: 1px solid #f59e0b; }
        .badge-red { background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid #ef4444; }
        
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.image("https://img.icons8.com/clouds/200/farm.png", width=120)
        st.title("AgriTech AI")
        st.markdown("---")
        
        page = st.radio("Navigation", ["Dashboard", "AI Advisor"])
        
        st.markdown("---")
        st.subheader("Active Crop")
        active_crop = st.session_state.get('crop_type', 'Wheat')
        st.info(f"{active_crop} (Stage: Flowering)")
        
        st.markdown("---")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.page = "login"
            st.rerun()
            
        if st.button("Field Setup"):
            st.session_state.page = "welcome"
            st.rerun()

    if page == "Dashboard":
        st.markdown(f"""
            <div class='header-container'>
                <div>
                    <h1 style='margin:0;'>Farmer Dashboard</h1>
                    <p style='color:#94a3b8;'>Monitoring your {st.session_state.get('crop_type', 'crop')} in {st.session_state.get('soil_type', 'your')} soil.</p>
                </div>
                <div>
                    <span class='badge badge-green'>System Online</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        col_back, col_space = st.columns([1, 4])
        with col_back:
            if st.button("Change Field Details"):
                st.session_state.page = "welcome"
                st.rerun()

        col1, col2, col3, col4 = st.columns(4)
        
        env = st.session_state.get('env_data', {})
        weather = env.get('weather', {})
        soil = env.get('soil', {})
        
        real_temp = weather.get('temperature_c', 'N/A')
        real_humid = weather.get('humidity', 'N/A')
        real_moist = soil.get('soil_moisture', 'N/A')
        
        with col1:
            st.markdown(f"""
                <div class='glass-card'>
                    <p class='stat-label'>Soil Moisture</p>
                    <p class='stat-value'>{real_moist}%</p>
                    <p style='color:#10b981; font-size:0.8rem;'>Real-time Sensor Data</p>
                </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
                <div class='glass-card'>
                    <p class='stat-label'>Avg Temp</p>
                    <p class='stat-value'>{real_temp}°C</p>
                    <p style='color:#f59e0b; font-size:0.8rem;'>Humidity: {real_humid}%</p>
                </div>
            """, unsafe_allow_html=True)
            
        with col3:
            ph = st.session_state.get('ph_level', 7.0)
            if 6.0 <= ph <= 7.5:
                nutrient_status = "Excellent"
                nutrient_color = "#10b981"
            elif 5.5 <= ph < 6.0 or 7.5 < ph <= 8.0:
                nutrient_status = "Good"
                nutrient_color = "#f59e0b"
            else:
                nutrient_status = "Critical"
                nutrient_color = "#ef4444"
                
            st.markdown(f"""
                <div class='glass-card'>
                    <p class='stat-label'>Nutrient Level</p>
                    <p class='stat-value' style='color:{nutrient_color};'>{nutrient_status}</p>
                    <p style='color:#94a3b8; font-size:0.8rem;'>pH {ph}</p>
                </div>
            """, unsafe_allow_html=True)
            
        with col4:
            alert = st.session_state.get('weather_alert')
            risk_color = "#ef4444" if alert and alert != "None" else "#10b981"
            risk_val = "Moderate" if alert and alert != "None" else "Low"
            risk_sub = alert if alert and alert != "None" else "No active threats"
            
            st.markdown(f"""
                <div class='glass-card'>
                    <p class='stat-label'>Risk Level</p>
                    <p class='stat-value' style='color:{risk_color};'>{risk_val}</p>
                    <p style='color:#94a3b8; font-size:0.8rem;'>{risk_sub}</p>
                </div>
            """, unsafe_allow_html=True)

        left_col, right_col = st.columns([1, 1])

        with left_col:
            st.markdown("### AI Recommended Action")
            
            action_plan = st.session_state.get('action_plan', [])
            if not action_plan:
                st.info("Optimizing crop management strategies...")
                action_plan = [
                    "Monitor soil moisture levels daily",
                    "Check for local weather alerts before irrigation",
                    "Maintain current crop growth schedule"
                ]
            
            for action in action_plan:
                st.markdown(f"""
                    <div class='glass-card'>
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <div>
                                <h4 style='margin:0; color:#00c6ff;'>{action}</h4>
                                <p style='margin:5px 0; font-size:0.9rem; color:#cbd5e1;'>Strategized based on your field's real-time environmental data.</p>
                            </div>
                            <span class='badge badge-green'>Active</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        with right_col:
            st.markdown(f"### {active_crop} Growth Progress")
            
            days = range(1, 11)
            if active_crop == "Rice":
                base_height = [2, 5, 8, 12, 18, 25, 32, 40, 50, 60]
            elif active_crop == "Wheat":
                base_height = [5, 10, 18, 28, 40, 55, 70, 85, 100, 115]
            else:
                base_height = [3, 7, 12, 20, 30, 42, 55, 68, 82, 95]
                
            chart_data = pd.DataFrame({
                'Day': days,
                'Actual Height (cm)': base_height,
                'Projected Height': [h + random.randint(-2, 5) for h in base_height]
            })
            
            fig = px.line(chart_data, x='Day', y=['Actual Height (cm)', 'Projected Height'], 
                          color_discrete_sequence=['#00c6ff', 'rgba(0, 198, 255, 0.3)'],
                          labels={'value': 'Height (cm)'})
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Environmental Status")
        current_alert = st.session_state.get('weather_alert')
        if current_alert and current_alert != "None":
            st.warning(f"**Alert:** {current_alert}. Adjust your farm management accordingly.")
        else:
            st.success("Environmental conditions are optimal for core activities today.")


    elif page == "AI Advisor":
        st.markdown(f"<h1 style='margin-bottom:0;'>AI Advisor</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#94a3b8;'>Expert guidance for your {active_crop} in {st.session_state.get('soil_type', 'your')} soil.</p>", unsafe_allow_html=True)
        
        if st.button("Change Field Details"):
            st.session_state.page = "welcome"
            st.rerun()
        
        if "chat_crop" not in st.session_state or st.session_state.chat_crop != active_crop:
            st.session_state.messages = []
            st.session_state.chat_crop = active_crop
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"Hello! I see you are managing your **{active_crop}** crops. I have analyzed your current weather and soil conditions. How can I assist you with your farming today?"
            })
            
        with st.sidebar:
            if st.button("Clear Chat History"):
                del st.session_state.messages
                st.rerun()

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask about irrigation, pests, or fertilizer..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Consulting AI Agronomist..."):
                    env = st.session_state.get('env_data', {})
                    weather = env.get('weather', {})
                    soil = env.get('soil', {})
                    
                    context = {
                        "crop_type": st.session_state.get('crop_type'),
                        "soil_type": st.session_state.get('soil_type'),
                        "ph_level": st.session_state.get('ph_level'),
                        "weather_alert": st.session_state.get('weather_alert'),
                        "temperature_c": weather.get('temperature_c'),
                        "humidity": weather.get('humidity'),
                        "rainfall_mm": weather.get('rainfall_mm'),
                        "soil_moisture": soil.get('soil_moisture'),
                        "soil_ph": soil.get('soil_ph')
                    }
                    response = get_chat_response(st.session_state.messages, context)
                    st.markdown(response)

            
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    show_farmer_dashboard()