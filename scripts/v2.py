import re
import argparse
import os


def correct_json_syntax(json_string):
    """Correct common JSON syntax issues."""
    json_string = re.sub(r'(?<!")\b(\w+)\b\s*:', r'"\1":', json_string)
    json_string = re.sub(r':\s*(?![\[{"])(\w+)', r': "\1"', json_string)
    json_string = json_string.replace("'", '"')
    return json_string


def format_json_string(json_string):
    """Format the JSON string to ensure correct structure."""
    json_string = correct_json_syntax(json_string)
    return json_string.strip()


def generate_changelog(mongodb_query, changeset_id, author_name, context):
    """Generate Liquibase changeset XML content."""
    print(f"Raw MongoDB Query Received: {mongodb_query}")

    mongodb_query = re.sub(r'\s+', ' ', mongodb_query).strip()
    print(f"Normalized MongoDB Query: {mongodb_query}")

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

    # Handle dropCollection
    elif "dropCollection" in mongodb_query or "drop" in mongodb_query:
        match = re.search(r'db\.(?:getCollection\("([^"]+)"\)|([^.]+))\.drop\(\)', mongodb_query)
        if match:
            collection_name = match.group(1) or match.group(2)
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
        raise FileNotFoundError(f"Changelog file '{changelog_path}' does not exist.")

    with open(changelog_path, "r") as f:
        content = f.read()

    # Check if <databaseChangeLog> exists
    if "<databaseChangeLog" not in content or "</databaseChangeLog>" not in content:
        raise ValueError("Invalid changelog structure. Missing <databaseChangeLog> tags.")

    # Append <changeSet> before </databaseChangeLog>
    updated_content = re.sub(
        r"(</databaseChangeLog>)",
        f"\n{changeset_xml.strip()}\n\\1",  # Append before closing </databaseChangeLog>
        content,
        flags=re.DOTALL
    )

    # Write back the updated content to the changelog file
    with open(changelog_path, "w") as f:
        f.write(updated_content)

    print(f"✅ Changeset successfully appended to {changelog_path}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate and append Liquibase XML content from MongoDB query.")
    parser.add_argument("--query", required=True, help="MongoDB query to process and convert.")
    parser.add_argument("--changeset-id", required=True, help="Liquibase Changeset ID.")
    parser.add_argument("--author", required=True, help="Author of the changeset.")
    parser.add_argument("--context", required=True, help="Database context.")
    parser.add_argument("--changelog", default="changelog.xml", help="Path to changelog file to append to.")
    args = parser.parse_args()

    print("🔄 Processing MongoDB query...\n")
    changeset_xml = generate_changelog(
        mongodb_query=args.query,
        changeset_id=args.changeset_id,
        author_name=args.author,
        context=args.context
    )

    if changeset_xml:
        append_to_changelog(changeset_xml, args.changelog)
