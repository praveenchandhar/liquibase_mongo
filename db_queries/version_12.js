// context: liquibase_test
// This file contains changes for the liquibase_test database

// Remove old permissions from sk_uam_permission
db.getCollection("sk_uam_permission").deleteMany({'permission':{$in:["sp.benefits.benefitguide.list", "sp.benefits.benefitguide.sharewithprospecthire"]}});

// Insert new permissions into sk_uam_permission
db.getCollection("sk_uam_permission").insertMany([
{ 
    "permission" : "sp.benefits.benefitguide.list",
    "suiteKey" : "sp",
    "productKey" : "sp.benefits",
    "type" : "normal",
    "moduleKey" : "sp.benefits.benefits",
    "createdBy" : "1",
    "createdAt" : ISODate(),
    "updatedBy" : "1",
    "updatedAt" : ISODate(),
    "description" : "Permission to list Benefits guide.",
    "featureKey" : "sp.benefits.benefits.benefits"
},
{ 
    "permission" : "sp.benefits.benefitguide.sharewithprospecthire",
    "suiteKey" : "sp",
    "productKey" : "sp.benefits",
    "type" : "normal",
    "moduleKey" : "sp.benefits.benefits",
    "createdBy" : "1",
    "createdAt" : ISODate(),
    "updatedBy" : "1",
    "updatedAt" : ISODate(),
    "description" : "Permission to share with prospect hire.",
    "featureKey" : "sp.benefits.benefits.benefits"
}
]);

// Remove old permission features
db.getCollection("sk_uam_permission_feature").deleteMany({'permission':{$in:["sp.benefits.benefitguide.list", "sp.benefits.benefitguide.sharewithprospecthire"]}});

// Insert new permission features
db.getCollection("sk_uam_permission_feature").insertMany([
{   "permission" : "sp.benefits.benefitguide.list",
    "description" : "Permission to list Benefits guide.",
    "featureKey" : "sp.benefits.benefits.benefits"
},
{   "permission" : "sp.benefits.benefitguide.sharewithprospecthire",
    "description" : "Permission to share with prospect hire.",
    "featureKey" : "sp.benefits.benefits.benefits"
}
]);

// Remove old permission groups
db.getCollection("sk_uam_permission_group").deleteMany({'permissionGroupName':{$in: ["sp.benefits.benefitguide.viewer", "sp.benefits.benefitguide.tpviewer"]}});

// Insert new permission groups
db.getCollection("sk_uam_permission_group").insertMany([{
    "permissionGroupName" : "sp.benefits.benefitguide.viewer",
    "description" : "Permissions for benefits guide viewer.",
    "permissions" : [
        { "permission" : "sp.benefits.benefitguide.list" }
    ],
    "accessLevel" : [
        "ALL",
        "PUBLIC",
        "SENSITIVE",
        "COMP",
        "PERSONAL",
        "NON_SENSITIVE"
    ]
},
{
    "permissionGroupName" : "sp.benefits.benefitguide.tpviewer",
    "description" : "Permissions for benefits guide tp viewer.",
    "permissions" : [
        { "permission" : "sp.benefits.benefitguide.sharewithprospecthire" }
    ],
    "accessLevel" : [
        "ALL",
        "PUBLIC",
        "SENSITIVE",
        "COMP",
        "PERSONAL",
        "NON_SENSITIVE"
    ]
}
]);

// Remove old permission groups from roles
db.getCollection("sk_uam_role").updateMany(
    { "roleKey": {"$in": ["CONTENT_EDITOR", "GLOBAL_BENEFITS_MANAGER"]} },
    { $pull: { permissionGroups: { permissionGroup: { $in: ["sp.benefits.benefitguide.viewer"] } } } }
);

// Add new permission groups to roles
db.getCollection("sk_uam_role").updateMany(
    { "roleKey": {"$in": ["CONTENT_EDITOR", "GLOBAL_BENEFITS_MANAGER"]} },
    {
        $push: {
            "permissionGroups": {
                $each: [{
                    "permissionGroup": "sp.benefits.benefitguide.viewer",
                    "accessLevel": "ALL"
                }]
            }
        }
    }
);

// Remove old TP permission groups from roles
db.getCollection("sk_uam_role").updateMany(
    { "roleKey": {"$in": ["TALENT_PARTNER"]} },
    { $pull: { permissionGroups: { permissionGroup: { $in: ["sp.benefits.benefitguide.tpviewer"] } } } }
);

// Add new TP permission groups to roles
db.getCollection("sk_uam_role").updateMany(
    { "roleKey": {"$in": ["TALENT_PARTNER"]} },
    {
        $push: {
            "permissionGroups": {
                $each: [{
                    "permissionGroup": "sp.benefits.benefitguide.tpviewer",
                    "accessLevel": "ALL"
                }]
            }
        }
    }
);
