import streamlit as st
import requests
from typing import Dict, Any
import time

# Set page configuration
st.set_page_config(
    page_title="Research Paper Insights",
    page_icon="📚",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
        .stButton button {
            width: 100%;
            border-radius: 5px;
            height: 3em;
        }
        .paper-card {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #dee2e6;
            margin: 10px 0;
        }
        .insights-container {
            background-color: #ffffff;
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #e9ecef;
            margin-top: 10px;
        }
        .meta-info {
            color: #6c757d;
            font-size: 0.9em;
        }
        .section-title {
            color: #2c3e50;
            font-weight: bold;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

def display_paper(paper: Dict[Any, Any]):
    """Display a single paper with enhanced formatting"""
    with st.container():
        # Paper card container
        # st.markdown('<div class="paper-card">', unsafe_allow_html=True)
        
        # Summary and Insights
        if 'summary' in paper and paper['summary']:
            with st.expander("📝 Summary", expanded=True):
                st.write(paper['summary'])
                st.markdown('</div>', unsafe_allow_html=True)
        
        if 'insights' in paper and paper['insights']:
            with st.expander("💡 Key Insights", expanded=True):
                st.write(paper['insights'])
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Abstract hidden by default
        # if paper['abstract']:
        #     with st.expander("📄 View Abstract", expanded=False):
        #         st.write(paper['abstract'])
        #         st.markdown('</div>', unsafe_allow_html=True)
        
        # st.markdown('</div>', unsafe_allow_html=True)

def main():
    # Header
    st.title("📚 Research Paper Insights")
    st.markdown("""
    <p style='font-size: 1.2em; color: #666;'>
        Discover and analyze research papers with AI-generated summaries and key insights
    </p>
    """, unsafe_allow_html=True)
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Search Settings")
        user_query = st.text_area("Enter your research query:", 
                                 height=100,
                                 placeholder="e.g., recent advances in machine learning")
        num_papers = st.slider("Number of papers to retrieve", 
                             min_value=5, 
                             max_value=50, 
                             value=10,
                             help="Adjust the number of papers to fetch")
        
        search_button = st.button("🔍 Search Papers")
        
        # Add tips in sidebar
        st.markdown("---")
        st.markdown("### 💡 Search Tips")
        st.markdown("""
        - Use specific keywords
        - Include relevant authors
        - Specify year ranges
        - Add domain-specific terms
        """)
    
    # Main content area
    if search_button:
        if user_query:
            with st.spinner("🔍 Searching for papers..."):
                try:
                    response = requests.post(
                        "http://127.0.0.1:8000/fetch_papers/",
                        json={"text": user_query, "limit": num_papers}
                    )
                    
                    if response.status_code == 200:
                        papers = response.json()["papers"]
                        
                        if not papers:
                            st.warning("🔍 No papers found for your query.")
                        else:
                            st.success(f"Found relevant papers")
                            
                            # Display papers
                            for paper in papers:
                                display_paper(paper)
                                time.sleep(0.1)  # Smooth loading animation
                    else:
                        st.error(f"❌ Error: {response.text}")
                
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")
        else:
            st.warning("⚠️ Please enter a search query.")

if __name__ == "__main__":
    main()

