"""
AI Math Tutor
"""

import streamlit as st
from PIL import Image

# ---------------------------------------------------
# Placeholder Imports (Replace with your actual modules)
# ---------------------------------------------------
try:
    from utils.image_utils import preprocess_for_ocr
    from vision.ocr import OCREngine, llm_convert_to_latex
    from solver.equation_solver import parse_latex_to_sympy, solve_equation, generate_steps
    from checker.mistake_checker import detect_mistakes
except ImportError:
    pass # Bypassing for UI demonstration purposes

# ---------------------------------------------------
# Page Configuration & State
# ---------------------------------------------------
st.set_page_config(page_title="AI Math Tutor", page_icon="📐", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []
if "current_solution" not in st.session_state:
    st.session_state.current_solution = None
if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = ""

# ---------------------------------------------------
# CSS Injection (Stacked Uploader & UI Polish)
# ---------------------------------------------------
st.markdown("""
<style>
    /* Base Theme */
    .stApp { background: #0d1117; color: #e6edf3; }

    /* COMPLETELY HIDE WIDGET LABELS FOR CLEANER LOOK */
    [data-testid="stFileUploader"] > label, 
    [data-testid="stCameraInput"] > label {
        display: none !important;
    }

    /* STACK FILE UPLOADER TEXT AND BUTTON VERTICALLY */
    [data-testid="stFileUploader"] section {
        height: 345px !important; 
        background-color: #161b22 !important;
        border: 2px dashed #30363d !important;
        border-radius: 12px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    /* TARGET THE DRAG-AND-DROP INNER CONTAINER */
    [data-testid="stFileUploader"] section > div {
        display: flex !important;
        flex-direction: column !important; /* Stacks text and button vertically */
        align-items: center !important;    /* Centers horizontally */
        justify-content: center !important; /* Centers vertically */
        text-align: center !important;
        gap: 15px !important;              /* Space between text and button */
        width: 100% !important;
        height: 100% !important;
    }

    /* OPTIONAL: Center the 'Browse files' button itself within its sub-div */
    [data-testid="stFileUploader"] section > div > div {
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
    }

    /* Center any wrapper divs inside the uploader */
    [data-testid="stFileUploader"] section > div > div {
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
    }

    /* Style the Camera Input container */
    [data-testid="stCameraInput"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 10px;
    }

    /* Results & Steps Styling */
    .solution-box {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 20px;
        margin-top: 10px;
    }
    .step-box {
        background: #0d1117;
        border-left: 4px solid #58a6ff;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 6px;
    }
    
    /* Sidebar History Item */
    .history-item {
        background: #21262d;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 8px;
        border: 1px solid #30363d;
        font-family: monospace;
        color: #58a6ff;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# Sidebar - History & Controls
# ---------------------------------------------------
with st.sidebar:
    st.title("📐 AI Math Tutor")
    st.caption("Vision + Symbolic Math Engine")
    
    st.markdown("---")
    
    st.subheader("📜 History")
    if st.session_state.history:
        for item in reversed(st.session_state.history[-10:]):
            st.markdown(f'<div class="history-item">{item}</div>', unsafe_allow_html=True)
        if st.button("Clear History", use_container_width=True):
            st.session_state.history = []
            st.session_state.current_solution = None
            st.rerun()
    else:
        st.caption("No problems solved yet.")
        
    st.markdown("---")
    st.subheader("⚙️ Controls")
    use_llm = st.toggle("Use LLM for LaTeX conversion", value=True)

# ---------------------------------------------------
# Main Header
# ---------------------------------------------------
st.title("Solve Math Problems Instantly")
st.markdown("Upload an image, use your camera, or type your problem manually below.")
st.write("") 

# ---------------------------------------------------
# Input Section: Vision (Row 1)
# ---------------------------------------------------
col1, col2 = st.columns(2, gap="large")
image = None

with col1:
    st.subheader("📁 Upload Problem")
    uploaded = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])
    if uploaded:
        image = Image.open(uploaded)

with col2:
    st.subheader("📸 Capture From Camera")
    camera = st.camera_input("Take Photo")
    if camera:
        image = Image.open(camera)

# --- Image Processing Step ---
if image:
    st.markdown("---")
    preview_col, action_col = st.columns([1, 1])
    
    with preview_col:
        st.image(image, use_container_width=True, caption="Image Preview")
        
    with action_col:
        st.write("### 🔍 Extract Equation")
        st.write("Scan the image to convert it into editable text.")
        if st.button("Extract Text", use_container_width=True):
            with st.spinner("Scanning image..."):
                try:
                    # --- BACKEND OCR LOGIC ---
                    processed = preprocess_for_ocr(image)
                    ocr_engine = OCREngine()
                    raw_text = ocr_engine.extract_math(processed)
                    extracted_latex = llm_convert_to_latex(raw_text) if use_llm else raw_text
                    
                    # Save to session state so it populates the text box below
                    st.session_state.extracted_text = extracted_latex
                    st.rerun()
                except Exception as e:
                    st.error("Text extraction failed.")
                    # st.exception(e) # Uncomment to debug

# ---------------------------------------------------
# Input Section: Manual/Editable Text (Row 2)
# ---------------------------------------------------
st.markdown("---")
st.subheader("⌨️ Type or Edit Equation")
st.caption("Review the scanned text from your image, or manually type a new math problem here.")

# The text area takes its default value from the session state (updated by OCR)
user_equation = st.text_area(
    "Equation Input", 
    value=st.session_state.extracted_text, 
    height=100,
    placeholder="e.g. 2x^2 + 5x - 3 = 0 or \\frac{1}{2}x + 4 = 10",
    label_visibility="collapsed"
)

# ---------------------------------------------------
# Solving Logic
# ---------------------------------------------------
if st.button("🚀 Solve Problem", type="primary"):
    if not user_equation.strip():
        st.warning("Please enter an equation or extract one from an image first.")
    else:
        with st.spinner("AI is solving the equation..."):
            try:
                # --- BACKEND SOLVING LOGIC ---
                expr = parse_latex_to_sympy(user_equation)
                solution = solve_equation(expr)
                steps = generate_steps(expr)
                mistakes = detect_mistakes(user_equation, expr)

                # Update History
                if user_equation not in st.session_state.history:
                    st.session_state.history.append(user_equation)

                # Save to session state
                st.session_state.current_solution = {
                    "latex": user_equation,
                    "answer": solution,
                    "steps": steps,
                    "mistakes": mistakes
                }
                st.rerun()

            except Exception as e:
                st.error("Solving failed. Please ensure the equation is formatted correctly.")
                # st.exception(e) # Uncomment to debug

# ---------------------------------------------------
# Results Display
# ---------------------------------------------------
if st.session_state.current_solution:
    res = st.session_state.current_solution
    
    st.markdown("---")
    st.markdown("## ✨ Solution")
    
    st.markdown('<div class="solution-box">', unsafe_allow_html=True)
    st.write("### Equation")
    try:
        st.latex(res["latex"])
    except:
        st.code(res["latex"])

    st.write("### Final Answer")
    st.success(f"**{res['answer']}**")
    st.markdown('</div>', unsafe_allow_html=True)

    if res["steps"]:
        st.markdown("### 📝 Step-by-Step Explanation")
        for i, step in enumerate(res["steps"], 1):
            st.markdown(f'<div class="step-box"><b>Step {i}:</b> {step}</div>', unsafe_allow_html=True)

    if res["mistakes"]:
        st.markdown("### ⚠️ Possible Mistakes Detected")
        for m in res["mistakes"]:
            st.warning(m)