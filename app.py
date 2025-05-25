import streamlit as st
import json
import os
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai
from agents.agent_clarity import run_clarity_agent
from agents.agent_proof import run_proof_agent
import logging
import plotly.graph_objects as go

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="RealityPatch - AI-Powered Fact Checking",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .agent-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        background-color: rgba(255, 255, 255, 0.1);
    }
    .verdict-badge {
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-weight: bold;
        text-align: center;
    }
    .verdict-verified {
        background-color: #28a745;
        color: white;
    }
    .verdict-unverified {
        background-color: #dc3545;
        color: white;
    }
    .verdict-unknown {
        background-color: #6c757d;
        color: white;
    }
    .confidence-bar {
        height: 1.5rem;
        border-radius: 0.25rem;
        background-color: #e9ecef;
    }
    .confidence-fill {
        height: 100%;
        border-radius: 0.25rem;
        background-color: #007bff;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'clarity_results' not in st.session_state:
    st.session_state.clarity_results = None
if 'proof_results' not in st.session_state:
    st.session_state.proof_results = None

# Agent definitions
AGENTS = {
    "Factra": {
        "emoji": "🧾",
        "role": "Claim Analyzer",
        "description": "The final evaluator that synthesizes all agent outputs to decide truth."
    },
    "LogiX": {
        "emoji": "📡",
        "role": "Proof Agent",
        "description": "A data-focused agent searching for real-time evidence from APIs."
    },
    "Veritas": {
        "emoji": "🧠",
        "role": "Context Analyst",
        "description": "A logical scholar checking context and argumentative consistency."
    },
    "Spectra": {
        "emoji": "👁️",
        "role": "Media Scanner",
        "description": "A sleek visual forensics expert that scans media for deepfakes."
    }
}

def init_gemini():
    """Initialize Gemini API"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("GEMINI_API_KEY not found in environment variables")
        return None
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('models/gemini-1.5-flash-latest')

async def analyze_claims(clarity_results, search_api_key):
    """Analyze claims asynchronously"""
    proof_results = []
    for claim in clarity_results:
        try:
            # Convert claim dictionary to string format
            claim_text = f"{claim.get('subject', '')} {claim.get('predicate', '')} {claim.get('object', '')}".strip()
            if not claim_text:
                continue
                
            proof = await run_proof_agent(claim_text, search_api_key)
            if proof and 'results' in proof:  # Check if we got valid results
                # Get the first result since we're processing one claim at a time
                result = proof['results'][0] if proof['results'] else {
                    "status": "Not Verified",
                    "confidence": 0.0,
                    "evidence": []
                }
                proof_results.append(result)
            else:
                proof_results.append({
                    "status": "Error",
                    "confidence": 0.0,
                    "evidence": [],
                    "error": "No results returned"
                })
        except Exception as e:
            st.error(f"Error analyzing claim: {str(e)}")
            proof_results.append({
                "status": "Error",
                "confidence": 0.0,
                "evidence": [],
                "error": str(e)
            })
    return proof_results

def format_claim(claim):
    """Format a single claim for display"""
    if isinstance(claim, str):
        try:
            claim = json.loads(claim)
        except json.JSONDecodeError:
            return f"Invalid claim format: {claim}"
    
    if not isinstance(claim, dict):
        return f"Invalid claim format: {claim}"
    
    return f"""
    **Subject:** {claim.get('subject', 'N/A')}  
    **Action:** {claim.get('predicate', 'N/A')}  
    **Object:** {claim.get('object', 'N/A')}  
    **Quantifier:** {claim.get('quantifier', 'N/A')}  
    **Time:** {claim.get('time_reference', 'N/A')}  
    **Location:** {claim.get('location', 'N/A')}  
    **Source:** {claim.get('source', 'N/A')}  
    **Confidence:** {claim.get('confidence', 0.0):.2f}
    """

def format_proof(proof):
    """Format proof results for display"""
    if isinstance(proof, str):
        try:
            proof = json.loads(proof)
        except json.JSONDecodeError:
            return f"Invalid proof format: {proof}"
    
    if not isinstance(proof, dict):
        return f"Invalid proof format: {proof}"
    
    # Format evidence snippets
    evidence_text = []
    for evidence in proof.get('evidence', []):
        evidence_text.append(f"- {evidence.get('title', 'No title')}: {evidence.get('snippet', 'No snippet')}")
    
    return f"""
    **Status:** {proof.get('status', 'N/A')}  
    **Confidence:** {proof.get('confidence', 0.0):.2f}  
    **Evidence:**  
    {chr(10).join(evidence_text) if evidence_text else 'None'}
    """

def display_verdict_badge(status):
    """Display a color-coded verdict badge"""
    if status == "Verified":
        return f'<div class="verdict-badge verdict-verified">✅ {status}</div>'
    elif status == "Not Verified":
        return f'<div class="verdict-badge verdict-unverified">❌ {status}</div>'
    else:
        return f'<div class="verdict-badge verdict-unknown">❔ {status}</div>'

def display_confidence_bar(confidence):
    """Display a confidence score as a progress bar"""
    return f"""
    <div class="confidence-bar">
        <div class="confidence-fill" style="width: {confidence * 100}%"></div>
    </div>
    <div style="text-align: right; font-size: 0.8rem;">{confidence:.2f}</div>
    """

def main():
    # Sidebar
    with st.sidebar:
        st.title("🤖 RealityPatch Agents")
        for name, info in AGENTS.items():
            with st.container():
                st.markdown(f"### {info['emoji']} {name}")
                st.markdown(f"**{info['role']}**")
                st.markdown(info['description'])
                st.markdown("---")
        
        # Theme toggle
        st.markdown("### 🎨 Theme")
        st.toggle("Dark Mode", value=False)
    
    # Main content
    st.title("🔍 RealityPatch Fact Checker")
    
    # Initialize Gemini
    model = init_gemini()
    if not model:
        return
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📑 Detailed Report", "🧬 Meet the Agents"])
    
    with tab1:
        # Example claims
        st.markdown("### Example Claims")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🌍 Earth is Flat"):
                st.session_state.text_input = "Is the earth flat?"
        with col2:
            if st.button("🌙 Moon Landing"):
                st.session_state.text_input = "The moon landing was faked"
        with col3:
            if st.button("🇮🇳 India Ceasefire"):
                st.session_state.text_input = "India broke the ceasefire"
        
        # Text input
        text_input = st.text_area(
            "Enter your claim to analyze:",
            value=getattr(st.session_state, 'text_input', ''),
            height=150,
            help="Enter a claim or statement to fact-check"
        )
        
        # Analysis button
        if st.button("🔍 Analyze Claim", type="primary"):
            if not text_input:
                st.warning("Please enter a claim to analyze")
                return
            
            with st.spinner("🤖 Agents are analyzing your claim..."):
                try:
                    # Run clarity analysis
                    clarity_results = run_clarity_agent(text_input, model)
                    if not clarity_results:
                        st.warning("No claims could be extracted. Please try rephrasing your input.")
                        return
                    st.session_state.clarity_results = clarity_results
                    
                    # Run proof analysis
                    search_api_key = os.getenv("SEARCH_API_KEY", "placeholder_key")
                    proof_results = asyncio.run(analyze_claims(clarity_results, search_api_key))
                    
                    if not proof_results:
                        st.warning("Could not verify any claims. Please check your search API configuration.")
                        return
                    
                    st.session_state.proof_results = proof_results
                    
                except Exception as e:
                    st.error(f"Error during analysis: {str(e)}")
                    return
        
        # Display results if available
        if st.session_state.clarity_results is not None:
            st.markdown("### 📊 Analysis Results")
            
            # Overall verdict
            if st.session_state.proof_results:
                latest_result = st.session_state.proof_results[-1]
                st.markdown("### Overall Verdict")
                st.markdown(display_verdict_badge(latest_result.get('status', 'Unknown')), unsafe_allow_html=True)
                
                # Confidence scores
                st.markdown("### Confidence Scores")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### Factra 🧾")
                    st.markdown(display_confidence_bar(latest_result.get('confidence', 0.0)), unsafe_allow_html=True)
                
                with col2:
                    st.markdown("#### LogiX 📡")
                    st.markdown(display_confidence_bar(latest_result.get('confidence', 0.0)), unsafe_allow_html=True)
                
                with col3:
                    st.markdown("#### Veritas 🧠")
                    st.markdown(display_confidence_bar(0.8), unsafe_allow_html=True)  # Placeholder
    
    with tab2:
        if st.session_state.clarity_results is not None:
            for i, (claim, proof) in enumerate(zip(st.session_state.clarity_results, st.session_state.proof_results)):
                with st.expander(f"Claim {i+1}"):
                    # Factra's Analysis
                    st.markdown(f"### 🧾 Factra's Claim Analysis")
                    st.markdown(format_claim(claim))
                    
                    # LogiX's Verification
                    st.markdown(f"### 📡 LogiX's Verification")
                    st.markdown(format_proof(proof))
                    
                    # Veritas's Context Analysis
                    st.markdown(f"### 🧠 Veritas's Context Analysis")
                    st.markdown("Context analysis coming soon...")
    
    with tab3:
        st.markdown("### 🤖 Meet the RealityPatch Agents")
        
        for name, info in AGENTS.items():
            with st.container():
                st.markdown(f"### {info['emoji']} {name}")
                st.markdown(f"**Role:** {info['role']}")
                st.markdown(info['description'])
                st.markdown("---")

if __name__ == "__main__":
    main() 