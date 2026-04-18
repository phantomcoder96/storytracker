import os
import sqlite3
import base64
import requests
import instaloader
from dotenv import load_dotenv
import brevo_python
from brevo_python.rest import ApiException
from datetime import datetime

# Load environment variables
load_dotenv()

TARGET_USERNAME = os.getenv("TARGET_USERNAME")
BURNER_USERNAME = os.getenv("BURNER_USERNAME")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
TO_EMAIL = os.getenv("TO_EMAIL")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

DB_FILE = "processed_stories.db"

def init_db():
    """Initializes the SQLite database to track processed stories."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stories (
            story_id TEXT PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn, cursor

def is_processed(cursor, story_id):
    """Checks if a story has already been processed."""
    cursor.execute('SELECT 1 FROM stories WHERE story_id = ?', (story_id,))
    return cursor.fetchone() is not None

def mark_processed(conn, cursor, story_id):
    """Marks a story as processed in the database."""
    cursor.execute('INSERT INTO stories (story_id) VALUES (?)', (story_id,))
    conn.commit()

def download_image_as_base64(url):
    """Downloads an image from a URL and returns it as a base64 encoded string."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return base64.b64encode(response.content).decode('utf-8')
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

def extract_story_data(item):
    """
    Extracts relevant data from an Instaloader StoryItem.
    Attempts to pull text overlays, link stickers, and the thumbnail URL.
    """
    data = {
        "links": [],
        "text": [],
        "image_url": item.url, # URL of the image or video thumbnail
        "is_video": item.is_video
    }
    
    # 1. Standard text caption (often used for accessibility or direct text)
    if item.caption:
        data["text"].append(item.caption)
        
    # 2. Extract from raw JSON node (sticker data)
    node = item._node
    
    # Search for link stickers
    if 'story_link_stickers' in node:
        for sticker in node['story_link_stickers']:
            if 'story_link' in sticker and 'url' in sticker['story_link']:
                data["links"].append(sticker['story_link']['url'])
                
    # Story app attributions or other external URLs (Instaloader exposes this sometimes)
    if hasattr(item, 'external_url') and item.external_url:
        if item.external_url not in data["links"]:
            data["links"].append(item.external_url)

    # Note: text stickers are often burned into the image or stored in complex JSON structures 
    # under 'story_bloks_stickers' or 'story_text_stickers' which frequently change.
    # We grab what we can from accessibility fields.
    if 'accessibility_caption' in node and node['accessibility_caption']:
        if node['accessibility_caption'] not in data["text"]:
            data["text"].append(node['accessibility_caption'])
            
    return data

def send_alert(story_id, target_username, story_data):
    """
    Constructs an HTML email and sends it via Brevo API.
    Embeds the downloaded thumbnail to prevent CDN URL expiry issues.
    """
    configuration = brevo_python.Configuration()
    configuration.api_key['api-key'] = BREVO_API_KEY
    api_instance = brevo_python.TransactionalEmailsApi(brevo_python.ApiClient(configuration))
    
    # Download image for embedding
    base64_image = download_image_as_base64(story_data["image_url"])
    
    # Construct HTML Content
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #E1306C;">New Story from @{target_username}</h2>
                <p><strong>Story ID:</strong> {story_id}</p>
                <p><strong>Type:</strong> {'Video' if story_data['is_video'] else 'Image'}</p>
    """
    
    if story_data["text"]:
        html_content += f"<h3>Extracted Text:</h3><blockquote>{'<br>'.join(story_data['text'])}</blockquote>"
        
    if story_data["links"]:
        html_content += "<h3>Extracted Links:</h3><ul>"
        for link in story_data["links"]:
            html_content += f'<li><a href="{link}" target="_blank">{link}</a></li>'
        html_content += "</ul>"
        
    if base64_image:
        html_content += f'<hr><p><strong>Thumbnail:</strong></p><img src="data:image/jpeg;base64,{base64_image}" alt="Story Thumbnail" style="max-width: 100%; height: auto; border-radius: 8px;"/>'
    else:
        html_content += f'<hr><p><em>Could not download thumbnail. Original URL: <a href="{story_data["image_url"]}">Link</a></em></p>'

    html_content += """
            </div>
        </body>
    </html>
    """

    send_smtp_email = brevo_python.SendSmtpEmail(
        to=[{"email": TO_EMAIL}],
        sender={"email": SENDER_EMAIL, "name": "Lumina-IG Monitor"},
        subject=f"New Instagram Story from @{target_username}",
        html_content=html_content
    )
    
    try:
        api_instance.send_transac_email(send_smtp_email)
        print(f"[{datetime.now()}] Successfully sent alert for story {story_id}.")
        return True
    except ApiException as e:
        print(f"Exception when calling Brevo API: {e}")
        return False

def main():
    print(f"[{datetime.now()}] Starting Lumina-IG Monitor...")
    
    if not all([TARGET_USERNAME, BURNER_USERNAME, BREVO_API_KEY, TO_EMAIL, SENDER_EMAIL]):
        print("Error: Missing environment variables. Please check your .env file.")
        return

    conn, cursor = init_db()
    
    # Initialize Instaloader
    loader = instaloader.Instaloader(
        download_pictures=False,
        download_video_thumbnails=False,
        download_videos=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False
    )
    
    # Load session
    try:
        loader.load_session_from_file(BURNER_USERNAME, filename=f"session-{BURNER_USERNAME}")
        print(f"Session loaded for {BURNER_USERNAME}.")
    except Exception as e:
        print(f"Could not load session for {BURNER_USERNAME}. Make sure to generate it locally using 'instaloader --login {BURNER_USERNAME}'. Error: {e}")
        return

    TARGET_USERID = os.getenv("TARGET_USERID")
    
    try:
        if TARGET_USERID:
            print(f"Using direct User ID {TARGET_USERID} (bypassing strict username lookup)...")
            userid = int(TARGET_USERID)
        else:
            profile = instaloader.Profile.from_username(loader.context, TARGET_USERNAME)
            userid = profile.userid
            print(f"Fetching stories for {TARGET_USERNAME} (User ID: {userid})...")
            print(f"TIP: To prevent rate limits, add TARGET_USERID={userid} to your .env file!")
        
        # It's an iterator of Story objects
        for story in loader.get_stories(userids=[userid]):
            for item in story.get_items():
                story_id = str(item.mediaid)
                
                if not is_processed(cursor, story_id):
                    print(f"Found new story: {story_id}. Extracting data...")
                    
                    story_data = extract_story_data(item)
                    
                    if send_alert(story_id, TARGET_USERNAME, story_data):
                        mark_processed(conn, cursor, story_id)
                else:
                    # Depending on how verbose you want the logs, you might want to comment this out
                    # print(f"Story {story_id} already processed. Skipping.")
                    pass
                    
    except instaloader.exceptions.InstaloaderException as e:
        print(f"Instaloader error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        conn.close()
        print(f"[{datetime.now()}] Lumina-IG Monitor finished.")

if __name__ == "__main__":
    main()
