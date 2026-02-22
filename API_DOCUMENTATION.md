# Article Management System - API Documentation

## Overview
The Article Management System provides a complete REST API for managing articles, publications, researchers, projects, and related entities with a PostgreSQL database backend.

## Accessing the Swagger UI

### Interactive API Documentation
Once the application is running, access the Swagger UI at:
```
http://localhost:8081/swagger-ui.html
```

### OpenAPI JSON Specification
Download the OpenAPI specification at:
```
http://localhost:8081/api-docs
```

## API Endpoints

### Authentication & Authorization
*Note: User authentication and role-based access control can be implemented as needed.*

### 1. Article Management

#### Create Article
- **Method:** `POST /api/articles`
- **Description:** Create a new article
- **Request Body:**
```json
{
  "title": "Article Title",
  "content": "Article content",
  "author": "Author Name"
}
```

#### Get All Articles
- **Method:** `GET /api/articles`
- **Description:** Retrieve all articles

#### Get Article by ID
- **Method:** `GET /api/articles/{id}`
- **Description:** Retrieve specific article

#### Get Articles by Author
- **Method:** `GET /api/articles/author/{author}`
- **Description:** Search articles by author name

#### Get Published Articles
- **Method:** `GET /api/articles/published/all`
- **Description:** Get all published articles

#### Update Article
- **Method:** `PUT /api/articles/{id}`
- **Description:** Update an article

#### Delete Article
- **Method:** `DELETE /api/articles/{id}`
- **Description:** Delete an article

#### Delete All Articles
- **Method:** `DELETE /api/articles`
- **Description:** Delete all articles

---

### 2. User Management

#### Create User
- **Method:** `POST /api/users`
- **Description:** Create a new user
- **Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "password123",
  "enabled": true
}
```

#### Get All Users
- **Method:** `GET /api/users`
- **Description:** Retrieve all users

#### Get User by ID
- **Method:** `GET /api/users/{id}`

#### Get User by Username
- **Method:** `GET /api/users/username/{username}`

#### Get User by Email
- **Method:** `GET /api/users/email/{email}`

#### Update User
- **Method:** `PUT /api/users/{id}`

#### Delete User
- **Method:** `DELETE /api/users/{id}`

---

### 3. Role Management

#### Create Role
- **Method:** `POST /api/roles`
- **Request Body:**
```json
{
  "name": "ROLE_ADMIN"
}
```

#### Get All Roles
- **Method:** `GET /api/roles`

#### Get Role by ID
- **Method:** `GET /api/roles/{id}`

#### Get Role by Name
- **Method:** `GET /api/roles/name/{name}`

#### Update Role
- **Method:** `PUT /api/roles/{id}`

#### Delete Role
- **Method:** `DELETE /api/roles/{id}`

---

### 4. Researcher Management

#### Create Researcher
- **Method:** `POST /api/researchers`
- **Request Body:**
```json
{
  "fullName": "Dr. Jane Smith",
  "email": "jane@university.edu",
  "affiliation": "MIT",
  "biography": "Research biography..."
}
```

#### Get All Researchers
- **Method:** `GET /api/researchers`

#### Get Researcher by ID
- **Method:** `GET /api/researchers/{id}`

#### Get Researcher by Email
- **Method:** `GET /api/researchers/email/{email}`

#### Update Researcher
- **Method:** `PUT /api/researchers/{id}`

#### Delete Researcher
- **Method:** `DELETE /api/researchers/{id}`

---

### 5. Domain Management

#### Create Domain
- **Method:** `POST /api/domains`
- **Request Body:**
```json
{
  "name": "Artificial Intelligence",
  "description": "AI and Machine Learning research domain"
}
```

#### Get All Domains
- **Method:** `GET /api/domains`

#### Get Domain by ID
- **Method:** `GET /api/domains/{id}`

#### Get Domain by Name
- **Method:** `GET /api/domains/name/{name}`

#### Update Domain
- **Method:** `PUT /api/domains/{id}`

#### Delete Domain
- **Method:** `DELETE /api/domains/{id}`

---

### 6. Publication Management

#### Create Publication
- **Method:** `POST /api/publications`
- **Request Body:**
```json
{
  "title": "Research Paper Title",
  "abstractText": "Abstract of the paper",
  "publicationDate": "2024-02-22",
  "pdfUrl": "https://example.com/paper.pdf",
  "doi": "10.1234/example.doi",
  "domain": {
    "id": 1
  }
}
```

#### Get All Publications
- **Method:** `GET /api/publications`

#### Get Publication by ID
- **Method:** `GET /api/publications/{id}`

#### Get Publication by DOI
- **Method:** `GET /api/publications/doi/{doi}`

#### Get Publications by Domain
- **Method:** `GET /api/publications/domain/{domainId}`

#### Update Publication
- **Method:** `PUT /api/publications/{id}`

#### Delete Publication
- **Method:** `DELETE /api/publications/{id}`

---

### 7. Project Management

#### Create Project
- **Method:** `POST /api/projects`
- **Request Body:**
```json
{
  "title": "AI Research Project",
  "description": "Project description",
  "aiCategory": "Deep Learning",
  "domain": {
    "id": 1
  }
}
```

#### Get All Projects
- **Method:** `GET /api/projects`

#### Get Project by ID
- **Method:** `GET /api/projects/{id}`

#### Get Projects by Domain
- **Method:** `GET /api/projects/domain/{domainId}`

#### Get Projects by AI Category
- **Method:** `GET /api/projects/category/{aiCategory}`

#### Update Project
- **Method:** `PUT /api/projects/{id}`

#### Delete Project
- **Method:** `DELETE /api/projects/{id}`

---

### 8. News Management

#### Create News
- **Method:** `POST /api/news`
- **Request Body:**
```json
{
  "title": "Latest News",
  "content": "News content",
  "user": {
    "id": 1
  }
}
```

#### Get All News
- **Method:** `GET /api/news`

#### Get News by ID
- **Method:** `GET /api/news/{id}`

#### Get News by User
- **Method:** `GET /api/news/user/{userId}`

#### Update News
- **Method:** `PUT /api/news/{id}`

#### Delete News
- **Method:** `DELETE /api/news/{id}`

---

## Data Model Relationships

```
User 1 ---> Many Roles (Many-to-Many)
Researcher Many ---> Many Publications (Many-to-Many)
Publication Many ---> One Domain (Many-to-One)
Project Many ---> One Domain (Many-to-One)
News Many ---> One User (Many-to-One)
```

## Response Codes

- **200 OK:** Successful GET request
- **201 Created:** Successful POST request (resource created)
- **204 No Content:** Successful DELETE request
- **400 Bad Request:** Invalid request data
- **404 Not Found:** Resource not found
- **500 Internal Server Error:** Server error

## Example cURL Commands

### Create a User
```bash
curl -X POST http://localhost:8081/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "password123",
    "enabled": true
  }'
```

### Get All Articles
```bash
curl -X GET http://localhost:8081/api/articles
```

### Update an Article
```bash
curl -X PUT http://localhost:8081/api/articles/1 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Title",
    "content": "Updated content",
    "author": "John Doe",
    "published": true
  }'
```

### Delete an Article
```bash
curl -X DELETE http://localhost:8081/api/articles/1
```

## Testing with Swagger UI

1. Navigate to `http://localhost:8081/swagger-ui.html`
2. Select an endpoint by clicking on it
3. Click the "Try it out" button
4. Fill in the required parameters
5. Click "Execute" to test the endpoint
6. View the response and response code

## Running the Application

```bash
# Build the project
mvn clean package

# Run the application
mvn spring-boot:run
```

The API will be available at `http://localhost:8081`

## Error Handling

All endpoints return appropriate HTTP status codes and error messages:

```json
{
  "timestamp": "2024-02-22T10:30:00",
  "status": 404,
  "message": "Article not found",
  "path": "/api/articles/999"
}
```

## Security Considerations

1. Passwords should be encrypted in production
2. Implement authentication and authorization
3. Use HTTPS in production
4. Validate all input data
5. Implement rate limiting
6. Use parameterized queries (already done with JPA)
