   // context: liquibase_test
   // Test changeset for security validation
   // Author: Security Test
   // Description: Testing secure workflow implementation

   db.getCollection("security_test").insertOne({
       test_id: "security_001",
       created_date: new Date(),
       description: "Testing secure changeset generation",
       status: "active"
   });

   db.getCollection("security_test").createIndex({
       test_id: 1
   }, {
       name: "idx_security_test_id"
   });
