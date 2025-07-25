import os
import re
import xml.etree.ElementTree as ET
import xml.dom.minidom
import argparse
from github import Github

def parse_js_file(js_file_path):
    """Parse MongoDB queries from a .js file."""
    if not os.path.exists(js_file_path):
        raise FileNotFoundError(f"JS file not found: {js_file_path}")
    
    with open(js_file_path, "r", encoding="utf-8") as file:
        content = file.read()
        print(f"DEBUG: JS file content ({len(content)} characters):")
        print("=" * 50)
        print(content)
        print("=" * 50)
        return content

def extract_mongodb_operations(content):
    """Extract MongoDB operations from JS content - Enhanced version."""
    operations = []
    
    print("DEBUG: Looking for MongoDB operations...")
    
    # Remove comments first
    content_no_comments = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
    content_no_comments = re.sub(r'/\*.*?\*/', '', content_no_comments, flags=re.DOTALL)
    
    # Define patterns for different operations
    patterns = {
        # Insert operations
        'insertMany': r'db\.getCollection\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.insertMany\s*\(\s*(\[.*?\])\s*\)\s*;?',
        'insertOne': r'db\.getCollection\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.insertOne\s*\(\s*(\{.*?\})\s*\)\s*;?',
        'insert': r'db\.getCollection\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.insert\s*\(\s*(\{.*?\}|\[.*?\])\s*\)\s*;?',
        
        # Update operations  
        'updateOne': r'db\.getCollection\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.updateOne\s*\(\s*(\{.*?\})\s*,\s*(\{.*?\})\s*(?:,\s*(\{.*?\}))?\s*\)\s*;?',
        'updateMany': r'db\.getCollection\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.updateMany\s*\(\s*(\{.*?\})\s*,\s*(\{.*?\})\s*(?:,\s*(\{.*?\}))?\s*\)\s*;?',
        'replaceOne': r'db\.getCollection\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.replaceOne\s*\(\s*(\{.*?\})\s*,\s*(\{.*?\})\s*(?:,\s*(\{.*?\}))?\s*\)\s*;?',
        
        # Delete operations
        'deleteOne': r'db\.getCollection\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.deleteOne\s*\(\s*(\{.*?\})\s*(?:,\s*(\{.*?\}))?\s*\)\s*;?',
        'deleteMany': r'db\.getCollection\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.deleteMany\s*\(\s*(\{.*?\})\s*(?:,\s*(\{.*?\}))?\s*\)\s*;?',
        'remove': r'db\.getCollection\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.remove\s*\(\s*(\{.*?\})\s*(?:,\s*(\{.*?\}))?\s*\)\s*;?',
        
        # Index operations
        'createIndex': r'db\.getCollection\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.createIndex\s*\(\s*(\{.*?\})\s*(?:,\s*(\{.*?\}))?\s*\)\s*;?',
        'dropIndex': r'db\.getCollection\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.dropIndex\s*\(\s*(["\'][^"\']*["\']|\{.*?\})\s*\)\s*;?',
        
        # Collection operations
        'createCollection': r'db\.createCollection\s*\(\s*["\']([^"\']+)["\']\s*(?:,\s*(\{.*?\}))?\s*\)\s*;?',
        'dropCollection': r'db\.getCollection\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.drop\s*\(\s*\)\s*;?|db\.([^.]+)\.drop\s*\(\s*\)\s*;?',
    }
    
    for operation_type, pattern in patterns.items():
        for match in re.finditer(pattern, content_no_comments, re.DOTALL):
            groups = match.groups()
            
            operation = {
                'type': operation_type,
                'collection': groups[0],
                'raw_match': match.group(0)
            }
            
            # Handle different parameter structures
            if operation_type in ['insertMany', 'insertOne', 'insert']:
                operation['documents'] = groups[1]
            elif operation_type in ['updateOne', 'updateMany', 'replaceOne']:
                operation['filter'] = groups[1]
                operation['update'] = groups[2]
                operation['options'] = groups[3] if len(groups) > 3 and groups[3] else None
            elif operation_type in ['deleteOne', 'deleteMany', 'remove']:
                operation['filter'] = groups[1]
                operation['options'] = groups[2] if len(groups) > 2 and groups[2] else None
            elif operation_type == 'createIndex':
                operation['index_key'] = groups[1]
                operation['options'] = groups[2] if len(groups) > 2 and groups[2] else None
            elif operation_type == 'dropIndex':
                operation['index_spec'] = groups[1]
            elif operation_type == 'createCollection':
                operation['options'] = groups[1] if len(groups) > 1 and groups[1] else None
            elif operation_type == 'dropCollection':
                # Handle both db.collection.drop() and db.getCollection("name").drop()
                operation['collection'] = groups[0] if groups[0] else groups[1]
            
            operations.append(operation)
            print(f"DEBUG: Found {operation_type} operation on collection '{operation['collection']}'")
    
    print(f"DEBUG: Total operations found: {len(operations)}")
    return operations

def clean_json_for_xml(json_str):
    """Clean and format JSON for XML inclusion."""
    if not json_str:
        return "{}"
    # Remove extra whitespace but preserve structure
    return json_str.strip()

def extract_index_name(options_str):
    """Extract index name from options string."""
    if not options_str:
        return None
    # Look for name field in options
    name_match = re.search(r'["\']?name["\']?\s*:\s*["\']([^"\']+)["\']', options_str)
    return name_match.group(1) if name_match else None

def generate_liquibase_xml(version, operations, author_name, context="dev"):
    """Generate Liquibase XML from MongoDB operations following reference structure."""
    root = ET.Element("databaseChangeLog")
    root.set("xmlns", "http://www.liquibase.org/xml/ns/dbchangelog")
    root.set("xmlns:mongodb", "http://www.liquibase.org/xml/ns/mongodb")

    if not operations:
        # Create a single changeset with comment
        changeset = ET.SubElement(root, "changeSet")
        changeset.set("id", version)
        changeset.set("author", author_name)
        changeset.set("context", context)
        comment = ET.Comment(" No MongoDB operations found in the JS file ")
        changeset.append(comment)
        return root

    # Create separate changeSet for each operation
    for i, operation in enumerate(operations):
        op_type = operation['type']
        collection = operation['collection']
        changeset_id = f"{version}_{i+1}" if len(operations) > 1 else version
        
        changeset = ET.SubElement(root, "changeSet")
        changeset.set("id", changeset_id)
        changeset.set("author", author_name)
        changeset.set("context", context)
        
        try:
            if op_type == 'createCollection':
                create_collection = ET.SubElement(changeset, "mongodb:createCollection")
                create_collection.set("collectionName", collection)
                
            elif op_type == 'createIndex':
                run_command = ET.SubElement(changeset, "mongodb:runCommand")
                command = ET.SubElement(run_command, "mongodb:command")
                
                index_key = clean_json_for_xml(operation['index_key'])
                index_name = extract_index_name(operation.get('options', '')) or f"{collection}_index_{i+1}"
                
                command_json = f'''{{
    "createIndexes": "{collection}",
    "indexes": [
        {{
            "key": {index_key},
            "name": "{index_name}"
        }}
    ]
}}'''
                command.text = f"\n        {command_json}\n        "
                
            elif op_type == 'insertOne':
                insert_one = ET.SubElement(changeset, "mongodb:insertOne")
                insert_one.set("collectionName", collection)
                document = ET.SubElement(insert_one, "mongodb:document")
                
                doc_content = clean_json_for_xml(operation['documents'])
                document.text = f"\n        {doc_content}\n        "
                
            elif op_type in ['insertMany', 'insert']:
                insert_many = ET.SubElement(changeset, "mongodb:insertMany")
                insert_many.set("collectionName", collection)
                documents = ET.SubElement(insert_many, "mongodb:documents")
                
                docs_content = clean_json_for_xml(operation['documents'])
                # Ensure it's an array
                if not docs_content.strip().startswith('['):
                    docs_content = f"[{docs_content}]"
                documents.text = f"\n        {docs_content}\n        "
                
            elif op_type in ['updateOne', 'updateMany']:
                run_command = ET.SubElement(changeset, "mongodb:runCommand")
                command = ET.SubElement(run_command, "mongodb:command")
                
                filter_json = clean_json_for_xml(operation['filter'])
                update_json = clean_json_for_xml(operation['update'])
                multi = "true" if op_type == "updateMany" else "false"
                
                update_payload = f'''{{
    "update": "{collection}",
    "updates": [
        {{
            "q": {filter_json},
            "u": {update_json},
            "multi": {multi}
        }}
    ]
}}'''
                command.text = f"\n        {update_payload}\n        "
                
            elif op_type == 'replaceOne':
                run_command = ET.SubElement(changeset, "mongodb:runCommand")
                command = ET.SubElement(run_command, "mongodb:command")
                
                filter_json = clean_json_for_xml(operation['filter'])
                replacement_json = clean_json_for_xml(operation['update'])
                
                replace_payload = f'''{{
    "findAndModify": "{collection}",
    "query": {filter_json},
    "update": {replacement_json},
    "new": true
}}'''
                command.text = f"\n        {replace_payload}\n        "
                
            elif op_type in ['deleteOne', 'deleteMany', 'remove']:
                run_command = ET.SubElement(changeset, "mongodb:runCommand")
                command = ET.SubElement(run_command, "mongodb:command")
                
                filter_json = clean_json_for_xml(operation['filter'])
                limit = 1 if op_type == "deleteOne" else 0
                
                delete_payload = f'''{{
    "delete": "{collection}",
    "deletes": [
        {{
            "q": {filter_json},
            "limit": {limit}
        }}
    ]
}}'''
                command.text = f"\n        {delete_payload}\n        "
                
            elif op_type == 'dropIndex':
                drop_index = ET.SubElement(changeset, "mongodb:dropIndex")
                drop_index.set("collectionName", collection)
                
                index_spec = operation['index_spec']
                # Extract index name if it's a string
                if index_spec.startswith('"') or index_spec.startswith("'"):
                    index_name = index_spec.strip('"\'')
                    drop_index.set("indexName", index_name)
                else:
                    # It's a key specification
                    keys = ET.SubElement(drop_index, "mongodb:keys")
                    keys.text = f"\n        {clean_json_for_xml(index_spec)}\n        "
                
            elif op_type == 'dropCollection':
                drop_collection = ET.SubElement(changeset, "mongodb:dropCollection")
                drop_collection.set("collectionName", collection)
                
        except Exception as e:
            print(f"DEBUG: Error processing operation {i+1}: {str(e)}")
            error_comment = ET.Comment(f" Failed to process {op_type} operation: {str(e)} ")
            changeset.append(error_comment)

    return root

def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, encoding='unicode')
    reparsed = xml.dom.minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ", encoding=None)

def write_to_file(xml_tree, output_file_path):
    """Write XML tree to a file with proper formatting."""
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    
    pretty_xml = prettify_xml(xml_tree)
    
    # Remove extra empty lines that minidom adds
    lines = pretty_xml.split('\n')
    cleaned_lines = []
    for line in lines:
        if line.strip():
            cleaned_lines.append(line)
    
    pretty_xml = '\n'.join(cleaned_lines) + '\n'
    
    with open(output_file_path, "w", encoding="utf-8") as file:
        file.write(pretty_xml)

def create_pull_request(repo_name, branch_name, changeset_file_path, js_file_path, github_token):
    """Create a GitHub Pull Request with the newly generated XML file."""
    try:
        g = Github(github_token)
        repo = g.get_repo(repo_name)

        with open(changeset_file_path, "r", encoding="utf-8") as file:
            changeset_content = file.read()

        # Check if branch already exists
        try:
            existing_branch = repo.get_branch(branch_name)
            print(f"Branch {branch_name} already exists, deleting it first...")
            ref = repo.get_git_ref(f"heads/{branch_name}")
            ref.delete()
        except:
            pass

        # Create a new branch
        main_branch = repo.get_branch("main")
        ref = repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_branch.commit.sha)

        # Add / commit the file to the branch
        file_path_in_repo = f"json_changesets/{os.path.basename(changeset_file_path)}"
        
        try:
            existing_file = repo.get_contents(file_path_in_repo, ref=branch_name)
            repo.update_file(
                path=file_path_in_repo,
                message=f"Updated {os.path.basename(changeset_file_path)} for {os.path.basename(js_file_path)}",
                content=changeset_content,
                sha=existing_file.sha,
                branch=branch_name
            )
        except:
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
                f"Please review the generated changeset and merge if correct.\n\n"
                f"### Generated XML Preview:\n"
                f"```xml\n{changeset_content}\n```"
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
    parser.add_argument("--context", default="dev", help="Context for the changeset (default: dev).")
    args = parser.parse_args()

    try:
        js_file_path = args.js_file
        version = args.version
        author = args.author
        repo_name = args.repo
        branch_name = args.branch
        github_token = args.token
        context = args.context

        print(f"Processing JS file: {js_file_path}")
        content = parse_js_file(js_file_path)
        
        print(f"Extracting MongoDB operations...")
        operations = extract_mongodb_operations(content)
        
        print(f"Generating XML for version: {version}")
        xml_tree = generate_liquibase_xml(version, operations, author, context)
        
        changeset_file_path = f"json_changesets/{version}.xml"
        print(f"Writing XML to: {changeset_file_path}")
        write_to_file(xml_tree, changeset_file_path)
        
        print(f"Creating pull request...")
        pr = create_pull_request(repo_name, branch_name, changeset_file_path, js_file_path, github_token)
        print(f"Pull Request created successfully: {pr.html_url}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)
