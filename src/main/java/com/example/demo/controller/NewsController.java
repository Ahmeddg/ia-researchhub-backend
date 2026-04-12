package com.example.demo.controller;

import com.example.demo.dto.CreateNewsRequest;
import com.example.demo.exception.ResourceNotFoundException;
import com.example.demo.model.News;
import com.example.demo.model.User;
import com.example.demo.service.NewsService;
import com.example.demo.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;

@RestController
@RequestMapping("/api/news")
@Tag(name = "News Management", description = "APIs for managing news articles")
public class NewsController {

    private final NewsService newsService;
    private final UserService userService;

    @Autowired
    public NewsController(NewsService newsService, UserService userService) {
        this.newsService = newsService;
        this.userService = userService;
    }

    @PostMapping
    @Operation(summary = "Create a new news article")
    public ResponseEntity<News> createNews(@Valid @RequestBody CreateNewsRequest request) {
        String username = currentUsername();
        User user = userService.findByUsername(username)
                .orElseThrow(() -> new ResourceNotFoundException("User", "username", username));

        News news = new News();
        news.setTitle(request.getTitle());
        news.setContent(request.getContent());
        news.setCategory(request.getCategory());
        news.setExcerpt(request.getExcerpt());
        news.setImageUrl(request.getImageUrl());
        news.setReadTime(request.getReadTime());
        news.setFeatured(request.getFeatured() != null && request.getFeatured());
        news.setTags(request.getTags());
        news.setAuthor(request.getAuthor());
        news.setUser(user);
        
        // Set publishedAt if provided, otherwise set to creation time
        if (request.getPublishedAt() != null && !request.getPublishedAt().isEmpty()) {
            try {
                news.setPublishedAt(LocalDateTime.parse(request.getPublishedAt()));
            } catch (Exception e) {
                news.setPublishedAt(LocalDateTime.now());
            }
        } else {
            news.setPublishedAt(LocalDateTime.now());
        }

        News savedNews = newsService.create(news);
        return ResponseEntity.status(HttpStatus.CREATED).body(savedNews);
    }

    @GetMapping
    @Operation(summary = "Get all news articles")
    public ResponseEntity<List<News>> getAllNews() {
        List<News> newsList = newsService.findAll();
        return ResponseEntity.ok(newsList);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get news article by ID")
    public ResponseEntity<News> getNewsById(@PathVariable("id") @Parameter(description = "News ID") Long id) {
        return newsService.findById(id)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @GetMapping("/latest")
    @Operation(summary = "Get latest news articles")
    public ResponseEntity<List<News>> getLatestNews(
            @RequestParam(defaultValue = "5") @Parameter(description = "Number of news to retrieve") int limit) {
        List<News> newsList = newsService.findLatest(limit);
        return ResponseEntity.ok(newsList);
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update a news article")
    public ResponseEntity<News> updateNews(
            @PathVariable("id") @Parameter(description = "News ID") Long id,
            @RequestBody CreateNewsRequest request) {
        enforceAdminOrModeratorAccess();
        
        News existingNews = newsService.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("News", "id", id));

        // Update only the fields that are provided (not null)
        if (request.getTitle() != null && !request.getTitle().isEmpty()) {
            existingNews.setTitle(request.getTitle());
        }
        if (request.getContent() != null && !request.getContent().isEmpty()) {
            existingNews.setContent(request.getContent());
        }
        if (request.getCategory() != null && !request.getCategory().isEmpty()) {
            existingNews.setCategory(request.getCategory());
        }
        if (request.getExcerpt() != null && !request.getExcerpt().isEmpty()) {
            existingNews.setExcerpt(request.getExcerpt());
        }
        if (request.getImageUrl() != null && !request.getImageUrl().isEmpty()) {
            existingNews.setImageUrl(request.getImageUrl());
        }
        if (request.getReadTime() != null) {
            existingNews.setReadTime(request.getReadTime());
        }
        if (request.getFeatured() != null) {
            existingNews.setFeatured(request.getFeatured());
        }
        if (request.getTags() != null && !request.getTags().isEmpty()) {
            existingNews.setTags(request.getTags());
        }
        if (request.getAuthor() != null && !request.getAuthor().isEmpty()) {
            existingNews.setAuthor(request.getAuthor());
        }
        if (request.getPublishedAt() != null && !request.getPublishedAt().isEmpty()) {
            try {
                existingNews.setPublishedAt(LocalDateTime.parse(request.getPublishedAt()));
            } catch (Exception e) {
                // Keep existing publishedAt if parsing fails
            }
        }

        News updatedNews = newsService.update(id, existingNews);
        return ResponseEntity.ok(updatedNews);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a news article by ID")
    public ResponseEntity<Void> deleteNews(@PathVariable("id") @Parameter(description = "News ID") Long id) {
        enforceAdminOrModeratorAccess();
        
        if (!newsService.findById(id).isPresent()) {
            throw new ResourceNotFoundException("News", "id", id);
        }
        
        newsService.delete(id);
        return ResponseEntity.noContent().build();
    }

    private String currentUsername() {
        return SecurityContextHolder.getContext().getAuthentication().getName();
    }

    private void enforceAdminOrModeratorAccess() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        boolean allowed = authentication.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .anyMatch(authority -> authority.equals("ROLE_ADMIN")
                        || authority.equals("ROLE_MODERATOR"));
        if (!allowed) {
            throw new AccessDeniedException("Only admins and moderators can manage news articles");
        }
    }
}
