#!/bin/bash
cd /home/rain/Downloads/storytracker
source venv/bin/activate

echo "Extracting fresh cookie from Brave..."
if ! python import_session.py brave; then
    python send_error.py "Arch Linux Auth Node" "Failed to extract session cookie from Brave browser."
    exit 1
fi

echo "Beaming fresh cookie to AWS Cloud Worker..."
if ! scp -o StrictHostKeyChecking=no -i ~/Downloads/aws-key.pem session-elric889 ubuntu@100.105.78.78:/home/ubuntu/storytracker/; then
    python send_error.py "Arch Linux Auth Node" "Failed to SCP the session cookie to the AWS server. The server might be down or Tailscale is disconnected."
    exit 1
fi

echo "Cookie sync complete!"
