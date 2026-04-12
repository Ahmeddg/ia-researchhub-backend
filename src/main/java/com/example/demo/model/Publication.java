package com.example.demo.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.LocalDate;
import java.util.HashSet;
import java.util.Set;

@Entity
@Table(name = "publications")
public class Publication {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotBlank(message = "Title is required")
    @Size(min = 2, max = 500, message = "Title must be between 2 and 500 characters")
    @Column(nullable = false)
    private String title;

    @Size(max = 5000, message = "Abstract must not exceed 5000 characters")
    @Column(length = 5000)
    private String abstractText;

    @Column(name = "publication_date")
    private LocalDate publicationDate;

    @Column(name = "pdf_url")
    private String pdfUrl;

    @Column(unique = true)
    private String doi;

    @NotNull(message = "Domain is required")
    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "domain_id", nullable = false)
    private Domain domain;

    @ManyToMany(fetch = FetchType.EAGER)
    @JoinTable(name = "publication_researchers",
            joinColumns = @JoinColumn(name = "publication_id"),
            inverseJoinColumns = @JoinColumn(name = "researcher_id"))
    private Set<Researcher> researchers = new HashSet<>();

    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "created_by")
    @JsonIgnore
    private User createdBy;

    // ── Publication lifecycle status ─────────────────────────────────────────
    /** DRAFT = saved but awaiting user confirmation after AI classification.
     *  PUBLISHED = confirmed and visible to all. */
    @Column(name = "status", nullable = false)
    private String status = "PUBLISHED";

    // ── AI Cluster Assignment (written by Python classification service) ──────
    @Column(name = "cluster_id")
    private Integer clusterId;

    @Column(name = "cluster_label", length = 200)
    private String clusterLabel;

    @Column(name = "suggested_cluster_id")
    private Integer suggestedClusterId;

    @Column(name = "suggested_cluster_label", length = 200)
    private String suggestedClusterLabel;

    // ── User-approved AI metadata (stored after user review) ─────────────────
    /** JSON array of approved CategoryPrediction objects */
    @Column(name = "ai_categories", columnDefinition = "TEXT")
    private String aiCategories;

    /** JSON array of approved keyword strings */
    @Column(name = "ai_keywords", columnDefinition = "TEXT")
    private String aiKeywords;

    @Column(name = "ai_confidence")
    private Double aiConfidence;

    public Publication() {
    }

    public Publication(String title, String abstractText, Domain domain) {
        this.title = title;
        this.abstractText = abstractText;
        this.domain = domain;
    }

    // ── Getters & Setters ─────────────────────────────────────────────────────

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public String getAbstractText() { return abstractText; }
    public void setAbstractText(String abstractText) { this.abstractText = abstractText; }

    public LocalDate getPublicationDate() { return publicationDate; }
    public void setPublicationDate(LocalDate publicationDate) { this.publicationDate = publicationDate; }

    public String getPdfUrl() { return pdfUrl; }
    public void setPdfUrl(String pdfUrl) { this.pdfUrl = pdfUrl; }

    public String getDoi() { return doi; }
    public void setDoi(String doi) { this.doi = doi; }

    public Domain getDomain() { return domain; }
    public void setDomain(Domain domain) { this.domain = domain; }

    public Set<Researcher> getResearchers() { return researchers; }
    public void setResearchers(Set<Researcher> researchers) { this.researchers = researchers; }

    public void addResearcher(Researcher researcher) { this.researchers.add(researcher); }
    public void removeResearcher(Researcher researcher) { this.researchers.remove(researcher); }

    public User getCreatedBy() { return createdBy; }
    public void setCreatedBy(User createdBy) { this.createdBy = createdBy; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public Integer getClusterId() { return clusterId; }
    public void setClusterId(Integer clusterId) { this.clusterId = clusterId; }

    public String getClusterLabel() { return clusterLabel; }
    public void setClusterLabel(String clusterLabel) { this.clusterLabel = clusterLabel; }

    public Integer getSuggestedClusterId() { return suggestedClusterId; }
    public void setSuggestedClusterId(Integer suggestedClusterId) { this.suggestedClusterId = suggestedClusterId; }

    public String getSuggestedClusterLabel() { return suggestedClusterLabel; }
    public void setSuggestedClusterLabel(String suggestedClusterLabel) { this.suggestedClusterLabel = suggestedClusterLabel; }

    public String getAiCategories() { return aiCategories; }
    public void setAiCategories(String aiCategories) { this.aiCategories = aiCategories; }

    public String getAiKeywords() { return aiKeywords; }
    public void setAiKeywords(String aiKeywords) { this.aiKeywords = aiKeywords; }

    public Double getAiConfidence() { return aiConfidence; }
    public void setAiConfidence(Double aiConfidence) { this.aiConfidence = aiConfidence; }
}
