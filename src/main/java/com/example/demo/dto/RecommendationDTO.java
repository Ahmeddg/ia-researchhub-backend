package com.example.demo.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class RecommendationDTO {
    @JsonProperty("publication_id")
    private Long publicationId;

    @JsonProperty("similarity_score")
    private Double similarityScore;

    public RecommendationDTO() {}

    public RecommendationDTO(Long publicationId, Double similarityScore) {
        this.publicationId = publicationId;
        this.similarityScore = similarityScore;
    }

    public Long getPublicationId() {
        return publicationId;
    }

    public void setPublicationId(Long publicationId) {
        this.publicationId = publicationId;
    }

    public Double getSimilarityScore() {
        return similarityScore;
    }

    public void setSimilarityScore(Double similarityScore) {
        this.similarityScore = similarityScore;
    }
}
