# Automated Instagram Story Notifications

## Project Overview
Automated Instagram Story Notifications is an automated script designed to track targeted Instagram accounts, extract their stories (including images and embedded links), and deliver them directly to an email inbox.

## Motivation
The primary motivation for this project was to establish a healthier relationship with social media while maintaining access to critical career opportunities. Mindless scrolling on Instagram is a massive time-sink, but many niche tech accounts exclusively post valuable job applications and networking events via their Instagram Stories. 

This system allows me to completely remove Instagram from my phone while ensuring I never miss a high-priority opportunity by parsing the story and sending the info straight to my inbox.

## Architecture
This project implements several techniques to bypass aggressive anti-bot security measures and extract deeply nested JSON data:
- **Session Extraction (`browser-cookie3`)**: Instagram aggressively flags automated logins. To bypass this, the project extracts a pristine, human-verified session cookie directly from a local browser's internal database and uses it to authenticate the scraper.
- **JSON Metadata Parsing (`instaloader` & `re`)**: Instagram frequently changes its API structure and hides Story Link Stickers (e.g., job application URLs) deep within nested, undocumented dictionaries like `iphone_struct` or `story_bloks_stickers`. The script implements a robust recursive search to dynamically locate and extract these outbound URLs regardless of how the JSON tree is restructured.
- **Transactional Email Delivery (Brevo API)**: To avoid standard email spam filters, the script uses the Brevo API to dynamically generate HTML emails and natively attach the scraped story thumbnails.
- **State Management (SQLite3)**: A lightweight, persistent SQLite database tracks previously processed `story_id`s, ensuring that duplicate emails are never sent across the execution intervals.
- **Systemd Automation (Arch Linux)**: The script is scheduled locally via native Arch Linux `systemd` timers with `Persistent=true`. If the computer is asleep during a scheduled run, the Linux kernel automatically triggers a catch-up execution the exact second the machine reconnects to the network.

## Next Steps: Automated Job Applications
The next phase of this project is to close the loop on the job application pipeline. Currently, the system delivers the job link to an email inbox. In the next iterations, I want to include:
1. **Link Parsing & Categorization**: Automatically follow the scraped links and use an LLM API to determine if the destination page is a supported job board (e.g., Greenhouse, Lever, Workday).
2. **Automated Submission**: Integrate headless browser automation (such as Playwright) to automatically map my personal data and resume to the application fields and submit the application without manual intervention.
3. **Tracking Dashboard**: Log successfully submitted applications to a personal database or spreadsheet for tracking purposes.
