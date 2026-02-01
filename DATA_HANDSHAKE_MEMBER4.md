#  Data Handshake Document - Member 4 (Prompt & LLM Specialist)

**Status:**  All connections defined and ready for integration  
**Date:** February 1, 2026  
**Ownership:** Member 4 (Prompt Engineering & LLM Chains)

---

##  Connection Map: Member 4  Other Teams

### **Connection 1: Member 4  Member 1 (UI/Frontend)**

**Purpose:** Member 1 displays validation errors to the farmer.

**Data Flow:**
```
UI (Member 1)
    
    Captures FarmerInput (crop, soil_type, location, reported_action)
    
Member 4's Validation Chain
    
    Returns ValidationResult (is_valid, error_message, warnings)
    
UI (Member 1)
    
    If is_valid=False, show error_message as popup
```

**Shared Data Contracts:**

| Field | Type | Origin | Description | Example |
|-------|------|--------|-------------|---------|
| `FarmerInput.crop` | `str` (2+ chars) | UI sends | Crop name | "tomato", "wheat" |
| `FarmerInput.soil_type` | `Literal[...]` | UI sends | Soil category | "loamy", "clay" |
| `FarmerInput.location` | `str` (2+ chars) | UI sends | Location name | "Punjab, India" |
| `FarmerInput.reported_action` | `str` (5+ chars) | UI sends | Issue description | "Yellow leaves appearing..." |
| `ValidationResult.is_valid` | `bool` | Member 4 returns | Pass/fail status | `True` or `False` |
| `ValidationResult.error_message` | `str` | Member 4 returns | Reason for failure | "Invalid crop name" |
| `ValidationResult.warnings` | `List[str]` | Member 4 returns | Non-blocking issues | ["Consider soil test"] |

**Code Location:**
- `src/agents/state.py`: `FarmerInput`, `ValidationResult`
- `src/agents/prompts.py`: `create_validation_chain()`, `extract_keywords_from_query_sync()`

---

### **Connection 2: Member 4  Member 2 (Workflow/Graph)**

**Purpose:** Member 2 orchestrates the workflow by calling Member 4's chains.

**Data Flow:**
```
Member 2's LangGraph (graph.py)
    
    [Node 1] Call extract_extraction_chain()  ExtractionModel
    [Node 2] Call create_validation_chain()  ValidationResult  
    [Node 3] Call create_advice_chain()  Advisory string
    
    Route based on results (conditional edges)
    
Return final advice to User
```

**Chain Functions to Import:**

| Function | Location | Returns | Used For |
|----------|----------|---------|----------|
| `create_extraction_chain()` | `prompts.py` | `ExtractionModel` | Extract crop, pests, symptoms, urgency |
| `create_validation_chain()` | `prompts.py` | `ValidationResult` | Check if input conflicts with sensor data |
| `create_advice_chain()` | `prompts.py` | Advisory string | Generate personalized recommendations |
| `create_vision_chain()` | `prompts.py` | Vision analysis | Compare photo vs. sensor data (optional) |
| `create_truth_check_chain()` | `prompts.py` | JSON conflict status | Detect discrepancies |

**Code Location:**
- `src/agents/prompts.py`: All `create_X_chain()` functions
- `src/agents/graph.py`: Will import and call these functions

**Example Import (for Member 2):**
```python
from src.agents.prompts import (
    create_extraction_chain,
    create_validation_chain,
    create_advice_chain,
)

# In graph node:
extraction_chain = create_extraction_chain()
result = extraction_chain.invoke({"query": farmer_query})
```

---

### **Connection 3: Member 4  Member 3 (API/Tools Integration)**

**Purpose:** Member 3 fetches real-time data; Member 4 uses it in prompts.

**Data Flow:**
```
Member 3's Tools (soil_service.py, weather_api.py)
    
    Fetches weather data  WeatherData model
    Fetches soil data  SoilData model
    
Member 4's Prompts
    
    Injects {soil_ph}, {temperature_c}, {rainfall_mm}, etc. into prompt
    
Gemini AI grounds advice in real environmental facts
```

**Shared Data Contracts:**

**WeatherData (from Member 3):**
| Field | Type | Constraint | Used In Prompt |
|-------|------|-----------|-----------------|
| `temperature_c` | `float` | Any | `{temperature_c}C` |
| `humidity` | `int` | 0-100 | Not yet used |
| `rainfall_mm` | `float (optional)` | 0 | `{rainfall_mm}mm` |
| `weather_alert` | `str (optional)` | Any | `{weather_alert}` |

**SoilData (from Member 3):**
| Field | Type | Constraint | Used In Prompt |
|-------|------|-----------|-----------------|
| `soil_ph` | `float (optional)` | 0-14 | `{soil_ph}` |
| `soil_moisture` | `float (optional)` | 0-100 | `{soil_moisture}%` |
| `nitrogen` | `float (optional)` | 0 | Available for future prompts |
| `phosphorus` | `float (optional)` | 0 | Available for future prompts |
| `potassium` | `float (optional)` | 0 | Available for future prompts |

**Prompts Using These Variables:**

1. **VALIDATION_SYSTEM_PROMPT** (line ~180 in prompts.py):
   ```
   - Soil Data: pH {soil_ph}, Moisture {soil_moisture}%
   - Weather: {temperature_c}C, Alert: {weather_alert}
   ```
   Variables needed: `soil_ph`, `soil_moisture`, `temperature_c`, `weather_alert`

2. **ADVICE_GENERATION_SYSTEM_PROMPT** (line ~206):
   ```
   - Soil pH: {soil_ph}
   - Soil Moisture: {soil_moisture}%
   - Rainfall (24h): {rainfall_mm}mm
   ```
   Variables needed: `soil_ph`, `soil_moisture`, `rainfall_mm`

**Code Location:**
- `src/agents/state.py`: `WeatherData`, `SoilData` models
- `src/tools/weather_api.py`: Should return `WeatherData` (Member 3)
- `src/tools/soil_service.py`: Should return `SoilData` (Member 3)
- `src/agents/prompts.py`: Uses these in chain invocations

---

### **Connection 4: Member 4  Member 5 (Database/Memory)**

**Purpose:** Member 5 retrieves history; Member 4 injects it into prompts so AI "remembers."

**Data Flow:**
```
Member 5's Memory Agent (database/memory.py)
    
    Query: Get history for this farmer
    
    Returns: String of past interactions
    
Member 4's Prompt
    
    Injects {history} into ADVICE_GENERATION_SYSTEM_PROMPT
    
    Gemini AI considers past advice before responding
```

**History Format Specification:**

| Field | Type | Example |
|-------|------|---------|
| `history` | `str` | `"Visit 1 (2026-01-15): Farmer reported tomato yellowing. Advised: increase soil pH. Visit 2 (2026-01-22): Farmer says leaves turning brown. Previously advised pH increase."` |
| Default (if no history) | `str` | `"No previous history."` |

**Usage in Code:**

In `generate_agricultural_advice()` function (prompts.py, line ~329):
```python
def generate_agricultural_advice(
    farmer_query: str,
    soil_ph: float,
    soil_moisture: float,
    rainfall_mm: float,
    temperature_c: float,
    weather_alert: str = None,
    history: str = "No previous history.",  # <-- From Member 5
    model_name: str = "gemini-3-flash-preview"
) -> str:
```

The `history` parameter is passed to the chain:
```python
result = chain.invoke({
    ...
    "history": history,  # <-- Injected into prompt as {history}
    ...
})
```

**Code Location:**
- `src/database/memory.py`: Should have function like `get_farmer_history(farmer_id: str) -> str`
- `src/agents/prompts.py`: Uses `{history}` in ADVICE_GENERATION_SYSTEM_PROMPT
- `generate_agricultural_advice()`: Accepts `history` parameter from Member 5

---

##  Summary Table: All Data Handshakes

| From/To | Shared Asset | Type | Direction | Status |
|---------|--------------|------|-----------|--------|
| **Member 1** | `FarmerInput`, `ValidationResult` | Pydantic Models |  |  Ready |
| **Member 2** | `create_X_chain()` functions | Callables |  |  Ready |
| **Member 3** | `WeatherData`, `SoilData` | Pydantic Models |  |  Defined, awaiting data |
| **Member 5** | `{history}` string | Template Variable |  |  Ready |

---

##  Integration Checklist

### For Member 1 (UI):
- [ ] Import `FarmerInput` and `ValidationResult` from `src/agents/state.py`
- [ ] Send form data as `FarmerInput` to Member 4's validation chain
- [ ] Display `ValidationResult.error_message` as popup on validation failure
- [ ] Display `ValidationResult.warnings` as yellow banner (non-blocking)

### For Member 2 (Graph):
- [ ] Import all `create_X_chain()` functions from `src/agents/prompts.py`
- [ ] Call `create_extraction_chain().invoke({"query": ...})`
- [ ] Call `create_validation_chain().invoke({...})`
- [ ] Call `create_advice_chain().invoke({...})`
- [ ] Route based on `ValidationResult.is_valid`

### For Member 3 (Tools):
- [ ] Return `WeatherData` object (matching schema in `src/agents/state.py`)
- [ ] Return `SoilData` object (matching schema in `src/agents/state.py`)
- [ ] Implement `get_weather_data(location: str) -> WeatherData`
- [ ] Implement `get_soil_data(location: str) -> SoilData`

### For Member 5 (Memory):
- [ ] Store past interactions with farmer in database
- [ ] Implement `get_farmer_history(farmer_id: str) -> str`
- [ ] Return formatted string of past visits/advice
- [ ] Pass to `generate_agricultural_advice(history=...)`

---

##  Ready for Integration

**All Data Contracts Defined **

Member 4's code is ready to be integrated with all other members. All variable names, types, and prompt placeholders are locked in and documented.

**Next Steps:**
1. Member 1 imports `FarmerInput` and `ValidationResult`
2. Member 2 imports chain functions and builds graph
3. Member 3 ensures tool outputs match `WeatherData` and `SoilData`
4. Member 5 provides `get_farmer_history()` function
5. All pieces connect in `graph.py` for end-to-end workflow
