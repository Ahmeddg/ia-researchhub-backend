package com.example.demo.controller;

import com.example.demo.dto.ClassificationResponseDTO;
import com.example.demo.dto.ConfirmPublicationRequest;
import com.example.demo.dto.PublicationWithClassificationDTO;
import com.example.demo.model.Publication;
import com.example.demo.model.User;
import com.example.demo.exception.ResourceNotFoundException;
import com.example.demo.service.ClassificationServiceClient;
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
    private final ClassificationServiceClient classificationServiceClient;

    @Autowired
    public PublicationController(PublicationService publicationService,
            UserService userService,
            ClassificationServiceClient classificationServiceClient) {
        this.publicationService = publicationService;
        this.userService = userService;
        this.classificationServiceClient = classificationServiceClient;
    }

    /**
     * Create a publication as DRAFT, immediately call the classification service,
     * and return both the saved publication (with its real DB ID) and the AI
     * result.
     *
     * The frontend shows the AI result for review. Once the user confirms (or
     * edits),
     * they call PUT /api/publications/{id}/confirm to finalise.
     */
    @PostMapping
    @Operation(summary = "Create a publication (draft) and classify it", description = "Saves the publication as DRAFT, calls the AI classification service, "
            +
            "and returns the combined result for the user to review before confirming.")
    public ResponseEntity<PublicationWithClassificationDTO> createPublication(
            @Valid @RequestBody Publication publication) {

        enforceAllowedPublicationWrite();
        String username = currentUsername();
        User creator = userService.findByUsername(username)
                .orElseThrow(() -> new ResourceNotFoundException("User", "username", username));
        publication.setCreatedBy(creator);

        // 1. Save as DRAFT to get a real DB ID (shared with Python service)
        Publication savedDraft = publicationService.createDraft(publication);

        // 2. Call Python classification service (uses same DB — writes cluster_id etc.)
        ClassificationResponseDTO classification = classificationServiceClient.classify(savedDraft);

        // 3. Return both together — frontend shows AI review panel
        PublicationWithClassificationDTO response = new PublicationWithClassificationDTO(savedDraft, classification);

        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    /**
     * Confirm a DRAFT publication after the user reviews and optionally edits the
     * AI results.
     * Sets status=PUBLISHED and stores the approved AI metadata.
     */
    @PutMapping("/{id}/confirm")
    @Operation(summary = "Confirm a draft publication with approved AI classification", description = "Transitions a DRAFT publication to PUBLISHED status and "
            +
            "stores the user-approved categories, keywords, and confidence.")
    public ResponseEntity<Publication> confirmPublication(
            @PathVariable @Parameter(description = "Publication ID") Long id,
            @RequestBody ConfirmPublicationRequest request) {

        enforceOwnershipForChercheur(id);
        Publication confirmed = publicationService.confirmPublication(
                id,
                request.getAiCategories(),
                request.getAiKeywords(),
                request.getAiConfidence());
        return ResponseEntity.ok(confirmed);
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
    public ResponseEntity<Publication> getPublicationByDoi(
            @PathVariable("doi") @Parameter(description = "DOI") String doi) {
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
    public ResponseEntity<Void> deletePublication(
            @PathVariable("id") @Parameter(description = "Publication ID") Long id) {
        enforceOwnershipForChercheur(id);
        publicationService.delete(id);
        return ResponseEntity.noContent().build();
    }

    // ── Security helpers ──────────────────────────────────────────────────────

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
