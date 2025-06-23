import argparse
import re
import openai
import os
import xml.etree.ElementTree as ET

# OpenAI API Configuration
openai.api_type = "azure"
openai.api_base = "https://sequoia-engg-openai.openai.azure.com/"  # Replace with your Azure endpoint
openai.api_key = os.environ.get("OPENAI_API_KEY")  # Fetch OpenAI key from environment (set in GitHub Secrets)
openai.api_version = "2024-12-01-preview"

# Liquibase command templates
LOCAL_REFERENCES = {
    "createCollection": """
<changeSet id="{changeset_id}" author="{author}" context="{context}">
    <mongodb:createCollection collectionName="{collection_name}" />
</changeSet>
""",
    "createIndex": """
<changeSet id="{changeset_id}" author="{author}" context="{context}">
    <mongodb:runCommand>
        <mongodb:command><![CDATA[
        {{
            "createIndexes": "{collection_name}",
            "indexes": [
            {{
                "key": {index_key},
                "name": "{index_name}"
            }}
            ]
        }}
        ]]></mongodb:command>
    </mongodb:runCommand>
</changeSet>
""",
    "insertOne": """
<changeSet id="{changeset_id}" author="{author}" context="{context}">
    <mongodb:insertOne collectionName="{collection_name}">
        <mongodb:document><![CDATA[
        {document}
        ]]></mongodb:document>
    </mongodb:insertOne>
</changeSet>
""",
    "insertMany": """
<changeSet id="{changeset_id}" author="{author}" context="{context}">
    <mongodb:insertMany collectionName="{collection_name}">
        <mongodb:documents><![CDATA[
        {documents}
        ]]></mongodb:documents>
    </mongodb:insertMany>
</changeSet>
""",
    "updateOne": """
<changeSet id="{changeset_id}" author="{author}" context="{context}">
    <mongodb:runCommand>
        <mongodb:command><![CDATA[
        {update_payload}
        ]]></mongodb:command>
    </mongodb:runCommand>
</changeSet>
""",
    "updateMany": """
<changeSet id="{changeset_id}" author="{author}" context="{context}">
    <mongodb:runCommand>
        <mongodb:command><![CDATA[
        {update_payload}
        ]]></mongodb:command>
    </mongodb:runCommand>
</changeSet>
""",
    "deleteOne": """
<changeSet id="{changeset_id}" author="{author}" context="{context}">
    <mongodb:runCommand>
        <mongodb:command><![CDATA[
        {delete_payload}
        ]]></mongodb:command>
    </mongodb:runCommand>
</changeSet>
""",
    "deleteMany": """
<changeSet id="{changeset_id}" author="{author}" context="{context}">
    <mongodb:runCommand>
        <mongodb:command><![CDATA[
        {{
            "delete": "{collection_name}",
            "deletes": [
            {{
                "q": {filter_payload},
                "limit": {limit}
            }}
            ]
        }}
        ]]></mongodb:command>
    </mongodb:runCommand>
</changeSet>
""",
    "dropIndex": """
<changeSet id="{changeset_id}" author="{author}" context="{context}">
    <mongodb:dropIndex collectionName="{collection_name}" indexName="{index_name}">
        <mongodb:keys>
        {index_key}
        </mongodb:keys>
    </mongodb:dropIndex>
</changeSet>
""",
    "dropCollections": """
<changeSet id="{changeset_id}" author="{author}" context="{context}">
    <mongodb:dropCollection collectionName="{collection_name}" />
</changeSet>
"""
}

def extract_collection_name_and_command(query):
    """
    Extracts MongoDB collection name and command type from the query.
    """
    commands = [
        "createCollection", "createIndex", "insertOne", "insertMany",
        "updateOne", "updateMany", "deleteOne", "deleteMany", "dropIndex",
        "dropCollections"
    ]

    # Match for db.collection.command() and db.getCollection("collection_name")
    match = re.search(r'db\.(?:getCollection\("([^"]+)"\)|(\w+))\.(\w+)\(', query)
    if match:
        collection_name = match.group(1) or match.group(2)
        command = match.group(3) if match.group(3) in commands else None
        if command:
            return collection_name, command

    return None, None

def validate_syntax_via_local_library(xml_output):
    """
    Validates the Liquibase XML using Python's XML parsing library.
    """
    try:
        ET.fromstring(xml_output)  # Parse the XML structure
        return "✅ Local XML validation passed."
    except ET.ParseError as e:
        return f"❌ Local XML validation failed: {e}"

def generate_liquibase_xml(query, changeset_id, author, context):
    """
    Generates Liquibase XML for a MongoDB query.
    """
    collection_name, command_type = extract_collection_name_and_command(query)
    if not command_type:
        return f"Error: Unable to extract command type from query.", ""

    template = LOCAL_REFERENCES.get(command_type)
    if not template:
        return f"Error: No template found for command `{command_type}`.", ""

    xml_output = template.format(
        changeset_id=changeset_id,
        author=author,
        context=context,
        collection_name=collection_name
    )

    validation_result = validate_syntax_via_local_library(xml_output)
    return validation_result, xml_output

if __name__ == "__main__":
    # CLI argument handling
    parser = argparse.ArgumentParser(description="Convert MongoDB query to Liquibase XML changeset")
    parser.add_argument("--query", required=True, help="MongoDB query (e.g., db.createCollection('test'))")
    parser.add_argument("--changeset-id", required=True, help="Liquibase Changeset ID")
    parser.add_argument("--author", required=True, help="Changeset author name")
    parser.add_argument("--context", required=True, help="Database context name")

    args = parser.parse_args()

    print("Processing MongoDB query into Liquibase XML...")
    validation_result, liquibase_xml = generate_liquibase_xml(
        args.query, args.changeset_id, args.author, args.context
    )

    print("\nValidation Result:\n", validation_result)
    print("\nGenerated XML:\n", liquibase_xml)

    # Append the generated XML to a Liquibase changelog file
    changelog_file = "changeset/changelog.xml"
    with open(changelog_file, "a") as f:
        f.write("\n" + liquibase_xml + "\n")
        f.write("\n")

    print(f"\nLiquibase XML appended to {changelog_file} successfully!")
