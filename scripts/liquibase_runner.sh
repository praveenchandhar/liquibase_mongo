#!/bin/bash

# Define an associative array of databases and their corresponding contexts
declare -A databases
databases=(
    ["pp_data_common_pre-production"]="pp_data_common_pre-production"
    ["pp_data_common_preproduction"]="pp_data_common_preproduction"
    ["pp_data_common_production"]="pp_data_common_production"
    ["benefitos_tenant_1_db_preproduction"]="benefitos_tenant_1_db_preproduction"
    ["tenant_1_db_production"]="tenant_1_db_production"
)

# Check if no commands are provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <command> [<database1> <database2> ...]"
    exit 1
fi

# Read the first argument as the command (`status` or `update`)
command=$1
shift  # Shift to process subsequent arguments (databases)

case $command in
    "status")
        echo "Running Liquibase status check..."
        liquibase \
            --logLevel=debug \
            --changeLogFile=changelog.xml \
            status
        echo "Liquibase status check complete."
        ;;
    "update")
        # Loop through each provided database and apply Liquibase updates
        for db in "$@"
        do
            if [ -n "${databases[$db]}" ]; then
                echo "Updating Liquibase for database: $db"
                liquibase \
                    --url="mongodb+srv://praveen-mongodb-github.lhhwdqa.mongodb.net/$db?retryWrites=true&w=majority" \
                    --username=praveenchandharts \
                    --password=kixIUsDWGd3n6w5S \
                    --changeLogFile=changelog.xml \
                    --contexts="${databases[$db]}" \
                    --logLevel=debug \
                    update > liquibase_$db.log 2>&1
                echo "Update applied to $db. Log saved to liquibase_$db.log"
            else
                echo "Database $db not found in the list."
            fi
        done
        ;;
    *)
        echo "Unknown command: $command. Supported commands are 'status' and 'update'."
        exit 1
        ;;
esac
