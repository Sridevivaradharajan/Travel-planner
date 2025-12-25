# AI Travel Planner App

## Overview

The AI Travel Planner is an intelligent, agent-driven application designed to simplify and personalize trip planning. By analyzing user preferences such as destination, budget, travel dates, and interests, the system automatically generates optimized and practical travel itineraries.

This project demonstrates the real-world application of **agentic AI**, combining reasoning, recommendation logic, and automation to deliver end-to-end travel planning solutions.

---

## Key Features

* 🧠 AI-powered personalized itinerary generation
* 📍 Destination-based recommendations
* 💰 Budget-aware trip planning
* 📅 Optimized schedules based on travel duration
* 🤖 Agentic AI workflow for reasoning and decision-making
* 🧩 Modular and scalable architecture
* 🖥️ User-friendly interface for seamless interaction

---

## Technology Stack

* **Programming Language:** Python
* **Framework:** Streamlit
* **AI/LLM Integration:** LangChain + LLM (Gemini)
* **Database:** PostgreSQL 
* **APIs (Optional):** Weather

---

## How It Works

1. User inputs travel details (destination, budget, dates, preferences).
2. AI agent processes constraints and preferences.
3. Recommendation engine generates a customized itinerary.
4. Results are presented in a structured and easy-to-understand format.

---

## Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Sridevivaradharajan/Travel-planner.git
cd Travel-planner
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv travelplanner
source travelplanner/bin/activate   # Windows: travelplanner\Scripts\activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment Variables

Create a `.env` file:

```env
# LLM Configuration
LLM_API_KEY=your_llm_api_key

# Database Configuration (Credential-based)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=travel_planner
DB_USER=postgres
DB_PASSWORD=your_password

```

---

## Run the Application

```bash
streamlit run app.py
```

---

## Use Cases

* Individual travelers planning trips
* Budget-conscious travel planning
* Smart itinerary generation
* AI agent demonstrations

---

## Future Enhancements

* 🌐 Real-time pricing and booking integration
* ☁️ Live traffic updates
* 🧾 Automated booking and reservation management
* 📊 User feedback and learning loops
* 📱 Mobile app deployment

---

## Project Outcomes

* Demonstrates operational use of agentic AI beyond prototypes
* Applies AI to real-world consumer problems
* Highlights intelligent decision-support systems in travel tech

* Add **architecture diagram text**
* Customize it for **Agent.ai / HackerEarth submission**
