import os
import time
import functools
import asyncio
from dotenv import load_dotenv
load_dotenv() 

from typing import List, Literal, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from .state import ValidationResult, ExtractionModel, WeatherData, SoilData
from .integration import fetch_and_validate_environment_data, format_environment_for_prompt


def retry_on_rate_limit(max_retries=3, initial_wait=2):
    """Decorator to retry function calls with exponential backoff on rate limit errors."""
    def decorator(func):
        # Check if it's an async function
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                wait_time = initial_wait
                for i in range(max_retries):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                            if i < max_retries - 1:
                                print(f"Rate limit hit. Retrying in {wait_time}s... (Attempt {i+1}/{max_retries})")
                                await asyncio.sleep(wait_time)
                                wait_time *= 2
                            else:
                                raise e
                        else:
                            raise e
                return await func(*args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                wait_time = initial_wait
                for i in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                            if i < max_retries - 1:
                                print(f"Rate limit hit. Retrying in {wait_time}s... (Attempt {i+1}/{max_retries})")
                                time.sleep(wait_time)
                                wait_time *= 2
                            else:
                                raise e
                        else:
                            raise e
                return func(*args, **kwargs)
            return sync_wrapper
    return decorator

# System Instructions - Extraction

EXTRACTION_SYSTEM_PROMPT = """You are an expert agricultural entity extraction specialist.
Analyze the farmer's query and extract structured info into JSON. 
Normalize all biological terms and use lowercase for consistency."""

FEW_SHOT_EXAMPLES = [
    {
        "input": "My tomato plants have yellow leaves and I see small green bugs on them. I sprayed some neem oil yesterday but they keep coming back. It's getting worse!",
        "output": {
            "crop": "tomato",
            "symptoms": ["yellow leaves", "small green bugs on plants"],
            "pests": ["aphids"],
            "action_taken": "sprayed neem oil yesterday",
            "urgency": "high",
            "primary_category": "pest"
        }
    },
    {
        "input": "I'm growing wheat and noticed some brown spots appearing on the leaves. Haven't done anything yet.",
        "output": {
            "crop": "wheat",
            "symptoms": ["brown spots on leaves"],
            "pests": [],
            "action_taken": "",
            "urgency": "medium",
            "primary_category": "disease"
        }
    },
    {
        "input": "URGENT: My rice crop is dying! The stems are rotting and there's a bad smell. Water is standing in the field. Used urea fertilizer last week.",
        "output": {
            "crop": "rice",
            "symptoms": ["rotting stems", "bad smell", "standing water in field"],
            "pests": ["bacterial blight"],
            "action_taken": "applied urea fertilizer last week",
            "urgency": "critical",
            "primary_category": "disease"
        }
    },
    {
        "input": "Potato plants looking healthy but growth seems slow. Maybe the soil is too dry? Nothing unusual otherwise.",
        "output": {
            "crop": "potato",
            "symptoms": ["slow growth", "dry soil"],
            "pests": [],
            "action_taken": "",
            "urgency": "low",
            "primary_category": "irrigation"
        }
    },
    {
        "input": "Cotton leaves curling and white powder on them. Applied sulfur dust 3 days ago but problem persists. Spreading to other plants quickly!",
        "output": {
            "crop": "cotton",
            "symptoms": ["curling leaves", "white powdery coating"],
            "pests": ["powdery mildew"],
            "action_taken": "applied sulfur dust 3 days ago",
            "urgency": "high",
            "primary_category": "disease"
        }
    }
]


def format_few_shot_examples() -> str:
    """Format few-shot examples into a string for the prompt (with escaped braces for LangChain)."""
    import json
    examples_text = "\n\n".join([
        f"Example {i+1}:\nInput: {ex['input']}\nOutput: {json.dumps(ex['output']).replace('{', '{{').replace('}', '}}')}"
        for i, ex in enumerate(FEW_SHOT_EXAMPLES)
    ])
    return f"\n\nHere are examples of correct extractions:\n\n{examples_text}"

# System Instructions - Validation

VALIDATION_SYSTEM_PROMPT = """You are an agricultural data auditor. 
Your job is to ensure the farmer's input is logical compared to real-time data.

Current Environment:
- Temperature: {temp}C
- Soil Moisture: {moisture}%
- Rainfall (24h): {rain}mm
- Soil pH: {ph}

Farmer Input: {query}

TASK: 
1. Check for 'saying but not doing' discrepancies.
   - E.g., if farmer says 'soil is dry' but moisture is > 80%, flag as invalid.
2. Determine if the query is safe and relevant.

Respond with the ValidationResult Pydantic schema."""

# System Instructions - Photo Verification (Vision Model)

VISION_TIE_BREAKER_PROMPT = """
=== VISUAL AGRONOMIST PERSONA ===
You are an expert at identifying crop health and soil conditions through photography.

=== MISSION ===
Analyze the uploaded image to verify the farmer's claim: "{farmer_claim}"
and resolve the conflict with API data:
- Soil Moisture API: {soil_moisture}%
- Rainfall API: {rainfall_mm}mm

=== ANALYSIS TASKS ===
1. SOIL CHECK: Does the soil look parched/cracked (dry) or dark/reflective (wet)?
2. CONSISTENCY: If the API says it rained but the photo shows bone-dry dust, explain the likely reason
     (e.g., "The surface is dry due to high evaporation, but the sensors might be reading deeper moisture").
3. VERDICT: Should we trust the farmer's observation or the sensor data for the next step?

Respond with a clear, supportive explanation for the farmer.
"""

# System Instructions - Advice Generation

ADVICE_GENERATION_SYSTEM_PROMPT = """
=== SENIOR AGRONOMIST PERSONA ===
You are a Senior Agronomist. Provide practical, low-cost, and science-backed solutions.

=== CONTEXTUAL DATA ===
- Soil Data: pH {soil_ph}, Moisture {soil_moisture}%
- Weather: {temperature_c}C, Alert: {weather_alert}
- History (Memory Agent): {history}

=== FARMER'S QUESTION ===
{query}


=== TRUTH-CHECKING PROTOCOL ===
If farmer claims conflict with environmental data, respond with GENTLE VERIFICATION.
Example: "Your data shows 85% moisture, but since you observed dryness, we will proceed with a cautious irrigation plan."

=== CORE PRINCIPLE ===
"Precaution is better than cure". If heavy rain is forecast, advise DELAYING fertilizer or irrigation.

=== OUTPUT FORMAT ===
- ROOT CAUSE ANALYSIS
- IMMEDIATE ACTIONS (Next 48h)
- LONG-TERM PREVENTION
- SAFETY WARNINGS
"""

# Truth-Checking Prompt (Pre-Advice Filter)

TRUTH_CHECK_SYSTEM_PROMPT = """You are a data validation expert for agricultural advice.

Your job: Compare the farmer's claim against real-time environmental data and flag discrepancies.
Respond with gentle verification suggestions - NOT rejection.

ENVIRONMENTAL DATA:
- Soil pH: {soil_ph}
- Soil Moisture: {soil_moisture}%
- Rainfall (24h): {rainfall_mm}mm
- Temperature: {temperature_c}C
- Weather Alert: {weather_alert}

FARMER'S CLAIM: {farmer_claim}

TASK:
1. Identify conflicts between claim and data
2. Suggest gentle clarification questions
3. Format response as JSON:
{{
  "has_conflict": true/false,
  "conflict_description": "description if conflict exists",
  "verification_question": "gentle question to ask farmer",
  "proceed_with_advice": true/false,
  "confidence": 0-1
}}

EXAMPLES:
Claim: "Soil is very dry"
Data: Moisture = 85%
Response: {{"has_conflict": true, "conflict_description": "Soil shows 85% moisture (wet, not dry)",
"verification_question": "Could the issue be poor drainage rather than dryness?",
"proceed_with_advice": true}}

Claim: "Need to irrigate immediately"
Data: Rain alert shows 100mm expected
Response: {{"has_conflict": true, ..., "proceed_with_advice": false}}
"""

def create_extraction_chain(model_name: str = "gemini-3-flash-preview"):
    """Chain for keyword extraction using Gemini (free quota)."""
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0,
        google_api_key=os.getenv("GEMINI_API_KEY")
    ).with_structured_output(ExtractionModel)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Extract agricultural entities into JSON." + format_few_shot_examples()),
        ("human", "Query: {query}")
    ])
    return prompt | llm


def create_validation_chain(model_name: str = "gemini-3-flash-preview"):
    """Validates input using Gemini (free quota). Binds to ValidationResult for workflow branching."""
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0,
        google_api_key=os.getenv("GEMINI_API_KEY")
    ).with_structured_output(ValidationResult)
    prompt = ChatPromptTemplate.from_template(
        "Validate this farmer query: {query} against env data: Temp {temp}, Rain {rain}."
    )
    return prompt | llm


def create_vision_chain(model_name: str = "gemini-3-flash-preview"):
    """Member 4's Photo Model. Resolves Farmer vs API conflicts."""
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.1,
        google_api_key=os.getenv("GEMINI_API_KEY")
    )
    prompt = ChatPromptTemplate.from_template(VISION_TIE_BREAKER_PROMPT)
    return prompt | llm


def create_advice_chain(model_name: str = "gemini-3-flash-preview"):
    """Main Advisory Engine using Gemini for high-level reasoning."""
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.2,
        google_api_key=os.getenv("GEMINI_API_KEY")
    )
    prompt = ChatPromptTemplate.from_template(ADVICE_GENERATION_SYSTEM_PROMPT)
    return prompt | llm


def create_truth_check_chain(model_name: str = "gpt-4o-mini"):
    """
    Dedicated chain for comparing farmer claims against environmental data.
    Detects discrepancies and suggests gentle verification before advice.
    This acts as a guardrail before the main advice engine.
    Args:
        model_name: LLM model for truth checking
    Returns:
        Runnable chain that outputs JSON with conflict detection
    """
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0,
        api_key=os.getenv("GEMINI_API_KEY")
    )
    prompt = ChatPromptTemplate.from_template(TRUTH_CHECK_SYSTEM_PROMPT)
    return prompt | llm

@retry_on_rate_limit(max_retries=3)
def extract_keywords_from_query_sync(query: str, model_name: str = "gemini-3-flash-preview") -> ExtractionModel:
    """
    Extract structured keywords from a farmer's natural language query.
    Args:
        query: The farmer's input text
        model_name: Gemini model to use (default: gemini-3-flash-preview)   
    Returns:
        ExtractionModel with extracted entities
    """
    chain = create_extraction_chain(model_name=model_name)
    result = chain.invoke({"query": query})
    return result


@retry_on_rate_limit(max_retries=3)
async def extract_keywords_from_query(query: str, model_name: str = "gemini-3-flash-preview") -> ExtractionModel:
    """
    Async version: Extract structured keywords from a farmer's natural language query.
    Args:
        query: The farmer's input text
        model_name: Gemini model to use (default: gemini-3-flash-preview)
    Returns:
        ExtractionModel with extracted entities
    """
    chain = create_extraction_chain(model_name=model_name)
    result = await chain.ainvoke({"query": query})
    return result


async def get_verified_advice(state: dict):
    
    truth_chain = create_truth_check_chain()
    truth_result = await truth_chain.ainvoke(state)

    if truth_result.get("has_conflict") and state.get("image_data"):
        vision_chain = create_vision_chain()
        await vision_chain.ainvoke(state)

    advice_chain = create_advice_chain()
    return await advice_chain.ainvoke({
        **state,
        "history": state.get("history", "No previous history found.")
    })

# Helper Functions - Advisory Engine

@retry_on_rate_limit(max_retries=3)
def generate_agricultural_advice(
    farmer_query: str,
    soil_ph: float,
    soil_moisture: float,
    rainfall_mm: float,
    temperature_c: float,
    weather_alert: str = None,
    history: str = "No previous history.",
    model_name: str = "gemini-3-flash-preview"
) -> str:
    """
    Generate agricultural advice grounded in environmental context.
    
    Args:
        farmer_query: The farmer's question or problem description
        soil_ph: Current soil pH
        soil_moisture: Current soil moisture percentage
        rainfall_mm: Rainfall in last 24 hours
        temperature_c: Current temperature
        weather_alert: Any active weather alerts
        history: Historical context from Memory Agent (default: empty)
        model_name: LLM to use (Gemini for better free tier support)
        
    Returns:
        String containing detailed agricultural advice
    """
    chain = create_advice_chain(model_name=model_name)
    result = chain.invoke({
        "soil_ph": soil_ph,
        "rainfall_mm": rainfall_mm,
        "soil_moisture": soil_moisture,
        "temperature_c": temperature_c,
        "weather_alert": weather_alert or "None",
        "history": history,
        "query": farmer_query
    })
    # Handle different response formats from Gemini/OpenAI
    if isinstance(result, str):
        return result
    elif hasattr(result, 'content'):
        content = result.content
        if isinstance(content, list):
            # Join text blocks if it's a list (common in multimodal or newer LangChain versions)
            text_blocks = []
            for block in content:
                if isinstance(block, dict) and 'text' in block:
                    text_blocks.append(block['text'])
                elif isinstance(block, str):
                    text_blocks.append(block)
                else:
                    text_blocks.append(str(block))
            return " ".join(text_blocks)
        return str(content)
    elif isinstance(result, dict) and 'text' in result:
        return result['text']
    elif isinstance(result, list) and len(result) > 0:
        if isinstance(result[0], dict) and 'text' in result[0]:
            return result[0]['text']
        return str(result[0])
    return str(result)



@retry_on_rate_limit(max_retries=3)
def verify_farmer_claim(
    farmer_claim: str,
    soil_ph: float,
    soil_moisture: float,
    rainfall_mm: float,
    temperature_c: float,
    weather_alert: str = None,
    model_name: str = "gemini-3-flash-preview"
) -> dict:
    """
    Verify farmer's claim against environmental data before advice.
    Detects conflicts and returns verification status.
    
    Args:
        farmer_claim: What the farmer is claiming about conditions
        soil_ph: Current soil pH
        soil_moisture: Current soil moisture percentage
        rainfall_mm: Rainfall in last 24 hours
        temperature_c: Current temperature
        weather_alert: Any active weather alerts
        model_name: LLM to use
        
    Returns:
        Dictionary with keys: has_conflict, conflict_description, verification_question, proceed_with_advice
    """
    chain = create_truth_check_chain(model_name=model_name)
    result = chain.invoke({
        "soil_ph": soil_ph,
        "rainfall_mm": rainfall_mm,
        "soil_moisture": soil_moisture,
        "temperature_c": temperature_c,
        "weather_alert": weather_alert or "None",
        "farmer_claim": farmer_claim
    })
    
    # Parse JSON response
    import json
    try:
        response_text = result.content if hasattr(result, 'content') else str(result)
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(response_text[json_start:json_end])
    except json.JSONDecodeError:
        pass
    
    # Fallback if parsing fails
    return {
        "has_conflict": False,
        "conflict_description": "",
        "verification_question": "",
        "proceed_with_advice": True,
        "confidence": 0.5
    }


# Integration Layer

def get_environmental_data_from_member3(latitude: float, longitude: float) -> dict:
    """
    Fetch and validate environmental data from Member 3's tools.
    
    This is the connection point between Member 3 (Environment/Tools) 
    and Member 4 (Prompts/LLM).
    
    Args:
        latitude: GPS latitude
        longitude: GPS longitude
        
    Returns:
        dict with keys:
            - weather_data: WeatherData model
            - soil_data: SoilData model
            - prompt_vars: dict of prompt template variables
    """
    try:
        # Fetch from Member 3's integration layer
        env_data = fetch_and_validate_environment_data(latitude, longitude)
        
        # Format for prompt templates
        prompt_vars = format_environment_for_prompt(
            env_data["weather_data"],
            env_data["soil_data"]
        )
        
        return {
            "weather_data": env_data["weather_data"],
            "soil_data": env_data["soil_data"],
            "prompt_vars": prompt_vars,
            "raw_response": env_data.get("raw_response")
        }
    except Exception as e:
        print(f"Error getting environmental data from Member 3: {str(e)}")
        # Return safe defaults
        return {
            "weather_data": WeatherData(temperature_c=None, humidity=0),
            "soil_data": SoilData(soil_ph=None),
            "prompt_vars": {},
            "raw_response": None
        }


def generate_advice_with_environment(
    farmer_query: str,
    latitude: float,
    longitude: float,
    history: str = "No previous history.",
    model_name: str = "gemini-3-flash-preview"
) -> str:
    """
    Generate agricultural advice by automatically fetching environmental data 
    from Member 3's APIs.
    
    This is the **recommended way** to call generate_agricultural_advice() because
    it automatically handles Member 3 integration.
    
    Args:
        farmer_query: The farmer's question/problem
        latitude: GPS latitude for location
        longitude: GPS longitude for location
        history: Historical context from Member 5 (optional)
        model_name: Gemini model (default: gemini-3-flash-preview)
        
    Returns:
        str: Detailed agricultural advice
        
    Example:
        ```python
        advice = generate_advice_with_environment(
            farmer_query="My tomato plants have yellow leaves",
            latitude=31.5497,
            longitude=74.3436,
            history="Previous visit: advised pH adjustment"
        )
        ```
    """
    # Get environmental data from Member 3
    env_context = get_environmental_data_from_member3(latitude, longitude)
    
    # Extract the validated data
    weather_data = env_context["weather_data"]
    soil_data = env_context["soil_data"]
    
    # Call the standard advice function with Member 3's data
    return generate_agricultural_advice(
        farmer_query=farmer_query,
        soil_ph=soil_data.soil_ph or 6.5,  # Default to neutral pH
        soil_moisture=soil_data.soil_moisture or 50,  # Default to moderate moisture
        rainfall_mm=weather_data.rainfall_mm or 0,  # Default to no rain
        temperature_c=weather_data.temperature_c or 25,  # Default to 25C
        weather_alert=weather_data.weather_alert,
        history=history,
        model_name=model_name
    )
