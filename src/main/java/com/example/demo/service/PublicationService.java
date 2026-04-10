package com.example.demo.service;

import com.example.demo.model.Publication;
import java.util.List;
import java.util.Optional;

public interface PublicationService {
    Publication create(Publication publication);

    List<Publication> findAll();

    Optional<Publication> findById(Long id);

    Optional<Publication> findByDoi(String doi);

    List<Publication> findByDomainId(Long domainId);

    List<Publication> findByResearcherId(Long researcherId);

    List<Publication> findByCreatedByUsername(String username);

    Publication update(Long id, Publication publicationDetails);

    void delete(Long id);

    boolean existsById(Long id);

    long count();

    long countByDomainId(Long domainId);

    boolean isOwner(Long publicationId, String username);
}
