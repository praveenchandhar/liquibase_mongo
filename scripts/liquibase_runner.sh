#!/bin/bash

# Fail the script if an error occurs or if an undefined variable is used
set -euo pipefail

# MongoDB Atlas connection base (without database)
MONGO_CONNECTION_BASE="mongodb+srv://praveenchandharts:kixIUsDWGd3n6w5S@praveen-mongodb-github.lhhwdqa.mongodb.net"

# Ensure that the minimum number of arguments is provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <command> <database>"
    echo "Available commands: status, update"
    exit 1
fi

# Read command and database parameters
command="$1"
database="$2"

# Validate that the database name is provided (non-empty)
if [ -z "$database" ]; then
    echo "Error: Database name cannot be empty."
    exit 1
fi

# Path to the directory containing Liquibase JAR files
JARS_DIR="$HOME/liquibase-jars"

# Ensure that the JARs directory exists
if [ ! -d "$JARS_DIR" ]; then
    echo "Error: JARs directory '$JARS_DIR' does not exist. Please place the required jars in this directory."
    exit 1
fi

# Construct CLASSPATH by including all JAR files in the specified directory
CLASSPATH=$(find "$JARS_DIR" -name "*.jar" | tr '\n' ':')

# Ensure that CLASSPATH is not empty
if [ -z "$CLASSPATH" ]; then
    echo "Error: No JAR files found in '$JARS_DIR'. Ensure that all required dependencies are present."
    exit 1
fi

# Print classpath for debugging purposes
echo "Using CLASSPATH: $CLASSPATH"

# Common Liquibase options
LIQUIBASE_OPTS=(
  --url="${MONGO_CONNECTION_BASE}/${database}?retryWrites=true&w=majority&tls=true"
  --logLevel=debug
  --changeLogFile=changeset/changelog.xml
)

# Execute the appropriate Liquibase command based on the input argument
case "$command" in
  status)
    echo "Running Liquibase 'status' command for database: $database"
    java -cp "$CLASSPATH" liquibase.integration.commandline.Main "${LIQUIBASE_OPTS[@]}" status
    ;;
  update)
    echo "Running Liquibase 'update' command for database: $database"
    java -cp "$CLASSPATH" liquibase.integration.commandline.Main "${LIQUIBASE_OPTS[@]}" update
    ;;
  *)
    echo "Unknown command: $command"
    echo "Supported commands: status, update"
    exit 1
    ;;
esac
