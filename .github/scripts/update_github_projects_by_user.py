# filepath: .github/scripts/update_github_projects.py
import os
import yaml
import requests
from datetime import datetime

# Your GitHub username
username = "beastmp"

# Get public repositories
url = f"https://api.github.com/users/{username}/repos"
response = requests.get(url)
repos_data = response.json()

repositories = []
for repo in repos_data:
    # Skip forks and archived repos
    if not repo.get("fork") and not repo.get("archived"):
        # Get topics through API
        topics_url = f"https://api.github.com/repos/{username}/{repo['name']}/topics"
        topics_response = requests.get(topics_url, headers={"Accept": "application/vnd.github.mercy-preview+json"})
        topics = topics_response.json().get("names", [])
        
        repositories.append({
            "name": repo["name"],
            "title": repo["name"].replace('-', ' ').replace('_', ' ').title(),
            "description": repo["description"] or f"A {repo.get('language', 'Unknown')} project.",
            "url": repo["html_url"],
            "homepage": repo.get("homepage") or "",
            "language": repo.get("language") or "Unknown",
            "stars": repo["stargazers_count"],
            "forks": repo["forks_count"],
            "created_at": repo["created_at"].split("T")[0],
            "updated_at": repo["updated_at"].split("T")[0],
            "topics": topics,
            "tags": topics,
            "categories": ["work", "github"],
            "highlight_home": repo["stargazers_count"] > 0,
            "teaser_image": f"https://opengraph.githubassets.com/1/{username}/{repo['name']}"
        })

# Sort by stars (desc), then updated_at (desc)
repositories.sort(key=lambda x: (-x["stars"], x["updated_at"]), reverse=True)

# Write to YAML file
os.makedirs("_data", exist_ok=True)
with open('_data/github_projects.yml', 'w') as f:
    yaml.dump(repositories, f, default_flow_style=False)

print(f"Updated {len(repositories)} GitHub projects")