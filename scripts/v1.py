import argparse
import os
import re
import openai
import xml.etree.ElementTree as ET

# OpenAI API Configuration
openai.api_type = "azure"
openai.api_base = "https://sequoia-engg-openai.openai.azure.com/"
openai.api_key = os.getenv("OPENAI_API_KEY")  # Fetch OpenAI key from the environment
openai.api_version = "2024-12-01-preview"

# Liquibase command templates
LOCAL_REFERENCES = {
    "insertMany": """
<changeSet id="{changeset_id}" author="{author}" context="{context}">
    <mongodb:insertMany collectionName="{collection_name}">
        <mongodb:documents><![CDATA[
        {documents}
        ]]></mongodb:documents>
    </mongodb:insertMany>
</changeSet>
"""
}

def extract_collection_name_and_command(query):
    """
    Extract the MongoDB collection name and command type from the query.
    """
    match = re.search(r'db\.(\w+)\.(insertMany)\(', query)
    if match:
        return match.group(1), match.group(2)  # Returns (collection_name, command_type)
    return None, None

def validate_and_correct_via_openai(xml_output):
    """
    Validate and correct Liquibase XML via OpenAI.
    """
    prompt = f"""
    Here’s a generated Liquibase XML based on a MongoDB query. Please validate this XML and correct any syntax or logical issues. If correct, return the XML without changes:
    {xml_output}
    """
    try:
        response = openai.ChatCompletion.create(
            deployment_id="gpt-4o-Engg-AI-Assitant",
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert in Liquibase XML for MongoDB."},
                {"role": "user", "content": prompt},
            ],
        )
        corrected_result = response['choices'][0]['message']['content'].strip()
        return corrected_result
    except Exception as e:
        return f"Error using OpenAI for XML correction: {e}"

def append_to_changelog(corrected_xml):
    """
    Append the corrected XML to the changelog file.
    """
    changelog_dir = "changeset"
    changelog_file = os.path.join(changelog_dir, "changelog.xml")

    # Ensure the directory exists
    if not os.path.exists(changelog_dir):
        os.makedirs(changelog_dir)

    # Append to XML changelog
    with open(changelog_file, "a") as f:
        f.write("\n" + corrected_xml + "\n")
    print(f"\n✅ Corrected XML output appended to {changelog_file} successfully!")

def generate_liquibase_xml(query, changeset_id, author, context):
    """
    Generate Liquibase XML from MongoDB query.
    """
    collection_name, command_type = extract_collection_name_and_command(query)
    if not command_type or command_type not in LOCAL_REFERENCES:
        return None, f"Error: Unsupported command or failed to parse query: {query}"

    # Format the Liquibase XML template
    documents_section = query.split("insertMany(", 1)[1].strip("[]); \n")
    xml_output = LOCAL_REFERENCES[command_type].format(
        changeset_id=changeset_id,
        author=author,
        context=context,
        collection_name=collection_name,
        documents=documents_section
    )
    return xml_output, None

if __name__ == "__main__":
    # Command-line argument parser
    parser = argparse.ArgumentParser(description="Convert MongoDB query to Liquibase XML changeset")
    parser.add_argument("--query", required=True, help="MongoDB query (e.g., db.collection.insertMany([...])")
    parser.add_argument("--changeset-id", required=True, help="Liquibase changeset ID")
    parser.add_argument("--author", required=True, help="Author of the changeset")
    parser.add_argument("--context", required=True, help="Database context name")

    args = parser.parse_args()

    print("\n🔄 Processing query into Liquibase XML...")
    liquibase_xml, error = generate_liquibase_xml(args.query, args.changeset_id, args.author, args.context)

    if error:
        print(f"\n❌ Error: {error}")
        exit(1)

    print("\n✅ Generated Liquibase XML:\n", liquibase_xml)

    # Validate and correct XML with OpenAI
    print("\n🔄 Validating Liquibase XML via OpenAI...")
    corrected_xml = validate_and_correct_via_openai(liquibase_xml)

    if corrected_xml.startswith("Error"):
        print(f"\n❌ OpenAI Validation Error: {corrected_xml}")
        exit(1)

    print("\n✅ Corrected Liquibase XML:\n", corrected_xml)

    # Append corrected XML to changelog
    append_to_changelog(corrected_xml)
