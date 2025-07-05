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

# Prepare Workspace and Install Dependencies
JARS_DIR=$HOME/liquibase-jars

# Setup Liquibase CLASSPATH
export CLASSPATH=$(find $JARS_DIR -name "*.jar" | tr '\n' ':')

case "$command" in
    status)
        echo "Running Liquibase status for database: '$database'"
        java -cp "$CLASSPATH" liquibase.integration.commandline.Main \
            --url="$MONGO_CONNECTION_BASE/$database?retryWrites=true&w=majority&tls=true" \
            --logLevel=debug \
            --changeLogFile=changeset/changelog.xml \
            status
        ;;
    update)
        echo "Running Liquibase update for database: '$database'"
        java -cp "$CLASSPATH" liquibase.integration.commandline.Main \
            --url="$MONGO_CONNECTION_BASE/$database?retryWrites=true&w=majority&tls=true" \
            --logLevel=debug \
            --changeLogFile=changeset/changelog.xml \
            update
        ;;
    *)
        echo "Unknown command: $command"
        exit 1
        ;;
esac
