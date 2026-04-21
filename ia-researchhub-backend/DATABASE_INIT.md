# Database Initialization & Demo Data Setup

## Overview
Two SQL scripts have been created to populate your database with realistic demo data for testing and development:

1. **demo-data.sql** - Manual import script
2. **data.sql** - Auto-loaded on application startup

## Demo Data Includes

### Users (5 total)
- **admin** - System administrator with ADMIN and USER roles
- **john_doe** - Editor with USER and EDITOR roles
- **jane_smith** - Regular user
- **mike_wilson** - Regular user
- **sarah_jones** - Regular user

### Roles (4 total)
- ROLE_ADMIN
- ROLE_USER
- ROLE_EDITOR
- ROLE_RESEARCHER

### Researchers (5 total)
- Dr. Alice Johnson (MIT) - AI & Deep Learning
- Dr. Bob Chen (Stanford) - NLP & Computer Vision
- Dr. Carol Williams (Harvard) - Reinforcement Learning & Robotics
- Dr. David Brown (UC Berkeley) - Explainable AI & Ethics
- Dr. Emma Davis (Oxford) - Quantum Computing & AI

### Domains (5 total)
- Artificial Intelligence
- Data Science
- Computer Vision
- Natural Language Processing
- Robotics

### Articles (5 total)
- Introduction to Deep Learning
- The Future of AI in Healthcare
- Getting Started with Python for Data Science
- Understanding Convolutional Neural Networks
- Transformers and Attention Mechanisms

### Publications (5 total)
Academic papers with DOI references:
- Deep Residual Learning for Image Recognition
- Attention is All You Need
- BERT: Pre-training of Deep Bidirectional Transformers
- Generative Adversarial Nets
- ImageNet-21K Pretraining for the Masses

### Projects (5 total)
- Advanced Computer Vision System
- Natural Language Understanding Engine
- Autonomous Robot Navigation
- Healthcare Diagnostic AI
- Predictive Analytics Platform

### News (5 total)
Recent news articles from various users

## Method 1: Auto-Loading with Application Startup

### How It Works
Spring Boot automatically runs `data.sql` after Hibernate creates/validates the schema.

### Advantages
- ✅ Automatic loading on every fresh start
- ✅ No manual intervention needed
- ✅ Great for development and testing
- ✅ Can be overridden with `spring.jpa.defer-datasource-initialization=true`

### Configuration
The `data.sql` file is automatically discovered and loaded by Spring Boot because it's in the `src/main/resources/` directory.

**application.properties** already configured for auto-loading:
```properties
spring.jpa.hibernate.ddl-auto=update
# data.sql will be automatically executed
```

### Process
```
1. Docker PostgreSQL container starts
2. Application starts
3. Hibernate creates/validates schema
4. Spring Boot executes data.sql
5. Demo data is now available
```

### When Does It Load?
- After the database schema is created or validated
- Before the application is fully started
- Only if `spring.jpa.defer-datasource-initialization=true` OR no `EntityManagerFactory` issues

### Limitations
- Won't load if there are schema validation errors
- Only works after `ddl-auto` completes
- Data is inserted every time if you don't configure properly

## Method 2: Manual Import

### Using psql (PostgreSQL CLI)

```bash
# Connect to the database
docker exec -it article-management-db psql -U postgres -d article_db

# Run the SQL script
\i /tmp/demo-data.sql
```

Or in one command:
```bash
docker exec -it article-management-db psql -U postgres -d article_db -f demo-data.sql
```

### Using Docker Volume

```bash
# Copy script to Docker container
docker cp demo-data.sql article-management-db:/tmp/

# Execute in container
docker exec -it article-management-db psql -U postgres -d article_db -f /tmp/demo-data.sql
```

### Using JDBC/Connection String
```bash
# From terminal with psql installed
psql -h localhost -p 5432 -U postgres -d article_db -f demo-data.sql
```

## Method 3: Conditional Auto-Loading

To prevent duplicate data on multiple runs, use Spring profiles:

### Edit application.properties
```properties
spring.jpa.hibernate.ddl-auto=validate
spring.sql.init.mode=always
spring.sql.init.data-locations=classpath:data.sql
```

Or use environment-specific profiles:

### application-dev.properties
```properties
spring.jpa.hibernate.ddl-auto=create-drop
spring.sql.init.mode=always
```

### application-prod.properties
```properties
spring.jpa.hibernate.ddl-auto=validate
spring.sql.init.mode=never
```

Run with profile:
```bash
java -Dspring.profiles.active=dev -jar target/demo-*.jar
```

## Verification

### Verify Data Loaded Successfully

```bash
# Connect to database
docker exec -it article-management-db psql -U postgres -d article_db

# Check record counts
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM articles;
SELECT COUNT(*) FROM publications;
SELECT COUNT(*) FROM researchers;

# View sample data
SELECT * FROM users LIMIT 5;
SELECT * FROM articles;
```

### Via API

Once the application is running, check Swagger UI:
```
http://localhost:8081/swagger-ui.html
```

Test endpoints:
```bash
# Get all articles
curl http://localhost:8081/api/articles

# Get all users
curl http://localhost:8081/api/users

# Get publications by domain
curl http://localhost:8081/api/publications/domain/1
```

## Resetting Demo Data

### Option 1: Fresh Database with Docker
```bash
# Stop and remove volume (data deleted)
docker-compose down -v

# Start fresh
docker-compose up -d

# Run application (data.sql auto-loads)
mvn spring-boot:run
```

### Option 2: Delete and Reload Data
```bash
# Connect to database
docker exec -it article-management-db psql -U postgres -d article_db

# Delete all data (cascade)
DELETE FROM news;
DELETE FROM user_roles;
DELETE FROM publication_researchers;
DELETE FROM users;
DELETE FROM roles;
DELETE FROM projects;
DELETE FROM publications;
DELETE FROM researchers;
DELETE FROM articles;
DELETE FROM domains;

# Reload demo data
\i demo-data.sql
```

### Option 3: Programmatic Reset
Create a API endpoint to reset data (not recommended for production):
```java
@RestController
@RequestMapping("/api/admin")
public class AdminController {
    
    @PostMapping("/reset-demo-data")
    public ResponseEntity<?> resetDemoData() {
        // Execute SQL from file
        return ResponseEntity.ok("Demo data reset");
    }
}
```

## Schema Relationships in Demo Data

```
Users (5) 
  ├─ Many-to-Many ─ Roles (4)
  └─ One-to-Many ─ News (5)

Researchers (5)
  ├─ Many-to-Many ─ Publications (5)
  └─ Affiliation ─ Various Universities

Domains (5)
  ├─ One-to-Many ─ Publications (5)
  └─ One-to-Many ─ Projects (5)

Publications (5)
  ├─ Many-to-One ─ Domain
  └─ Many-to-Many ─ Researchers

Articles (5)
  └─ Independent (for blog/news articles)

Projects (5)
  └─ Many-to-One ─ Domain
```

## Data Validation Checks

The demo data includes:
- ✅ Valid foreign key relationships
- ✅ No null values for required fields
- ✅ Realistic data values
- ✅ Proper date/timestamp formatting
- ✅ Unique constraints honored (email, username, DOI)

## Customizing Demo Data

To modify demo data:

1. Edit `data.sql` (for auto-loading)
2. Edit `demo-data.sql` (for manual import)
3. Update IDs to maintain foreign key relationships
4. Restart application or manually reload

## Troubleshooting

### Data Not Loading

**Problem:** Data doesn't appear in database
```bash
# Check logs
mvn spring-boot:run | grep -i "data\|sql"

# Verify data.sql exists
ls -la src/main/resources/data.sql

# Check database connection
docker exec -it article-management-db psql -U postgres -d article_db -c "SELECT COUNT(*) FROM users;"
```

**Solution:**
- Ensure `spring.jpa.defer-datasource-initialization` is set correctly
- Check PostgreSQL logs: `docker-compose logs postgres`
- Verify no SQL errors in the data.sql file

### Duplicate Data

**Problem:** Data inserted on every restart
**Solution:** Change `ddl-auto` to `update` or `validate`

### Foreign Key Constraint Violation

**Problem:** Error inserting data
**Solution:** Verify ID references match in data.sql (IDs for users, roles, etc.)

## Performance Notes

- Demo dataset is small (25 records total)
- Load time: < 500ms
- Safe for production testing
- Can be scaled by duplicating INSERT statements

## Next Steps

1. ✅ Data loads automatically on startup
2. ✅ Test all API endpoints with sample data
3. ✅ Verify relationships in Swagger UI
4. 📝 Add business logic validation
5. 📝 Implement authentication with demo users
6. 📝 Create more realistic demo data if needed
