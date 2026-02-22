package com.example.demo.controller;

import com.example.demo.model.Domain;
import com.example.demo.repository.DomainRepository;
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
@RequestMapping("/api/domains")
@CrossOrigin(origins = "*")
@Tag(name = "Domain Management", description = "APIs for managing research domains")
public class DomainController {

    @Autowired
    private DomainRepository domainRepository;

    @PostMapping
    @Operation(summary = "Create a new domain")
    public ResponseEntity<Domain> createDomain(@RequestBody Domain domain) {
        try {
            Domain savedDomain = domainRepository.save(domain);
            return ResponseEntity.status(HttpStatus.CREATED).body(savedDomain);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping
    @Operation(summary = "Get all domains")
    public ResponseEntity<List<Domain>> getAllDomains() {
        try {
            List<Domain> domains = domainRepository.findAll();
            return ResponseEntity.ok(domains);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get domain by ID")
    public ResponseEntity<Domain> getDomainById(@PathVariable @Parameter(description = "Domain ID") Long id) {
        try {
            Optional<Domain> domain = domainRepository.findById(id);
            return domain.map(ResponseEntity::ok)
                    .orElseGet(() -> ResponseEntity.notFound().build());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/name/{name}")
    @Operation(summary = "Get domain by name")
    public ResponseEntity<Domain> getDomainByName(@PathVariable @Parameter(description = "Domain name") String name) {
        try {
            Optional<Domain> domain = domainRepository.findByName(name);
            return domain.map(ResponseEntity::ok)
                    .orElseGet(() -> ResponseEntity.notFound().build());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update a domain")
    public ResponseEntity<Domain> updateDomain(@PathVariable @Parameter(description = "Domain ID") Long id,
                                              @RequestBody Domain domainDetails) {
        try {
            Optional<Domain> domain = domainRepository.findById(id);
            if (domain.isPresent()) {
                Domain existingDomain = domain.get();
                if (domainDetails.getName() != null) {
                    existingDomain.setName(domainDetails.getName());
                }
                if (domainDetails.getDescription() != null) {
                    existingDomain.setDescription(domainDetails.getDescription());
                }
                Domain updatedDomain = domainRepository.save(existingDomain);
                return ResponseEntity.ok(updatedDomain);
            } else {
                return ResponseEntity.notFound().build();
            }
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a domain by ID")
    public ResponseEntity<Void> deleteDomain(@PathVariable @Parameter(description = "Domain ID") Long id) {
        try {
            if (domainRepository.existsById(id)) {
                domainRepository.deleteById(id);
                return ResponseEntity.noContent().build();
            } else {
                return ResponseEntity.notFound().build();
            }
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
}
