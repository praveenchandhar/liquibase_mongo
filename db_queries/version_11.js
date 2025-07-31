// context: liquibase_test
// This file contains changes for the liquibase_test database

// 1. Insert sample data into sk_uam_permission collection
db.getCollection("sk_uam_permission").insertMany([
    {
        "permission": "sp.benefits.benefitguide.list",
        "suiteKey": "sp",
        "productKey": "sp.benefits",
        "type": "normal",
        "moduleKey": "sp.benefits.benefits",
        "createdBy": "system",
        "createdAt": new Date("2023-01-01"),
        "updatedBy": "system",
        "updatedAt": new Date("2023-01-01"),
        "description": "Old permission to list Benefits guide.",
        "featureKey": "sp.benefits.benefits.old"
    },
    {
        "permission": "sp.benefits.benefitguide.sharewithprospecthire",
        "suiteKey": "sp",
        "productKey": "sp.benefits",
        "type": "normal",
        "moduleKey": "sp.benefits.benefits",
        "createdBy": "system",
        "createdAt": new Date("2023-01-01"),
        "updatedBy": "system",
        "updatedAt": new Date("2023-01-01"),
        "description": "Old permission to share with prospect hire.",
        "featureKey": "sp.benefits.benefits.old"
    },
    {
        "permission": "sp.benefits.other.permission",
        "suiteKey": "sp",
        "productKey": "sp.benefits",
        "type": "normal",
        "moduleKey": "sp.benefits.other",
        "createdBy": "system",
        "createdAt": new Date("2023-01-01"),
        "updatedBy": "system",
        "updatedAt": new Date("2023-01-01"),
        "description": "Other permission that should remain.",
        "featureKey": "sp.benefits.other.feature"
    }
]);

// 2. Insert sample data into sk_uam_permission_feature collection
db.getCollection("sk_uam_permission_feature").insertMany([
    {
        "permission": "sp.benefits.benefitguide.list",
        "description": "Old permission to list Benefits guide.",
        "featureKey": "sp.benefits.benefits.old"
    },
    {
        "permission": "sp.benefits.benefitguide.sharewithprospecthire",
        "description": "Old permission to share with prospect hire.",
        "featureKey": "sp.benefits.benefits.old"
    },
    {
        "permission": "sp.benefits.other.permission",
        "description": "Other permission feature that should remain.",
        "featureKey": "sp.benefits.other.feature"
    }
]);

// 3. Insert sample data into sk_uam_permission_group collection
db.getCollection("sk_uam_permission_group").insertMany([
    {
        "permissionGroupName": "sp.benefits.benefitguide.viewer",
        "description": "Old permissions for benefits guide viewer.",
        "permissions": [
            { "permission": "sp.benefits.old.permission" }
        ],
        "accessLevel": [
            "PUBLIC",
            "NON_SENSITIVE"
        ]
    },
    {
        "permissionGroupName": "sp.benefits.benefitguide.tpviewer",
        "description": "Old permissions for benefits guide tp viewer.",
        "permissions": [
            { "permission": "sp.benefits.old.tppermission" }
        ],
        "accessLevel": [
            "PUBLIC"
        ]
    },
    {
        "permissionGroupName": "sp.benefits.other.group",
        "description": "Other permission group that should remain.",
        "permissions": [
            { "permission": "sp.benefits.other.permission" }
        ],
        "accessLevel": [
            "ALL",
            "PUBLIC"
        ]
    }
]);

// 4. Insert sample data into sk_uam_role collection
db.getCollection("sk_uam_role").insertMany([
    {
        "roleKey": "CONTENT_EDITOR",
        "roleName": "Content Editor",
        "description": "Role for content editing",
        "permissionGroups": [
            {
                "permissionGroup": "sp.benefits.benefitguide.viewer",
                "accessLevel": "PUBLIC"
            },
            {
                "permissionGroup": "sp.benefits.other.group",
                "accessLevel": "ALL"
            }
        ],
        "createdBy": "system",
        "createdAt": new Date("2023-01-01")
    },
    {
        "roleKey": "GLOBAL_BENEFITS_MANAGER",
        "roleName": "Global Benefits Manager",
        "description": "Role for managing global benefits",
        "permissionGroups": [
            {
                "permissionGroup": "sp.benefits.benefitguide.viewer",
                "accessLevel": "ALL"
            },
            {
                "permissionGroup": "sp.benefits.other.group",
                "accessLevel": "ALL"
            }
        ],
        "createdBy": "system",
        "createdAt": new Date("2023-01-01")
    },
    {
        "roleKey": "TALENT_PARTNER",
        "roleName": "Talent Partner",
        "description": "Role for talent partners",
        "permissionGroups": [
            {
                "permissionGroup": "sp.benefits.benefitguide.tpviewer",
                "accessLevel": "PUBLIC"
            },
            {
                "permissionGroup": "sp.benefits.other.group",
                "accessLevel": "ALL"
            }
        ],
        "createdBy": "system",
        "createdAt": new Date("2023-01-01")
    }
]);
