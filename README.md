# RealityPatch

![Python](https://img.shields.io/badge/python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/ui-streamlit-orange)
![License](https://img.shields.io/badge/license-MIT-green)

**AI-Powered Fact-Checking and Claim Verification System**

RealityPatch is a robust, multi-agent AI system designed for real-time fact-checking and claim verification. It offers a clean and user-friendly Streamlit-based web interface and leverages powerful AI agents, search APIs, and language models to analyze text and media-based claims. Built with a modular and scalable architecture, RealityPatch provides detailed, explainable results for users ranging from casual fact-checkers to journalists and researchers.

---

## 📽️ Demo Preview

> Placeholder for demo GIF — replace with your real screen recording or walkthrough:

![RealityPatch Demo](demo.gif)

---

## 🔍 Core Purpose

RealityPatch enables users to:

* Input a claim or upload media
* Analyze the content using specialized AI agents
* View structured, multi-dimensional insights
* Understand credibility through clear metrics and summaries

---

## 🔹 Key Components

### 1. 📅 User Interface (`app.py`)

A sleek, modern **Streamlit web app** that includes:

* Text input for claims or questions
* Tabbed interface for viewing agent analyses
* Summary and detailed views
* Interactive metrics and visualizations
* Agent-styled responses with personality-like behavior

### 2. 🧠 Agent System

#### ✅ Clarity Agent (`agents/agent_clarity.py`)

* Breaks down a claim into logical components:

  * Subject, Predicate, Object
  * Quantifiers, Time, Location, Sources
* Outputs structured JSON
* Provides **confidence scores** for each part

#### 🔬 Proof Agent (`agents/agent_proof.py`)

* Verifies factual accuracy using the **Serper API** (Google search wrapper)
* Collects live evidence from search results
* Confidence scoring & fallback to mock mode if API is unavailable

#### 📈 ContextNet Agent (`contextnet_agent.py`)

* Provides **background knowledge** and **bias analysis**
* Extracts ideological slant, controversial aspects, and context

#### 🎨 MediaScan Agent (`media_scan_agent.py`)

* Analyzes media authenticity using:

  * Metadata extraction
  * Reverse image search
  * Gemini-based reasoning on real-world matches

### 3. ⚖️ Orchestration (`orchestrator.py`)

* Routes claims/media to the appropriate agents
* Aggregates all insights into a unified response
* Handles edge cases and graceful fallback logic

---

## 🚀 Technical Features

### 🌐 API Integration

* [x] Gemini (Google Generative AI)
* [x] Serper (Google Search API)
* [x] Optional fallback to mock data

### ⚡ Async & Modular Architecture

* Built for scalability and low-latency responses
* Plug-and-play agent modules

### ❌ Error Handling

* Graceful degradation if APIs fail
* Friendly UI messages
* Error logging for debugging

### 🛡️ Security & Config

* `.env`-based key management
* No hardcoded credentials
* API abstraction and modular utilities

---

## 🧪 Sample Usage

Run RealityPatch logic in Python without UI:

```python
from orchestrator import analyze_claim

result = analyze_claim("The Great Wall of China is visible from space.")

print("Clarity:", result['clarity_analysis'])
print("Evidence:", result['proof_evidence'])
```

This is useful for CLI-based batch testing or custom integrations.

---

## 📁 Project Structure

```
RealityPatch/
├── app.py                  # Streamlit frontend
├── orchestrator.py         # Core orchestrator
├── agents/
│   ├── agent_clarity.py
│   ├── agent_proof.py
│   ├── contextnet_agent.py
│   └── media_scan_agent.py
├── utils/
│   └── helpers.py          # API wrappers, parsing tools, etc.
├── requirements.txt
└── .env                    # API keys and environment config
```

---

## 🛠 Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_key_here
SERPER_API_KEY=your_serper_key_here  # Optional
```

### 3. Run the App

```bash
streamlit run app.py
```

---

## 🌟 Features at a Glance

* Multi-agent system: clarity, proof, media, and context agents
* Real-time fact-checking via Serper and Gemini APIs
* Visual confidence scoring
* Agent personas and summary detail toggles
* Bias detection and contextual narrative framing
* Works with both **text and image** inputs

---

## 🚀 Future Enhancements

* [ ] Batch/bulk claim processing
* [ ] Historical claim comparison
* [ ] User accounts and authentication
* [ ] Enhanced media detection with ML models
* [ ] Integration with public fact-checking databases (e.g., Snopes, PolitiFact)
* [ ] Admin dashboard for dataset review

---

## 📊 Built With

* [Streamlit](https://streamlit.io/) – UI framework
* [OpenAI / Gemini](https://ai.google.dev/) – AI reasoning and analysis
* [Serper.dev](https://serper.dev) – Search-based fact checking
* \[Python + AsyncIO] – Backend logic

---

## 🚀 License

This project is under active development for the Google AI Hackathon. Rights reserved to the author/team until post-hackathon publication.

---

## 📚 Credits

Developed by a passionate AI engineering team for the Google AI Hackathon. Special thanks to the open-source and API tool communities.

---

## 🆘 Need Help?

Open an issue or reach out to the dev team via the contact provided in the hackathon submission portal.

---

**RealityPatch** — Patch misinformation, one claim at a time.
