package com.example.demo.controller;

import com.example.demo.model.Publication;
import com.example.demo.service.PublicationService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/publications")
@Tag(name = "Publication Management", description = "APIs for managing academic publications")
public class PublicationController {

    private final PublicationService publicationService;

    @Autowired
    public PublicationController(PublicationService publicationService) {
        this.publicationService = publicationService;
    }

    @PostMapping
    @Operation(summary = "Create a new publication")
    public ResponseEntity<Publication> createPublication(@Valid @RequestBody Publication publication) {
        Publication savedPublication = publicationService.create(publication);
        return ResponseEntity.status(HttpStatus.CREATED).body(savedPublication);
    }

    @GetMapping
    @Operation(summary = "Get all publications")
    public ResponseEntity<List<Publication>> getAllPublications() {
        List<Publication> publications = publicationService.findAll();
        return ResponseEntity.ok(publications);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get publication by ID")
    public ResponseEntity<Publication> getPublicationById(
            @PathVariable @Parameter(description = "Publication ID") Long id) {
        return publicationService.findById(id)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @GetMapping("/doi/{doi}")
    @Operation(summary = "Get publication by DOI")
    public ResponseEntity<Publication> getPublicationByDoi(@PathVariable @Parameter(description = "DOI") String doi) {
        return publicationService.findByDoi(doi)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @GetMapping("/domain/{domainId}")
    @Operation(summary = "Get publications by domain ID")
    public ResponseEntity<List<Publication>> getPublicationsByDomain(
            @PathVariable @Parameter(description = "Domain ID") Long domainId) {
        List<Publication> publications = publicationService.findByDomainId(domainId);
        return ResponseEntity.ok(publications);
    }

    @GetMapping("/researcher/{researcherId}")
    @Operation(summary = "Get publications by researcher ID")
    public ResponseEntity<List<Publication>> getPublicationsByResearcher(
            @PathVariable @Parameter(description = "Researcher ID") Long researcherId) {
        List<Publication> publications = publicationService.findByResearcherId(researcherId);
        return ResponseEntity.ok(publications);
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update a publication")
    public ResponseEntity<Publication> updatePublication(
            @PathVariable @Parameter(description = "Publication ID") Long id,
            @Valid @RequestBody Publication publicationDetails) {
        Publication updatedPublication = publicationService.update(id, publicationDetails);
        return ResponseEntity.ok(updatedPublication);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a publication by ID")
    public ResponseEntity<Void> deletePublication(@PathVariable @Parameter(description = "Publication ID") Long id) {
        publicationService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
