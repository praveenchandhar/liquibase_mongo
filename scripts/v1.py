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


def validate_and_standardize_query(query):
    """
    Validate and standardize MongoDB query via OpenAI.
    """
    prompt = f"Standardize and validate the MongoDB query:\n{query}\nEnsure proper syntax, consistent formatting, and logical correctness."
    try:
        response = openai.ChatCompletion.create(
            deployment_id="gpt-4o-Engg-AI-Assitant",
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert in MongoDB query processing and optimization."},
                {"role": "user", "content": prompt}
            ],
        )
        standardized_query = response['choices'][0]['message']['content'].strip()
        return standardized_query
    except Exception as e:
        return f"Error during OpenAI query validation: {e}"


def validate_syntax_via_openai(xml_output):
    """
    Validate and ensure the syntax of the Liquibase XML output using OpenAI.
    """
    prompt = f"Validate the syntax of this Liquibase XML output:\n{xml_output}\nFix any issues and return the corrected XML."
    try:
        response = openai.ChatCompletion.create(
            deployment_id="gpt-4o-Engg-AI-Assitant",
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert in Liquibase XML syntax validation."},
                {"role": "user", "content": prompt}
            ],
        )
        corrected_xml = response['choices'][0]['message']['content'].strip()
        return corrected_xml
    except Exception as e:
        return f"Error during OpenAI XML validation: {e}"


def extract_collection_name_and_command(query):
    """
    Extract MongoDB collection name and command from the query. Handles both single and double quotes.
    """
    commands = [
        "createCollection", "createIndex", "insertOne", "insertMany",
        "updateOne", "updateMany", "deleteOne", "deleteMany", "dropIndex",
        "dropCollections"
    ]

    match = re.search(r'db\.(?:getCollection\(["\']([^"\']+)["\']\)|(\w+))\.(\w+)\(', query)
    if match:
        collection_name = match.group(1) or match.group(2)
        command = match.group(3) if match.group(3) in commands else None
        if command:
            return collection_name, command

    match_create_collection = re.search(r'db\.createCollection\(["\']([^"\']+)["\']\)', query)
    if match_create_collection:
        collection_name = match_create_collection.group(1)
        return collection_name, "createCollection"

    return None, None


def generate_liquibase_xml(query, changeset_id, author, context):
    """
    Generate Liquibase XML from MongoDB query using local references
    and OpenAI validation.
    """
    # Step 1: Standardize the MongoDB query
    standardized_query = validate_and_standardize_query(query)
    print(f"[DEBUG] Standardized Query: {standardized_query}")

    # Step 2: Extract collection name and command type
    collection_name, command_type = extract_collection_name_and_command(standardized_query)
    if not command_type or command_type not in LOCAL_REFERENCES:
        return None, f"Error: Unsupported command or failed to extract information from query."

    # Step 3: Extract `documents` field for insertMany (if applicable)
    documents = None
    if command_type == "insertMany":
        try:
            # Extract the `documents` array using regex for insertMany
            match = re.search(r"insertMany\(\s*\[(.*)\]\)", standardized_query, re.DOTALL)
            if match:
                documents = match.group(1).strip()
        except Exception as e:
            return None, f"Error extracting documents from query: {e}"

    # Step 4: Format the XML template
    template = LOCAL_REFERENCES[command_type]
    try:
        # Pass `documents` only if it's required
        liquibase_xml = template.format(
            changeset_id=changeset_id,
            author=author,
            context=context,
            collection_name=collection_name,
            # Pass `documents` to insertMany template
            documents=documents if command_type == "insertMany" else ""
        )
    except KeyError as e:
        return None, f"Error: Missing placeholder in template: {e}"

    # Step 5: Validate and correct the Liquibase XML via OpenAI
    corrected_xml = validate_syntax_via_openai(liquibase_xml)
    return corrected_xml, None


def append_to_changelog(corrected_xml):
    """
    Append corrected Liquibase XML to changelog file.
    """
    changelog_dir = "changeset"
    changelog_file = os.path.join(changelog_dir, "changelog.xml")
    os.makedirs(changelog_dir, exist_ok=True)

    with open(changelog_file, "a") as f:
        f.write("\n" + corrected_xml + "\n")
    print(f"✅ XML successfully appended to {changelog_file}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Liquibase XML from MongoDB query.")
    parser.add_argument("--query", required=True, help="MongoDB query to process and convert.")
    parser.add_argument("--changeset-id", required=True, help="Liquibase Changeset ID.")
    parser.add_argument("--author", required=True, help="Author of the changeset.")
    parser.add_argument("--context", required=True, help="Database context.")
    args = parser.parse_args()

    print("🔄 Processing MongoDB query...\n")
    corrected_xml, error = generate_liquibase_xml(args.query, args.changeset_id, args.author, args.context)

    if error:
        print(f"❌ Error: {error}")
        exit(1)

    print(f"✅ Final Liquibase XML:\n{corrected_xml}")
    append_to_changelog(corrected_xml)
