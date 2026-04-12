package com.example.demo.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * DTO received from the Python classification service POST /classify response.
 * Fields match the Python ClassifyResponse Pydantic schema (snake_case → camelCase).
 */
public class ClassificationResponseDTO {

    @JsonProperty("publication_id")
    private Long publicationId;

    @JsonProperty("cluster_id")
    private Integer clusterId;

    @JsonProperty("cluster_label")
    private String clusterLabel;

    @JsonProperty("confidence")
    private Double confidence;

    @JsonProperty("categories")
    private List<CategoryPredictionDTO> categories;

    @JsonProperty("keywords")
    private List<String> keywords;

    @JsonProperty("suggested_cluster_id")
    private Integer suggestedClusterId;

    @JsonProperty("suggested_cluster_label")
    private String suggestedClusterLabel;

    public ClassificationResponseDTO() {}

    // ── Nested DTO ────────────────────────────────────────────────────────────

    public static class CategoryPredictionDTO {
        private String category;
        private Double confidence;
        private String reason;

        public CategoryPredictionDTO() {}

        public String getCategory() { return category; }
        public void setCategory(String category) { this.category = category; }

        public Double getConfidence() { return confidence; }
        public void setConfidence(Double confidence) { this.confidence = confidence; }

        public String getReason() { return reason; }
        public void setReason(String reason) { this.reason = reason; }
    }

    // ── Getters & Setters ─────────────────────────────────────────────────────

    public Long getPublicationId() { return publicationId; }
    public void setPublicationId(Long publicationId) { this.publicationId = publicationId; }

    public Integer getClusterId() { return clusterId; }
    public void setClusterId(Integer clusterId) { this.clusterId = clusterId; }

    public String getClusterLabel() { return clusterLabel; }
    public void setClusterLabel(String clusterLabel) { this.clusterLabel = clusterLabel; }

    public Double getConfidence() { return confidence; }
    public void setConfidence(Double confidence) { this.confidence = confidence; }

    public List<CategoryPredictionDTO> getCategories() { return categories; }
    public void setCategories(List<CategoryPredictionDTO> categories) { this.categories = categories; }

    public List<String> getKeywords() { return keywords; }
    public void setKeywords(List<String> keywords) { this.keywords = keywords; }

    public Integer getSuggestedClusterId() { return suggestedClusterId; }
    public void setSuggestedClusterId(Integer suggestedClusterId) { this.suggestedClusterId = suggestedClusterId; }

    public String getSuggestedClusterLabel() { return suggestedClusterLabel; }
    public void setSuggestedClusterLabel(String suggestedClusterLabel) { this.suggestedClusterLabel = suggestedClusterLabel; }
}
