#!/bin/bash

# MongoDB Atlas connection base (without database)
MONGO_CONNECTION_BASE="mongodb+srv://praveenchandharts:kixIUsDWGd3n6w5S@praveen-mongodb-github.lhhwdqa.mongodb.net"

# Define an associative array for databases and their corresponding contexts
declare -A DATABASE_CONTEXTS=(
    ["liquibase_test"]="liquibase_test"
    ["sample_mflix"]="sample_mflix"
)

# Validate input arguments
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <command> <database1,database2,...>"
    exit 1
fi

# Read command (status/update) and raw database input
command="$1"
raw_databases="$2"

# Validate the Liquibase command
if [[ "$command" != "status" && "$command" != "update" ]]; then
    echo "Invalid command: $command."
    echo "Only 'status' or 'update' commands are allowed."
    exit 1
fi

# Setup CLASSPATH for Liquibase dependencies
CLASSPATH=$(find "$HOME/liquibase-jars" -name "*.jar" | tr '\n' ':')
export CLASSPATH

# Debug information
echo "Running Liquibase runner script..."
echo "Command: $command"
echo "Databases (raw input): $raw_databases"

# Split and clean the database input
IFS=',' read -r -a database_array <<< "$raw_databases"
sanitized_databases=()
for db in "${database_array[@]}"; do
    db=$(echo "$db" | xargs) # Trim leading/trailing spaces
    if [[ -n "$db" ]]; then
        sanitized_databases+=("$db")
    fi
done

# Validate databases against the associative array
valid_databases=()
for db in "${sanitized_databases[@]}"; do
    if [[ -n "${DATABASE_CONTEXTS[$db]}" ]]; then
        valid_databases+=("$db")
    else
        echo "Skipping invalid or unknown database: '$db'"
    fi
done

# Ensure there are valid databases
if [[ ${#valid_databases[@]} -eq 0 ]]; then
    echo "No valid databases provided. Exiting."
    exit 1
fi

# Execute the Liquibase command for each valid database and context
for db in "${valid_databases[@]}"; do
    context="${DATABASE_CONTEXTS[$db]}"
    echo "Running Liquibase '$command' for database: '$db' with context: '$context'"

    liquibase \
        --url="${MONGO_CONNECTION_BASE}/${db}?retryWrites=true&w=majority&tls=true" \
        --username="liquibase_user" \
        --password="qggDXaeeyro9NlwNKK1V" \
        --changeLogFile="changeset/changelog.xml" \
        --contexts="$context" \
        --logLevel="debug" \
        "$command" # Redirect output dynamically based on the workflow

    if [[ $? -eq 0 ]]; then
        echo "Liquibase '$command' for database '$db' executed successfully."
    else
        echo "Liquibase failed for database '$db'. Please check the logs."
        exit 1
    fi

    echo "------------------------------------------------------------"
done

echo "Liquibase runner script completed successfully."
exit 0
