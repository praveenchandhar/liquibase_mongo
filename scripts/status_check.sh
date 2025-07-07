#!/bin/bash

# Allowed/Pre-Approved Databases List
ALLOWED_DATABASES=(
  "liquibase_test"
  "sample_mflix"
)

# Liquibase Connection Base URL
MONGO_CONNECTION_BASE="mongodb+srv://praveenchandharts:kixIUsDWGd3n6w5S@praveen-mongodb-github.lhhwdqa.mongodb.net"

# Liquibase Status for All Allowed Databases (Without Explicitly Providing Database Names)
command="status"

echo "Performing Liquibase '$command' for all allowed databases..."
for db in "${ALLOWED_DATABASES[@]}"; do
    echo "Checking status for database: $db"
    liquibase \
        --url="${MONGO_CONNECTION_BASE}/${db}?retryWrites=true&w=majority&tls=true" \
        --changeLogFile="changeset/changelog.xml" \
        --logLevel="debug" \
        "$command"

    if [[ $? -eq 0 ]]; then
        echo "Liquibase '$command' for database '$db' executed successfully."
    else
        echo "Liquibase '$command' for database '$db' failed. Please check logs."
        exit 1
    fi

    echo "------------------------------------------------------------"
done
echo "Status checks for all databases completed successfully!"
