package com.example.demo.controller;

import com.example.demo.model.Domain;
import com.example.demo.service.DomainService;
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
@RequestMapping("/api/domains")
@Tag(name = "Domain Management", description = "APIs for managing research domains")
public class DomainController {

    private final DomainService domainService;

    @Autowired
    public DomainController(DomainService domainService) {
        this.domainService = domainService;
    }

    @PostMapping
    @Operation(summary = "Create a new domain")
    public ResponseEntity<Domain> createDomain(@Valid @RequestBody Domain domain) {
        Domain savedDomain = domainService.create(domain);
        return ResponseEntity.status(HttpStatus.CREATED).body(savedDomain);
    }

    @GetMapping
    @Operation(summary = "Get all domains")
    public ResponseEntity<List<Domain>> getAllDomains() {
        List<Domain> domains = domainService.findAll();
        return ResponseEntity.ok(domains);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get domain by ID")
    public ResponseEntity<Domain> getDomainById(@PathVariable("id") @Parameter(description = "Domain ID") Long id) {
        return domainService.findById(id)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @GetMapping("/name/{name}")
    @Operation(summary = "Get domain by name")
    public ResponseEntity<Domain> getDomainByName(@PathVariable("name") @Parameter(description = "Domain name") String name) {
        return domainService.findByName(name)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update a domain")
    public ResponseEntity<Domain> updateDomain(
            @PathVariable("id") @Parameter(description = "Domain ID") Long id,
            @Valid @RequestBody Domain domainDetails) {
        Domain updatedDomain = domainService.update(id, domainDetails);
        return ResponseEntity.ok(updatedDomain);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a domain by ID")
    public ResponseEntity<Void> deleteDomain(@PathVariable("id") @Parameter(description = "Domain ID") Long id) {
        domainService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
