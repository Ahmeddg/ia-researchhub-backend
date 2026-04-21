package com.example.demo.dto;

import java.util.List;

/**
 * Request body for PUT /api/publications/{id}/confirm.
 * Contains the user-approved classification metadata after review.
 */
public class ConfirmPublicationRequest {

    /** JSON string of approved CategoryPrediction array.
     *  Frontend serializes List<CategoryPrediction> to JSON string before sending. */
    private String aiCategories;

    /** JSON string of approved keyword string array. */
    private String aiKeywords;

    /** The confidence score from the classification service. */
    private Double aiConfidence;

    public ConfirmPublicationRequest() {}

    public String getAiCategories() { return aiCategories; }
    public void setAiCategories(String aiCategories) { this.aiCategories = aiCategories; }

    public String getAiKeywords() { return aiKeywords; }
    public void setAiKeywords(String aiKeywords) { this.aiKeywords = aiKeywords; }

    public Double getAiConfidence() { return aiConfidence; }
    public void setAiConfidence(Double aiConfidence) { this.aiConfidence = aiConfidence; }
}
