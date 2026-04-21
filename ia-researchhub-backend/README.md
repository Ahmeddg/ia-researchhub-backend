# Article Management System

A comprehensive Spring Boot REST API for managing articles, publications, researchers, projects, and related entities with PostgreSQL backend.

## 🚀 Quick Start

### Prerequisites
- Java 17+
- Maven 3.8.1+
- Docker & Docker Compose

### Get Running in 3 Commands

```bash
# 1. Start PostgreSQL database
docker-compose up -d

# 2. Build project
mvn clean package

# 3. Run application
mvn spring-boot:run
```

**Then visit:** http://localhost:8081/swagger-ui.html

## 📁 Project Structure

```
article-management/demo/
├── src/
│   ├── main/
│   │   ├── java/com/example/demo/
│   │   │   ├── config/           # Swagger configuration
│   │   │   ├── controller/       # REST API controllers
│   │   │   ├── model/            # JPA entities
│   │   │   ├── repository/       # Data repositories
│   │   │   └── DemoApplication.java
│   │   └── resources/
│   │       ├── application.properties
│   │       ├── data.sql          # Demo data (auto-loaded)
│   │       └── demo-data.sql     # Demo data (manual import)
│   └── test/
├── docker-compose.yml            # PostgreSQL setup
├── Dockerfile.postgres           # PostgreSQL container
├── pom.xml                        # Maven dependencies
├── QUICK_START.md                 # Step-by-step guide
├── API_DOCUMENTATION.md           # API endpoint reference
├── DATABASE_SETUP.md              # Database configuration
├── DATABASE_INIT.md               # Demo data setup
└── README.md                      # This file
```

## 💾 Database

### PostgreSQL Setup
```bash
# Start database
docker-compose up -d

# Stop database
docker-compose down

# Reset database (delete all data)
docker-compose down -v
```

Connection details:
- **Host:** localhost
- **Port:** 5432
- **Database:** article_db
- **User:** postgres
- **Password:** password

## 📊 Demo Data

The application automatically loads realistic demo data including:
- **5 Users** with roles (Admin, User, Editor, Researcher)
- **4 Roles** for access control
- **5 Researchers** from top universities
- **5 Domains** (AI, Data Science, Computer Vision, NLP, Robotics)
- **5 Articles** with various topics
- **5 Publications** with real academic papers
- **5 Projects** in different AI categories
- **5 News** items from different users

Auto-loaded on startup via `data.sql`. See [DATABASE_INIT.md](DATABASE_INIT.md) for details.

## 🔗 API Endpoints

### Base URL: `http://localhost:8081/api`

| Resource | Endpoints | 
|----------|-----------|
| **Articles** | GET, POST, PUT, DELETE `/articles` |
| **Users** | GET, POST, PUT, DELETE `/users` |
| **Roles** | GET, POST, PUT, DELETE `/roles` |
| **Researchers** | GET, POST, PUT, DELETE `/researchers` |
| **Domains** | GET, POST, PUT, DELETE `/domains` |
| **Publications** | GET, POST, PUT, DELETE `/publications` |
| **Projects** | GET, POST, PUT, DELETE `/projects` |
| **News** | GET, POST, PUT, DELETE `/news` |

### Advanced Queries
```
GET /api/articles/author/{author}          # Get articles by author
GET /api/articles/published/all              # Get published articles
GET /api/users/username/{username}          # Find user by username
GET /api/users/email/{email}                # Find user by email
GET /api/publications/doi/{doi}              # Find publication by DOI
GET /api/publications/domain/{domainId}     # Get publications in domain
GET /api/projects/category/{aiCategory}    # Find projects by AI category
GET /api/news/user/{userId}                 # Get news from specific user
```

## 🔍 Interactive API Testing

### Swagger UI
```
http://localhost:8081/swagger-ui.html
```
Features:
- Browse all endpoints
- Test endpoints interactively
- View request/response schemas
- Download OpenAPI specification

### cURL Examples
```bash
# Get all articles
curl http://localhost:8081/api/articles

# Create article
curl -X POST http://localhost:8081/api/articles \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","content":"Content","author":"Me"}'

# Get user by email
curl http://localhost:8081/api/users/email/john@example.com

# Get published articles
curl http://localhost:8081/api/articles/published/all
```

## 🏗️ Application Architecture

```
┌─────────────────────────────────────────────────┐
│           Swagger UI & OpenAPI Docs             │
│         http://localhost:8081/swagger-ui        │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│         REST Controllers (@RestController)      │
│  ArticleController, UserController, etc.        │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│     Data Access (JpaRepository Interfaces)      │
│  ArticleRepository, UserRepository, etc.        │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│     Hibernate ORM (Entity Mapping)               │
│  @Entity, @Table, @JoinColumn annotations       │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│       PostgreSQL Database (Docker)              │
│      localhost:5432, article_db                 │
└─────────────────────────────────────────────────┘
```

## 📝 Entity Relationships

```
User (Many) ──→ Roles (Many)
   ↓
News (Many) ──→ User (One)

Researcher (Many) ──→ Publications (Many)
   
Publication (Many) ──→ Domain (One)

Project (Many) ──→ Domain (One)

Article (Independent)
```

## 🛠️ Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Runtime** | Java | 17+ |
| **Framework** | Spring Boot | 4.0.3 |
| **ORM** | Hibernate/JPA | 6.x |
| **Database** | PostgreSQL | 15 (Alpine) |
| **API Docs** | Springdoc OpenAPI | 2.1.0 |
| **Build Tool** | Maven | 3.8.1+ |
| **Container** | Docker | Latest |

## 📚 Documentation

- [QUICK_START.md](QUICK_START.md) - Step-by-step setup and usage guide
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Complete API endpoint reference with examples
- [DATABASE_SETUP.md](DATABASE_SETUP.md) - Database configuration and Docker setup
- [DATABASE_INIT.md](DATABASE_INIT.md) - Demo data initialization guide

## ✅ Verification Checklist

- [ ] Docker installed and running
- [ ] PostgreSQL container started: `docker-compose ps`
- [ ] Application running: `mvn spring-boot:run`
- [ ] Swagger accessible: http://localhost:8081/swagger-ui.html
- [ ] Demo data loaded: GET `/api/projects` returns 5 projects
- [ ] All endpoints functional via Swagger UI

## 🔧 Configuration

### Change Database Credentials
Edit `docker-compose.yml`:
```yaml
environment:
  POSTGRES_DB: my_db
  POSTGRES_USER: my_user
  POSTGRES_PASSWORD: my_password
```

Then update `application.properties`:
```properties
spring.datasource.url=jdbc:postgresql://localhost:5432/my_db
spring.datasource.username=my_user
spring.datasource.password=my_password
```

### Change Application Port
Edit `application.properties`:
```properties
server.port=8082
```

### Disable Auto-Data Loading
Edit `application.properties`:
```properties
spring.sql.init.mode=never
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Change port in application.properties
server.port=8082
```

### Database Connection Failed
```bash
# Restart PostgreSQL
docker-compose down
docker-compose up -d
```

### No Data in Database
```bash
# Check data.sql exists
ls -la src/main/resources/data.sql

# Verify logs for errors
mvn spring-boot:run | grep -i error
```

See [QUICK_START.md](QUICK_START.md#troubleshooting) for more solutions.

## 🚢 Deployment

### Production Checklist
- [ ] Change default passwords
- [ ] Use environment variables for secrets
- [ ] Disable SQL logging (`spring.jpa.show-sql=false`)
- [ ] Set `ddl-auto=validate` 
- [ ] Implement authentication
- [ ] Enable HTTPS
- [ ] Set up PostgreSQL backups
- [ ] Configure firewall rules

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the Apache License 2.0 - see LICENSE file for details.

## 👥 Support

For issues or questions:
1. Check the documentation files
2. Review Swagger UI at http://localhost:8081/swagger-ui.html
3. Check application logs
4. Consult the troubleshooting section

## 🎯 Roadmap

- [ ] User authentication (JWT)
- [ ] Role-based access control (RBAC)
- [ ] Advanced search and filtering
- [ ] Export to PDF/CSV
- [ ] Email notifications
- [ ] Admin dashboard
- [ ] API versioning
- [ ] GraphQL support
- [ ] Caching layer
- [ ] Audit logging

## 📞 Contact

Email: support@articlemgmt.com

---

**Ready to dive in?** Start with [QUICK_START.md](QUICK_START.md)!
