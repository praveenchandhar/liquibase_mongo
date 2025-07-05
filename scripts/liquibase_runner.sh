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

# Check if a command is provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <command>"
    exit 1
fi

# Read the command (`status` or `update`)
command=$1
shift  # Shift to process database arguments

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
        for db in "$@"; do
            if [ -n "${databases[$db]}" ]; then
                echo "Updating database: $db"
                java -cp "$CLASSPATH" liquibase.integration.commandline.Main \
                    --url="jdbc:mongodb+srv://praveenchandharts:kixIUsDWGd3n6w5S@your-cluster.mongodb.net/$db?retryWrites=true&w=majority" \
                    --changeLogFile=changelog.xml \
                    --logLevel=debug \
                    update
            else
                echo "Database $db not found."
            fi
        done
        ;;
    
    *)
        echo "Unknown command: $command"
        exit 1
        ;;
esac
