#!/bin/bash

# Define an associative array of databases and their corresponding contexts
declare -A databases
databases=(
    ["pp_data_common_pre-production"]="pp_data_common_pre-production"
    ["pp_data_common_preproduction"]="pp_data_common_preproduction"
    ["pp_data_common_production"]="pp_data_common_production"
    ["benefitos_tenant_1_db_preproduction"]="benefitos_tenant_1_db_preproduction"
    ["tenant_1_db_production"]="tenant_1_db_production"
    ["liquibase_test"]="liquibase_test"
)

# Check that a command is provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <command>"
    exit 1
fi

# Setup CLASSPATH dynamically
CLASSPATH=$(find $HOME/liquibase-jars -name "*.jar" | tr '\n' ':')

command=$1  # Read command (`status` or `update`)

case "$command" in
    status)
        echo "Running Liquibase status..."
        java -cp "$CLASSPATH" liquibase.integration.commandline.Main \
            --logLevel=debug \
            --changeLogFile=changelog.xml \
            status
        ;;
    update)
        echo "Running Liquibase update..."
        for db in "${!databases[@]}"; do
            echo "Updating database: $db..."
            java -cp "$CLASSPATH" liquibase.integration.commandline.Main \
                --url="jdbc:mongodb://praveen-mongodb-github.lhhwdqa.mongodb.net$db?authSource=admin" \
                --username="praveenchandharts" \
                --password="kixIUsDWGd3n6w5S" \
                --changeLogFile=changelog.xml \
                --contexts="${databases[$db]}" \
                --logLevel=debug \
                update
        done
        ;;
    *)
        echo "Unknown command: $command. Supported commands are 'status' and 'update'."
        exit 1
        ;;
esac
