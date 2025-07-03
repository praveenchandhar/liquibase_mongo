import re
import sys

def correct_json_syntax(json_string):
    """Correct common JSON syntax issues."""
    # Quote unquoted keys (e.g., `name:` becomes `"name":`)
    json_string = re.sub(r'(?<!")\b(\w+)\b\s*:', r'"\1":', json_string)
    
    # Quote unquoted values if they're not JSON-like
    json_string = re.sub(r':\s*(?![\[{"])(\w+)', r': "\1"', json_string)

    # Replace single quotes with double quotes
    json_string = json_string.replace("'", '"')
    
    return json_string

def format_json_string(json_string):
    """Format the JSON string to ensure correct structure."""
    json_string = correct_json_syntax(json_string)
    return json_string.strip()

def generate_changelog(mongodb_query, changeset_id, author_name, context):
    # Normalize the whitespace in the input query
    mongodb_query = re.sub(r'\s+', ' ', mongodb_query).strip()
    print(f"Normalized MongoDB Query: {mongodb_query}")

    # Initialize xml_content
    xml_content = ""

    if "createCollection" in mongodb_query:
        match = re.search(r'createCollection\("([^"]+)"', mongodb_query)
        if match:
            collection_name = match.group(1)
            xml_content = f"""
<changeSet id="{changeset_id}" author="{author_name}" context="{context}">
    <mongodb:createCollection collectionName="{collection_name}" />
</changeSet>
"""
    elif "dropCollection" in mongodb_query or "drop" in mongodb_query:
        match = re.search(r'db\.(?:getCollection\("([^"]+)"\)|([^.]+))\.drop\(\)', mongodb_query)
        if match:
            collection_name = match.group(1) or match.group(2)
            xml_content = f"""
<changeSet id="{changeset_id}" author="{author_name}" context="{context}">
    <mongodb:dropCollection collectionName="{collection_name}" />
</changeSet>
"""
    elif "insertOne" in mongodb_query:
        match = re.search(r'db\.(?:getCollection\("([^"]+)"\)|([^.]+))\.insertOne\((.*?)\)', mongodb_query, re.DOTALL)
        if match:
            collection_name = match.group(1) or match.group(2)
            document = match.group(3).strip()
            document = correct_json_syntax(document)  # Ensure valid JSON
            xml_content = f"""
<changeSet id="{changeset_id}" author="{author_name}" context="{context}">
    <mongodb:insertOne collectionName="{collection_name}">
        <mongodb:document><![CDATA[
            {document}
        ]]></mongodb:document>
    </mongodb:insertOne>
</changeSet>
"""
    elif "insertMany" in mongodb_query:
        match = re.search(r'db\.(?:getCollection\("([^"]+)"\)|([^.]+))\.insertMany\((.*?)\)', mongodb_query, re.DOTALL)
        if match:
            collection_name = match.group(1) or match.group(2)
            documents = match.group(3).strip()
            documents = correct_json_syntax(documents)  # Ensure valid JSON
            xml_content = f"""
<changeSet id="{changeset_id}" author="{author_name}" context="{context}">
    <mongodb:insertMany collectionName="{collection_name}">
        <mongodb:documents><![CDATA[
            {documents}
        ]]></mongodb:documents>
    </mongodb:insertMany>
</changeSet>
"""
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
        print("Error: The MongoDB query format is not recognized.")
        return

    # Print the XML content to the console
    print(f"Generated XML Content:\n{xml_content.strip()}")

# Read command-line arguments for parameters
if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python v1.py <mongodb_query> <changeset_id> <author_name> <context>")
        sys.exit(1)

    generate_changelog(
        mongodb_query=sys.argv[1],
        changeset_id=sys.argv[2],
        author_name=sys.argv[3],
        context=sys.argv[4]
    )
