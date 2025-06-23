import argparse
import os
import re
import openai
import xml.etree.ElementTree as ET

# OpenAI API Configuration
openai.api_type = "azure"
openai.api_base = "https://sequoia-engg-openai.openai.azure.com/"  # Replace with your Azure endpoint
openai.api_key = os.getenv("OPENAI_API_KEY")  # Fetch OpenAI key from the environment
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
    Extracts the MongoDB collection name and command type from the query.
    Supports commands like `db.createCollection()`, `db.collection.insertMany()`, etc.
    Handles both single and double quotes.
    """
    commands = [
        "createCollection", "createIndex", "insertOne", "insertMany",
        "updateOne", "updateMany", "deleteOne", "deleteMany", "dropIndex",
        "dropCollections"
    ]

    # Match for db.collection.command() and db.getCollection("collection_name")
    match = re.search(r'db\.(?:getCollection\(["\']([^"\']+)["\']\)|(\w+))\.(\w+)\(', query)
    if match:
        collection_name = match.group(1) or match.group(2)
        command = match.group(3) if match.group(3) in commands else None
        if command:
            return collection_name, command

    # Match for db.createCollection("collection_name") or db.createCollection('collection_name')
    match_create_collection = re.search(r'db\.createCollection\(["\']([^"\']+)["\']\)', query)
    if match_create_collection:
        collection_name = match_create_collection.group(1)
        return collection_name, "createCollection"

    # Match for db.dropCollection("collection_name") or db.dropCollection('collection_name')
    match_drop_collection = re.search(r'db\.dropCollection\(["\']([^"\']+)["\']\)', query)
    if match_drop_collection:
        collection_name = match_drop_collection.group(1)
        return collection_name, "dropCollections"

    # No match for any commands
    return None, None


def validate_and_standardize_query(query):
    """
    Standardizes and validates the MongoDB query using OpenAI.
    """
    prompt = f"Standardize the following MongoDB query:\n{query}"
    try:
        response = openai.ChatCompletion.create(
            deployment_id="gpt-4o-Engg-AI-Assitant",
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert in MongoDB query transformation."},
                {"role": "user", "content": prompt},
            ],
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error using OpenAI for standardizing query: {e}"


def append_to_changelog(corrected_xml):
    """
    Append the corrected Liquibase changeset XML to changelog.xml.
    """
    changelog_dir = "changeset"
    changelog_file = os.path.join(changelog_dir, "changelog.xml")

    # Ensure the directory exists
    os.makedirs(changelog_dir, exist_ok=True)

    with open(changelog_file, "a") as f:
        f.write("\n" + corrected_xml + "\n")
    print(f"✅ Successfully appended to {changelog_file}.")


def generate_liquibase_xml(query, changeset_id, author, context):
    """
    Generate Liquibase XML from a MongoDB query.
    """
    collection_name, command_type = extract_collection_name_and_command(query)
    if not command_type or command_type not in LOCAL_REFERENCES:
        return None, f"Error: Unsupported or invalid command in query: {query}"

    # Format the XML based on the command template
    template = LOCAL_REFERENCES[command_type]
    xml_output = template.format(
        changeset_id=changeset_id,
        author=author,
        context=context,
        collection_name=collection_name
    )
    return xml_output, None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Liquibase XML from MongoDB query.")
    parser.add_argument("--query", required=True, help="MongoDB query (e.g., db.collection.insertMany([...]).")
    parser.add_argument("--changeset-id", required=True, help="Liquibase Changeset ID.")
    parser.add_argument("--author", required=True, help="Author of the changeset.")
    parser.add_argument("--context", required=True, help="Database context used in Liquibase.")
    args = parser.parse_args()

    print("Processing query into Liquibase XML...\n")
    liquibase_xml, error = generate_liquibase_xml(args.query, args.changeset_id, args.author, args.context)

    if error:
        print(f"❌ {error}")
        exit(1)

    print(f"✅ Generated Liquibase XML:\n{liquibase_xml}")
    append_to_changelog(liquibase_xml)
