package com.example.demo.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.HashSet;
import java.util.Set;

public class CreateProjectRequest {
    @NotBlank(message = "Title is required")
    @Size(min = 2, max = 200, message = "Title must be between 2 and 200 characters")
    private String title;

    @Size(max = 2000, message = "Description must not exceed 2000 characters")
    private String description;

    @NotBlank(message = "AI category is required")
    @Size(max = 100, message = "AI category must not exceed 100 characters")
    private String aiCategory;

    @NotNull(message = "Domain ID is required")
    private Long domainId;

    private Set<Long> researcherIds = new HashSet<>();

    public CreateProjectRequest() {
    }

    public CreateProjectRequest(String title, String description, String aiCategory, Long domainId) {
        this.title = title;
        this.description = description;
        this.aiCategory = aiCategory;
        this.domainId = domainId;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getAiCategory() {
        return aiCategory;
    }

    public void setAiCategory(String aiCategory) {
        this.aiCategory = aiCategory;
    }

    public Long getDomainId() {
        return domainId;
    }

    public void setDomainId(Long domainId) {
        this.domainId = domainId;
    }

    public Set<Long> getResearcherIds() {
        return researcherIds;
    }

    public void setResearcherIds(Set<Long> researcherIds) {
        this.researcherIds = researcherIds;
    }
}
