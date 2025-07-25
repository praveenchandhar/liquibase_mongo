import os
import re
import xml.etree.ElementTree as ET
import argparse
from github import Github

def parse_js_file(js_file_path):
    """Parse MongoDB queries from a .js file."""
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
    tree = ET.ElementTree(xml_tree)
    with open(output_file_path, "wb") as file:
        tree.write(file, encoding="utf-8", xml_declaration=True)

def create_pull_request(repo_name, branch_name, changeset_file_path, js_file_path, github_token):
    """Create a GitHub Pull Request with the newly generated XML file."""
    g = Github(github_token)
    repo = g.get_repo(repo_name)

    with open(changeset_file_path, "r") as file:
        changeset_content = file.read()

    # Create a new branch
    ref = repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=repo.get_branch("main").commit.sha)

    # Add / commit the file to the branch
    file_path_in_repo = os.path.basename(changeset_file_path)
    repo.create_file(
        path=f"json_changesets/{file_path_in_repo}",
        message=f"Generated {os.path.basename(changeset_file_path)} for {os.path.basename(js_file_path)}",
        content=changeset_content,
        branch=branch_name
    )

    # Create PR
    pr = repo.create_pull(
        title=f"[Auto-Generated] XML Changeset for {os.path.basename(js_file_path)}",
        body=(
            f"This PR was auto-generated from `{os.path.basename(js_file_path)}`.\n\n"
            f"- Generated XML: `json_changesets/{os.path.basename(changeset_file_path)}`\n"
            f"- Source JS: `{js_file_path}`"
        ),
        head=branch_name,
        base="main"
    )

    return pr

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Liquibase XML and create a PR.")
    parser.add_argument("--js_file", required=True, help="Path to the .js file.")
    parser.add_argument("--version", required=True, help="Version for the XML changeset.")
    parser.add_argument("--author", required=True, help="Author for the changeset.")
    parser.add_argument("--repo", required=True, help="GitHub repository (e.g., 'owner/repo').")
    parser.add_argument("--branch", required=True, help="Target branch for the PR.")
    parser.add_argument("--token", required=True, help="GitHub token for authentication.")
    args = parser.parse_args()

    js_file_path = args.js_file
    version = args.version
    author = args.author
    repo_name = args.repo
    branch_name = args.branch
    github_token = args.token

    queries = parse_js_file(js_file_path)
    xml_tree = generate_liquibase_xml(version, queries, author)
    changeset_file_path = f"json_changesets/{version}.xml"
    write_to_file(xml_tree, changeset_file_path)
    pr = create_pull_request(repo_name, branch_name, changeset_file_path, js_file_path, github_token)
    print(f"Pull Request created successfully: {pr.html_url}")
