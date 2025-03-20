# filepath: .github/scripts/update_github_posts.py
import os
import yaml
import base64
import re
from github import Github
from datetime import datetime
from pathlib import Path

# Configuration
POSTS_DIR = "_posts"
README_FILENAMES = ["portfolio.md", "portfolio.markdown", "PORTFOLIO.md", "PORTFOLIO.markdown", "Portfolio.md", "Portfolio.markdown"]

# Initialize GitHub client
token = os.environ.get("GITHUB_TOKEN")
g = Github(token)

# Ensure posts directory exists
Path(POSTS_DIR).mkdir(exist_ok=True)

# Track created/updated posts for summary
created_posts = []
updated_posts = []
failed_posts = []

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

# Process repositories
for repo in repos:
    try:
        # Skip forks, private and archived repos
        if repo.fork or repo.private or repo.archived:
            continue
            
        repo_name = repo.name
        repo_url = repo.html_url
        
        print(f"Processing repository: {repo_name}")
        
        # Try each possible README filename
        readme_content = None
        readme_path = None
        
        for readme_file in README_FILENAMES:
            try:
                readme = repo.get_contents(readme_file)
                if readme:
                    readme_content = base64.b64decode(readme.content).decode("utf-8")
                    readme_path = readme_file
                    break
            except Exception:
                continue
                
        # If no README is found, create a minimal one
        if not readme_content:
            print(f"No Portfolio page found for {repo_name}, creating minimal content")
            readme_content = f"# {repo_name.replace('-', ' ').replace('_', ' ').title()}\n\nThis repository contains a {repo.language or 'software'} project."
        
        # Generate Jekyll frontmatter
        creation_date = repo.created_at.strftime("%Y-%m-%d")
        post_title = repo_name.replace('-', ' ').replace('_', ' ').title()
        description = repo.description or f"A {repo.language or 'software'} project."
        
        # Get topics as tags
        topics = repo.get_topics()
            
        # If no topics, use language as tag
        if not topics and repo.language:
            topics = [repo.language.lower()]
        
        # Format tags as string
        tags_str = "[" + ", ".join(f'"{topic}"' for topic in topics) + "]"
        if tags_str == "[]":
            tags_str = '["github", "project"]'
            
        # Create Jekyll frontmatter
        frontmatter = f"""---
layout: posts
title:  "{post_title}"
date:   {creation_date} 12:00:00 +0000
tags: {tags_str}
author_profile: true
author: Michael Palmer
categories: work
highlight_home: {str(repo.stargazers_count > 0).lower()}
tagline: "{description}"
header:
  overlay_image: https://opengraph.githubassets.com/1/{username}/{repo_name}
  teaser: https://opengraph.githubassets.com/1/{username}/{repo_name}
  caption: "GitHub Repository: [{repo_name}]({repo_url})"
description: {description}
---
"""

        # Add repository link to the content
        repo_info = f"""
> This post is automatically generated from my [GitHub repository]({repo_url}).  
> Last updated: {repo.updated_at.strftime("%Y-%m-%d")}

"""

        # Create the post content
        post_content = frontmatter + repo_info + readme_content
        
        # Sanitize filename - replace spaces and special chars
        safe_name = repo_name.lower().replace(' ', '-')
        safe_name = re.sub(r'[^a-z0-9-]', '', safe_name)
        
        # Create post filename
        post_filename = f"{POSTS_DIR}/{creation_date}-github-{safe_name}.markdown"
        
        # Check if post exists and has different content
        update_post = False
        if os.path.exists(post_filename):
            with open(post_filename, 'r', encoding='utf-8') as f:
                existing_content = f.read()
                if existing_content != post_content:
                    update_post = True
        else:
            update_post = True
            
        # Write to file if it needs updating
        if update_post:
            with open(post_filename, 'w', encoding='utf-8') as f:
                f.write(post_content)
                
            if os.path.exists(post_filename) and not os.path.exists(f"{post_filename}.new"):
                updated_posts.append(repo_name)
                print(f"✓ Updated post for {repo_name}")
            else:
                created_posts.append(repo_name)
                print(f"✓ Created new post for {repo_name}")
        else:
            print(f"- No changes for {repo_name}")
            
    except Exception as e:
        failed_posts.append(repo_name)
        print(f"✕ Failed to process {repo_name}: {str(e)}")
        
# Print summary
print(f"\nSummary:")
print(f"- Created {len(created_posts)} new posts")
print(f"- Updated {len(updated_posts)} existing posts")
if failed_posts:
    print(f"- Failed to process {len(failed_posts)} repositories: {', '.join(failed_posts)}")