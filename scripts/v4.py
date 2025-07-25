import os
import re
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

def extract_context_from_content(content):
    """Extract context from the top of the JS file."""
    lines = content.split('\n')[:10]
    first_lines = '\n'.join(lines)
    
    print("DEBUG: Looking for context in first 10 lines:")
    print("=" * 30)
    print(first_lines)
    print("=" * 30)
    
    context_patterns = [
        r'//\s*@?context\s*:?\s*([a-zA-Z0-9_]+)',
        r'/\*\s*@?context\s*:?\s*([a-zA-Z0-9_]+)\s*\*/',
        r'//\s*@?Context\s*:?\s*([a-zA-Z0-9_]+)',
        r'/\*\s*@?Context\s*:?\s*([a-zA-Z0-9_]+)\s*\*/',
        r'//\s*DATABASE\s*:?\s*([a-zA-Z0-9_]+)',
        r'/\*\s*DATABASE\s*:?\s*([a-zA-Z0-9_]+)\s*\*/',
    ]
    
    for pattern in context_patterns:
        match = re.search(pattern, first_lines, re.IGNORECASE)
        if match:
            context = match.group(1)
            print(f"DEBUG: Found context: '{context}' using pattern: {pattern}")
            return context
    
    print("DEBUG: No context found in file, using default 'dev'")
    return "dev"

def extract_mongodb_operations(content):
    """Extract MongoDB operations from JS content."""
    operations = []
    
    print("DEBUG: Looking for MongoDB operations...")
    
    # Remove comments first
    content_no_comments = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
    content_no_comments = re.sub(r'/\*.*?\*/', '', content_no_comments, flags=re.DOTALL)
    
    patterns = {
        'insertMany': r'db\.getCollection\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.insertMany\s*\(\s*(\[.*?\])\s*\)\s*;?',
        'insertOne': r'db\.getCollection\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.insertOne\s*\(\s*(\{.*?\})\s*\)\s*;?',
        'updateOne': r'db\.getCollection\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.updateOne\s*\(\s*(\{.*?\})\s*,\s*(\{.*?\})\s*(?:,\s*(\{.*?\}))?\s*\)\s*;?',
        'updateMany': r'db\.getCollection\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.updateMany\s*\(\s*(\{.*?\})\s*,\s*(\{.*?\})\s*(?:,\s*(\{.*?\}))?\s*\)\s*;?',
        'deleteOne': r'db\.getCollection\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.deleteOne\s*\(\s*(\{.*?\})\s*(?:,\s*(\{.*?\}))?\s*\)\s*;?',
        'deleteMany': r'db\.getCollection\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.deleteMany\s*\(\s*(\{.*?\})\s*(?:,\s*(\{.*?\}))?\s*\)\s*;?',
        'createIndex': r'db\.getCollection\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.createIndex\s*\(\s*(\{.*?\})\s*(?:,\s*(\{.*?\}))?\s*\)\s*;?',
        'dropIndex': r'db\.getCollection\s*\(\s*["\']([^"\']+)["\']\s*\)\s*\.dropIndex\s*\(\s*(["\'][^"\']*["\']|\{.*?\})\s*\)\s*;?',
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
            
            if operation_type in ['insertMany', 'insertOne']:
                operation['documents'] = groups[1]
            elif operation_type in ['updateOne', 'updateMany']:
                operation['filter'] = groups[1]
                operation['update'] = groups[2]
                operation['options'] = groups[3] if len(groups) > 3 and groups[3] else None
            elif operation_type in ['deleteOne', 'deleteMany']:
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
                operation['collection'] = groups[0] if groups[0] else groups[1]
            
            operations.append(operation)
            print(f"DEBUG: Found {operation_type} operation on collection '{operation['collection']}'")
    
    print(f"DEBUG: Total operations found: {len(operations)}")
    return operations

def clean_json_for_xml(json_str):
    """Clean and format JSON for XML inclusion."""
    if not json_str:
        return "{}"
    return json_str.strip()

def extract_version_number(version_string):
    """Extract numeric part from version string."""
    # Look for numbers in the version string
    match = re.search(r'(\d+)', version_string)
    if match:
        return match.group(1)
    return "1"  # Default fallback

def generate_liquibase_xml(version, operations, author_name, context):
    """Generate Liquibase XML with decimal changeset IDs like 4.1, 4.2, 4.3."""
    
    # Extract base number from version
    base_version_num = extract_version_number(version)
    
    # Build XML manually to control CDATA sections and avoid HTML encoding
    xml_lines = []
    xml_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    xml_lines.append('<databaseChangeLog')
    xml_lines.append('    xmlns="http://www.liquibase.org/xml/ns/dbchangelog"')
    xml_lines.append('    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"')
    xml_lines.append('    xmlns:mongodb="http://www.liquibase.org/xml/ns/dbchangelog-ext"')
    xml_lines.append('    xsi:schemaLocation="')
    xml_lines.append('        http://www.liquibase.org/xml/ns/dbchangelog')
    xml_lines.append('        http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-4.5.xsd')
    xml_lines.append('        http://www.liquibase.org/xml/ns/dbchangelog-ext')
    xml_lines.append('        http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-ext.xsd">')

    if not operations:
        # Create a single changeset with comment
        xml_lines.append(f'    <changeSet id="{base_version_num}" author="{author_name}" context="{context}">')
        xml_lines.append('        <!-- No MongoDB operations found in the JS file -->')
        xml_lines.append('    </changeSet>')
    else:
        # Create separate changeSet for each operation with decimal IDs
        for i, operation in enumerate(operations):
            op_type = operation['type']
            collection = operation['collection']
            
            # Use decimal notation for changeset IDs
            if len(operations) == 1:
                changeset_id = base_version_num
            else:
                changeset_id = f"{base_version_num}.{i+1}"  # e.g., "4.1", "4.2", "4.3"
            
            xml_lines.append(f'    <changeSet id="{changeset_id}" author="{author_name}" context="{context}">')
            
            try:
                if op_type == 'createCollection':
                    xml_lines.append(f'        <mongodb:createCollection collectionName="{collection}" />')
                    
                elif op_type == 'createIndex':
                    index_key = clean_json_for_xml(operation['index_key'])
                    index_name = f"{collection}_index_{i+1}"
                    
                    xml_lines.append('        <mongodb:runCommand>')
                    xml_lines.append('            <mongodb:command><![CDATA[')
                    xml_lines.append('            {')
                    xml_lines.append(f'                "createIndexes": "{collection}",')
                    xml_lines.append('                "indexes": [')
                    xml_lines.append('                    {')
                    xml_lines.append(f'                        "key": {index_key},')
                    xml_lines.append(f'                        "name": "{index_name}"')
                    xml_lines.append('                    }')
                    xml_lines.append('                ]')
                    xml_lines.append('            }')
                    xml_lines.append('            ]]></mongodb:command>')
                    xml_lines.append('        </mongodb:runCommand>')
                    
                elif op_type == 'insertOne':
                    doc_content = clean_json_for_xml(operation['documents'])
                    xml_lines.append(f'        <mongodb:insertOne collectionName="{collection}">')
                    xml_lines.append('            <mongodb:document><![CDATA[')
                    xml_lines.append(f'            {doc_content}')
                    xml_lines.append('            ]]></mongodb:document>')
                    xml_lines.append('        </mongodb:insertOne>')
                    
                elif op_type == 'insertMany':
                    docs_content = clean_json_for_xml(operation['documents'])
                    if not docs_content.strip().startswith('['):
                        docs_content = f"[{docs_content}]"
                    
                    xml_lines.append(f'        <mongodb:insertMany collectionName="{collection}">')
                    xml_lines.append('            <mongodb:documents><![CDATA[')
                    xml_lines.append(f'            {docs_content}')
                    xml_lines.append('            ]]></mongodb:documents>')
                    xml_lines.append('        </mongodb:insertMany>')
                    
                elif op_type in ['updateOne', 'updateMany']:
                    filter_json = clean_json_for_xml(operation['filter'])
                    update_json = clean_json_for_xml(operation['update'])
                    multi = "true" if op_type == "updateMany" else "false"
                    
                    xml_lines.append('        <mongodb:runCommand>')
                    xml_lines.append('            <mongodb:command><![CDATA[')
                    xml_lines.append('            {')
                    xml_lines.append(f'                "update": "{collection}",')
                    xml_lines.append('                "updates": [')
                    xml_lines.append('                    {')
                    xml_lines.append(f'                        "q": {filter_json},')
                    xml_lines.append(f'                        "u": {update_json},')
                    xml_lines.append(f'                        "multi": {multi}')
                    xml_lines.append('                    }')
                    xml_lines.append('                ]')
                    xml_lines.append('            }')
                    xml_lines.append('            ]]></mongodb:command>')
                    xml_lines.append('        </mongodb:runCommand>')
                    
                elif op_type in ['deleteOne', 'deleteMany']:
                    filter_json = clean_json_for_xml(operation['filter'])
                    limit = 1 if op_type == "deleteOne" else 0
                    
                    xml_lines.append('        <mongodb:runCommand>')
                    xml_lines.append('            <mongodb:command><![CDATA[')
                    xml_lines.append('            {')
                    xml_lines.append(f'                "delete": "{collection}",')
                    xml_lines.append('                "deletes": [')
                    xml_lines.append('                    {')
                    xml_lines.append(f'                        "q": {filter_json},')
                    xml_lines.append(f'                        "limit": {limit}')
                    xml_lines.append('                    }')
                    xml_lines.append('                ]')
                    xml_lines.append('            }')
                    xml_lines.append('            ]]></mongodb:command>')
                    xml_lines.append('        </mongodb:runCommand>')
                    
                elif op_type == 'dropIndex':
                    index_spec = operation['index_spec']
                    if index_spec.startswith('"') or index_spec.startswith("'"):
                        index_name = index_spec.strip('"\'')
                        xml_lines.append(f'        <mongodb:dropIndex collectionName="{collection}" indexName="{index_name}" />')
                    else:
                        xml_lines.append(f'        <mongodb:dropIndex collectionName="{collection}">')
                        xml_lines.append('            <mongodb:keys><![CDATA[')
                        xml_lines.append(f'            {clean_json_for_xml(index_spec)}')
                        xml_lines.append('            ]]></mongodb:keys>')
                        xml_lines.append('        </mongodb:dropIndex>')
                    
                elif op_type == 'dropCollection':
                    xml_lines.append(f'        <mongodb:dropCollection collectionName="{collection}" />')
                    
            except Exception as e:
                print(f"DEBUG: Error processing operation {i+1}: {str(e)}")
                xml_lines.append(f'        <!-- Failed to process {op_type} operation: {str(e)} -->')
            
            xml_lines.append('    </changeSet>')

    xml_lines.append('</databaseChangeLog>')
    return '\n'.join(xml_lines)

def write_to_file(xml_content, output_file_path):
    """Write XML content to a file."""
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    
    with open(output_file_path, "w", encoding="utf-8") as file:
        file.write(xml_content)

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
    args = parser.parse_args()

    try:
        js_file_path = args.js_file
        version = args.version
        author = args.author
        repo_name = args.repo
        branch_name = args.branch
        github_token = args.token

        print(f"Processing JS file: {js_file_path}")
        content = parse_js_file(js_file_path)
        
        print(f"Extracting context from file...")
        context = extract_context_from_content(content)
        print(f"Using context: '{context}'")
        
        print(f"Extracting MongoDB operations...")
        operations = extract_mongodb_operations(content)
        
        print(f"Generating XML for version: {version}")
        xml_content = generate_liquibase_xml(version, operations, author, context)
        
        changeset_file_path = f"json_changesets/{version}.xml"
        print(f"Writing XML to: {changeset_file_path}")
        write_to_file(xml_content, changeset_file_path)
        
        print(f"Creating pull request...")
        pr = create_pull_request(repo_name, branch_name, changeset_file_path, js_file_path, github_token)
        print(f"Pull Request created successfully: {pr.html_url}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)
