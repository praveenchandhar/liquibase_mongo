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

# Check if at least one database is provided as an argument
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <database1> <database2> ..."
    exit 1
fi

# Loop through each provided database and run the Liquibase update command with detailed logging
for db in "$@"
do
    if [ -n "${databases[$db]}" ]; then
        liquibase \
            --url="mongodb://10.3.16.85:27017/$db?authSource=admin" \
            --username=liquibase_user \
            --password=qggDXaeeyro9NlwNKK1V \
            --changeLogFile=changelog.xml \
            --contexts="${databases[$db]}" \
            --logLevel=debug \
            update  > liquibase_$db.log 2>&1
        echo "Update applied to $db. Log saved to liquibase_$db.log"
    else
        echo "Database $db not found in the list."
    fi
done
