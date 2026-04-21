package com.example.demo.controller;

import com.example.demo.dto.ResearcherRoleRequestCreateRequest;
import com.example.demo.dto.ResearcherRoleRequestResponse;
import com.example.demo.model.ResearcherRoleRequest;
import com.example.demo.service.ResearcherRoleRequestService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/researcher-requests")
@Tag(name = "Researcher Role Requests", description = "APIs for requesting and reviewing CHERCHEUR role")
public class ResearcherRoleRequestController {

    private final ResearcherRoleRequestService requestService;

    @Autowired
    public ResearcherRoleRequestController(ResearcherRoleRequestService requestService) {
        this.requestService = requestService;
    }

    @PostMapping
    @Operation(summary = "Request CHERCHEUR role (USER only)")
    public ResponseEntity<ResearcherRoleRequestResponse> createRequest(
            @Valid @RequestBody ResearcherRoleRequestCreateRequest request) {
        String username = currentUsername();
        ResearcherRoleRequest created = requestService.createRequest(username, request);
        return ResponseEntity.status(HttpStatus.CREATED).body(toResponse(created));
    }

    @GetMapping("/me")
    @Operation(summary = "Get my researcher role requests")
    public ResponseEntity<List<ResearcherRoleRequestResponse>> getMyRequests() {
        String username = currentUsername();
        List<ResearcherRoleRequestResponse> responses = requestService.getMyRequests(username).stream()
                .map(this::toResponse)
                .toList();
        return ResponseEntity.ok(responses);
    }

    @GetMapping("/pending")
    @Operation(summary = "Get pending researcher role requests (ADMIN)")
    public ResponseEntity<List<ResearcherRoleRequestResponse>> getPendingRequests() {
        List<ResearcherRoleRequestResponse> responses = requestService.getPendingRequests().stream()
                .map(this::toResponse)
                .toList();
        return ResponseEntity.ok(responses);
    }

    @PostMapping("/{id}/approve")
    @Operation(summary = "Approve a researcher role request")
    public ResponseEntity<ResearcherRoleRequestResponse> approve(@PathVariable("id") Long id) {
        String adminUsername = currentUsername();
        ResearcherRoleRequest approved = requestService.approveRequest(id, adminUsername);
        return ResponseEntity.ok(toResponse(approved));
    }

    @PostMapping("/{id}/reject")
    @Operation(summary = "Reject a researcher role request")
    public ResponseEntity<ResearcherRoleRequestResponse> reject(@PathVariable("id") Long id) {
        String adminUsername = currentUsername();
        ResearcherRoleRequest rejected = requestService.rejectRequest(id, adminUsername);
        return ResponseEntity.ok(toResponse(rejected));
    }

    private String currentUsername() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        return authentication.getName();
    }

    private ResearcherRoleRequestResponse toResponse(ResearcherRoleRequest request) {
        ResearcherRoleRequestResponse response = new ResearcherRoleRequestResponse();
        response.setId(request.getId());
        response.setUserId(request.getUser().getId());
        response.setUsername(request.getUser().getUsername());
        response.setEmail(request.getUser().getEmail());
        response.setFullName(request.getFullName());
        response.setAffiliation(request.getAffiliation());
        response.setBiography(request.getBiography());
        response.setMotivation(request.getMotivation());
        response.setStatus(request.getStatus());
        response.setCreatedAt(request.getCreatedAt());
        response.setReviewedAt(request.getReviewedAt());
        if (request.getReviewedBy() != null) {
            response.setReviewedById(request.getReviewedBy().getId());
            response.setReviewedByUsername(request.getReviewedBy().getUsername());
        }
        return response;
    }
}
