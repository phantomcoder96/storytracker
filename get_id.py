import instaloader
import os
from dotenv import load_dotenv

load_dotenv()
BURNER = os.getenv("BURNER_USERNAME")
TARGET = os.getenv("TARGET_USERNAME")

loader = instaloader.Instaloader()
try:
    loader.load_session_from_file(BURNER, filename=f"session-{BURNER}")
except Exception as e:
    print(f"Session load error: {e}")
    exit(1)

print(f"Searching for {TARGET} to get User ID...")
try:
    search = instaloader.TopSearchResults(loader.context, TARGET)
    for profile in search.get_profiles():
        if profile.username == TARGET:
            print(f"Found it! User ID for {TARGET} is: {profile.userid}")
            print(f"\nPlease add this line to your .env file:\nTARGET_USERID={profile.userid}")
            break
except Exception as e:
    print(f"Error during search: {e}")
