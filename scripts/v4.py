import os
import re
import xml.etree.ElementTree as ET
import argparse
from github import Github

def parse_js_file(js_file_path):
    """Parse MongoDB queries from a .js file."""
    if not os.path.exists(js_file_path):
        raise FileNotFoundError(f"JS file not found: {js_file_path}")
    
    with open(js_file_path, "r") as file:
        queries = file.readlines()
        return queries

def correct_json_syntax(json_string):
    """Correct common JSON syntax issues."""
    json_string = re.sub(r'(?<!")\b(\w+)\b\s*:', r'"\1":', json_string)  # Add quotes around keys
    json_string = json_string.replace("'", '"')  # Replace single quotes with double quotes
    return json_string

def generate_liquibase_xml(version, queries, author_name):
    """Generate Liquibase XML from MongoDB queries."""
    root = ET.Element("databaseChangeLog", xmlns="http://www.liquibase.org/xml/ns/dbchangelog")
    root.set("xmlns:mongodb", "http://www.liquibase.org/xml/ns/mongodb")
    changeset = ET.SubElement(root, "changeSet", id=version, author=author_name)

    for query in queries:
        query = re.sub(r'\s+', ' ', query).strip()  # Clean up query spaces

        # InsertMany
        if "insertMany" in query:
            match = re.search(r'db\.getCollection\("([^"]+)"\)\.insertMany\((.*?)\)', query, re.DOTALL)
            if match:
                collection_name = match.group(1)
                document = correct_json_syntax(match.group(2))
                insert_many = ET.SubElement(changeset, "mongodb:insertMany", collectionName=collection_name)
                documents = ET.SubElement(insert_many, "mongodb:documents")
                documents.text = f"<![CDATA[{document}]]>"

        # UpdateOne
        elif "updateOne" in query:
            match = re.search(r'db\.getCollection\("([^"]+)"\)\.updateOne\((.*?),\s*(.*?)\)', query, re.DOTALL)
            if match:
                collection_name = match.group(1)
                query_string = correct_json_syntax(match.group(2))
                update_string = correct_json_syntax(match.group(3))
                update_command = ET.SubElement(changeset, "mongodb:runCommand")
                command = ET.SubElement(update_command, "mongodb:command")
                command.text = f"""
                <![CDATA[
                    {{
                        "update": "{collection_name}",
                        "updates": [
                            {{
                                "q": {query_string},
                                "u": {update_string},
                                "upsert": false
                            }}
                        ]
                    }}
                ]]>
                """

        # DeleteMany
        elif "deleteMany" in query:
            match = re.search(r'db\.getCollection\("([^"]+)"\)\.deleteMany\((.*?)\)', query, re.DOTALL)
            if match:
                collection_name = match.group(1)
                query_string = correct_json_syntax(match.group(2))
                delete_command = ET.SubElement(changeset, "mongodb:runCommand")
                command = ET.SubElement(delete_command, "mongodb:command")
                command.text = f"""
                <![CDATA[
                    {{
                        "delete": "{collection_name}",
                        "deletes": [
                            {{
                                "q": {query_string},
                                "limit": 0
                            }}
                        ]
                    }}
                ]]>
                """

    return root

def write_to_file(xml_tree, output_file_path):
    """Write XML tree to a file."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    
    tree = ET.ElementTree(xml_tree)
    with open(output_file_path, "wb") as file:
        tree.write(file, encoding="utf-8", xml_declaration=True)

def create_pull_request(repo_name, branch_name, changeset_file_path, js_file_path, github_token):
    """Create a GitHub Pull Request with the newly generated XML file."""
    try:
        g = Github(github_token)
        repo = g.get_repo(repo_name)

        with open(changeset_file_path, "r") as file:
            changeset_content = file.read()

        # Check if branch already exists
        try:
            existing_branch = repo.get_branch(branch_name)
            print(f"Branch {branch_name} already exists, deleting it first...")
            ref = repo.get_git_ref(f"heads/{branch_name}")
            ref.delete()
        except:
            pass  # Branch doesn't exist, which is fine

        # Create a new branch
        main_branch = repo.get_branch("main")
        ref = repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_branch.commit.sha)

        # Add / commit the file to the branch
        file_path_in_repo = f"json_changesets/{os.path.basename(changeset_file_path)}"
        
        # Check if file already exists
        try:
            existing_file = repo.get_contents(file_path_in_repo, ref=branch_name)
            # Update existing file
            repo.update_file(
                path=file_path_in_repo,
                message=f"Updated {os.path.basename(changeset_file_path)} for {os.path.basename(js_file_path)}",
                content=changeset_content,
                sha=existing_file.sha,
                branch=branch_name
            )
        except:
            # Create new file
            repo.create_file(
                path=file_path_in_repo,
                message=f"Generated {os.path.basename(changeset_file_path)} for {os.path.basename(js_file_path)}",
                content=changeset_content,
                branch=branch_name
            )

        # Create PR
        pr = repo.create_pull(
            title=f"[Auto-Generated] XML Changeset for {os.path.basename(js_file_path)}",
            body=(
                f"This PR was auto-generated from `{os.path.basename(js_file_path)}`.\n\n"
                f"- Generated XML: `{file_path_in_repo}`\n"
                f"- Source JS: `{js_file_path}`\n\n"
                f"Please review the generated changeset and merge if correct."
            ),
            head=branch_name,
            base="main"
        )

        return pr
    
    except Exception as e:
        print(f"Error creating pull request: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Liquibase XML and create a PR.")
    parser.add_argument("--js_file", required=True, help="Path to the .js file.")
    parser.add_argument("--version", required=True, help="Version for the XML changeset.")
    parser.add_argument("--author", required=True, help="Author for the changeset.")
    parser.add_argument("--repo", required=True, help="GitHub repository (e.g., 'owner/repo').")
    parser.add_argument("--branch", required=True, help="Target branch for the PR.")
    parser.add_argument("--token", required=True, help="GitHub token for authentication.")
    args = parser.parse_args()

    try:
        js_file_path = args.js_file
        version = args.version
        author = args.author
        repo_name = args.repo
        branch_name = args.branch
        github_token = args.token

        print(f"Processing JS file: {js_file_path}")
        queries = parse_js_file(js_file_path)
        
        print(f"Generating XML for version: {version}")
        xml_tree = generate_liquibase_xml(version, queries, author)
        
        changeset_file_path = f"json_changesets/{version}.xml"
        print(f"Writing XML to: {changeset_file_path}")
        write_to_file(xml_tree, changeset_file_path)
        
        print(f"Creating pull request...")
        pr = create_pull_request(repo_name, branch_name, changeset_file_path, js_file_path, github_token)
        print(f"Pull Request created successfully: {pr.html_url}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)
