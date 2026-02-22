# Article Management System - Quick Start Guide

## Prerequisites
- Java 17+
- Maven 3.8.1+
- Docker & Docker Compose
- PostgreSQL (via Docker)

## Setup & Running the Application

### Step 1: Start PostgreSQL Database

```bash
# Navigate to project directory
cd article-management/demo

# Start PostgreSQL container
docker-compose up -d

# Verify the database is running
docker-compose ps
```

### Step 2: Build the Application

```bash
# Clean build the project
mvn clean package

# Or just compile without tests
mvn clean compile
```

### Step 3: Run the Spring Boot Application

**Option A: Using Maven**
```bash
mvn spring-boot:run
```

**Option B: Direct Java execution**
```bash
java -jar target/demo-0.0.1-SNAPSHOT.jar
```

### Step 4: Access the Application

- **Swagger UI:** http://localhost:8081/swagger-ui.html
- **API Documentation:** http://localhost:8081/api-docs
- **Health Check:** http://localhost:8081/actuator/health (if enabled)

## Swagger UI Interface

The Swagger UI provides an interactive interface to test all API endpoints:

1. **Browse Endpoints:** All endpoints are organized by resource type (Articles, Users, Roles, etc.)
2. **Test Endpoints:** Click "Try it out" on any endpoint to test it
3. **View Details:** See request/response schemas and examples
4. **Download API Spec:** Get the OpenAPI specification in JSON or YAML format

### Common Swagger Actions

#### Testing a GET endpoint
```
1. Click on the GET endpoint
2. Click "Try it out"
3. Enter any required parameters
4. Click "Execute"
5. View the response
```

#### Testing a POST endpoint
```
1. Click on the POST endpoint
2. Click "Try it out"
3. The request body schema appears
4. Enter or modify the JSON data
5. Click "Execute"
6. Check the response status (should be 201 Created)
```

#### Testing with Path Parameters
```
1. Click on the endpoint (e.g., GET /api/articles/{id})
2. Click "Try it out"
3. Enter the ID value in the parameter field
4. Click "Execute"
```

## API Endpoint Summary

| Resource | Create | Read | Update | Delete |
|----------|--------|------|--------|--------|
| Users | POST | GET | PUT | DELETE |
| Roles | POST | GET | PUT | DELETE |
| Researchers | POST | GET | PUT | DELETE |
| Domains | POST | GET | PUT | DELETE |
| Publications | POST | GET | PUT | DELETE |
| Projects | POST | GET | PUT | DELETE |
| News | POST | GET | PUT | DELETE |

## Example Workflows

### Workflow 1: Create an Article

1. Open Swagger UI: http://localhost:8081/swagger-ui.html
2. Expand "Article Management" section
3. Click POST /api/articles
4. Click "Try it out"
5. Enter JSON:
```json
{
  "title": "Introduction to AI",
  "content": "This article discusses AI fundamentals...",
  "author": "John Doe"
}
```
6. Click "Execute"
7. Article is created with auto-generated ID and timestamps

### Workflow 2: Create a Publication with Researchers

1. First, create a Domain via POST /api/domains
2. Create Researchers via POST /api/researchers
3. Create Publication via POST /api/publications with:
   - Domain ID reference
   - Researcher associations
4. View related publications via GET /api/publications/domain/{domainId}

### Workflow 3: Manage Users and Roles

1. Create Roles: POST /api/roles (e.g., "ADMIN", "USER", "EDITOR")
2. Create Users: POST /api/users
3. Assign roles (relationships stored in many-to-many table)
4. Query users: GET /api/users/{id}

## Database Management

### View Database Tables
```bash
# Connect to PostgreSQL container
docker exec -it article-management-db psql -U postgres -d article_db

# List tables
\dt

# View table structure
\d table_name

# Query data
SELECT * FROM articles;
```

### Reset Database
```bash
# Stop and remove containers and volumes
docker-compose down -v

# Restart fresh
docker-compose up -d
```

### Database Credentials
- **Host:** localhost
- **Port:** 5432
- **Database:** article_db
- **Username:** postgres
- **Password:** password

## Troubleshooting

### Application won't start
```bash
# Check if port 8081 is already in use
# Change port in application.properties: server.port=8082

# Check Java version
java -version

# Check Maven is installed
mvn -version
```

### Database connection error
```bash
# Verify PostgreSQL is running
docker-compose ps

# Check logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

### Swagger UI not loading
```bash
# Clear Maven cache
mvn clean install

# Verify dependency was added to pom.xml
# Check application.properties for Swagger config
```

### Port 5432 already in use
```bash
# Stop PostgreSQL container
docker-compose down

# Or use different port in docker-compose.yml
# Change "5432:5432" to "5433:5432"
```

## Development Tips

### Enable SQL Logging
In `application.properties`:
```properties
spring.jpa.show-sql=true
spring.jpa.properties.hibernate.format_sql=true
spring.jpa.properties.hibernate.use_sql_comments=true
```

### Database Auto-Update
- `ddl-auto=update` - Updates schema (default)
- `ddl-auto=create` - Creates fresh schema each restart
- `ddl-auto=validate` - Only validates schema
- `ddl-auto=none` - No automatic updates

### Testing Endpoints

Using command line:
```bash
# GET request
curl http://localhost:8081/api/articles

# POST request
curl -X POST http://localhost:8081/api/articles \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","content":"Content","author":"Me"}'
```

## File Structure

```
article-management/demo/
├── src/
│   ├── main/
│   │   ├── java/com/example/demo/
│   │   │   ├── config/          # Swagger config
│   │   │   ├── controller/      # API controllers
│   │   │   ├── model/           # Entity classes
│   │   │   ├── repository/      # Data repositories
│   │   │   └── DemoApplication.java
│   │   └── resources/
│   │       └── application.properties
│   └── test/
├── docker-compose.yml           # PostgreSQL setup
├── pom.xml                       # Maven dependencies
├── DATABASE_SETUP.md            # Database guide
└── API_DOCUMENTATION.md         # API reference
```

## Next Steps

1. ✅ Start the PostgreSQL container
2. ✅ Run the Spring Boot application
3. ✅ Access Swagger UI
4. ✅ Test API endpoints
5. 📝 Implement authentication/authorization
6. 📝 Add input validation
7. 📝 Implement business logic layer (Services)
8. 📝 Add unit and integration tests
9. 📝 Implement error handling
10. 📝 Deploy to production

## Support

For issues or questions:
1. Check the API_DOCUMENTATION.md for endpoint details
2. Review DATABASE_SETUP.md for database issues
3. Check application logs: `mvn spring-boot:run`
4. Verify Docker containers: `docker-compose ps`
