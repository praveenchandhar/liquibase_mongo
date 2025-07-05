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
# Prioritize commons-lang3 and other essential jars first
CLASSPATH="$JARS_DIR/commons-lang3.jar:$JARS_DIR/liquibase-core.jar:$JARS_DIR/liquibase-mongodb.jar:$JARS_DIR/jackson-annotations.jar:$JARS_DIR/jackson-core.jar:$JARS_DIR/jackson-databind.jar:$JARS_DIR/mongodb-driver-sync.jar:$JARS_DIR/mongodb-driver-core.jar:$JARS_DIR/bson.jar:$JARS_DIR/commons-io.jar:$JARS_DIR/snakeyaml.jar:$JARS_DIR/slf4j-api.jar:$JARS_DIR/slf4j-simple.jar:$JARS_DIR/opencsv.jar"

export CLASSPATH

echo "--------------- DEBUGGING START ---------------"
echo "CLASSPATH=${CLASSPATH}" | tr ':' '\n'
echo "Files in JARS_DIR ($JARS_DIR):"
ls -l "$JARS_DIR"
echo "--------------- DEBUGGING END -----------------"

# Check if commons-lang3 is included in dependencies
if ! jar tf "$JARS_DIR/commons-lang3.jar" | grep -q "org/apache/commons/lang3/SystemProperties.class"; then
    echo "Error: commons-lang3.jar does not contain SystemProperties class."
    exit 1
fi

# Validate that Liquibase is accessible
echo "Validating Liquibase binary..."
java -cp "$CLASSPATH" liquibase.integration.commandline.Main --version || {
    echo "Liquibase execution failed: please check dependencies."
    exit 1
}

# Command Execution
case "$command" in
    status)
        echo "Running Liquibase status for database: '$database'..."
        java -cp "$CLASSPATH" liquibase.integration.commandline.Main \
            status \
            --url="$MONGO_CONNECTION_BASE/$database?retryWrites=true&w=majority&tls=true" \
            --logLevel=debug \
            --changeLogFile=changeset/changelog.xml
        ;;

    update)
        echo "Running Liquibase update for database: '$database'..."
        java -cp "$CLASSPATH" liquibase.integration.commandline.Main \
            update \
            --url="$MONGO_CONNECTION_BASE/$database?retryWrites=true&w=majority&tls=true" \
            --logLevel=debug \
            --changeLogFile=changeset/changelog.xml
        ;;

    *)
        echo "Unknown command: $command"
        exit 1
        ;;
esac
