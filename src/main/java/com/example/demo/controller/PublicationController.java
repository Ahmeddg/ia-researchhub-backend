package com.example.demo.controller;

import com.example.demo.model.Publication;
import com.example.demo.model.User;
import com.example.demo.exception.ResourceNotFoundException;
import com.example.demo.service.UserService;
import com.example.demo.service.PublicationService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/publications")
@Tag(name = "Publication Management", description = "APIs for managing academic publications")
public class PublicationController {

    private final PublicationService publicationService;
    private final UserService userService;

    @Autowired
    public PublicationController(PublicationService publicationService, UserService userService) {
        this.publicationService = publicationService;
        this.userService = userService;
    }

    @PostMapping
    @Operation(summary = "Create a new publication")
    public ResponseEntity<Publication> createPublication(@Valid @RequestBody Publication publication) {
        enforceAllowedPublicationWrite();
        String username = currentUsername();
        User creator = userService.findByUsername(username)
                .orElseThrow(() -> new ResourceNotFoundException("User", "username", username));
        publication.setCreatedBy(creator);
        Publication savedPublication = publicationService.create(publication);
        return ResponseEntity.status(HttpStatus.CREATED).body(savedPublication);
    }

    @GetMapping
    @Operation(summary = "Get all publications")
    public ResponseEntity<List<Publication>> getAllPublications() {
        List<Publication> publications = publicationService.findAll();
        return ResponseEntity.ok(publications);
    }

    @GetMapping("/me")
    @Operation(summary = "Get my publications")
    public ResponseEntity<List<Publication>> getMyPublications() {
        List<Publication> publications = publicationService.findByCreatedByUsername(currentUsername());
        return ResponseEntity.ok(publications);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get publication by ID")
    public ResponseEntity<Publication> getPublicationById(
            @PathVariable("id") @Parameter(description = "Publication ID") Long id) {
        return publicationService.findById(id)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @GetMapping("/doi/{doi}")
    @Operation(summary = "Get publication by DOI")
    public ResponseEntity<Publication> getPublicationByDoi(@PathVariable("doi") @Parameter(description = "DOI") String doi) {
        return publicationService.findByDoi(doi)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @GetMapping("/domain/{domainId}")
    @Operation(summary = "Get publications by domain ID")
    public ResponseEntity<List<Publication>> getPublicationsByDomain(
            @PathVariable("domainId") @Parameter(description = "Domain ID") Long domainId) {
        List<Publication> publications = publicationService.findByDomainId(domainId);
        return ResponseEntity.ok(publications);
    }

    @GetMapping("/researcher/{researcherId}")
    @Operation(summary = "Get publications by researcher ID")
    public ResponseEntity<List<Publication>> getPublicationsByResearcher(
            @PathVariable("researcherId") @Parameter(description = "Researcher ID") Long researcherId) {
        List<Publication> publications = publicationService.findByResearcherId(researcherId);
        return ResponseEntity.ok(publications);
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update a publication")
    public ResponseEntity<Publication> updatePublication(
            @PathVariable("id") @Parameter(description = "Publication ID") Long id,
            @Valid @RequestBody Publication publicationDetails) {
        enforceOwnershipForChercheur(id);
        Publication updatedPublication = publicationService.update(id, publicationDetails);
        return ResponseEntity.ok(updatedPublication);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a publication by ID")
    public ResponseEntity<Void> deletePublication(@PathVariable("id") @Parameter(description = "Publication ID") Long id) {
        enforceOwnershipForChercheur(id);
        publicationService.delete(id);
        return ResponseEntity.noContent().build();
    }

    private void enforceOwnershipForChercheur(Long publicationId) {
        enforceAllowedPublicationWrite();
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        boolean isChercheur = authentication.getAuthorities().stream()
                .anyMatch(a -> "ROLE_CHERCHEUR".equals(a.getAuthority()));
        if (isChercheur && !publicationService.isOwner(publicationId, authentication.getName())) {
            throw new AccessDeniedException("CHERCHEUR can only manage their own publications");
        }
    }

    private String currentUsername() {
        return SecurityContextHolder.getContext().getAuthentication().getName();
    }

    private void enforceAllowedPublicationWrite() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        boolean allowed = authentication.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .anyMatch(authority -> authority.equals("ROLE_ADMIN")
                        || authority.equals("ROLE_MODERATEUR")
                        || authority.equals("ROLE_CHERCHEUR"));
        if (!allowed) {
            throw new AccessDeniedException("You are not allowed to manage publications");
        }
    }
}
