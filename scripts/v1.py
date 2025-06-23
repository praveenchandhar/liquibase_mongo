import re
import openai
import os
import xml.etree.ElementTree as ET

# OpenAI API Configuration
openai.api_type = "azure"
openai.api_base = "https://sequoia-engg-openai.openai.azure.com/"  # Replace with your Azure endpoint
openai.api_key = "FdGJdU7Uvx6eAwZZPNZ9J8zWI8dprYxRm64BisoNDqF7ncKdf4BhJQQJ99BDACYeBjFXJ3w3AAABACOGtl7F"  # Replace with your key
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
    Supports multiple formats for each command type.
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

    # Match for db.createCollection("collection_name")
    match_create_collection = re.search(r'db\.createCollection\("([^"]+)"\)', query)
    if match_create_collection:
        collection_name = match_create_collection.group(1)
        return collection_name, "createCollection"

    # Match for db.dropCollection("collection_name")
    match_drop_collection = re.search(r'db\.dropCollection\("([^"]+)"\)', query)
    if match_drop_collection:
        collection_name = match_drop_collection.group(1)
        return collection_name, "dropCollections"

    # Match for db.collection_name.drop()
    match_collection_drop = re.search(r'db\.(\w+)\.drop\(\)', query)
    if match_collection_drop:
        collection_name = match_collection_drop.group(1)
        return collection_name, "dropCollections"

    return None, None

def validate_and_standardize_query(query):
    """
    Standardizes and validates the MongoDB query using OpenAI.
    """
    prompt = f"""
    Validate and standardize this MongoDB query:
    Query: {query}
    Ensure collection and commands follow the standard db.collection.<command>() format,
    replacing constructs like db.dropCollection and db.collection.drop() with consistent formatting.
    Convert new Date() to ISO 8601 if present.
    """
    try:
        response = openai.ChatCompletion.create(
            deployment_id="gpt-4o-Engg-AI-Assitant",
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert in normalizing MongoDB queries."},
                {"role": "user", "content": prompt},
            ],
        )
        result = response['choices'][0]['message']['content'].strip()
        return result
    except Exception as e:
        return f"Error using OpenAI for query validation: {e}"

def validate_syntax_via_openai(xml_output):
    """
    Validates the Liquibase XML output syntax using OpenAI.
    """
    prompt = f"""
    Validate and ensure the syntax for the provided Liquibase XML output:
    {xml_output}
    """
    try:
        response = openai.ChatCompletion.create(
            deployment_id="gpt-4o-Engg-AI-Assitant",
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert in Liquibase XML syntax validation."},
                {"role": "user", "content": prompt},
            ],
        )
        validated_result = response['choices'][0]['message']['content'].strip()
        return validated_result
    except Exception as e:
        return f"Error using OpenAI for syntax validation: {e}"

def validate_syntax_via_local_library(xml_output):
    """
    Validates the Liquibase XML output syntax using Python's built-in XML parsing library.
    """
    try:
        ET.fromstring(xml_output)  # Parse the XML structure
        return "✅ Local XML validation passed."
    except ET.ParseError as e:
        return f"❌ Local XML validation failed: {e}"

def generate_changeset_via_openai(command, query, template, changeset_id, collection_name, author, context):
    """
    Generates Liquibase XML for the specified MongoDB command using OpenAI.
    """
    prompt = f"""
    Using the provided MongoDB local reference template, transform this query into Liquibase XML:
    Query: {query}
    Template: {template}
    Changeset ID: {changeset_id}
    Collection Name: {collection_name}
    Author: {author}
    Context: {context}
    """
    try:
        response = openai.ChatCompletion.create(
            deployment_id="gpt-4o-Engg-AI-Assitant",
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert in generating Liquibase entries from MongoDB queries."},
                {"role": "user", "content": prompt},
            ],
        )
        result = response['choices'][0]['message']['content'].strip()
        return result
    except Exception as e:
        return f"Error using OpenAI for Liquibase XML generation: {e}"

def process_query(query, changeset_id, author, context):
    """
    Main processing function for MongoDB queries.
    """
    # Step 1: Validate and standardize the query using OpenAI
    standardized_query = validate_and_standardize_query(query)
    print(f"[DEBUG] Standardized Query: {standardized_query}")

    # Step 2: Extract collection name and command type from the standardized query
    collection_name, command_type = extract_collection_name_and_command(standardized_query)
    if not command_type:
        return f"Error: Unable to extract a valid MongoDB command from the query. Original: {query}"

    # Step 3: Reference template lookup
    template = LOCAL_REFERENCES.get(command_type)
    if not template:
        return f"Error: No reference template defined for `{command_type}`."

    # Step 4: Generate Liquibase XML via OpenAI
    liquibase_xml = generate_changeset_via_openai(
        command_type, standardized_query, template, changeset_id, collection_name, author, context
    )

    # Step 5: Validate the syntax of generated XML via OpenAI
    openai_validation_result = validate_syntax_via_openai(liquibase_xml)

    # Step 6: Validate the syntax of generated XML via Python library
    local_validation_result = validate_syntax_via_local_library(liquibase_xml)

    return liquibase_xml, openai_validation_result, local_validation_result

def multi_line_input(prompt):
    """
    Captures multi-line input from the user.
    Input ends when the user presses Enter twice.
    """
    print(prompt)
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)
    return "\n".join(lines)

if __name__ == "__main__":
    print("Welcome to the MongoDB Query to Liquibase XML Converter!")
    while True:
        mongo_query = multi_line_input("Enter the MongoDB query (press Enter twice to end):")
        if mongo_query.strip().lower() == "stop":
            print("Exiting... Goodbye!")
            break
        changeset_id = input("Enter the Liquibase Changeset ID: ").strip()
        author = input("Enter the Author Name: ").strip()
        context = input("Enter the Database Name (context): ").strip()

        print("\nValidating and processing the MongoDB query...")
        liquibase_xml, openai_validation, local_validation = process_query(mongo_query, changeset_id, author, context)

        print("\nLiquibase XML Output:\n")
        print(liquibase_xml)
        print("\nValidation Results:")
        print(f"OpenAI Validation: {openai_validation}")
        print(f"Local Validation: {local_validation}")

        continue_choice = input("\nWould you like to process another query? (yes/no): ").strip().lower()
        if continue_choice != "yes":
            print("Goodbye! Have a great day!")
            break
