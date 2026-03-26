package com.example.demo.controller;

import com.example.demo.model.News;
import com.example.demo.service.NewsService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/news")
@Tag(name = "News Management", description = "APIs for managing news articles")
public class NewsController {

    private final NewsService newsService;

    @Autowired
    public NewsController(NewsService newsService) {
        this.newsService = newsService;
    }

    @PostMapping
    @Operation(summary = "Create a new news article")
    public ResponseEntity<News> createNews(@Valid @RequestBody News news) {
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
    public ResponseEntity<News> getNewsById(@PathVariable @Parameter(description = "News ID") Long id) {
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
            @PathVariable @Parameter(description = "News ID") Long id,
            @Valid @RequestBody News newsDetails) {
        News updatedNews = newsService.update(id, newsDetails);
        return ResponseEntity.ok(updatedNews);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a news article by ID")
    public ResponseEntity<Void> deleteNews(@PathVariable @Parameter(description = "News ID") Long id) {
        newsService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
