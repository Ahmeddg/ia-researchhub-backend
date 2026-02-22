# Article Management System - PostgreSQL Setup

## Overview
This Spring Boot application has been migrated from MongoDB to PostgreSQL for improved support of complex relationships. The domain model includes Users, Roles, Researchers, Domains, Publications, Projects, and News.

## Database Setup with Docker

### Prerequisites
- Docker Desktop installed and running
- Docker Compose installed

### Quick Start

1. **Start PostgreSQL using Docker Compose:**
   ```bash
   docker-compose up -d
   ```
   This will:
   - Create a PostgreSQL 15 Alpine container
   - Set up the database: `article_db`
   - Create the user: `postgres` with password: `password`
   - Expose the database on port `5432`
   - Create a persistent volume for data

2. **Verify the database is running:**
   ```bash
   docker-compose ps
   ```

3. **Stop the database:**
   ```bash
   docker-compose down
   ```

4. **Stop and remove all data:**
   ```bash
   docker-compose down -v
   ```

## Application Configuration

The application is configured in `application.properties`:

```properties
spring.datasource.url=jdbc:postgresql://localhost:5432/article_db
spring.datasource.username=postgres
spring.datasource.password=password
spring.jpa.hibernate.ddl-auto=update
```

## Running the Application

1. **Build the project:**
   ```bash
   mvn clean package
   ```

2. **Run the Spring Boot application:**
   ```bash
   mvn spring-boot:run
   ```

The application will start on `http://localhost:8081`

## Data Model

### Entities:
- **User** - System users with roles (many-to-many relationship with Role)
- **Role** - User roles (ADMIN, USER, etc.)
- **Researcher** - Research professionals (many-to-many with Publication)
- **Domain** - Research domains/categories (one-to-many with Publication and Project)
- **Publication** - Academic publications (many-to-many with Researcher, many-to-one with Domain)
- **Project** - Research projects (many-to-one with Domain)
- **News** - News items (many-to-one with User)
- **Article** - Articles/blog posts

## Database Connection Details

- **Host:** localhost (when running Docker)
- **Port:** 5432
- **Database:** article_db
- **Username:** postgres
- **Password:** password
- **Driver:** PostgreSQL 42.7.1

## Using Alternative PostgreSQL Configuration

If you want to use a different hostname, port, or credentials, update the Docker environment variables in `docker-compose.yml`:

```yaml
environment:
  POSTGRES_DB: your_db_name
  POSTGRES_USER: your_username
  POSTGRES_PASSWORD: your_password
```

And also update `application.properties` accordingly.

## Troubleshooting

**Port already in use:**
```bash
docker-compose down
# Then try again
docker-compose up -d
```

**Need to reset database:**
```bash
docker-compose down -v
docker-compose up -d
```

**Check database logs:**
```bash
docker-compose logs postgres
```

**Connect to database directly:**
```bash
docker exec -it article-management-db psql -U postgres -d article_db
```
