"""
LegoWorld V3 - My Lego Sets Mobile App
Streamlit web app for capturing and managing Lego set photos
"""

import streamlit as st
import requests
import time
import io
import os
from PIL import Image

# Configuration
st.set_page_config(
    page_title="My Lego Sets",
    page_icon="🧱",
    layout="wide"
)

# Backend URL - reads from environment variable for Streamlit Cloud deployment
# Set BACKEND_URL in Streamlit Cloud secrets or use localhost for local development
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")

# Custom CSS - Premium Lego Design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;900&display=swap');
    
    :root {
        --lego-red: #E3000B;
        --lego-yellow: #FFCF00;
        --lego-blue: #0055BF;
        --lego-white: #FFFFFF;
        --lego-black: #2C2C2C;
        --lego-gray: #F5F5F5;
    }
    
    .stApp {
        background: linear-gradient(135deg, #FFCF00 0%, #FFE066 100%);
        font-family: 'Poppins', sans-serif;
    }
    
    h1 {
        color: var(--lego-red);
        font-weight: 900;
        text-shadow: 4px 4px 0px var(--lego-black);
        text-transform: uppercase;
        text-align: center;
        padding: 2rem 0;
        font-size: 3.5rem;
        letter-spacing: 2px;
    }
    
    .stButton button {
        background: linear-gradient(135deg, var(--lego-blue) 0%, #004099 100%);
        color: white;
        border-radius: 30px;
        border: 4px solid var(--lego-black);
        font-weight: 700;
        font-size: 1.1rem;
        padding: 1rem 2rem;
        box-shadow: 0 8px 0 var(--lego-black);
        transition: all 0.2s;
        text-transform: uppercase;
    }
    
    .stButton button:hover {
        transform: translateY(4px);
        box-shadow: 0 4px 0 var(--lego-black);
        background: linear-gradient(135deg, #004099 0%, var(--lego-blue) 100%);
    }
    
    .stButton button:active {
        transform: translateY(8px);
        box-shadow: 0 0 0 var(--lego-black);
    }
    
    [data-testid="stFileUploader"] {
        background: white;
        border-radius: 20px;
        border: 4px solid var(--lego-black);
        padding: 2rem;
        box-shadow: 0 8px 0 var(--lego-black);
    }
    
    div[data-testid="stImage"] {
        border-radius: 15px;
        overflow: hidden;
        border: 4px solid var(--lego-black);
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
        transition: transform 0.3s;
    }
    
    div[data-testid="stImage"]:hover {
        transform: scale(1.05);
    }
    
    .photo-card {
        background: white;
        border-radius: 20px;
        border: 4px solid var(--lego-black);
        padding: 1.5rem;
        box-shadow: 0 8px 0 var(--lego-black);
        margin-bottom: 1rem;
    }
    
    .new-badge {
        display: inline-block;
        background: var(--lego-red);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 900;
        font-size: 0.9rem;
        border: 3px solid var(--lego-black);
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1>🧱 My Lego Sets</h1>", unsafe_allow_html=True)

# Main Content
tab1, tab2 = st.tabs(["📸 Add Photo", "🖼️ My Gallery"])

with tab1:
    st.markdown("### Upload Your Lego Photos")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a photo", 
        type=['jpg', 'png', 'jpeg'],
        help="Upload a photo of your Lego set"
    )
    
    # Optional caption
    caption = st.text_input("Add a caption (optional)", placeholder="e.g., Millennium Falcon, City Fire Station...")
    
    # Submit button
    if st.button("📤 Add to Collection", type="primary", use_container_width=True):
        if uploaded_file:
            with st.spinner("Saving to your collection..."):
                try:
                    # Prepare file for upload
                    files = {'file': uploaded_file.getvalue()}
                    data = {'caption': caption} if caption else {}
                    
                    # Upload to backend
                    response = requests.post(
                        f"{BACKEND_URL}/api/photos", 
                        files=files, 
                        data=data,
                        headers={'ngrok-skip-browser-warning': 'true'}
                    )
                    
                    if response.status_code == 200:
                        st.success("✅ Photo added successfully!")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Failed to upload photo: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.info("Make sure the backend server is running on http://localhost:5000")
        else:
            st.warning("Please take a photo or upload a file first!")

with tab2:
    st.markdown("### Your Collection")
    
    try:
        # Fetch photos from backend
        response = requests.get(
            f"{BACKEND_URL}/api/photos",
            headers={'ngrok-skip-browser-warning': 'true'}
        )
        
        if response.status_code == 200:
            photos = response.json()
            
            if not photos:
                st.info("No photos yet. Add your first Lego set!")
            else:
                # Display photos in a grid
                cols = st.columns(2)
                
                for idx, photo in enumerate(photos):
                    col = cols[idx % 2]
                    
                    with col:
                        with st.container(border=True):
                            # Fetch and display image
                            img_response = requests.get(
                                f"{BACKEND_URL}/api/photos/{photo['filename']}",
                                headers={'ngrok-skip-browser-warning': 'true'}
                            )
                            if img_response.status_code == 200:
                                img = Image.open(io.BytesIO(img_response.content))
                                st.image(img, use_container_width=True)
                            
                            # Caption
                            if photo.get('caption'):
                                st.markdown(f"**{photo['caption']}**")
                            
                            # Timestamp and new badge
                            time_diff = time.time() - photo['created_at']
                            col_a, col_b = st.columns([3, 1])
                            
                            with col_a:
                                if time_diff < 3600:  # Less than 1 hour
                                    minutes_ago = int(time_diff / 60)
                                    st.caption(f"Added {minutes_ago} min ago")
                                elif time_diff < 86400:  # Less than 1 day
                                    hours_ago = int(time_diff / 3600)
                                    st.caption(f"Added {hours_ago}h ago")
                                else:
                                    days_ago = int(time_diff / 86400)
                                    st.caption(f"Added {days_ago}d ago")
                            
                            with col_b:
                                if time_diff < 3600:  # Show NEW badge for 1 hour
                                    st.markdown('<span class="new-badge">NEW</span>', unsafe_allow_html=True)
                            
                            # Delete button
                            if st.button("🗑️ Delete", key=f"del_{photo['id']}", use_container_width=True):
                                del_response = requests.delete(
                                    f"{BACKEND_URL}/api/photos/{photo['id']}",
                                    headers={'ngrok-skip-browser-warning': 'true'}
                                )
                                if del_response.status_code == 200:
                                    st.success("Deleted!")
                                    st.rerun()
        else:
            st.error("Failed to fetch photos from server")
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend server")
        st.info("Please start the server with: `python server/app.py`")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #2C2C2C; font-weight: 600;'>"
    "LegoWorld V3 © 2026 | 📺 Check your TV for photo updates!"
    "</div>",
    unsafe_allow_html=True
)
