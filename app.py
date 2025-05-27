import streamlit as st
import json
import os
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai
import logging
import plotly.graph_objects as go
from agents import run_clarity_agent, run_proof_agent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="RealityPatch Terminal",
    page_icon="🕵️‍♂️",
    layout="wide"
)

# Custom CSS for terminal theme
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #2ec4b6;
        --bg-color: #f8f9fa;
        --secondary-bg: #ffffff;
        --text-color: #212529;
        --text-secondary: #6c757d;
    }
    
    /* Global styles */
    .stApp {
        background-color: var(--bg-color);
        color: var(--text-color);
        font-family: 'Inter', 'IBM Plex Sans', 'Segoe UI', sans-serif;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-color) !important;
        font-weight: 600 !important;
        margin-bottom: 1.5rem !important;
        letter-spacing: -0.02em;
        font-family: 'Inter', 'IBM Plex Sans', 'Segoe UI', sans-serif;
    }
    
    /* Cards and containers */
    .stCard {
        background-color: var(--secondary-bg);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #dee2e6;
        box-shadow: none;
        transition: box-shadow 0.3s ease;
        font-family: 'Inter', 'IBM Plex Sans', 'Segoe UI', sans-serif;
        margin-bottom: 1.5rem;
    }
    
    .stCard:hover {
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    
    /* Buttons */
    .stButton>button {
        background-color: white;
        border: 1px solid #ced4da;
        color: #212529;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        transition: background-color 0.2s ease;
        font-family: 'Inter', 'IBM Plex Sans', 'Segoe UI', sans-serif;
        font-weight: 500;
    }
    
    .stButton>button:hover {
        background-color: #e9ecef;
    }
    
    /* Input fields */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea {
        background-color: var(--secondary-bg);
        color: var(--text-color);
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 0.75rem;
        font-family: 'Inter', 'IBM Plex Sans', 'Segoe UI', sans-serif;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        border-bottom: 1px solid #dee2e6;
        margin-bottom: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: var(--secondary-bg);
        border-radius: 8px 8px 0 0;
        gap: 1rem;
        padding: 10px 20px;
        color: var(--text-color);
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-color);
        color: var(--secondary-bg);
    }
    
    /* Loading animation */
    .stSpinner>div {
        border-color: var(--primary-color);
    }
    
    /* Evidence cards */
    .evidence-card {
        background-color: var(--secondary-bg);
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
        transition: box-shadow 0.3s ease;
    }
    
    .evidence-card:hover {
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    
    /* Status badges */
    .status-badge {
        padding: 0.4em 0.9em;
        border-radius: 1em;
        font-size: 0.9em;
        font-weight: 500;
        color: #fff;
    }
    
    .status-verified { background-color: #198754; }
    .status-partial { background-color: #ffc107; color: #212529; }
    .status-unclear { background-color: #6c757d; }
    
    /* Links */
    a {
        color: var(--primary-color);
        text-decoration: none;
    }
    
    a:hover {
        text-decoration: underline;
    }
    
    /* Title */
    .title {
        font-size: 2.2em;
        font-weight: 600;
        color: var(--text-color);
        margin-bottom: 0.5em;
        letter-spacing: -0.02em;
    }
    
    /* Section titles */
    .section-title {
        font-size: 1.4em;
        font-weight: 600;
        margin-top: 2.5em;
        margin-bottom: 1.5em;
        color: var(--text-color);
        border-bottom: 1px solid #dee2e6;
        padding-bottom: 0.5em;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'history' not in st.session_state:
    st.session_state.history = []

def init_gemini():
    """Initialize Gemini API"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("Please set GEMINI_API_KEY in your .env file")
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('models/gemini-1.5-flash-latest')

async def analyze_claim(claim: str):
    """Analyze a claim using both agents"""
    try:
        # Run clarity agent
        clarity_result = await run_clarity_agent(claim)
        
        # Run proof agent
        proof_result = await run_proof_agent(claim, os.getenv("SERPER_API_KEY"))
        
        return {
            "clarity": clarity_result,
            "proof": proof_result
        }
    except Exception as e:
        logger.error(f"Error analyzing claim: {str(e)}")
        return None

def create_confidence_gauge(confidence: float):
    """Create a confidence gauge using Plotly"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=confidence * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#2ec4b6"},
            'steps': [
                {'range': [0, 33], 'color': "#f0f0f0"},
                {'range': [33, 66], 'color': "#dee2e6"},
                {'range': [66, 100], 'color': "#b2f0e3"}
            ],
            'threshold': {
                'line': {'color': "#2ec4b6", 'width': 2},
                'thickness': 0.75,
                'value': confidence * 100
            }
        },
        title={'text': "Confidence Level", 'font': {'color': "#212529"}}
    ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': "#212529"},
        height=200,
        margin=dict(t=30, b=0, l=0, r=0)
    )
    
    return fig

def display_claim_components(components):
    """Display claim components in a structured way"""
    st.markdown("<div class='section-title'>Claim Components</div>", unsafe_allow_html=True)
    
    for component in components:
        with st.container():
            st.markdown(f"""
            <div class="evidence-card">
                <h4>{component['type']}</h4>
                <p>{component['text']}</p>
            </div>
            """, unsafe_allow_html=True)

def main():
    """Main application function"""
    st.markdown("<div class='title'>RealityPatch Terminal</div>", unsafe_allow_html=True)
    st.caption("AI-powered claim verification and analysis")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Home", "Clarity Agent", "Proof Agent", "Results & Summary"])
    
    with tab1:
        st.markdown("## Welcome to RealityPatch Terminal")
        st.markdown("""
        RealityPatch is an AI-powered fact-checking tool that helps you verify claims and statements. 
        Our system uses multiple AI agents to analyze claims for clarity and provide evidence-based verification.
        """)
        
        st.markdown("### How it works:")
        st.markdown("""
        1. Enter your claim in the Clarity Agent tab
        2. Our AI will analyze the claim for clarity and structure
        3. The Proof Agent will search for evidence and verify the claim
        4. View detailed results and evidence in the Results tab
        """)
        
        st.markdown("### Features:")
        st.markdown("""
        - 🔍 Claim analysis and verification
        - 📊 Confidence scoring
        - 🔗 Evidence linking
        - 📝 Detailed explanations
        """)
        
        # Add example claims
        st.markdown("### Example Claims")
        example_claims = [
            "The Earth's core is primarily composed of iron and nickel.",
            "The Great Wall of China is visible from space.",
            "Humans use only 10% of their brain capacity."
        ]
        
        for claim in example_claims:
            if st.button(claim, key=f"example_{claim[:10]}"):
                st.session_state.analysis_results = None
                st.session_state.history = []
                st.switch_page("Clarity Agent")
    
    with tab2:
        st.markdown("<div class='section-title'>Clarity Agent</div>", unsafe_allow_html=True)
        st.markdown("Enter a claim to analyze its clarity and structure.")
        
        claim = st.text_area(
            "Enter your claim:",
            height=100,
            key="clarity_claim_input",
            placeholder="e.g., The moon landing was faked in 1969.",
            help="Enter a clear, specific claim that you want to verify."
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            analyze_btn = st.button("Analyze Clarity", key="clarity_analyze_btn", use_container_width=True)
        
        if analyze_btn:
            if not claim:
                st.warning("Please enter a claim to analyze.")
            else:
                with st.spinner("Analyzing claim clarity..."):
                    try:
                        result = asyncio.run(run_clarity_agent(claim))
                        if result:
                            st.session_state.analysis_results = {"clarity": result}
                            st.success("Analysis complete!")
                            
                            # Display components
                            if "components" in result:
                                display_claim_components(result["components"])
                            
                            # Display clarity score
                            if "clarity_score" in result:
                                st.markdown(f"### Clarity Score: {result['clarity_score']:.2f}")
                                st.progress(result['clarity_score'])
                                
                                # Add suggestions if clarity score is low
                                if result['clarity_score'] < 0.6 and "suggestions" in result:
                                    st.markdown("### Suggestions for Improvement")
                                    for suggestion in result['suggestions']:
                                        st.markdown(f"- {suggestion}")
                        else:
                            st.error("Failed to analyze claim. Please try again.")
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
                        logger.error(f"Error in clarity analysis: {str(e)}")
    
    with tab3:
        st.markdown("<div class='section-title'>Proof Agent</div>", unsafe_allow_html=True)
        st.markdown("Verify your claim with evidence and analysis.")
        
        if st.session_state.analysis_results and "clarity" in st.session_state.analysis_results:
            claim = st.session_state.analysis_results["clarity"].get("original_claim", "")
            st.info("Using claim from Clarity Agent analysis.")
        else:
            claim = st.text_area(
                "Enter your claim:",
                height=100,
                key="proof_claim_input",
                placeholder="e.g., The moon landing was faked in 1969.",
                help="Enter a claim to verify with evidence."
            )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            verify_btn = st.button("Verify Claim", key="proof_verify_btn", use_container_width=True)
        
        if verify_btn:
            if not claim:
                st.warning("Please enter a claim to verify.")
            else:
                with st.spinner("Verifying claim..."):
                    try:
                        result = asyncio.run(run_proof_agent(claim, os.getenv("SERPER_API_KEY")))
                        if result:
                            if st.session_state.analysis_results:
                                st.session_state.analysis_results["proof"] = result
                            else:
                                st.session_state.analysis_results = {"proof": result}
                            st.success("Verification complete!")
                            
                            # Display confidence gauge
                            st.plotly_chart(create_confidence_gauge(result["confidence"]))
                            
                            # Display verdict
                            st.markdown(f"""
                            <div class="stCard">
                                <h3>Verdict: {result['verdict']}</h3>
                                <p>{result['explanation']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Display evidence
                            if result["evidence"]:
                                st.markdown("<div class='section-title'>Evidence</div>", unsafe_allow_html=True)
                                for evidence in result["evidence"]:
                                    st.markdown(f"""
                                    <div class="evidence-card">
                                        <h4>{evidence['title']}</h4>
                                        <p>{evidence['snippet']}</p>
                                        <small>Source: {evidence['source']}</small>
                                    </div>
                                    """, unsafe_allow_html=True)
                        else:
                            st.error("Failed to verify claim. Please try again.")
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
                        logger.error(f"Error in proof verification: {str(e)}")
    
    with tab4:
        st.markdown("<div class='section-title'>Results & Summary</div>", unsafe_allow_html=True)
        
        if st.session_state.analysis_results:
            clarity_result = st.session_state.analysis_results.get("clarity")
            proof_result = st.session_state.analysis_results.get("proof")
            
            if clarity_result and proof_result:
                # Display summary
                st.markdown("""
                <div class="stCard">
                    <h2>Analysis Summary</h2>
                </div>
                """, unsafe_allow_html=True)
                
                # Clarity results
                st.markdown("<div class='section-title'>Clarity Analysis</div>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class="evidence-card">
                    <h4>Original Claim</h4>
                    <p>{clarity_result['original_claim']}</p>
                    <h4>Clarity Score</h4>
                    <p>{clarity_result['clarity_score']:.2f}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Proof results
                st.markdown("<div class='section-title'>Verification Results</div>", unsafe_allow_html=True)
                st.plotly_chart(create_confidence_gauge(proof_result["confidence"]))
                
                st.markdown(f"""
                <div class="evidence-card">
                    <h4>Verdict</h4>
                    <p>{proof_result['verdict']}</p>
                    <h4>Explanation</h4>
                    <p>{proof_result['explanation']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Add to history
                st.session_state.history.append({
                    "claim": clarity_result['original_claim'],
                    "clarity_score": clarity_result['clarity_score'],
                    "verdict": proof_result['verdict'],
                    "confidence": proof_result['confidence'],
                    "timestamp": proof_result['timestamp']
                })
                
                # Display history
                if st.session_state.history:
                    st.markdown("<div class='section-title'>Analysis History</div>", unsafe_allow_html=True)
                    for item in reversed(st.session_state.history):
                        st.markdown(f"""
                        <div class="evidence-card">
                            <h4>{item['claim']}</h4>
                            <p>Verdict: {item['verdict']}</p>
                            <p>Confidence: {item['confidence']:.2%}</p>
                            <small>Analyzed: {item['timestamp']}</small>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("Please analyze a claim first using the Clarity and Proof agents.")
        else:
            st.info("No analysis results available. Please use the Clarity and Proof agents to analyze a claim.")

if __name__ == "__main__":
    main() 
