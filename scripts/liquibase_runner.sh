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

# Liquibase MongoDB connection details (replace with environment variables for security)
MONGO_CONNECTION_STRING="mongodb+srv://praveen-mongodb-github.lhhwdqa.mongodb.net"
MONGO_USERNAME="praveenchandharts"
MONGO_PASSWORD="kixIUsDWGd3n6w5S"

# Check if a command is provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <command> [<database1> <database2> ...]"
    exit 1
fi

# Read the command (`status` or `update`)
command=$1
shift  # Shift to process subsequent arguments (databases)

# Common CLASSPATH setup for Liquibase dependencies
CLASSPATH="$HOME/liquibase-jars/*"

case $command in
    "status")
        echo "Running Liquibase status check..."
        liquibase \
            --classpath=$CLASSPATH \
            --url="jdbc:$MONGO_CONNECTION_STRING/" \
            --username=$MONGO_USERNAME \
            --password=$MONGO_PASSWORD \
            --logLevel=debug \
            --changeLogFile=changelog.xml \
            status
        echo "Liquibase status check complete."
        ;;
    
    "update")
        for db in "$@"
        do
            if [ -n "${databases[$db]}" ]; then
                echo "Updating Liquibase for database: $db"
                liquibase \
                    --classpath=$CLASSPATH \
                    --url="jdbc:$MONGO_CONNECTION_STRING/$db?retryWrites=true&w=majority" \
                    --username=$MONGO_USERNAME \
                    --password=$MONGO_PASSWORD \
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
