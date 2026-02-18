"""
LegoWorld V3 - Backend Server (Cloud-Ready)
Flask API for photo management and TV sync
Supports both SQLite (local) and PostgreSQL (cloud)
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import time
from werkzeug.utils import secure_filename
import google.generativeai as genai

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')

# Database configuration - supports both SQLite and PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL')
USE_POSTGRESQL = DATABASE_URL is not None

if USE_POSTGRESQL:
    # PostgreSQL for cloud deployment
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    DB_FILE = None
    print("✅ Using PostgreSQL database")
else:
    # SQLite for local development
    import sqlite3
    
    DB_FILE = os.path.join(BASE_DIR, 'lego.db')
    # Ensure uploads directory exists for local
    if not os.path.exists(UPLOADS_DIR):
        os.makedirs(UPLOADS_DIR)
    print("✅ Using SQLite database")

# Cloudinary configuration for image storage
USE_CLOUDINARY = os.getenv('CLOUDINARY_CLOUD_NAME') is not None

if USE_CLOUDINARY:
    import cloudinary
    import cloudinary.uploader
    
    cloudinary.config(
        cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key = os.getenv("CLOUDINARY_API_KEY"),
        api_secret = os.getenv("CLOUDINARY_API_SECRET")
    )
    print("✅ Cloudinary configured for image storage")
else:
    print("ℹ️  Using local file storage")

# Configure Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Use gemini-2.5-flash - supports vision and generateContent
    model = genai.GenerativeModel('gemini-2.5-flash')
    print("✅ Gemini AI configured (gemini-2.5-flash)")
else:
    model = None
    print("⚠️  GEMINI_API_KEY not set - AI identification disabled")

# Database initialization
def init_db():
    if USE_POSTGRESQL:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS photos
                     (id SERIAL PRIMARY KEY,
                      filename TEXT NOT NULL,
                      caption TEXT,
                      created_at INTEGER NOT NULL,
                      ai_identified_name TEXT,
                      theme TEXT)''')
        conn.commit()
        conn.close()
        print(f"PostgreSQL database initialized")
    else:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS photos
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      filename TEXT NOT NULL,
                      caption TEXT,
                      created_at INTEGER NOT NULL,
                      ai_identified_name TEXT,
                      theme TEXT)''')
        conn.commit()
        conn.close()
        print(f"SQLite database initialized: {DB_FILE}")

# Initialize database on startup
init_db()

# Helper function to get database connection
def get_db():
    if USE_POSTGRESQL:
        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = RealDictCursor
        return conn
    else:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn

# AI Identification Function
def identify_lego_with_ai(file_object):
    """
    Use Gemini Vision to identify LEGO set from image
    
    Args:
        file_object: File object (from request.files) or file path string
    
    Returns:
        str: Identified LEGO set name or None if failed
    """
    if not model:
        return None
    
    try:
        # Prepare prompt
        prompt = """Analyze this image and identify the LEGO set.
        
Please provide ONLY the LEGO set name and number if visible.
If you can identify it, respond in this format: "LEGO [Set Name] ([Set Number])"
If you cannot identify it, respond: "Unknown LEGO Set"

Examples:
- "LEGO Star Wars Millennium Falcon (75192)"
- "LEGO Creator Expert Taj Mahal (10256)"
- "LEGO City Fire Truck (60331)"
- "Unknown LEGO Set"

Keep the response concise and in English."""
        
        # Gemini can accept file objects directly or file paths
        # For file objects, read the bytes
        if isinstance(file_object, str):
            # File path - read file
            with open(file_object, 'rb') as f:
                image_data = f.read()
        else:
            # File object from request.files - read bytes
            file_object.seek(0)  # Reset to beginning
            image_data = file_object.read()
        
        # Upload to Gemini
        image_part = {"mime_type": "image/jpeg", "data": image_data}
        
        # Generate content with prompt and image
        response = model.generate_content([prompt, image_part])
        
        if response and response.text:
            identified_name = response.text.strip()
            print(f"🤖 AI identified: {identified_name}")
            return identified_name
        
    except Exception as e:
        print(f"❌ AI identification failed: {e}")
        import traceback
        traceback.print_exc()
    
    return None

# API Routes

@app.route('/api/photos', methods=['GET'])
def get_photos():
    """Get all photos ordered by newest first"""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM photos ORDER BY created_at DESC")
        rows = c.fetchall()
        photos = [dict(row) for row in rows]
        conn.close()
        return jsonify(photos), 200
    except Exception as e:
        print(f"Error fetching photos: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/photos', methods=['POST'])
def upload_photo():
    """Upload a new photo with AI identification"""
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "Empty filename"}), 400
        
        # Get optional caption
        caption = request.form.get('caption', '')
        timestamp = int(time.time())
        
        # 🤖 AI Identification (before uploading to save bandwidth)
        file.seek(0)  # Reset file pointer
        ai_name = identify_lego_with_ai(file)
        
        # Upload to Cloudinary or save locally
        if USE_CLOUDINARY:
            # Upload to Cloudinary
            file.seek(0)  # Reset file pointer again
            upload_result = cloudinary.uploader.upload(
                file,
                folder="lego_photos",
                public_id=f"lego_{timestamp}"
            )
            filename = upload_result['secure_url']
            print(f"📤 Uploaded to Cloudinary: {filename}")
        else:
            # Save locally
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
            filename = f"lego_{timestamp}.{ext}"
            filepath = os.path.join(UPLOADS_DIR, filename)
            file.seek(0)  # Reset file pointer
            file.save(filepath)
            print(f"💾 Saved locally: {filename}")
        
        # Save to database with AI name
        conn = get_db()
        c = conn.cursor()
        
        if USE_POSTGRESQL:
            c.execute("""INSERT INTO photos 
                         (filename, caption, created_at, ai_identified_name) 
                         VALUES (%s, %s, %s, %s) RETURNING id""",
                      (filename, caption, timestamp, ai_name))
            photo_id = c.fetchone()['id']
        else:
            c.execute("""INSERT INTO photos 
                         (filename, caption, created_at, ai_identified_name) 
                         VALUES (?, ?, ?, ?)""",
                      (filename, caption, timestamp, ai_name))
            photo_id = c.lastrowid
        
        conn.commit()
        conn.close()
        
        # Return the new photo data
        new_photo = {
            "id": photo_id,
            "filename": filename,
            "caption": caption,
            "created_at": timestamp,
            "ai_identified_name": ai_name
        }
        
        print(f"📸 Photo uploaded: {filename}")
        if ai_name:
            print(f"   🤖 Identified as: {ai_name}")
        
        return jsonify(new_photo), 200
        
    except Exception as e:
        print(f"Error uploading photo: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/photos/<int:photo_id>', methods=['DELETE'])
def delete_photo(photo_id):
    """Delete a specific photo"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Get filename before deleting
        if USE_POSTGRESQL:
            c.execute("SELECT filename FROM photos WHERE id = %s", (photo_id,))
        else:
            c.execute("SELECT filename FROM photos WHERE id = ?", (photo_id,))
        
        row = c.fetchone()
        
        if not row:
            conn.close()
            return jsonify({"error": "Photo not found"}), 404
        
        filename = row['filename'] if USE_POSTGRESQL else row['filename']
        
        # Delete from database
        if USE_POSTGRESQL:
            c.execute("DELETE FROM photos WHERE id = %s", (photo_id,))
        else:
            c.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
        
        conn.commit()
        conn.close()
        
        # Delete from Cloudinary or local filesystem
        if USE_CLOUDINARY:
            # Extract public_id from Cloudinary URL
            if 'cloudinary.com' in filename:
                public_id = filename.split('/')[-1].split('.')[0]
                cloudinary.uploader.destroy(f"lego_photos/{public_id}")
                print(f"🗑️  Deleted from Cloudinary: {public_id}")
        else:
            # Delete file from filesystem
            filepath = os.path.join(UPLOADS_DIR, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"🗑️  Photo deleted: {filename}")
        
        return jsonify({"success": True}), 200
        
    except Exception as e:
        print(f"Error deleting photo: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/photos/<path:filename>', methods=['GET'])
def serve_photo(filename):
    """Serve a specific photo file (local storage only)"""
    try:
        # If using Cloudinary, the filename is already a full URL
        if USE_CLOUDINARY or filename.startswith('http'):
            # Redirect to Cloudinary URL
            from flask import redirect
            return redirect(filename)
        
        # Serve from local storage
        filepath = os.path.join(UPLOADS_DIR, filename)
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='image/jpeg')
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        print(f"Error serving photo: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/state', methods=['GET'])
def get_state():
    """Get current state for TV polling (latest photo info)"""
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM photos ORDER BY created_at DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        
        if row:
            latest_photo = dict(row)
            return jsonify({
                "latest_photo": latest_photo,
                "total_count": get_photo_count(),
                "timestamp": time.time()
            }), 200
        else:
            return jsonify({
                "latest_photo": None,
                "total_count": 0,
                "timestamp": time.time()
            }), 200
            
    except Exception as e:
        print(f"Error getting state: {e}")
        return jsonify({"error": str(e)}), 500

def get_photo_count():
    """Helper function to get total photo count"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        if USE_POSTGRESQL:
            c.execute("SELECT COUNT(*) as count FROM photos")
        else:
            c.execute("SELECT COUNT(*) as count FROM photos")
        
        result = c.fetchone()
        conn.close()
        return result['count']
    except:
        return 0

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "ok", "service": "LegoWorld V3 Backend"}), 200

if __name__ == '__main__':
    # Support cloud deployment with dynamic port
    port = int(os.getenv('PORT', 5001))
    
    print("=" * 60)
    print("LegoWorld V3 Backend Server (Cloud-Ready)")
    print("=" * 60)
    if USE_POSTGRESQL:
        print(f"Database: PostgreSQL")
    else:
        print(f"Database: SQLite - {DB_FILE}")
    
    if USE_CLOUDINARY:
        print(f"Storage: Cloudinary")
    else:
        print(f"Storage: Local - {UPLOADS_DIR}")
    
    print(f"Server: http://0.0.0.0:{port}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=True)
