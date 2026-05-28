
package com.example.demo.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.*;

/**
 * Admin-facing proxy to the Python classification microservice.
 * All AI Ops page data flows through this service.
 */
@Service
public class AiAdminService {

    private static final Logger log = LoggerFactory.getLogger(AiAdminService.class);

    private final RestTemplate restTemplate;
    private final String baseUrl;

    public AiAdminService(@Value("${classification.service.url}") String baseUrl) {
        this.restTemplate = new RestTemplate();
        this.baseUrl = baseUrl;
    }

    // ── Health ───────────────────────────────────────────────────────────────

    public Map<String, Object> getHealth() {
        try {
            ResponseEntity<Map<String, Object>> resp = restTemplate.exchange(
                    baseUrl + "/health", HttpMethod.GET, null,
                    new ParameterizedTypeReference<>() {});
            return resp.getStatusCode().is2xxSuccessful() && resp.getBody() != null
                    ? resp.getBody() : fallbackDown();
        } catch (RestClientException e) {
            log.warn("AI health check failed: {}", e.getMessage());
            return fallbackDown();
        }
    }

    // ── Clusters ─────────────────────────────────────────────────────────────

    public List<Map<String, Object>> getClusters() {
        try {
            ResponseEntity<List<Map<String, Object>>> resp = restTemplate.exchange(
                    baseUrl + "/clusters", HttpMethod.GET, null,
                    new ParameterizedTypeReference<>() {});
            return resp.getStatusCode().is2xxSuccessful() && resp.getBody() != null
                    ? resp.getBody() : Collections.emptyList();
        } catch (RestClientException e) {
            log.warn("Failed to fetch clusters: {}", e.getMessage());
            return Collections.emptyList();
        }
    }

    public Map<String, Object> getClusterDetail(int clusterId) {
        try {
            ResponseEntity<Map<String, Object>> resp = restTemplate.exchange(
                    baseUrl + "/clusters/" + clusterId, HttpMethod.GET, null,
                    new ParameterizedTypeReference<>() {});
            return resp.getStatusCode().is2xxSuccessful() && resp.getBody() != null
                    ? resp.getBody() : Collections.emptyMap();
        } catch (RestClientException e) {
            log.warn("Failed to fetch cluster {}: {}", clusterId, e.getMessage());
            return Collections.emptyMap();
        }
    }

    public List<Map<String, Object>> getClusterMetrics() {
        try {
            ResponseEntity<List<Map<String, Object>>> resp = restTemplate.exchange(
                    baseUrl + "/clusters/metrics", HttpMethod.GET, null,
                    new ParameterizedTypeReference<>() {});
            return resp.getStatusCode().is2xxSuccessful() && resp.getBody() != null
                    ? resp.getBody() : Collections.emptyList();
        } catch (RestClientException e) {
            log.warn("Failed to fetch cluster metrics: {}", e.getMessage());
            return Collections.emptyList();
        }
    }

    // ── Recluster ────────────────────────────────────────────────────────────

    public Map<String, Object> triggerRecluster() {
        try {
            ResponseEntity<Map<String, Object>> resp = restTemplate.exchange(
                    baseUrl + "/recluster", HttpMethod.POST,
                    new HttpEntity<>(Collections.emptyMap()),
                    new ParameterizedTypeReference<>() {});
            return resp.getStatusCode().is2xxSuccessful() && resp.getBody() != null
                    ? resp.getBody() : Map.of("error", "No response body");
        } catch (RestClientException e) {
            log.error("Failed to trigger recluster: {}", e.getMessage());
            return Map.of("error", e.getMessage());
        }
    }

    public List<Map<String, Object>> getReclusterHistory(int limit) {
        try {
            ResponseEntity<List<Map<String, Object>>> resp = restTemplate.exchange(
                    baseUrl + "/recluster/history?limit=" + limit, HttpMethod.GET, null,
                    new ParameterizedTypeReference<>() {});
            return resp.getStatusCode().is2xxSuccessful() && resp.getBody() != null
                    ? resp.getBody() : Collections.emptyList();
        } catch (RestClientException e) {
            log.warn("Failed to fetch recluster history: {}", e.getMessage());
            return Collections.emptyList();
        }
    }

    // ── Close Pairs ──────────────────────────────────────────────────────────

    public List<Map<String, Object>> getClosePairs(double threshold) {
        try {
            ResponseEntity<List<Map<String, Object>>> resp = restTemplate.exchange(
                    baseUrl + "/close-pairs?threshold=" + threshold, HttpMethod.GET, null,
                    new ParameterizedTypeReference<>() {});
            return resp.getStatusCode().is2xxSuccessful() && resp.getBody() != null
                    ? resp.getBody() : Collections.emptyList();
        } catch (RestClientException e) {
            log.warn("Failed to fetch close pairs: {}", e.getMessage());
            return Collections.emptyList();
        }
    }

    // ── Pending Pool ─────────────────────────────────────────────────────────

    public Map<String, Object> getPendingStatus() {
        try {
            // GET /clusters/metrics gives us pending_inflow_rate; we also need raw count.
            // FastAPI /health returns pending_count if present.
            Map<String, Object> health = getHealth();
            int pendingCount = health.containsKey("pending_count")
                    ? ((Number) health.get("pending_count")).intValue() : -1;
            return Map.of("pending_count", pendingCount);
        } catch (Exception e) {
            return Map.of("pending_count", -1);
        }
    }

    // ── Corrections ──────────────────────────────────────────────────────────

    public List<Map<String, Object>> getCorrections(int page, int pageSize) {
        try {
            ResponseEntity<List<Map<String, Object>>> resp = restTemplate.exchange(
                    baseUrl + "/corrections?page=" + page + "&page_size=" + pageSize,
                    HttpMethod.GET, null, new ParameterizedTypeReference<>() {});
            return resp.getStatusCode().is2xxSuccessful() && resp.getBody() != null
                    ? resp.getBody() : Collections.emptyList();
        } catch (RestClientException e) {
            log.warn("Failed to fetch corrections: {}", e.getMessage());
            return Collections.emptyList();
        }
    }

    // ── Helpers ──────────────────────────────────────────────────────────────

    private Map<String, Object> fallbackDown() {
        Map<String, Object> down = new HashMap<>();
        down.put("status", "DOWN");
        down.put("model_loaded", false);
        down.put("pending_count", -1);
        return down;
    }
}
