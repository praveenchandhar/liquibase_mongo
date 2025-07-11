import re
import argparse
import os
import ast
import json
import xml.etree.ElementTree as ET


def get_next_changeset_id(changelog_path):
    """Get the next changeset ID to follow the pattern 1.1, 1.2, 1.3."""
    if not os.path.exists(changelog_path):
        return "1.1"  # Start at 1.1 if the file doesn't exist

    # Parse the XML to extract all changeset IDs
    tree = ET.parse(changelog_path)
    root = tree.getroot()

    # Liquibase namespaces need to be handled
    namespace = "http://www.liquibase.org/xml/ns/dbchangelog"
    ET.register_namespace('', namespace)

    changeset_minor_ids = []
    for changeset in root.findall(f'.//{{{namespace}}}changeSet'):
        changeset_id = changeset.get("id")
        if changeset_id and changeset_id.startswith("1."):
            try:
                # Extract only the minor version (after "1.")
                minor_id = int(changeset_id.split(".")[1])
                changeset_minor_ids.append(minor_id)
            except (ValueError, IndexError):
                continue  # Ignore invalid or improperly formatted IDs

    if changeset_minor_ids:
        # Increment the highest minor version
        next_minor_id = max(changeset_minor_ids) + 1
        return f"1.{next_minor_id}"
    else:
        return "1.1"  # Start at 1.1 by default


def correct_json_syntax(json_string):
    """Correct common JSON syntax issues."""
    json_string = re.sub(r'(?<!")\b(\w+)\b\s*:', r'"\1":', json_string)
    json_string = re.sub(r':\s*(?![\[{"])(\w+)', r': "\1"', json_string)
    json_string = json_string.replace("'", '"')
    return json_string


def generate_changelog(mongodb_query, changeset_id, author_name, context):
    """Generate Liquibase changeset XML content based on MongoDB query."""
    mongodb_query = re.sub(r'\s+', ' ', mongodb_query).strip()

    xml_content = ""

    # Handle createCollection
    if "createCollection" in mongodb_query:
        match = re.search(r'createCollection\("([^"]+)"', mongodb_query)
        if match:
            collection_name = match.group(1)
            xml_content = f"""
<changeSet id="{changeset_id}" author="{author_name}" context="{context}">
    <mongodb:createCollection collectionName="{collection_name}" />
</changeSet>
"""

    # Add support for other MongoDB commands as per your requirements...
    
    # Add support for other MongoDB commands as per your requirements...
    # Handle dropCollection
    elif "dropCollection" in mongodb_query:
        match = re.search(r'db\.dropCollection\("([^"]+)"\)', mongodb_query)
        if match:
            collection_name = match.group(1)
            xml_content = f"""
<changeSet id="{changeset_id}" author="{author_name}" context="{context}">
    <mongodb:dropCollection collectionName="{collection_name}" />
</changeSet>
"""
    # Handle insertOne
    elif "insertOne" in mongodb_query:
        match = re.search(r'db\.(?:getCollection\("([^"]+)"\)|([^.]+))\.insertOne\((.*?)\)', mongodb_query, re.DOTALL)
        if match:
            collection_name = match.group(1) or match.group(2)
            document = match.group(3).strip()
            document = correct_json_syntax(document)
            xml_content = f"""
<changeSet id="{changeset_id}" author="{author_name}" context="{context}">
    <mongodb:insertOne collectionName="{collection_name}">
        <mongodb:document><![CDATA[
            {document}
        ]]></mongodb:document>
    </mongodb:insertOne>
</changeSet>
"""
    # Handle insertMany
    elif "insertMany" in mongodb_query:
        match = re.search(r'db\.(?:getCollection\("([^"]+)"\)|([^.]+))\.insertMany\((.*?)\)', mongodb_query, re.DOTALL)
        if match:
            collection_name = match.group(1) or match.group(2)
            documents = match.group(3).strip()
            documents = correct_json_syntax(documents)
            xml_content = f"""
<changeSet id="{changeset_id}" author="{author_name}" context="{context}">
    <mongodb:insertMany collectionName="{collection_name}">
        <mongodb:documents><![CDATA[
            {documents}
        ]]></mongodb:documents>
    </mongodb:insertMany>
</changeSet>
"""
    # Handle updateOne and updateMany
    elif "updateOne" in mongodb_query or "updateMany" in mongodb_query:
        operation = "updateOne" if "updateOne" in mongodb_query else "updateMany"
        match = re.search(r'db\.(?:getCollection\("([^"]+)"\)|([^.]+))\.' + operation + r'\((.*?),\s*(.*?)\)', mongodb_query, re.DOTALL)
        if match:
            collection_name = match.group(1) or match.group(2)
            query_string = match.group(3).strip()
            update_string = match.group(4).strip()
            query_string = correct_json_syntax(query_string)
            update_string = correct_json_syntax(update_string)
            xml_content = f"""
<changeSet id="{changeset_id}" author="{author_name}" context="{context}">
    <mongodb:runCommand>
        <mongodb:command><![CDATA[
            {{
                "update": "{collection_name}",
                "updates": [
                    {{
                        "q": {query_string},
                        "u": {update_string},
                        "upsert": false,
                        "multi": {"true" if operation == "updateMany" else "false"}
                    }}
                ]
            }}
        ]]></mongodb:command>
    </mongodb:runCommand>
</changeSet>
"""
    # Handle deleteOne and deleteMany
    elif "deleteOne" in mongodb_query or "deleteMany" in mongodb_query:
        operation = "deleteOne" if "deleteOne" in mongodb_query else "deleteMany"
        match = re.search(r'db\.(?:getCollection\("([^"]+)"\)|([^.]+))\.' + operation + r'\((.*?)\)', mongodb_query, re.DOTALL)
        if match:
            collection_name = match.group(1) or match.group(2)
            query_string = match.group(3).strip()
            query_string = correct_json_syntax(query_string)
            limit = 1 if operation == "deleteOne" else 0
            xml_content = f"""
<changeSet id="{changeset_id}" author="{author_name}" context="{context}">
    <mongodb:runCommand>
        <mongodb:command><![CDATA[
            {{
                "delete": "{collection_name}",
                "deletes": [
                    {{
                        "q": {query_string},
                        "limit": {limit}
                    }}
                ]
            }}
        ]]></mongodb:command>
    </mongodb:runCommand>
</changeSet>
"""
    else:
        print("Error: Unsupported MongoDB command or invalid query.")
        return None
    print(f"Generated XML Content:\n{xml_content.strip()}")

    return xml_content.strip()


def append_to_changelog(changeset_xml, changelog_path="changeset/changelog.xml"):
    """Append the generated <changeSet> block inside <databaseChangeLog>."""
    if not os.path.exists(changelog_path):
        # Create a new changelog XML file if it doesn't already exist
        with open(changelog_path, "w") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog">\n</databaseChangeLog>\n')

    print(f"Resolved changelog file path: {changelog_path}")

    with open(changelog_path, "r") as f:
        content = f.read()

    # Verify and append new changeSet
    updated_content = re.sub(
        r"(</databaseChangeLog>)",
        f"\n{changeset_xml.strip()}\n\\1",
        content,
        flags=re.DOTALL,
    )

    # Write back the updated content
    with open(changelog_path, "w") as f:
        f.write(updated_content)

    print(f"✅ Changeset successfully appended to {changelog_path}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate and append Liquibase XML content from MongoDB query.")
    parser.add_argument("--query", required=True, help="MongoDB query to process and convert.")
    parser.add_argument("--author", required=True, help="Author of the changeset.")
    parser.add_argument("--context", required=True, help="Database context.")
    parser.add_argument("--changelog", default="changeset/changelog.xml", help="Path to changelog file to append to.")
    args = parser.parse_args()

    print("🔄 Processing MongoDB query...\n")

    # Dynamically calculate the next changeset ID
    changeset_id = get_next_changeset_id(args.changelog)
    print(f"Next changeset ID: {changeset_id}")

    # Generate the changeset using the query
    changeset_xml = generate_changelog(
        mongodb_query=args.query,
        changeset_id=changeset_id,
        author_name=args.author,
        context=args.context
    )

    if changeset_xml:
        append_to_changelog(changeset_xml, args.changelog)
    else:
        print("❌ Failed: The provided query could not be processed.")
