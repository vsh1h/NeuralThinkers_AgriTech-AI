from typing import Dict, Any, List
import os
import random
import json

from src.agents.prompts import (
    generate_agricultural_advice, 
    extract_keywords_from_query_sync,
    generate_advice_with_environment,
    verify_farmer_claim
)
from src.agents.state import WeatherData, SoilData

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    try:
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
    except ImportError:
        from langchain.schema import SystemMessage, HumanMessage, AIMessage
    AI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AI dependencies missing ({e}). Using mock AI logic.")
    AI_AVAILABLE = False

def get_simulated_analysis(weather: Dict[str, Any], soil: Dict[str, Any]) -> Dict[str, Any]:
    temp = weather.get('temperature_c', 25)
    ph = soil.get('soil_ph', 7.0)
    
    if ph < 6.0:
        crops = ["Blueberries", "Potatoes", "Sweet Potatoes"]
        soil_note = "Your soil is acidic. These crops thrive in lower pH levels."
        actions = ["Apply agricultural lime to raise pH", "Monitor for nutrient deficiencies", "Add organic matter"]
    elif ph > 7.5:
        crops = ["Asparagus", "Beets", "Cabbage"]
        soil_note = "Your soil is alkaline. Selecting salt-tolerant crops is recommended."
        actions = ["Apply elemental sulfur", "Use acidifying fertilizers", "Ensure deep irrigation"]
    else:
        crops = ["Rice", "Wheat", "Maize", "Tomatoes"]
        soil_note = "Your soil pH is optimal (Neutral). Most major crops will thrive here."
        actions = ["Maintain current fertilization", "Monitor moisture during bloom", "Check for pests weekly"]

    return {
        "suggested_crops": crops,
        "soil_analysis": f"(Simulated) {soil_note}",
        "action_plan": actions
    }

def get_simulated_chat(prompt: str, context: Dict[str, Any]) -> str:
    prompt_lower = prompt.lower()
    crop = context.get('crop_type', 'crop')
    ph = context.get('ph_level', 7.0)
    moisture = context.get('soil_moisture', 50.0)
    temp = context.get('temperature_c', 25.0)
    
    print(f"DEBUG: Simulator received prompt: '{prompt}'")
    is_hindi = "hindi" in prompt_lower or any('\u0900' <= char <= '\u097F' for char in prompt)
    print(f"DEBUG: Hindi detected: {is_hindi}")
    
    header = f"### Senior Agronomist Advice (Simulated)\n\n"
    
    # Check for Hindi characters or explicit request for Hindi first
    if is_hindi:
         advice = f"""नमस्ते! आपकी **{crop}** की फसल के लिए यहां एक विस्तृत कृषि रिपोर्ट दी गई है:

#### मुख्य विश्लेषण (Root Cause Analysis)
आपकी मिट्टी का pH {ph} है और नमी {moisture}% है। आपके क्षेत्र का तापमान ({temp}°C) फसल की वृद्धि के लिए महत्वपूर्ण है।

#### तत्काल कार्रवाई (Immediate Actions)
- **सिंचाई:** यदि मिट्टी सूखी लगे, तो सुबह 5 से 8 बजे के बीच पानी दें।
- **निरीक्षण:** पत्तियों के नीचे कीटों या रोगों के शुरुआती संकेतों की जांच करें।
- **मिट्टी का संतुलन:** फसल की बेहतर उपज के लिए मिट्टी की नमी को स्थिर रखें।

#### दीर्घकालिक रोकथाम (Long-term Prevention)
- **जैविक खाद:** बेहतर फसल के लिए हर साल अच्छी तरह से सड़ी हुई गोबर की खाद डालें।
- **फसल चक्र:** कीटों के प्रभाव को कम करने के लिए फसल चक्र (Crop Rotation) का पालन करें।

#### सुरक्षा चेतावनी (Safety Warning)
- कृषि रसायनों का प्रयोग करते समय सुरक्षात्मक गियर पहनें।
- तेज धूप में सिंचाई करने से बचें।

**नोट:** यह एक सिम्युलेटेड (Simulated) विशेषज्ञ सलाह है क्योंकि AI नेटवर्क अभी व्यस्त है। पूरे अनुभव के लिए कृपया थोड़ी देर बाद प्रयास करें।"""
    
    elif "water" in prompt_lower or "irrigation" in prompt_lower:
        advice = f"""**Subject: Irrigation Management for {crop}**

#### ROOT CAUSE ANALYSIS
Based on your current soil moisture ({moisture}%) and temperature ({temp}°C), your {crop} is currently in a metabolic state that requires precise water management. Over-irrigation can lead to root rot, while under-irrigation causes nutrient lockout.

#### IMMEDIATE ACTIONS (Next 48h)
- **Moisture Check:** Verify the top 3 inches of soil. If it feels dusty, provide a deep soak.
- **Timing:** Irrigate specifically between 5:00 AM and 8:00 AM to minimize fungal development and evaporation.
- **Monitoring:** If rainfall is expected, delay any manual irrigation to prevent nitrogen leaching.

#### LONG-TERM PREVENTION
Consider installing a drip irrigation system to deliver water directly to the root zone. Mulching with organic matter can also help retain {moisture}% moisture levels more consistently.

#### SAFETY WARNING
Avoid overhead sprinkling during hot afternoon hours, as this can cause leaf scald and increase the risk of disease."""
    
    elif "pest" in prompt_lower or "bug" in prompt_lower or "insect" in prompt_lower:
        advice = f"""**Subject: Integrated Pest Management (IPM) for {crop}**

#### ROOT CAUSE ANALYSIS
Rising temperatures ({temp}°C) often accelerate the life cycle of common pests. Your {crop} may be vulnerable to attackers if the plant is stressed by moisture fluctuations or pH imbalances.

#### IMMEDIATE ACTIONS (Next 48h)
- **Manual Scouting:** Inspect the undersides of leaves for eggs or small larvae.
- **Organic Intervention:** Apply a 2% Neem Oil solution or a mild insecticidal soap if infestation is visible.
- **Biological Control:** Encourage natural predators like ladybugs or lacewings in your field.

#### LONG-TERM PREVENTION
Implement crop rotation in the next season to break pest cycles. Maintain strong plant immunity by keeping soil pH near {ph}.

#### SAFETY WARNING
Wear protective gear when applying any treatment, even organic ones. Avoid spraying during the presence of bees or other pollinators."""

    elif "fertilizer" in prompt_lower or "nutrient" in prompt_lower or "urea" in prompt_lower:
        advice = f"""**Subject: Nutrient and Soil Health for {crop}**

#### ROOT CAUSE ANALYSIS
Soil pH is the primary governor of nutrient availability. At pH {ph}, your {crop} may have specific needs. If the pH is outside the 6.0-7.0 range, some essential minerals like Phosphorus or Iron might be "locked" in the soil.

#### IMMEDIATE ACTIONS (Next 48h)
- **Soil Testing:** If you haven't recently, conduct a professional N-P-K test.
- **Targeted Feeding:** Use a balanced, slow-release fertilizer if growth appears stunted.
- **pH Adjustment:** If pH is too high, consider adding elemental sulfur; if too low, add agricultural lime.

#### LONG-TERM PREVENTION
Incorporate well-rotted compost annually to build soil structure and buffer pH levels over time.

#### SAFETY WARNING
Do not over-apply Nitrogen fertilizers, as this can lead to excessive leaf growth at the expense of fruit/grain production and can contaminate local groundwater."""

    else:
        advice = f"""**Subject: General Agronomy Assessment for {crop}**

#### ROOT CAUSE ANALYSIS
The query "{prompt[:30]}..." indicates an interest in optimizing your {crop} production. Your current environmental parameters (pH: {ph}, Temp: {temp}°C) provide a solid baseline for analysis.

#### IMMEDIATE ACTIONS (Next 48h)
- **Routine Inspection:** Walk your fields to check for any visible stress signals in the leaves or stems.
- **Data Monitoring:** Keep an eye on the weather alerts for any sudden changes in humidity or rainfall.
- **Soil Balance:** Maintain the soil pH and moisture at optimal levels for {crop}.

#### LONG-TERM PREVENTION
Keep a detailed farm journal to track how your {crop} responds to different weather patterns and interventions.

#### SAFETY WARNING
Always prioritize environmental safety and personal protection when performing any field operations."""

    return header + advice

def get_expert_analysis(weather_data: Dict[str, Any], soil_data: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip().strip('"').strip("'")
    
    if AI_AVAILABLE and api_key and "sk-" in api_key:
        try:
            llm = ChatOpenAI(temperature=0.7, model_name="gpt-4o-mini", openai_api_key=api_key)
            json_prompt = ChatPromptTemplate.from_template(
                """
                Analyze environmental data: Weather: {weather_data}, Soil: {soil_data}.
                Return JSON with keys: suggested_crops (list), soil_analysis (string), action_plan (list of 3).
                """
            )
            chain = json_prompt | llm
            result = chain.invoke({"weather_data": str(weather_data), "soil_data": str(soil_data)})
            clean_content = result.content.strip().replace("```json", "").replace("```", "")
            return json.loads(clean_content)
        except Exception as e:
            print(f"AI API failed, switching to Smart Simulator: {e}")

    return get_simulated_analysis(weather_data, soil_data)

def get_chat_response(messages: List[Dict[str, str]], context: Dict[str, Any]) -> str:
    """
    Get chat response using the advanced logic from src.agents.prompts.
    Priority: Gemini → OpenAI → Smart Simulator
    """
    api_key = os.environ.get("OPENAI_API_KEY", "").strip().strip('"').strip("'")
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    
    user_prompt = messages[-1]["content"] if messages else ""
    
    print(f"\n{'='*60}")
    print(f"AI ADVISOR DEBUG:")
    print(f"  AI_AVAILABLE: {AI_AVAILABLE}")
    print(f"  Gemini Key Present: {bool(gemini_key)}")
    print(f"  OpenAI Key Present: {bool(api_key and 'sk-' in api_key)}")
    print(f"  User Query: {user_prompt[:50]}...")
    print(f"{'='*60}\n")
    
    # Extract historical context from messages
    history = ""
    if len(messages) > 1:
        history = "\n".join([f"{m['role']}: {m['content']}" for m in messages[:-1]])
    
    # Try Gemini FIRST
    if AI_AVAILABLE and gemini_key:
        try:
            print("  → Trying Gemini Flash...")
            advice = generate_agricultural_advice(
                farmer_query=user_prompt,
                soil_ph=context.get('ph_level', 7.0),
                soil_moisture=context.get('soil_moisture', 50.0),
                rainfall_mm=context.get('rainfall_mm', 0.0),
                temperature_c=context.get('temperature_c', 25.0),
                weather_alert=context.get('weather_alert', 'None'),
                history=history,
                model_name="gemini-flash-latest" 
            )
            print(f"  ✓ Gemini Response received ({len(advice)} chars)")
            return advice
        except Exception as e:
            error_msg = str(e)
            if "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg:
                print(f"  ✗ Gemini rate limit hit (Quota full)")
            else:
                print(f"  ✗ Gemini FAILED: {error_msg[:100]}")
            print(f"  → Falling back to OpenAI...")

    # Try OpenAI as fallback
    if AI_AVAILABLE and api_key and "sk-" in api_key:
        try:
            print("  → Trying OpenAI GPT-4o-mini...")
            
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate
            
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.2,
                openai_api_key=api_key
            )
            
            prompt_template = """You are a Senior Agronomist providing expert agricultural advice.

=== LANGUAGE PROTOCOL ===
Identify the language of the farmer's question and respond ENTIRELY in that same language. 

FARMER'S QUESTION: {query}

ENVIRONMENTAL CONTEXT:
- Soil pH: {soil_ph}
- Soil Moisture: {soil_moisture}%
- Temperature: {temperature_c}°C
- Recent Rainfall: {rainfall_mm}mm
- Weather Alert: {weather_alert}
- Conversation History: {history}

Provide practical, science-backed advice. Be specific and actionable."""

            prompt = ChatPromptTemplate.from_template(prompt_template)
            chain = prompt | llm
            
            result = chain.invoke({
                "query": user_prompt,
                "soil_ph": context.get('ph_level', 7.0),
                "soil_moisture": context.get('soil_moisture', 50.0),
                "temperature_c": context.get('temperature_c', 25.0),
                "rainfall_mm": context.get('rainfall_mm', 0.0),
                "weather_alert": context.get('weather_alert', 'None'),
                "history": history or "No previous conversation"
            })
            
            advice = result.content if hasattr(result, 'content') else str(result)
            print(f"  ✓ OpenAI Response received ({len(advice)} chars)")
            return advice
            
        except Exception as e:
            print(f"  ✗ OpenAI FAILED: {str(e)[:100]}")
            print(f"  → Falling back to Smart Simulator")
    
    return get_simulated_chat(user_prompt, context)


