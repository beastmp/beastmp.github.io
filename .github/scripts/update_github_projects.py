# filepath: .github/scripts/update_github_projects.py
import os
import yaml
from github import Github
from datetime import datetime

# Initialize GitHub client
token = os.environ.get("GITHUB_TOKEN")
g = Github(token)

# Handle user information and repository access more robustly
try:
    # Try to get user info directly
    user = g.get_user()
    username = user.login
    repos = user.get_repos()
except Exception as e:
    print(f"Couldn't access user profile: {e}")
    # Fall back to accessing repos through authenticated client
    username = "beastmp"  # Hardcode your GitHub username as fallback
    repos = g.get_repos()  # This gets repos the token can access

# Get repositories
repositories = []
for repo in repos:
    try:
        # Skip forks, private and archived repos
        if not repo.fork and not repo.private and not repo.archived:
            # Get topics as tags
            topics = repo.get_topics()
            
            repositories.append({
                "name": repo.name,
                "title": repo.name.replace('-', ' ').replace('_', ' ').title(),
                "description": repo.description or f"A {repo.language} project.",
                "url": repo.html_url,
                "homepage": repo.homepage or "",
                "language": repo.language or "Unknown",
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "created_at": repo.created_at.strftime('%Y-%m-%d'),
                "updated_at": repo.updated_at.strftime('%Y-%m-%d'),
                "topics": topics,
                "tags": topics,  # Duplicate as tags for compatibility
                "categories": ["work", "github"],
                "highlight_home": repo.stargazers_count > 0,  # Highlight starred repos
                "teaser_image": f"https://opengraph.githubassets.com/1/{username}/{repo.name}"
            })
            print(f"Added repository: {repo.name}")
    except Exception as e:
        print(f"Error processing repo {repo.name}: {e}")

# Sort by stars (desc), then updated_at (desc)
repositories.sort(key=lambda x: (-x["stars"], x["updated_at"]), reverse=True)

# Write to YAML file
os.makedirs("_data", exist_ok=True)
with open('_data/github_projects.yml', 'w') as f:
    yaml.dump(repositories, f, default_flow_style=False)

print(f"Updated {len(repositories)} GitHub projects")