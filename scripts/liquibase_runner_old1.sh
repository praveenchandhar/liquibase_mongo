#!/bin/bash

# MongoDB Atlas connection base (without database)
MONGO_CONNECTION_BASE="mongodb+srv://praveenchandharts:kixIUsDWGd3n6w5S@praveen-mongodb-github.lhhwdqa.mongodb.net"

# Check if command and database are provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <command> <database>"
    exit 1
fi

# Read command and database
command="$1"
database="$2"

# Setup CLASSPATH for Liquibase dependencies
CLASSPATH=$(find "$HOME/liquibase-jars" -name "*.jar" | tr '\n' ':')

# Print classpath for debugging
echo "Using classpath: $CLASSPATH"

# Common Liquibase options
LIQUIBASE_OPTS=(
  --url="${MONGO_CONNECTION_BASE}/${database}?retryWrites=true&w=majority&tls=true"
  --logLevel=debug
  --changeLogFile=changeset/changelog.xml
)

# Execute the appropriate Liquibase command
case "$command" in
  status)
    echo "Running Liquibase status for database: $database"
    java -cp "$CLASSPATH" liquibase.integration.commandline.Main "${LIQUIBASE_OPTS[@]}" status
    ;;
  update)
    echo "Running Liquibase update for database: $database"
    java -cp "$CLASSPATH" liquibase.integration.commandline.Main "${LIQUIBASE_OPTS[@]}" update
    ;;
  *)
    echo "Unknown command: $command"
    exit 1
    ;;
esac
