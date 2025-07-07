#!/bin/bash

# MongoDB Atlas connection base (without database)
MONGO_CONNECTION_BASE="mongodb+srv://praveenchandharts:kixIUsDWGd3n6w5S@praveen-mongodb-github.lhhwdqa.mongodb.net"

# Define an associative array for databases and their corresponding contexts
declare -A DATABASE_CONTEXTS
DATABASE_CONTEXTS=(
  ["liquibase_test"]="liquibase_test"
  ["sample_mflix"]="sample_mflix"
)

# Check if at least one command and one database is provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <command> <database1,database2,...>"
    exit 1
fi

# Read the command (status/update) and raw database input
command="$1"
raw_databases="$2"

# Setup CLASSPATH for Liquibase dependencies
CLASSPATH=$(find "$HOME/liquibase-jars" -name "*.jar" | tr '\n' ':')

# Debug: Print command and raw database input
echo "Running command: $command"
echo "Raw database input: $raw_databases"

# Validate the command
if [[ "$command" != "status" && "$command" != "update" ]]; then
    echo "Invalid command: $command. Only 'status' or 'update' are allowed."
    exit 1
fi

# Split the raw database input by commas, trim whitespace, and sanitize
IFS=',' read -r -a database_array <<< "$raw_databases"
sanitized_databases=()
for db in "${database_array[@]}"; do
  db=$(echo "$db" | xargs) # Trim leading/trailing spaces
  if [[ -n "$db" ]]; then
    sanitized_databases+=("$db")
  fi
done

# Validate databases against the associative array and prepare valid databases
valid_databases=()
for db in "${sanitized_databases[@]}"; do
  if [ -n "${DATABASE_CONTEXTS[$db]}" ]; then
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

# Execute the Liquibase command for each valid database and its corresponding context
for db in "${valid_databases[@]}"; do
  context="${DATABASE_CONTEXTS[$db]}" # Get the context for the database
  echo "Running Liquibase $command for database: $db with context: $context"

  output=$(liquibase \
      --url="${MONGO_CONNECTION_BASE}/${db}?retryWrites=true&w=majority&tls=true" \
      --username=liquibase_user \
      --password=qggDXaeeyro9NlwNKK1V \
      --changeLogFile=changeset/changelog.xml \
      --contexts="$context" \
      --logLevel=debug \
      "$command" 2>&1) # Capture output

  echo "Liquibase output for database '$db':"
  echo "$output"
  echo "------------------------------------------------------------"
done
