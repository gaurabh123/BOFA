import streamlit as st

def load_styles():
    st.markdown("""
    <style>
        /* Main sidebar styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 20px !important;
        }
        
        /* Navigation buttons */
        .stButton>button {
            width: 100%;
            justify-content: left;
            padding: 12px 24px;
            margin: 8px 0;
            border-radius: 8px;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            border: none;
            text-align: left;
        }
        
        .stButton>button:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateX(5px);
        }
        
        /* Active page styling */
        [data-testid="stButton"][type="primary"]>button {
            background: rgba(255, 255, 255, 0.2);
            font-weight: 600;
        }
        
        /* Chat messages */
        .stChatMessage {
            max-width: 75%;
            margin: 12px 0;
            border-radius: 15px;
            padding: 1.2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* User message styling */
        [data-testid="stChatMessage"][aria-label="user"] {
            background: white;
            border: 1px solid #dee2e6;
            margin-left: auto;
        }
        
        /* Bot message styling */
        [data-testid="stChatMessage"][aria-label="assistant"] {
            background: #007bff;
            color: white;
            margin-right: auto;
        }
    </style>
    """, unsafe_allow_html=True)