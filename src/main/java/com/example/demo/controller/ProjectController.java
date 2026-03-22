package com.example.demo.controller;

import com.example.demo.model.Project;
import com.example.demo.repository.ProjectRepository;
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
@RequestMapping("/api/projects")
@Tag(name = "Project Management", description = "APIs for managing research projects")
public class ProjectController {

    @Autowired
    private ProjectRepository projectRepository;

    @PostMapping
    @Operation(summary = "Create a new project")
    public ResponseEntity<Project> createProject(@RequestBody Project project) {
        try {
            Project savedProject = projectRepository.save(project);
            return ResponseEntity.status(HttpStatus.CREATED).body(savedProject);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping
    @Operation(summary = "Get all projects")
    public ResponseEntity<List<Project>> getAllProjects() {
        try {
            List<Project> projects = projectRepository.findAll();
            return ResponseEntity.ok(projects);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get project by ID")
    public ResponseEntity<Project> getProjectById(@PathVariable @Parameter(description = "Project ID") Long id) {
        try {
            Optional<Project> project = projectRepository.findById(id);
            return project.map(ResponseEntity::ok)
                    .orElseGet(() -> ResponseEntity.notFound().build());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/domain/{domainId}")
    @Operation(summary = "Get projects by domain ID")
    public ResponseEntity<List<Project>> getProjectsByDomain(
            @PathVariable @Parameter(description = "Domain ID") Long domainId) {
        try {
            List<Project> projects = projectRepository.findByDomainId(domainId);
            return ResponseEntity.ok(projects);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/category/{aiCategory}")
    @Operation(summary = "Get projects by AI category")
    public ResponseEntity<List<Project>> getProjectsByAiCategory(
            @PathVariable @Parameter(description = "AI Category") String aiCategory) {
        try {
            List<Project> projects = projectRepository.findByAiCategory(aiCategory);
            return ResponseEntity.ok(projects);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update a project")
    public ResponseEntity<Project> updateProject(@PathVariable @Parameter(description = "Project ID") Long id,
                                                @RequestBody Project projectDetails) {
        try {
            Optional<Project> project = projectRepository.findById(id);
            if (project.isPresent()) {
                Project existingProject = project.get();
                if (projectDetails.getTitle() != null) {
                    existingProject.setTitle(projectDetails.getTitle());
                }
                if (projectDetails.getDescription() != null) {
                    existingProject.setDescription(projectDetails.getDescription());
                }
                if (projectDetails.getAiCategory() != null) {
                    existingProject.setAiCategory(projectDetails.getAiCategory());
                }
                if (projectDetails.getDomain() != null) {
                    existingProject.setDomain(projectDetails.getDomain());
                }
                Project updatedProject = projectRepository.save(existingProject);
                return ResponseEntity.ok(updatedProject);
            } else {
                return ResponseEntity.notFound().build();
            }
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a project by ID")
    public ResponseEntity<Void> deleteProject(@PathVariable @Parameter(description = "Project ID") Long id) {
        try {
            if (projectRepository.existsById(id)) {
                projectRepository.deleteById(id);
                return ResponseEntity.noContent().build();
            } else {
                return ResponseEntity.notFound().build();
            }
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
}
