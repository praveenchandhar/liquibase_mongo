#!/bin/bash

# MongoDB Atlas connection base (without database)
MONGO_CONNECTION_BASE="mongodb+srv://praveenchandharts:kixIUsDWGd3n6w5S@praveen-mongodb-github.lhhwdqa.mongodb.net"

# Define a list of allowed/pre-approved databases
ALLOWED_DATABASES=(
  "liquibase_test1"
  "liquibase_test2"
  "liquibase_test3"
  "liquibase_test4"
  "liquibase_test5"
)

# Check if command and database(s) are provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <command> <database(s)>"
    exit 1
fi

# Read command (status/update) and database(s)
command="$1"
databases="$2"

# Allow databases to be comma-separated and split them into an array
IFS=',' read -r -a database_array <<< "$databases"

# Setup CLASSPATH for Liquibase dependencies
CLASSPATH=$(find "$HOME/liquibase-jars" -name "*.jar" | tr '\n' ':')

# Print classpath for debugging
echo "Using classpath: $CLASSPATH"

# Helper function to check if a value is in the allowed database list
is_allowed_database() {
  local db=$1
  for allowed_db in "${ALLOWED_DATABASES[@]}"; do
    if [[ "$db" == "$allowed_db" ]]; then
      return 0
    fi
  done
  return 1
}

# Execute Liquibase for each database
for database in "${database_array[@]}"; do
  # Trim whitespace around the database name
  database=$(echo "$database" | xargs)

  # Validate if the database is in the allowed list
  if ! is_allowed_database "$database"; then
    echo "Skipping database '$database' - not in the allowed database list."
    continue
  fi

  echo "Running Liquibase $command for database: $database"

  # Common Liquibase options
  LIQUIBASE_OPTS=(
    --url="${MONGO_CONNECTION_BASE}/${database}?retryWrites=true&w=majority&tls=true"
    --logLevel=debug
    --changeLogFile=changeset/changelog.xml
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
      echo "Unknown command: $command"
      exit 1
      ;;
  esac

  echo "Liquibase command '$command' for database '$database' executed successfully."
  echo "------------------------------------------------------------"
done
