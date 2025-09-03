# 🚀 Kite - Infrastructure Management Platform 

**Kite** is a Python-based tool for managing database operations and infrastructure workflows for MongoDB, Liquibase, and multi-environment deployments.

## 🎯 Quick Start

**Note:** Ensure you are added to `us_india_eng_write` github role

- **Read queries**: [📹 Watch Demo](https://github.com/Sequoia-US/infra-kite/raw/main/docs/read.mp4)
- **Write Queries**: [📹 Watch Demo](https://github.com/Sequoia-US/infra-kite/raw/main/docs/write.mp4)
- **Change Approvers**: [👥 View Approvers](https://github.com/Sequoia-US/infra-kite/blob/main/ops/change_approvers.json)

# MongoDB to Liquibase XML Converter - Developer Reference

## 📋 MongoDB Operations Support Matrix

### ✅ Supported Operations

| Command/Operation | Reference Query | Supported |
|-------------------|-----------------|-----------|
| `insertOne` | `db.users.insertOne({name: "John", email: "john@example.com"})` | ✅ YES |
| `insertMany` | `db.users.insertMany([{name: "John"}, {name: "Jane"}])` | ✅ YES |
| `updateOne` | `db.users.updateOne({_id: ObjectId("123")}, {$set: {age: 31}})` | ✅ YES |
| `updateMany` | `db.users.updateMany({status: "pending"}, {$set: {status: "active"}})` | ✅ YES |
| `replaceOne` | `db.users.replaceOne({_id: ObjectId("123")}, {name: "John Updated"})` | ✅ YES |
| `deleteOne` | `db.users.deleteOne({email: "user@example.com"})` | ✅ YES |
| `deleteMany` | `db.users.deleteMany({status: "inactive"})` | ✅ YES |
| `find` | `db.users.find({status: "active"})` | ✅ YES |
| `findOne` | `db.users.findOne({email: "john@example.com"})` | ✅ YES |
| `createIndex` | `db.users.createIndex({email: 1}, {unique: true})` | ✅ YES |
| `dropIndex` (by name) | `db.users.dropIndex("email_index")` | ✅ YES |
| `dropIndex` (by keys) | `db.users.dropIndex({email: 1})` | ✅ YES |
| `createCollection` | `db.createCollection("users", {capped: true})` | ✅ YES |
| `dropCollection` | `db.users.drop()` | ✅ YES |
| `getCollection` | `db.getCollection("user-profiles").insertOne({name: "John"})` | ✅ YES |

### ❌ Unsupported Operations

| Command/Operation | Reference Query | Supported |
|-------------------|-----------------|-----------|
| `findOneAndUpdate` | `db.users.findOneAndUpdate({email: "john@example.com"}, {$set: {age: 31}})` | ❌ NO |
| `findOneAndDelete` | `db.users.findOneAndDelete({email: "john@example.com"})` | ❌ NO |
| `findOneAndReplace` | `db.users.findOneAndReplace({_id: ObjectId("123")}, {name: "New"})` | ❌ NO |
| `aggregate` | `db.users.aggregate([{$match: {status: "active"}}])` | ❌ NO |
| `distinct` | `db.users.distinct("department")` | ❌ NO |
| `count` | `db.users.count({status: "active"})` | ❌ NO |
| `countDocuments` | `db.users.countDocuments({status: "active"})` | ❌ NO |
| `estimatedDocumentCount` | `db.users.estimatedDocumentCount()` | ❌ NO |
| `bulkWrite` | `db.users.bulkWrite([{insertOne: {document: {name: "John"}}}])` | ❌ NO |
| `watch` | `db.users.watch()` | ❌ NO |
| `mapReduce` | `db.users.mapReduce(mapFunc, reduceFunc)` | ❌ NO |

### ⚠️ Deprecated Operations

| Command/Operation | Reference Query | Supported |
|-------------------|-----------------|-----------|
| `save` | `db.users.save({_id: ObjectId("123"), name: "John"})` | ❌ NO |
| `insert` | `db.users.insert({name: "John", email: "john@example.com"})` | ❌ NO |
| `remove` | `db.users.remove({status: "inactive"})` | ❌ NO |
| `update` | `db.users.update({status: "pending"}, {$set: {status: "active"}}, {multi: true})` | ❌ NO |
| `ensureIndex` | `db.users.ensureIndex({email: 1})` | ❌ NO |

### 🚫 Unsupported JavaScript Features

| Feature | Reference Query | Supported |
|---------|-----------------|-----------|
| Variables | `const user = {name: "John"}; db.users.insertOne(user)` | ❌ NO |
| Functions | `function createUser() {...}; db.users.insertOne(createUser())` | ❌ NO |
| Loops | `for(let i=0; i<5; i++) {db.users.insertOne({name: \`User${i}\`})}` | ❌ NO |
| Conditionals | `if(condition) {db.users.insertOne({name: "John"})}` | ❌ NO |
| Dynamic Collections | `const col = "users"; db[col].insertOne({name: "John"})` | ❌ NO |
| Imports/Requires | `const moment = require('moment')` | ❌ NO |

### 📝 Context Declaration

| Context Format | Reference Query | Supported |
|---------------|-----------------|-----------|
| Line Comment | `// context: dev` | ✅ YES |
| Block Comment | `/* context: production */` | ✅ YES |
| Database Comment | `// DATABASE: staging` | ✅ YES |

## 📖 Sample Queries for Copy-Paste

### Read Operations
```javascript
// context: dev

// Find multiple documents
db.users.find({
  status: "active",
  age: {$gte: 18}
});

// Find with projection
db.users.find(
  {status: "active"},
  {name: 1, email: 1, _id: 0}
);

// Find single document
db.users.findOne({email: "john@example.com"});

// Find with sorting and limit
db.users.find({status: "active"}).sort({createdAt: -1}).limit(10);
```

### Insert Operations
```javascript
// Insert single document
db.users.insertOne({
  name: "John Doe",
  email: "john@example.com",
  age: 30,
  status: "active"
});

// Insert multiple documents
db.users.insertMany([
  {name: "John", email: "john@example.com"},
  {name: "Jane", email: "jane@example.com"}
]);
```

### Update Operations
```javascript
// Update single document
db.users.updateOne(
  {email: "john@example.com"},
  {$set: {age: 31, lastLogin: new Date()}}
);

// Update multiple documents
db.users.updateMany(
  {status: "pending"},
  {$set: {status: "active"}}
);

// Replace entire document
db.users.replaceOne(
  {email: "john@example.com"},
  {name: "John Updated", email: "john@example.com", age: 32}
);
```

### Delete Operations
```javascript
// Delete single document
db.users.deleteOne({email: "user@example.com"});

// Delete multiple documents
db.users.deleteMany({status: "inactive"});
```

### Index Operations
```javascript
// Create index
db.users.createIndex(
  {email: 1, status: 1},
  {unique: true, name: "email_status_idx"}
);

// Drop index by name
db.users.dropIndex("email_status_idx");

// Drop index by specification
db.users.dropIndex({email: 1, status: 1});
```

### Collection Operations
```javascript
// Create collection
db.createCollection("audit_logs", {
  capped: true,
  size: 1048576
});

// Drop collection
db.old_users.drop();

// Alternative drop syntax
db.dropCollection("old_users");

// Access collection with special characters
db.getCollection("user-profiles").insertOne({
  userId: "12345",
  name: "John Doe"
});
```

## 📊 Summary Statistics

- ✅ **15 Supported Operations** - CRUD, read operations, and collection management
- ❌ **16 Unsupported Operations** - Complex operations and deprecated methods  
- ❌ **6 Unsupported JavaScript Features** - Dynamic code execution

**🔑 Key Rule:** Static MongoDB operations are supported including read operations. No variables, functions, or dynamic code execution.


## 📦 Installation

### Core Dependencies
```bash
# Install all dependencies (recommended)
pip install -r requirements.txt

# Or install only core dependencies
pip install boto3 click requests numpy pydantic
```

### RAG (Retrieval-Augmented Generation) Features
```bash
# Install all dependencies (includes RAG)
pip install -r requirements.txt

# Or install only RAG dependencies
pip install -r requirements-rag.txt
```

### Development Dependencies
```bash
# Install development tools
pip install -r requirements-dev.txt
```

## 📝 Change Control Process

1. **Create branch** from main
2. **Add query file** to `input/` directory with `.js` extension
3. **Create Pull Request** with descriptive title
4. **Execute via comment**: `/kite mongo -d <DB_NAME> -f input/query_data.js`
5. **Review results** and merge if approved

## ⚠️ Important Notes

- **Environment**: Use `-e stage|prod` flag to specify environment
- **File paths**: Always use relative paths from repository root
- **Permissions**: Write operations require approval from change approvers
- **Backup**: All write operations are automatically backed up before execution

## 🔧 Usage Examples

### MongoDB Commands

```bash
# 1. Get collection names
echo "db.getCollectionNames()" > test1.js
PYTHONPATH=src python -m kite mongo -d pp_data_common_production -f test1.js

# 2. Get database stats
echo "db.stats()" > test2.js
PYTHONPATH=src python -m kite mongo -d pp_data_common_production -f test2.js

# 3. Count documents
echo "db.users.count()" > test3.js
PYTHONPATH=src python -m kite mongo -d pp_data_common_production -f test3.js
```

### Liquibase Commands

```bash
# Check status
PYTHONPATH=src python -m kite liquibase -d pp_data_common_production status

# Validate changelog
PYTHONPATH=src python -m kite liquibase -d pp_data_common_production validate

# View history
PYTHONPATH=src python -m kite liquibase -d pp_data_common_production history
```

## 🔗 Helpful Links

- [MongoDB GitHub Runner Documentation](https://sequoiacg.atlassian.net/wiki/spaces/CICD/pages/edit-v2/3966108005?draftShareId=1cc0ba6d-8524-4c15-ba9a-5729403704c0)
- [Application Flow Diagram](https://lucid.app/lucidchart/44e1d698-ec14-4158-9b52-f22d95725936/edit?viewport_loc=-73%2C138%2C1794%2C934%2CtgJwuq9tjeOJH&invitationId=inv_3806c5f8-bd2c-4be1-b23b-f1f65e041b14)

## 💡 Best Practices

### Query Guidelines
- **Test first**: Always test queries in stage environment before production
- **Small batches**: Break large operations into smaller, manageable chunks
- **Documentation**: Include clear comments in your `.js` files explaining the purpose
- **Rollback plan**: Have a rollback strategy for write operations

### Common Patterns

```javascript
// Safe update pattern
db.collection.updateMany(
  { /* your filter */ },
  { $set: { /* your changes */ } },
  { multi: true }
);

// Safe delete pattern (use limit for safety)
db.collection.deleteMany(
  { /* your filter */ },
  { limit: 1000 } // Limit batch size
);
```

---

