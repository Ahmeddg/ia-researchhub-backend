package com.example.demo.controller;

import com.example.demo.service.PublicationService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/ai")
@Tag(name = "AI Insights", description = "AI-powered analysis and clustering tools")
public class AiController {

    private final PublicationService publicationService;

    @Autowired
    public AiController(PublicationService publicationService) {
        this.publicationService = publicationService;
    }

    @GetMapping("/health")
    @Operation(summary = "Check AI service health")
    public ResponseEntity<Map<String, Object>> getAiHealth() {
        Map<String, Object> health = new HashMap<>();
        health.put("status", "UP");
        health.put("mode", "LOCAL_FALLBACK");
        health.put("version", "1.0.0");
        return ResponseEntity.ok(health);
    }

    @GetMapping("/clusters")
    @Operation(summary = "Get all AI-generated clusters")
    public ResponseEntity<List<Map<String, Object>>> getClusters() {
        Map<Integer, String> clusters = publicationService.findAll().stream()
                .filter(p -> p.getClusterId() != null)
                .collect(Collectors.toMap(
                        p -> p.getClusterId(),
                        p -> p.getClusterLabel(),
                        (existing, replacement) -> existing
                ));

        List<Map<String, Object>> result = clusters.entrySet().stream()
                .map(e -> {
                    Map<String, Object> map = new HashMap<>();
                    map.put("id", e.getKey());
                    map.put("label", e.getValue());
                    map.put("count", publicationService.findAll().stream()
                            .filter(p -> e.getKey().equals(p.getClusterId())).count());
                    return map;
                })
                .collect(Collectors.toList());

        return ResponseEntity.ok(result);
    }

    @PostMapping("/recluster")
    @Operation(summary = "Trigger global AI re-clustering")
    public ResponseEntity<Map<String, String>> triggerRecluster() {
        Map<String, String> response = new HashMap<>();
        response.put("message", "Re-clustering triggered successfully (Simulated)");
        return ResponseEntity.ok(response);
    }
    
    @GetMapping("/close-pairs")
    @Operation(summary = "Find publications with high similarity")
    public ResponseEntity<List<Object>> getClosePairs() {
        return ResponseEntity.ok(new ArrayList<>());
    }
}
