package com.example.demo.dto;

/**
 * DTO sent to the Python classification service POST /classify endpoint.
 * Fields match the Python ClassifyRequest Pydantic schema.
 */
public class ClassificationRequestDTO {

    private Long publicationId;
    private String title;
    private String abstractText;
    private String domain;
    private String pdfUrl;

    public ClassificationRequestDTO() {}

    public ClassificationRequestDTO(Long publicationId, String title, String abstractText,
                                    String domain, String pdfUrl) {
        this.publicationId = publicationId;
        this.title = title;
        this.abstractText = abstractText;
        this.domain = domain;
        this.pdfUrl = pdfUrl;
    }

    // ── Getters & Setters ─────────────────────────────────────────────────────

    public Long getPublicationId() { return publicationId; }
    public void setPublicationId(Long publicationId) { this.publicationId = publicationId; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public String getAbstractText() { return abstractText; }
    public void setAbstractText(String abstractText) { this.abstractText = abstractText; }

    public String getDomain() { return domain; }
    public void setDomain(String domain) { this.domain = domain; }

    public String getPdfUrl() { return pdfUrl; }
    public void setPdfUrl(String pdfUrl) { this.pdfUrl = pdfUrl; }
}
