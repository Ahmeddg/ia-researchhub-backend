package com.example.demo.controller;

import com.example.demo.service.StatisticsService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/statistics")
@Tag(name = "Statistics", description = "APIs for dashboard statistics")
public class StatisticsController {

    private final StatisticsService statisticsService;

    @Autowired
    public StatisticsController(StatisticsService statisticsService) {
        this.statisticsService = statisticsService;
    }

    @GetMapping
    @Operation(summary = "Get all dashboard statistics")
    public ResponseEntity<Map<String, Object>> getDashboardStatistics() {
        return ResponseEntity.ok(statisticsService.getDashboardStatistics());
    }

    @GetMapping("/researchers/count")
    @Operation(summary = "Get total researchers count")
    public ResponseEntity<Long> getResearchersCount() {
        return ResponseEntity.ok(statisticsService.getResearchersCount());
    }

    @GetMapping("/publications/count")
    @Operation(summary = "Get total publications count")
    public ResponseEntity<Long> getPublicationsCount() {
        return ResponseEntity.ok(statisticsService.getPublicationsCount());
    }

    @GetMapping("/projects/count")
    @Operation(summary = "Get total projects count")
    public ResponseEntity<Long> getProjectsCount() {
        return ResponseEntity.ok(statisticsService.getProjectsCount());
    }

    @GetMapping("/domains/count")
    @Operation(summary = "Get total domains count")
    public ResponseEntity<Long> getDomainsCount() {
        return ResponseEntity.ok(statisticsService.getDomainsCount());
    }

    @GetMapping("/news/count")
    @Operation(summary = "Get total news count")
    public ResponseEntity<Long> getNewsCount() {
        return ResponseEntity.ok(statisticsService.getNewsCount());
    }

    @GetMapping("/users/count")
    @Operation(summary = "Get total users count")
    public ResponseEntity<Long> getUsersCount() {
        return ResponseEntity.ok(statisticsService.getUsersCount());
    }

    @GetMapping("/publications/by-domain")
    @Operation(summary = "Get publications count grouped by domain")
    public ResponseEntity<Map<String, Long>> getPublicationsByDomain() {
        return ResponseEntity.ok(statisticsService.getPublicationsCountByDomain());
    }

    @GetMapping("/projects/by-category")
    @Operation(summary = "Get projects count grouped by AI category")
    public ResponseEntity<Map<String, Long>> getProjectsByCategory() {
        return ResponseEntity.ok(statisticsService.getProjectsCountByCategory());
    }
}
