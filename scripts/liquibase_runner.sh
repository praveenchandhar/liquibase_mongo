#!/bin/bash

# MongoDB Atlas connection base (without database)
MONGO_CONNECTION_BASE="mongodb+srv://praveenchandharts:kixIUsDWGd3n6w5S@praveen-mongodb-github.lhhwdqa.mongodb.net"

# Define a list of allowed/pre-approved databases and their corresponding contexts
declare -A DATABASE_CONTEXTS
DATABASE_CONTEXTS=(
  ["liquibase_test"]="liquibase_test"
  ["sample_mflix"]="sample_mflix"
)

# Check if command and database(s) are provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <command> <database(s)>"
    exit 1
fi

# Read command (status/update) and raw input database(s)
command="$1"
raw_databases="$2"

# Setup CLASSPATH for Liquibase dependencies
CLASSPATH=$(find "$HOME/liquibase-jars" -name "*.jar" | tr '\n' ':')

# Print classpath for debugging
echo "Using classpath: $CLASSPATH"

# Step 1: Log Command to Debug
if [[ "$command" != "status" && "$command" != "update" ]]; then
  echo "Invalid command: $command."
  echo "Only 'status' or 'update' commands are allowed."
  exit 1
fi

echo "Running command: $command"
echo "Raw database input: $raw_databases"

# Step 2: Split Databases by Comma and Trim Each One
IFS=',' read -r -a database_array <<< "$raw_databases"
sanitized_databases=()
for db in "${database_array[@]}"; do
  # Trim leading/trailing spaces (if any)
  db=$(echo "$db" | xargs)

  # Add sanitized databases to the list
  if [[ -n "$db" ]]; then
    sanitized_databases+=("$db")
  fi
done

# Step 3: Validate Against Allowed Databases
valid_databases=()
for db in "${sanitized_databases[@]}"; do
  if [[ -n "${DATABASE_CONTEXTS[$db]}" ]]; then
    valid_databases+=("$db")
  else
    echo "Skipping invalid or unknown database: '$db'"
  fi
done

# Step 4: Ensure Valid Databases
if [[ ${#valid_databases[@]} -eq 0 ]]; then
  echo "No valid databases provided. Exiting."
  exit 1
fi

# Step 5: Execute Liquibase Command for Each Valid Database
for db in "${valid_databases[@]}"; do
  context="${DATABASE_CONTEXTS[$db]}"  # Get the context corresponding to the database
  echo "Running Liquibase $command for database: $db with context: $context"

  # Common Liquibase options
  LIQUIBASE_OPTS=(
    --url="${MONGO_CONNECTION_BASE}/${db}?retryWrites=true&w=majority&tls=true"
    --logLevel=debug
    --changeLogFile=changeset/changelog.xml
    --contexts="$context"
  )

  # Execute the appropriate Liquibase command
  case "$command" in
    status)
      java -cp "$CLASSPATH" liquibase.integration.commandline.Main "${LIQUIBASE_OPTS[@]}" status
      ;;
    update)
      java -cp "$CLASSPATH" liquibase.integration.commandline.Main "${LIQUIBASE_OPTS[@]}" update
      ;;
    *)
      # This condition shouldn't ever occur due to earlier validation
      echo "Unknown command: $command"
      exit 1
      ;;
  esac

  echo "Liquibase command '$command' for database '$db' executed successfully."
  echo "------------------------------------------------------------"
done
