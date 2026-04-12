package com.example.demo.dto;

import com.example.demo.model.Publication;

/**
 * Combined response returned to the frontend after creating a publication.
 * Contains both the saved Publication entity (DRAFT status, with real ID)
 * and the AI classification result from the Python service.
 */
public class PublicationWithClassificationDTO {

    private Publication publication;
    private ClassificationResponseDTO classification;

    public PublicationWithClassificationDTO() {}

    public PublicationWithClassificationDTO(Publication publication,
                                            ClassificationResponseDTO classification) {
        this.publication = publication;
        this.classification = classification;
    }

    public Publication getPublication() { return publication; }
    public void setPublication(Publication publication) { this.publication = publication; }

    public ClassificationResponseDTO getClassification() { return classification; }
    public void setClassification(ClassificationResponseDTO classification) { this.classification = classification; }
}
