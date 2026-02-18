"""
LegoWorld V3 - My Lego Sets Mobile App
Streamlit web app for capturing and managing Lego set photos
"""

import streamlit as st
import requests
import time
import io
import os

# Configuration
st.set_page_config(
    page_title="My Lego Sets",
    page_icon="🧱",
    layout="wide"
)

# Backend URL - reads from environment variable for Streamlit Cloud deployment
# Set BACKEND_URL in Streamlit Cloud secrets or use localhost for local development
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5001")

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
    
    # File uploader - now supports multiple files
    uploaded_files = st.file_uploader(
        "Choose photo(s)", 
        type=['jpg', 'png', 'jpeg'],
        accept_multiple_files=True,
        help="Upload one or more photos of your Lego sets"
    )
    
    # Optional caption for all photos
    caption = st.text_input("Add a caption for all photos (optional)", placeholder="e.g., My City Collection, Christmas 2025...")
    
    # Submit button
    if st.button("📤 Add to Collection", type="primary", use_container_width=True):
        if uploaded_files:
            total_files = len(uploaded_files)
            with st.spinner(f"Uploading {total_files} photo(s)..."):
                success_count = 0
                error_count = 0
                
                # Create a progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, uploaded_file in enumerate(uploaded_files):
                    try:
                        # Update progress
                        progress = (idx + 1) / total_files
                        progress_bar.progress(progress)
                        status_text.text(f"Uploading {uploaded_file.name}... ({idx + 1}/{total_files})")
                        
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
                            success_count += 1
                        else:
                            error_count += 1
                            st.error(f"Failed to upload {uploaded_file.name}: {response.text}")
                    except Exception as e:
                        error_count += 1
                        st.error(f"Error uploading {uploaded_file.name}: {str(e)}")
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Show final result
                if success_count > 0:
                    if success_count == total_files:
                        st.success(f"✅ All {success_count} photo(s) added successfully!")
                    else:
                        st.success(f"✅ {success_count} photo(s) added successfully!")
                        st.warning(f"⚠️ {error_count} photo(s) failed to upload")
                    
                    # Show AI identification note
                    st.info("🤖 AI is analyzing your photos to identify LEGO sets...")
                    
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to upload any photos. Make sure the backend server is running.")
        else:
            st.warning("Please select one or more photos to upload!")

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
                    
                # Display each photo in a card-like format
                for photo in photos:
                    with st.container(border=True): # Added border=True to the container
                        col_img, col_info = st.columns([1, 2])
                        
                        with col_img:
                            # Display photo
                            img_url = f"{BACKEND_URL}/api/photos/{photo['filename']}"
                            st.image(img_url, use_container_width=True)
                        
                        with col_info:
                            # Show AI-identified name if available
                            ai_name = photo.get('ai_identified_name')
                            if ai_name and ai_name != 'Unknown LEGO Set':
                                st.markdown(f"**🤖 {ai_name}**")
                            
                            # Show user caption if available
                            caption = photo.get('caption')
                            if caption:
                                st.caption(caption)
                            elif not ai_name or ai_name == 'Unknown LEGO Set':
                                st.caption("No caption")
                            
                            # Show timestamp
                            time_ago = time.time() - photo['created_at']
                            if time_ago < 3600:
                                time_str = f"{int(time_ago / 60)}m ago"
                            elif time_ago < 86400:
                                time_str = f"{int(time_ago / 3600)}h ago"
                            else:
                                time_str = f"{int(time_ago / 86400)}d ago"
                            
                            st.caption(f"🕒 {time_str}")
                            
                            # Show NEW badge if recent
                            if time_ago < 3600:  # Less than 1 hour
                                st.markdown(":red[**NEW**]")
                        
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
