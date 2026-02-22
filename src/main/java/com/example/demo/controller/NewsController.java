package com.example.demo.controller;

import com.example.demo.model.News;
import com.example.demo.repository.NewsRepository;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/api/news")
@CrossOrigin(origins = "*")
@Tag(name = "News Management", description = "APIs for managing news articles")
public class NewsController {

    @Autowired
    private NewsRepository newsRepository;

    @PostMapping
    @Operation(summary = "Create a new news article")
    public ResponseEntity<News> createNews(@RequestBody News news) {
        try {
            if (news.getCreatedAt() == null) {
                news.setCreatedAt(LocalDateTime.now());
            }
            News savedNews = newsRepository.save(news);
            return ResponseEntity.status(HttpStatus.CREATED).body(savedNews);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping
    @Operation(summary = "Get all news articles")
    public ResponseEntity<List<News>> getAllNews() {
        try {
            List<News> newsList = newsRepository.findAll();
            return ResponseEntity.ok(newsList);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get news article by ID")
    public ResponseEntity<News> getNewsById(@PathVariable @Parameter(description = "News ID") Long id) {
        try {
            Optional<News> news = newsRepository.findById(id);
            return news.map(ResponseEntity::ok)
                    .orElseGet(() -> ResponseEntity.notFound().build());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/user/{userId}")
    @Operation(summary = "Get news articles by user ID")
    public ResponseEntity<List<News>> getNewsByUserId(
            @PathVariable @Parameter(description = "User ID") Long userId) {
        try {
            List<News> newsList = newsRepository.findByUserId(userId);
            return ResponseEntity.ok(newsList);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update a news article")
    public ResponseEntity<News> updateNews(@PathVariable @Parameter(description = "News ID") Long id,
                                          @RequestBody News newsDetails) {
        try {
            Optional<News> news = newsRepository.findById(id);
            if (news.isPresent()) {
                News existingNews = news.get();
                if (newsDetails.getTitle() != null) {
                    existingNews.setTitle(newsDetails.getTitle());
                }
                if (newsDetails.getContent() != null) {
                    existingNews.setContent(newsDetails.getContent());
                }
                if (newsDetails.getUser() != null) {
                    existingNews.setUser(newsDetails.getUser());
                }
                News updatedNews = newsRepository.save(existingNews);
                return ResponseEntity.ok(updatedNews);
            } else {
                return ResponseEntity.notFound().build();
            }
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a news article by ID")
    public ResponseEntity<Void> deleteNews(@PathVariable @Parameter(description = "News ID") Long id) {
        try {
            if (newsRepository.existsById(id)) {
                newsRepository.deleteById(id);
                return ResponseEntity.noContent().build();
            } else {
                return ResponseEntity.notFound().build();
            }
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
}
