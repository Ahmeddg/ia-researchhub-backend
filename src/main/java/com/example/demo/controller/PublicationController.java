package com.example.demo.controller;

import com.example.demo.model.Publication;
import com.example.demo.repository.PublicationRepository;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/api/publications")
@Tag(name = "Publication Management", description = "APIs for managing academic publications")
public class PublicationController {

    @Autowired
    private PublicationRepository publicationRepository;

    @PostMapping
    @Operation(summary = "Create a new publication")
    public ResponseEntity<Publication> createPublication(@RequestBody Publication publication) {
        try {
            Publication savedPublication = publicationRepository.save(publication);
            return ResponseEntity.status(HttpStatus.CREATED).body(savedPublication);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping
    @Operation(summary = "Get all publications")
    public ResponseEntity<List<Publication>> getAllPublications() {
        try {
            List<Publication> publications = publicationRepository.findAll();
            return ResponseEntity.ok(publications);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get publication by ID")
    public ResponseEntity<Publication> getPublicationById(@PathVariable @Parameter(description = "Publication ID") Long id) {
        try {
            Optional<Publication> publication = publicationRepository.findById(id);
            return publication.map(ResponseEntity::ok)
                    .orElseGet(() -> ResponseEntity.notFound().build());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/doi/{doi}")
    @Operation(summary = "Get publication by DOI")
    public ResponseEntity<Publication> getPublicationByDoi(@PathVariable @Parameter(description = "DOI") String doi) {
        try {
            Optional<Publication> publication = publicationRepository.findByDoi(doi);
            return publication.map(ResponseEntity::ok)
                    .orElseGet(() -> ResponseEntity.notFound().build());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/domain/{domainId}")
    @Operation(summary = "Get publications by domain ID")
    public ResponseEntity<List<Publication>> getPublicationsByDomain(
            @PathVariable @Parameter(description = "Domain ID") Long domainId) {
        try {
            List<Publication> publications = publicationRepository.findByDomainId(domainId);
            return ResponseEntity.ok(publications);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update a publication")
    public ResponseEntity<Publication> updatePublication(@PathVariable @Parameter(description = "Publication ID") Long id,
                                                        @RequestBody Publication publicationDetails) {
        try {
            Optional<Publication> publication = publicationRepository.findById(id);
            if (publication.isPresent()) {
                Publication existingPublication = publication.get();
                if (publicationDetails.getTitle() != null) {
                    existingPublication.setTitle(publicationDetails.getTitle());
                }
                if (publicationDetails.getAbstractText() != null) {
                    existingPublication.setAbstractText(publicationDetails.getAbstractText());
                }
                if (publicationDetails.getPublicationDate() != null) {
                    existingPublication.setPublicationDate(publicationDetails.getPublicationDate());
                }
                if (publicationDetails.getPdfUrl() != null) {
                    existingPublication.setPdfUrl(publicationDetails.getPdfUrl());
                }
                if (publicationDetails.getDoi() != null) {
                    existingPublication.setDoi(publicationDetails.getDoi());
                }
                if (publicationDetails.getDomain() != null) {
                    existingPublication.setDomain(publicationDetails.getDomain());
                }
                Publication updatedPublication = publicationRepository.save(existingPublication);
                return ResponseEntity.ok(updatedPublication);
            } else {
                return ResponseEntity.notFound().build();
            }
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a publication by ID")
    public ResponseEntity<Void> deletePublication(@PathVariable @Parameter(description = "Publication ID") Long id) {
        try {
            if (publicationRepository.existsById(id)) {
                publicationRepository.deleteById(id);
                return ResponseEntity.noContent().build();
            } else {
                return ResponseEntity.notFound().build();
            }
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
}
