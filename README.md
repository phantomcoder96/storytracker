# Automated Instagram Story Notifications

## Project Overview
Automated Instagram Story Notifications is an automated script designed to track targeted Instagram accounts, extract their stories (including images and embedded links), and deliver them directly to an email inbox.

## Motivation
I realized how unhealthy my relationship with social media was, but I also didn't want to miss out on potential job opportunities from tech accounts that exclusively post via their Instagram stories. So I decided to create a system that would allow me to have the best of both worlds.

This project allows me to delete Instagram entirely from my phone while ensuring I never miss an opportunity by parsing the story and sending the info straight to my email inbox.

## Technical Architecture
This project implements a highly resilient, distributed cloud pipeline to bypass aggressive anti-bot security measures and extract deeply nested JSON data:

- **Distributed Authentication (Arch Linux -> AWS EC2)**: Instagram aggressively flags automated logins, particularly from AWS datacenter IPs. To bypass this, the architecture is split into two nodes:
  1. **Auth Node (Local Arch LinuxPC)**: A local `systemd` timer automatically extracts a new login cookie directly from the local browser every 30 minutes. It then securely beams this living cookie to the cloud worker via `scp`.
  2. **Worker Node (AWS EC2)**: The AWS server runs on a synchronized cron schedule, receiving the fresh cookie and executing the scraper. It routes its traffic back through the Arch PC via a **Tailscale VPN Exit Node**, fully masking the AWS IP and perfectly disguising the scrape as standard residential mobile traffic.
- **JSON Metadata Parsing (`instaloader` & `re`)**: Instagram frequently changes its API structure and hides Story Link Stickers (e.g., job application URLs) deep within nested, undocumented dictionaries like `iphone_struct`. The script implements a robust recursive search to dynamically locate and extract outbound URLs regardless of how the JSON tree is restructured.
- **Transactional Email Delivery (Brevo API)**: To avoid standard email spam filters, the script uses the Brevo API to dynamically generate HTML emails and natively attach the scraped story thumbnails.
- **State Management (SQLite3)**: A lightweight SQLite database tracks previously processed `story_id`s on the AWS server, ensuring that duplicate emails are never sent.
- **Error Reporting**: The distributed pipeline features comprehensive exception handling. If the Auth Node fails to extract the cookie or beam it via `scp`, or if the AWS Worker Node encounters a `400 Bad Request` or network timeout, the system intercepts the exception and immediately fires a priority email alert detailing the exact failure point and stack trace.

## Next Steps: Automated Job Applications
The next phase of this project is to close the loop on the job application pipeline. Currently, the system delivers the job link to an email inbox, but in the next iterations, I want to include:
1. **Link Parsing & Categorization**: Automatically follow the scraped links and use an LLM API to determine if the destination page is a supported job board (e.g., Greenhouse, Lever, Workday).
2. **Automated Submission**: Integrate headless browser automation (such as Playwright) to automatically map my personal data and resume to the application fields and submit the application without manual intervention.
3. **Tracking Dashboard**: Log successfully submitted applications to a personal database or spreadsheet for tracking purposes.
