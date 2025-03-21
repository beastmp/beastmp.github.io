# filepath: .github/scripts/update_github_posts.py
import os
import yaml
import base64
import re
from github import Github
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Configuration
POSTS_DIR = "_posts"
README_FILENAMES = ["portfolio.md", "portfolio.markdown", "PORTFOLIO.md", "PORTFOLIO.markdown", "Portfolio.md", "Portfolio.markdown", "README.md"]
EXCLUDE_TOPICS = ["no-portfolio", "exclude-portfolio"]

# Project grouping topic format: "project-{groupname}"
PROJECT_GROUP_PREFIX = "project-"

# Image topics won't work with URLs due to GitHub restrictions
# Use file-based approach instead (already implemented in the code)
HEADER_IMAGE_FILENAMES = ["portfolio-header.jpg", "portfolio-header.png", "header.jpg", "header.png"]
TEASER_IMAGE_FILENAMES = ["portfolio-teaser.jpg", "portfolio-teaser.png", "teaser.jpg", "teaser.png"]

# Initialize GitHub client
token = os.environ.get("GITHUB_TOKEN")
g = Github(token)

# Ensure posts directory exists
Path(POSTS_DIR).mkdir(exist_ok=True)

# Track created/updated posts for summary
created_posts = []
updated_posts = []
failed_posts = []
excluded_posts = []
project_groups = defaultdict(dict)

# Handle user information and repository access more robustly
try:
    # Try to get user info directly
    user = g.get_user()
    username = user.login
    repos = user.get_repos()
except Exception as e:
    print(f"Couldn't access user profile: {e}")
    # Fall back to accessing repos through authenticated client
    username = "beastmp"  # Hardcode GitHub username as fallback
    repos = g.get_repos()  # This gets repos the token can access

def get_repository_images(repo, username, repo_name, topics, readme_content):
    """Get header and teaser images using multiple methods in order of precedence"""
    
    # Default images
    header_image = f"https://opengraph.githubassets.com/1/{username}/{repo_name}"
    teaser_image = f"https://opengraph.githubassets.com/1/{username}/{repo_name}"
    
    # 1. No longer check for image topics since GitHub doesn't support URLs in topics
    # Instead, rely on frontmatter and files
    
    # 2. Check for frontmatter in README
    if readme_content and "---" in readme_content:
        frontmatter_match = re.search(r"---\n(.*?)\n---", readme_content, re.DOTALL)
        if frontmatter_match:
            frontmatter_text = frontmatter_match.group(1)
            # Extract header_image if not already set via topic
            header_match = re.search(r"header_image:\s*(.*?)(\n|$)", frontmatter_text)
            if header_match:
                header_image = header_match.group(1).strip()
            
            # Extract teaser_image if not already set via topic
            teaser_match = re.search(r"teaser_image:\s*(.*?)(\n|$)", frontmatter_text)
            if teaser_match:
                teaser_image = teaser_match.group(1).strip()
    
    # 3. Look for image files in repository
    if header_image == f"https://opengraph.githubassets.com/1/{username}/{repo_name}":
        for image_filename in HEADER_IMAGE_FILENAMES:
            try:
                repo.get_contents(image_filename)
                header_image = f"https://raw.githubusercontent.com/{username}/{repo_name}/main/{image_filename}"
                break
            except Exception:
                continue
    
    if teaser_image == f"https://opengraph.githubassets.com/1/{username}/{repo_name}":
        for image_filename in TEASER_IMAGE_FILENAMES:
            try:
                repo.get_contents(image_filename)
                teaser_image = f"https://raw.githubusercontent.com/{username}/{repo_name}/main/{image_filename}"
                break
            except Exception:
                continue
    
    return header_image, teaser_image

# First pass: collect repositories and group them by project
for repo in repos:
    try:
        # Skip forks, private and archived repos
        if repo.fork or repo.private or repo.archived:
            continue
            
        # Get topics for exclusion and grouping check
        topics = repo.get_topics()
        
        # Skip repositories with exclusion topics
        if any(topic in EXCLUDE_TOPICS for topic in topics):
            excluded_posts.append(repo.name)
            print(f"⊘ Excluding {repo.name} (has exclusion topic)")
            continue
            
        # Check if this repo belongs to a project group
        project_name = None
        project_display_name = None
        for topic in topics:
            if topic.startswith(PROJECT_GROUP_PREFIX):
                project_name = topic[len(PROJECT_GROUP_PREFIX):]  # Remove the prefix
                project_display_name = project_name  # Store original version with hyphens
                break
        
        # If it's part of a project, add to group with both raw name and display name
        if project_name:
            # Store both the raw name (for file paths) and display name (for titles)
            project_groups[project_name] = project_groups[project_name] or {"repos": [], "display_name": project_display_name}
            project_groups[project_name]["repos"].append(repo)
            print(f"➕ Adding {repo.name} to project group '{project_display_name}'")
        else:
            # Process as a regular standalone repository
            process_repo(repo)
            
    except Exception as e:
        failed_posts.append(repo.name)
        print(f"✕ Failed to process {repo.name}: {str(e)}")

# Second pass: process project groups
for project_name, group_data in project_groups.items():
    try:
        repos_in_group = group_data["repos"]
        display_name = group_data["display_name"]
        
        print(f"Processing project group: {display_name}")
        
        # Sort repositories by creation date
        repos_in_group.sort(key=lambda r: r.created_at)
        
        # Use the first repo's creation date for the post date
        first_repo = repos_in_group[0]
        creation_date = first_repo.created_at.strftime("%Y-%m-%d")
        
        # Use the newest repo for the last update date
        last_updated = max(repo.updated_at for repo in repos_in_group).strftime("%Y-%m-%d")
        
        # Collect all topics from all repos in the group
        all_topics = []
        for repo in repos_in_group:
            all_topics.extend(repo.get_topics())
        
        # Remove project: topics and deduplicate
        all_topics = [t for t in all_topics if not t.startswith("project:")]
        unique_topics = list(set(all_topics))
        
        # If no topics, use the first repo's language
        if not unique_topics and first_repo.language:
            unique_topics = [first_repo.language.lower()]
        
        # Format tags as string
        tags_str = "[" + ", ".join(f'"{topic}"' for topic in unique_topics) + "]"
        if tags_str == "[]":
            tags_str = '["github", "project"]'
            
        # Use first repo with a README for content or create minimal content
        project_content = f"# {display_name.replace('-', ' ').title()}\n\nThis project consists of multiple repositories:\n\n"
        
        # Get combined content
        for repo in repos_in_group:
            repo_name = repo.name
            repo_url = repo.html_url
            
            # Try to find a README
            readme_content = None
            for readme_file in README_FILENAMES:
                try:
                    readme = repo.get_contents(readme_file)
                    if readme:
                        readme_content = base64.b64decode(readme.content).decode("utf-8")
                        # Strip frontmatter if present
                        if readme_content and "---" in readme_content:
                            readme_content = re.sub(r"---\n.*?---\n", "", readme_content, 1, re.DOTALL)
                        break
                except Exception:
                    continue
            
            # Add repo summary to project content
            project_content += f"## [{repo_name}]({repo_url})\n\n"
            project_content += f"Language: {repo.language or 'Not specified'}\n\n"
            if repo.description:
                project_content += f"{repo.description}\n\n"
                
            # Add condensed README content if available
            if readme_content:
                # Extract first paragraph after any headings
                first_para = re.search(r"(?:^|\n)(?!#)(.+?)(?=\n\n|\n#|$)", readme_content)
                if first_para:
                    project_content += f"{first_para.group(1).strip()}\n\n"
            
            project_content += f"[View Repository]({repo_url})\n\n"
            project_content += "---\n\n"
        
        # Get a nice title for the project - preserve original hyphens for spacing
        # This is the key change - replace hyphens with spaces in the display name, not the project name
        post_title = display_name.replace('-', ' ').replace('_', ' ').title()
        
        # Create a description from the first repo
        description = (f"A {post_title} project consisting of {len(repos_in_group)} repositories: " + 
                      ", ".join([repo.name for repo in repos_in_group[:3]]) +
                      (f" and {len(repos_in_group) - 3} more" if len(repos_in_group) > 3 else ""))
        
        # Get images - prefer using first repo's images
        first_repo_topics = first_repo.get_topics()
        header_image, teaser_image = get_repository_images(
            first_repo, username, first_repo.name, first_repo_topics, readme_content)
        
        # Mark as highlight if any repo in group has stars
        has_stars = any(repo.stargazers_count > 0 for repo in repos_in_group)
        
        # Create Jekyll frontmatter
        frontmatter = f"""---
layout: posts
title:  "{post_title} (Project Group)"
date:   {creation_date} 12:00:00 +0000
tags: {tags_str}
author_profile: true
author: Michael Palmer
categories: work
highlight_home: {str(has_stars).lower()}
tagline: "{description}"
header:
  overlay_image: {header_image}
  teaser: {teaser_image}
  caption: "Project Group: {project_name}"
description: {description}
---

"""

        # Create the post content
        repo_info = f"""
> This post represents a project group with multiple GitHub repositories.  
> Last updated: {last_updated}
"""

        post_content = frontmatter + project_content + "\n\n---\n\n" + repo_info
        
        # Create post filename
        safe_name = project_name.lower().replace(' ', '-')
        safe_name = re.sub(r'[^a-z0-9-]', '', safe_name)
        
        post_filename = f"{POSTS_DIR}/{creation_date}-project-{safe_name}.markdown"
        
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
                
            if os.path.exists(post_filename):
                updated_posts.append(project_name)
                print(f"✓ Updated post for project group {project_name}")
            else:
                created_posts.append(project_name)
                print(f"✓ Created new post for project group {project_name}")
        else:
            print(f"- No changes for project group {project_name}")
        
    except Exception as e:
        failed_posts.append(f"Project group {project_name}")
        print(f"✕ Failed to process project group {project_name}: {str(e)}")

def process_repo(repo):
    """Process a single repository (moved to a function for clarity)"""
    try:
        repo_name = repo.name
        repo_url = repo.html_url
        
        print(f"Processing repository: {repo_name}")
        
        # Try each possible README filename
        readme_content = None
        readme_path = None
        
        for readme_file in README_FILENAMES:
            try:
                readme = repo.get_contents(readme_file)
                if (readme):
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
            
        # Get header and teaser images
        header_image, teaser_image = get_repository_images(repo, username, repo_name, topics, readme_content)
        
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
  overlay_image: {header_image}
  teaser: {teaser_image}
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
        post_content = frontmatter + readme_content + "\n\n---\n\n" + repo_info
        
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

# Process individual repos that aren't in project groups
for repo in repos:
    if repo.fork or repo.private or repo.archived:
        continue
        
    topics = repo.get_topics()
    
    # Skip if excluded or part of a project group
    if any(topic in EXCLUDE_TOPICS for topic in topics) or any(topic.startswith("project:") for topic in topics):
        continue
        
    process_repo(repo)
        
# Print summary
print(f"\nSummary:")
print(f"- Created {len(created_posts)} new posts")
print(f"- Updated {len(updated_posts)} existing posts")
print(f"- Processed {len(project_groups)} project groups")
print(f"- Excluded {len(excluded_posts)} repositories")
if failed_posts:
    print(f"- Failed to process {len(failed_posts)} repositories: {', '.join(failed_posts)}")