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

# Prepare Workspace and Dependencies
JARS_DIR=$HOME/liquibase-jars
CLASSPATH="$JARS_DIR/commons-lang3.jar:$JARS_DIR/liquibase-core.jar:$JARS_DIR/liquibase-mongodb.jar:$JARS_DIR/jackson-annotations.jar:$JARS_DIR/jackson-core.jar:$JARS_DIR/jackson-databind.jar:$JARS_DIR/snakeyaml.jar:$JARS_DIR/mongodb-driver-sync.jar:$JARS_DIR/mongodb-driver-core.jar:$JARS_DIR/bson.jar:$JARS_DIR/slf4j-api.jar:$JARS_DIR/slf4j-simple.jar:$JARS_DIR/commons-io.jar:$JARS_DIR/opencsv.jar"

export CLASSPATH

echo "--------------- DEBUGGING START ----------------"
echo "COMMAND: $command"
echo "DATABASE: $database"
echo "CLASSPATH:"
echo $CLASSPATH | tr ':' '\n'
echo "Files in JARS_DIR:"
ls -l $JARS_DIR
echo "Connection URL: $MONGO_CONNECTION_BASE/$database?retryWrites=true&w=majority&tls=true"
echo "--------------- DEBUGGING END ------------------"

# Validate Liquibase Binary
echo "Validating Liquibase binary execution..."
java -cp "$CLASSPATH" liquibase.integration.commandline.Main --version || {
    echo "Liquibase failed to execute. Please check dependencies and binary."
    exit 1
}

# Ensure changelog file exists
if [ ! -f changeset/changelog.xml ]; then
    echo "Error: changelog file does not exist at changeset/changelog.xml"
    exit 1
fi

# Command Execution
case "$command" in
    status)
        echo "Running Liquibase status for database: '$database'..."
        java -cp "$CLASSPATH" liquibase.integration.commandline.Main \
            status \
            --url="$MONGO_CONNECTION_BASE/$database?retryWrites=true&w=majority&tls=true" \
            --changeLogFile=changeset/changelog.xml \
            --logLevel=DEBUG
        ;;
    update)
        echo "Running Liquibase update for database: '$database'..."
        java -cp "$CLASSPATH" liquibase.integration.commandline.Main \
            update \
            --url="$MONGO_CONNECTION_BASE/$database?retryWrites=true&w=majority&tls=true" \
            --changeLogFile=changeset/changelog.xml \
            --logLevel=DEBUG
        ;;
    *)
        echo "Unknown command: $command"
        exit 1
        ;;
esac
