package com.example.demo.controller;

import com.example.demo.model.Researcher;
import com.example.demo.service.ResearcherService;
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
@RequestMapping("/api/researchers")
@Tag(name = "Researcher Management", description = "APIs for managing researchers")
public class ResearcherController {

    private final ResearcherService researcherService;

    @Autowired
    public ResearcherController(ResearcherService researcherService) {
        this.researcherService = researcherService;
    }

    @PostMapping
    @Operation(summary = "Create a new researcher")
    public ResponseEntity<Researcher> createResearcher(@Valid @RequestBody Researcher researcher) {
        Researcher savedResearcher = researcherService.create(researcher);
        return ResponseEntity.status(HttpStatus.CREATED).body(savedResearcher);
    }

    @GetMapping
    @Operation(summary = "Get all researchers")
    public ResponseEntity<List<Researcher>> getAllResearchers() {
        List<Researcher> researchers = researcherService.findAll();
        return ResponseEntity.ok(researchers);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get researcher by ID")
    public ResponseEntity<Researcher> getResearcherById(
            @PathVariable("id") @Parameter(description = "Researcher ID") Long id) {
        return researcherService.findById(id)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @GetMapping("/email/{email}")
    @Operation(summary = "Get researcher by email")
    public ResponseEntity<Researcher> getResearcherByEmail(
            @PathVariable("email") @Parameter(description = "Email address") String email) {
        return researcherService.findByEmail(email)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @GetMapping("/affiliation/{affiliation}")
    @Operation(summary = "Get researchers by affiliation")
    public ResponseEntity<List<Researcher>> getResearchersByAffiliation(
            @PathVariable("affiliation") @Parameter(description = "Affiliation") String affiliation) {
        List<Researcher> researchers = researcherService.findByAffiliation(affiliation);
        return ResponseEntity.ok(researchers);
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update a researcher")
    public ResponseEntity<Researcher> updateResearcher(
            @PathVariable("id") @Parameter(description = "Researcher ID") Long id,
            @Valid @RequestBody Researcher researcherDetails) {
        Researcher updatedResearcher = researcherService.update(id, researcherDetails);
        return ResponseEntity.ok(updatedResearcher);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a researcher by ID")
    public ResponseEntity<Void> deleteResearcher(@PathVariable("id") @Parameter(description = "Researcher ID") Long id) {
        researcherService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
