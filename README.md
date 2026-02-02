#  AI-Driven Decision Support Across the Crop Lifecycle

##  Hosted Application

 **Live URL:**  
https://neuralthinkersagritech-ai-izdhjypdnncbq495eygprt.streamlit.app/

## Project Overview

Farming decisions are **dynamic**, not one-time. Soil conditions evolve, weather changes unpredictably, and crop requirements vary at each growth stage. Most existing agricultural advisory systems provide **static or generic recommendations**, which quickly become outdated.

This project introduces an **agentic AI system** that acts as a **continuous digital agronomist**, guiding farmers with timely, adaptive, and context-aware decisions throughout the entire crop lifecycle — from **sowing to harvest**.

---

##  Problem Statement

Farmers struggle to make optimal decisions because:

- Soil conditions change over time  
- Weather is unpredictable  
- Crop needs vary by growth stage  
- Advisory systems are delayed or generic  

As a result, farmers rely on **one-time recommendations** that fail to adapt to real-world changes.

---

##  Project Goal

To design an **autonomous AI-driven decision support system** that:

- Continuously observes farm conditions  
- Tracks crop progression and past actions  
- Determines the **next best farming action**  
- Updates guidance dynamically as conditions evolve  

---

##  Core Idea

Farming is treated as a **sequential decision-making problem**, not a single recommendation task.

Instead of asking:

> *“What should I do now?”*

The system continuously answers:

> **“What should be done next, given what has already happened and what is changing?”**

---

##  Why Agentic AI?

This system is **agentic** because it:

- **Observes**: Farmer inputs, weather data, time, crop stage, and local conditions  
- **Remembers**: Past actions and current crop state  
- **Decides autonomously**: Determines the next best farming action  
- **Adapts**: Updates decisions when conditions change  
- **Acts continuously**: Provides proactive guidance throughout the crop lifecycle  

It does **not wait for user queries** — it actively supports decision-making.

---

##  High-Level Agentic Workflow

1. Collect farmer inputs, weather data, time, and local conditions  
2. Understand current farm and soil conditions  
3. Track crop growth stage and historical actions  
4. Decide the next best farming action  
5. Provide clear and actionable advice  
6. Receive farmer feedback  
7. Update internal state and repeat continuously  

---

##  Tech Stack

### AI & Decision Logic
- **Python** – Core agent logic and orchestration  
- **Rule-based System** – Transparent and explainable decision-making  
- **Future Scope** – Reinforcement Learning for adaptive policy optimization  

 
###  Data Validation & Schemas
- **Pydantic** – Strong data validation, structured inputs, and reliable state management  

###  State & Memory
- **SQLite** – Lightweight relational storage for crop state, action history, and feedback  


###  Frontend & Deployment
- **Streamlit** – Interactive web UI for farmer interaction and real-time recommendations  

---

