import instaloader
import browser_cookie3
import sys

def import_session(browser_name):
    print(f"Attempting to import Instagram session from {browser_name}...")
    try:
        if browser_name == 'firefox':
            cj = browser_cookie3.firefox(domain_name='instagram.com')
        elif browser_name == 'chrome':
            cj = browser_cookie3.chrome(domain_name='instagram.com')
        elif browser_name == 'brave':
            cj = browser_cookie3.brave(domain_name='instagram.com')
        elif browser_name == 'edge':
            cj = browser_cookie3.edge(domain_name='instagram.com')
        elif browser_name == 'chromium':
            cj = browser_cookie3.chromium(domain_name='instagram.com')
        elif browser_name == 'zen':
            import glob, os
            zen_path = os.path.expanduser("~/.zen")
            # Find the most recently modified cookies.sqlite
            cookie_files = glob.glob(os.path.join(zen_path, "*", "cookies.sqlite"))
            if not cookie_files:
                print("Could not find Zen browser cookies.")
                return
            cookie_file = max(cookie_files, key=os.path.getmtime)
            cj = browser_cookie3.firefox(domain_name='instagram.com', cookie_file=cookie_file)
        else:
            print("Unsupported browser")
            return
    except Exception as e:
        print(f"Failed to get cookies from {browser_name}: {e}")
        return

    has_session = False
    for cookie in cj:
        if cookie.name == 'sessionid':
            has_session = True
            break

    if not has_session:
        print(f"Could not find an active Instagram session in {browser_name}. Please log into instagram.com on {browser_name} first.")
        return

    # Initialize Instaloader
    loader = instaloader.Instaloader()
    
    # Inject cookies into the instaloader session
    loader.context._session.cookies.update(cj)
    
    try:
        username = loader.test_login()
        if not username:
            print("Login failed. The session cookie might be expired.")
            return
            
        print(f"Successfully connected as '{username}'.")
        loader.context.username = username
        loader.save_session_to_file(f"session-{username}")
        print(f"Session saved locally as 'session-{username}'! You can now run monitor.py.")
    except Exception as e:
        print(f"Login error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_session.py [firefox|chrome|brave|edge|chromium]")
        sys.exit(1)
    import_session(sys.argv[1].lower())
