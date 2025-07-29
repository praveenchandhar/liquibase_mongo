// context: liquibase_test
// This file contains changes for the liquibase_test database

// Insert operation
db.getCollection("san_mateo").insertMany([
    { name: "John Doe", email: "john@example.com", age: 30 },
    { name: "Jane Smith", email: "jane@example.com", age: 25 }
]);

// Update operation
db.getCollection("san_mateo").updateOne(
    { email: "john@example.com" },
    { $set: { age: 31, lastUpdated: new Date() } }
);

// Delete operation
db.getCollection("san_mateo").deleteMany({ age: { $lt: 18 } });
