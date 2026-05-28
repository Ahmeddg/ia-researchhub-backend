package com.example.demo.controller;

import com.example.demo.service.AiAdminService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/ai")
@Tag(name = "AI Ops", description = "Admin panel for the classification microservice")
public class AiController {

    private final AiAdminService aiAdminService;

    @Autowired
    public AiController(AiAdminService aiAdminService) {
        this.aiAdminService = aiAdminService;
    }

    // ── Section 1: Health ────────────────────────────────────────────────────

    @GetMapping("/health")
    @Operation(summary = "Extended AI service health (status, model, pending queue)")
    public ResponseEntity<Map<String, Object>> getHealth() {
        return ResponseEntity.ok(aiAdminService.getHealth());
    }

    // ── Section 1.2: HDBSCAN run log ────────────────────────────────────────

    @GetMapping("/recluster/history")
    @Operation(summary = "HDBSCAN run audit log — last N runs")
    public ResponseEntity<List<Map<String, Object>>> getReclusterHistory(
            @RequestParam(defaultValue = "20") int limit) {
        return ResponseEntity.ok(aiAdminService.getReclusterHistory(limit));
    }

    // ── Section 2: Cluster management ───────────────────────────────────────

    @GetMapping("/clusters")
    @Operation(summary = "All clusters with basic info")
    public ResponseEntity<List<Map<String, Object>>> getClusters() {
        return ResponseEntity.ok(aiAdminService.getClusters());
    }

    @GetMapping("/clusters/metrics")
    @Operation(summary = "Quality metrics for all clusters (tightness, drift, correction rate)")
    public ResponseEntity<List<Map<String, Object>>> getClusterMetrics() {
        return ResponseEntity.ok(aiAdminService.getClusterMetrics());
    }

    @GetMapping("/clusters/{id}")
    @Operation(summary = "Cluster detail: exemplars, member IDs, hierarchy")
    public ResponseEntity<Map<String, Object>> getClusterDetail(@PathVariable int id) {
        Map<String, Object> detail = aiAdminService.getClusterDetail(id);
        if (detail.isEmpty()) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(detail);
    }

    // ── Section 2.1: Recluster trigger ──────────────────────────────────────

    @PostMapping("/recluster")
    @Operation(summary = "Trigger HDBSCAN recluster (manual override)")
    public ResponseEntity<Map<String, Object>> triggerRecluster() {
        return ResponseEntity.ok(aiAdminService.triggerRecluster());
    }

    // ── Section 2.4: Close pairs ────────────────────────────────────────────

    @GetMapping("/close-pairs")
    @Operation(summary = "Find clusters with high centroid cosine similarity")
    public ResponseEntity<List<Map<String, Object>>> getClosePairs(
            @RequestParam(defaultValue = "0.90") double threshold) {
        return ResponseEntity.ok(aiAdminService.getClosePairs(threshold));
    }

    // ── Section 4.3: Pending pool count ─────────────────────────────────────

    @GetMapping("/pending/status")
    @Operation(summary = "Pending pool size and recent inflow rate")
    public ResponseEntity<Map<String, Object>> getPendingStatus() {
        return ResponseEntity.ok(aiAdminService.getPendingStatus());
    }

    // ── Section 5: Corrections ───────────────────────────────────────────────

    @GetMapping("/corrections")
    @Operation(summary = "Paginated correction history")
    public ResponseEntity<List<Map<String, Object>>> getCorrections(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int pageSize) {
        return ResponseEntity.ok(aiAdminService.getCorrections(page, pageSize));
    }
}
