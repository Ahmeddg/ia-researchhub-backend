package com.example.demo.controller;

import com.example.demo.model.Project;
import com.example.demo.service.ProjectService;
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
@RequestMapping("/api/projects")
@Tag(name = "Project Management", description = "APIs for managing research projects")
public class ProjectController {

    private final ProjectService projectService;

    @Autowired
    public ProjectController(ProjectService projectService) {
        this.projectService = projectService;
    }

    @PostMapping
    @Operation(summary = "Create a new project")
    public ResponseEntity<Project> createProject(@Valid @RequestBody Project project) {
        Project savedProject = projectService.create(project);
        return ResponseEntity.status(HttpStatus.CREATED).body(savedProject);
    }

    @GetMapping
    @Operation(summary = "Get all projects")
    public ResponseEntity<List<Project>> getAllProjects() {
        List<Project> projects = projectService.findAll();
        return ResponseEntity.ok(projects);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get project by ID")
    public ResponseEntity<Project> getProjectById(@PathVariable @Parameter(description = "Project ID") Long id) {
        return projectService.findById(id)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @GetMapping("/domain/{domainId}")
    @Operation(summary = "Get projects by domain ID")
    public ResponseEntity<List<Project>> getProjectsByDomain(
            @PathVariable @Parameter(description = "Domain ID") Long domainId) {
        List<Project> projects = projectService.findByDomainId(domainId);
        return ResponseEntity.ok(projects);
    }

    @GetMapping("/category/{aiCategory}")
    @Operation(summary = "Get projects by AI category")
    public ResponseEntity<List<Project>> getProjectsByAiCategory(
            @PathVariable @Parameter(description = "AI Category") String aiCategory) {
        List<Project> projects = projectService.findByAiCategory(aiCategory);
        return ResponseEntity.ok(projects);
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update a project")
    public ResponseEntity<Project> updateProject(
            @PathVariable @Parameter(description = "Project ID") Long id,
            @Valid @RequestBody Project projectDetails) {
        Project updatedProject = projectService.update(id, projectDetails);
        return ResponseEntity.ok(updatedProject);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a project by ID")
    public ResponseEntity<Void> deleteProject(@PathVariable @Parameter(description = "Project ID") Long id) {
        projectService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
