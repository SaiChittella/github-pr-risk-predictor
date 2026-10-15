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

    return Config(
        headers=headers,
        base_url=base_url,
        owner=owner,
        repo=repo,
    )

def paginate_pr_files(url: str, config: Config):
    all_files = []
    page = 1

    while True:
        response = requests.get(
            f"{url}/files",
            headers=config.headers,
            params={
                "page": page,
                "per_page": 100
            }
        )

        if not check_reponse(response):
            return None

        page_files = response.json()

        if len(page_files) == 0:
            break

        all_files.extend(page_files)
        page += 1

    return all_files

def build_pr_data(url:str, config:Config):
    data = requests.get(url, headers=config.headers)
    file_data = paginate_pr_files(url, config)

    if not check_reponse(data):
        return None
    
    data = data.json()

    if file_data is None or len(file_data) != data["changed_files"]:
        print(f"Mismatch in changed files count for PR #{data['number']}: expected {data['changed_files']}, got {len(file_data)}")
        return None

    return {
        "repository": f"{config.owner}/{config.repo}",
        "pr_number": data["number"],
        "title": data["title"],
        "author": data["user"]["login"],
        "created_at": data["created_at"],
        "updated_at": data["updated_at"],
        'merged_at': data["merged_at"],
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
        "head_sha": data["head"]["sha"],
        "base_sha": data["base"]["sha"],
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

def write_to_json(data: list, file_path: str):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

def get_repo_prs(merged_prs, response : requests.Response, config: Config, target: int):
    pr_data = response.json()

    for pr in pr_data:
        if pr.get("merged_at") is not None:
            pr = build_pr_data(pr.get("url"), config)
            
            if pr in merged_prs or not validate_pr(pr):
                print(f"Invalid PR data for PR #{pr.get('pr_number')}. Skipping.")
                continue

            merged_prs.append(pr)
            print(
                f"Added PR #{pr['pr_number']} "
                f"({len(merged_prs)}/{target})"
            )
        if len(merged_prs) >= target:
            break

def check_reponse(response: requests.Response):
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return False
    return True

def validate_pr(pr: dict):
    return (
    pr is not None
    and pr.get("repository") is not None
    and pr.get("pr_number") is not None
    and pr.get("merged_at") is not None
    and pr.get("changed_files") >= 0
    and pr.get("additions") >= 0
    and pr.get("deletions") >= 0
    and len(pr.get("files")) == pr.get("changed_files")
    and pr.get("merge_commit_sha") is not None
    and pr.get("head_sha") is not None
    and pr.get("base_sha") is not None
)

if __name__ == "__main__":
    config = load_env()
    headers = config.headers
    base_url = config.base_url
    owner = config.owner
    repo = config.repo
 
    merged_prs = []
    target = 20
    page = 1


    while len(merged_prs) < target:
        response = requests.get(f"{base_url}/repos/{owner}/{repo}/pulls", headers=headers, params={"state": "closed", "page": page, "per_page": 20})

        if not check_reponse(response):
            break

        if len (response.json()) == 0:
            print("No more PRs to fetch.")
            break

        get_repo_prs(merged_prs, response, config, target)
        page += 1

    print(f"Collected {len(merged_prs)} merged PRs.")
    write_to_json(merged_prs, f"data/raw/{owner}_{repo}_merged_prs.json")
    print(f"Saved data to data/raw/{owner}_{repo}_merged_prs.json")