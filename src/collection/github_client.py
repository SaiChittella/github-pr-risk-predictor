from dotenv import load_dotenv
import requests
import os
import json

load_dotenv()
token = os.getenv("GITHUB_TOKEN")

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json"
}

base_url = "https://api.github.com"
owner = "fastapi"
repo = "fastapi"
pull_number = 16350

pr_record = {}

response = requests.get(f"{base_url}/repos/{owner}/{repo}/pulls/{pull_number}", headers=headers)
response_file = requests.get(f"{base_url}/repos/{owner}/{repo}/pulls/{pull_number}/files", headers=headers)

if response.status_code == 200:
    data = response.json()
    file_data = response_file.json()

    pr_record = {
        "pr_number": data["number"],
        "title": data["title"],
        "author": data["user"]["login"],
        "created_at": data["created_at"],
        "updated_at": data["updated_at"],
        "state": data["state"],
        "merged": data["merged"],
        "mergeable": data["mergeable"],
        "mergeable_state": data["mergeable_state"],
        "comments": data["comments"],
        "review_comments": data["review_comments"],
        "commits": data["commits"],
        "additions": data["additions"],
        "deletions": data["deletions"],
        "changed_files": data["changed_files"],
        "files": [file_info["filename"] for file_info in file_data]
    }

    with open("data/raw/sample_pr.json", "w") as file:
        json.dump(pr_record, file, indent=4)
else: 
    print(f"Error: {response.status_code} - {response.text}")