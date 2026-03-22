package com.example.demo.controller;

import com.example.demo.model.Researcher;
import com.example.demo.repository.ResearcherRepository;
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
@RequestMapping("/api/researchers")
@Tag(name = "Researcher Management", description = "APIs for managing researchers")
public class ResearcherController {

    @Autowired
    private ResearcherRepository researcherRepository;

    @PostMapping
    @Operation(summary = "Create a new researcher")
    public ResponseEntity<Researcher> createResearcher(@RequestBody Researcher researcher) {
        try {
            Researcher savedResearcher = researcherRepository.save(researcher);
            return ResponseEntity.status(HttpStatus.CREATED).body(savedResearcher);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping
    @Operation(summary = "Get all researchers")
    public ResponseEntity<List<Researcher>> getAllResearchers() {
        try {
            List<Researcher> researchers = researcherRepository.findAll();
            return ResponseEntity.ok(researchers);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get researcher by ID")
    public ResponseEntity<Researcher> getResearcherById(@PathVariable @Parameter(description = "Researcher ID") Long id) {
        try {
            Optional<Researcher> researcher = researcherRepository.findById(id);
            return researcher.map(ResponseEntity::ok)
                    .orElseGet(() -> ResponseEntity.notFound().build());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/email/{email}")
    @Operation(summary = "Get researcher by email")
    public ResponseEntity<Researcher> getResearcherByEmail(@PathVariable @Parameter(description = "Email address") String email) {
        try {
            Optional<Researcher> researcher = researcherRepository.findByEmail(email);
            return researcher.map(ResponseEntity::ok)
                    .orElseGet(() -> ResponseEntity.notFound().build());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update a researcher")
    public ResponseEntity<Researcher> updateResearcher(@PathVariable @Parameter(description = "Researcher ID") Long id,
                                                      @RequestBody Researcher researcherDetails) {
        try {
            Optional<Researcher> researcher = researcherRepository.findById(id);
            if (researcher.isPresent()) {
                Researcher existingResearcher = researcher.get();
                if (researcherDetails.getFullName() != null) {
                    existingResearcher.setFullName(researcherDetails.getFullName());
                }
                if (researcherDetails.getEmail() != null) {
                    existingResearcher.setEmail(researcherDetails.getEmail());
                }
                if (researcherDetails.getAffiliation() != null) {
                    existingResearcher.setAffiliation(researcherDetails.getAffiliation());
                }
                if (researcherDetails.getBiography() != null) {
                    existingResearcher.setBiography(researcherDetails.getBiography());
                }
                Researcher updatedResearcher = researcherRepository.save(existingResearcher);
                return ResponseEntity.ok(updatedResearcher);
            } else {
                return ResponseEntity.notFound().build();
            }
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a researcher by ID")
    public ResponseEntity<Void> deleteResearcher(@PathVariable @Parameter(description = "Researcher ID") Long id) {
        try {
            if (researcherRepository.existsById(id)) {
                researcherRepository.deleteById(id);
                return ResponseEntity.noContent().build();
            } else {
                return ResponseEntity.notFound().build();
            }
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
}
