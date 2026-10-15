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

def build_pr_data(url:str, config:Config):
    data = requests.get(url, headers=config.headers)
    file_data = requests.get(f"{url}/files", headers=config.headers)

    if not check_reponse(data) or not check_reponse(file_data):
        return None
    
    data = data.json()
    file_data = file_data.json() 

    return {
        "repository": f"{config.owner}/{config.repo}",
        "pr_number": data["number"],
        "title": data["title"],
        "author": data["user"]["login"],
        "created_at": data["created_at"],
        'merged_at': data["merged_at"],
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
        "head.shah": data["head"]["sha"],
        "base.shah": data["base"]["sha"],
        "merge_commit_sha": data["merge_commit_sha"],
        "files": {
            file_info["filename"]: {
                "status": file_info["status"],
                "additions": file_info["additions"],
                "deletions": file_info["deletions"],
                "changes": file_info["changes"],
                "blob_url": file_info["blob_url"],
                "raw_url": file_info["raw_url"],
                "contents_url": file_info["contents_url"], 
            }
            for file_info in file_data
        },
    }

    # write_to_json(pr_data, "data/raw/sample_pr.json")

def write_to_json(data: dict, file_path: str):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

def get_repo_prs(merged_prs, response : requests.Response):
    pr_data = response.json()

    for pr in pr_data:
        if pr.get("merged_at") is not None:
            merged_prs.append(build_pr_data(pr.get("url"), config))

def check_reponse(response: requests.Response):
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return False
    return True

if __name__ == "__main__":
    config = load_env()
    headers = config.headers
    base_url = config.base_url
    owner = config.owner
    repo = config.repo
    pull_number = config.pull_number
   
    # GET https://github.com{owner}/{repo}/pulls?state=closed&page={page_number}&per_page={results_per_page}
    merged_prs = []
    target = 100
    page = 1

    while len(merged_prs) < target:
        response = requests.get(f"{base_url}/repos/{owner}/{repo}/pulls", headers=headers, params={"state": "closed", "page": page, "per_page": 20})

        if not check_reponse(response):
            break

        if len (response.json()) == 0:
            print("No more PRs to fetch.")
            break

        get_repo_prs(merged_prs, response)
        page += 1

    write_to_json(merged_prs, f"data/raw/{owner}_{repo}_merged_prs.json")


    # response = requests.get(f"{base_url}/repos/{owner}/{repo}/pulls/{pull_number}", headers=headers)
    # response_file = requests.get(f"{base_url}/repos/{owner}/{repo}/pulls/{pull_number}/files", headers=headers)

    # if response.status_code != 200 or response_file.status_code != 200:
    #     print(f"Error: {response.status_code} - {response.text}")
    #     print(f"Error: {response_file.status_code} - {response_file.text}")
    # else:
    #     get_pr_data(config, response, response_file)