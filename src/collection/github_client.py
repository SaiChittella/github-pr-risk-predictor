from dataclasses import dataclass

from dotenv import load_dotenv
import requests
import os
import json

@dataclass
class Config:
    headers: dict
    base_url: str
    owner: str
    repo: str
    pull_number: int
    pr_record: dict = None


def load_env():
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

    return Config(
        headers=headers,
        base_url=base_url,
        owner=owner,
        repo=repo,
        pull_number=pull_number
    )

def get_pr_data(config: Config, response : requests.Response, response_file: requests.Response):
    data = response.json()
    file_data = response_file.json()

    config.pr_record = {
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
        "files": {
            file_info["filename"]: {
                "status": file_info["status"],
                "additions": file_info["additions"],
                "deletions": file_info["deletions"],
                "changes": file_info["changes"],
                "blob_url": file_info["blob_url"],
                "raw_url": file_info["raw_url"],
                "contents_url": file_info["contents_url"], 
                'merged_at': data["merged_at"],
            }
            for file_info in file_data
        }
    }

    write_to_json(config.pr_record, "data/raw/sample_pr.json")

def write_to_json(data: dict, file_path: str):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

    
if __name__ == "__main__":
    config = load_env()
    headers = config.headers
    base_url = config.base_url
    owner = config.owner
    repo = config.repo
    pull_number = config.pull_number

    response = requests.get(f"{base_url}/repos/{owner}/{repo}/pulls/{pull_number}", headers=headers)
    response_file = requests.get(f"{base_url}/repos/{owner}/{repo}/pulls/{pull_number}/files", headers=headers)

    if response.status_code != 200 and response_file.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        print(f"Error: {response_file.status_code} - {response_file.text}")
    else:
        get_pr_data(config, response, response_file)