package com.example.demo.controller;

import com.example.demo.dto.CreateProjectRequest;
import com.example.demo.exception.ResourceNotFoundException;
import com.example.demo.model.Domain;
import com.example.demo.model.Project;
import com.example.demo.model.Researcher;
import com.example.demo.model.User;
import com.example.demo.service.DomainService;
import com.example.demo.service.ProjectService;
import com.example.demo.service.ResearcherService;
import com.example.demo.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

@RestController
@RequestMapping("/api/projects")
@Tag(name = "Project Management", description = "APIs for managing research projects")
public class ProjectController {

    private final ProjectService projectService;
    private final UserService userService;
    private final ResearcherService researcherService;
    private final DomainService domainService;

    @Autowired
    public ProjectController(ProjectService projectService, UserService userService, ResearcherService researcherService, DomainService domainService) {
        this.projectService = projectService;
        this.userService = userService;
        this.researcherService = researcherService;
        this.domainService = domainService;
    }

    @PostMapping
    @Operation(summary = "Create a new project")
    public ResponseEntity<Project> createProject(@Valid @RequestBody CreateProjectRequest request) {
        enforceAllowedProjectWrite();
        String username = currentUsername();
        User creator = userService.findByUsername(username)
                .orElseThrow(() -> new ResourceNotFoundException("User", "username", username));
        
        // Get domain
        Domain domain = domainService.findById(request.getDomainId())
                .orElseThrow(() -> new ResourceNotFoundException("Domain", "id", request.getDomainId()));
        
        // Create project
        Project project = new Project();
        project.setTitle(request.getTitle());
        project.setDescription(request.getDescription());
        project.setAiCategory(request.getAiCategory());
        project.setDomain(domain);
        project.setCreatedBy(creator);
        
        // Add researchers if provided
        if (request.getResearcherIds() != null && !request.getResearcherIds().isEmpty()) {
            Set<Researcher> researchers = new HashSet<>();
            for (Long researcherId : request.getResearcherIds()) {
                Researcher researcher = researcherService.findById(researcherId)
                        .orElseThrow(() -> new ResourceNotFoundException("Researcher", "id", researcherId));
                researchers.add(researcher);
            }
            project.setResearchers(researchers);
        }
        
        Project savedProject = projectService.create(project);
        return ResponseEntity.status(HttpStatus.CREATED).body(savedProject);
    }

    @GetMapping
    @Operation(summary = "Get all projects")
    public ResponseEntity<List<Project>> getAllProjects() {
        enforceProjectsReadAccess();
        List<Project> projects = projectService.findAll();
        return ResponseEntity.ok(projects);
    }

    @GetMapping("/me")
    @Operation(summary = "Get my projects")
    public ResponseEntity<List<Project>> getMyProjects() {
        List<Project> projects = projectService.findByCreatedByUsername(currentUsername());
        return ResponseEntity.ok(projects);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get project by ID")
    public ResponseEntity<Project> getProjectById(@PathVariable("id") @Parameter(description = "Project ID") Long id) {
        enforceProjectsReadAccess();
        return projectService.findById(id)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @GetMapping("/domain/{domainId}")
    @Operation(summary = "Get projects by domain ID")
    public ResponseEntity<List<Project>> getProjectsByDomain(
            @PathVariable("domainId") @Parameter(description = "Domain ID") Long domainId) {
        enforceProjectsReadAccess();
        List<Project> projects = projectService.findByDomainId(domainId);
        return ResponseEntity.ok(projects);
    }

    @GetMapping("/category/{aiCategory}")
    @Operation(summary = "Get projects by AI category")
    public ResponseEntity<List<Project>> getProjectsByAiCategory(
            @PathVariable("aiCategory") @Parameter(description = "AI Category") String aiCategory) {
        enforceProjectsReadAccess();
        List<Project> projects = projectService.findByAiCategory(aiCategory);
        return ResponseEntity.ok(projects);
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update a project")
    public ResponseEntity<Project> updateProject(
            @PathVariable("id") @Parameter(description = "Project ID") Long id,
            @Valid @RequestBody Project projectDetails) {
        enforceAllowedProjectWrite();
        enforceOwnershipForChercheur(id);
        Project updatedProject = projectService.update(id, projectDetails);
        return ResponseEntity.ok(updatedProject);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a project by ID")
    public ResponseEntity<Void> deleteProject(@PathVariable("id") @Parameter(description = "Project ID") Long id) {
        enforceAllowedProjectWrite();
        enforceOwnershipForChercheur(id);
        projectService.delete(id);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/{id}/researchers/{researcherId}")
    @Operation(summary = "Add researcher to project")
    public ResponseEntity<Project> addResearcherToProject(
            @PathVariable("id") @Parameter(description = "Project ID") Long id,
            @PathVariable("researcherId") @Parameter(description = "Researcher ID") Long researcherId) {
        enforceAllowedProjectWrite();
        enforceOwnershipForChercheur(id);
        Project project = projectService.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Project", "id", id));
        Researcher researcher = researcherService.findById(researcherId)
                .orElseThrow(() -> new ResourceNotFoundException("Researcher", "id", researcherId));
        project.addResearcher(researcher);
        Project updated = projectService.update(id, project);
        return ResponseEntity.ok(updated);
    }

    @DeleteMapping("/{id}/researchers/{researcherId}")
    @Operation(summary = "Remove researcher from project")
    public ResponseEntity<Project> removeResearcherFromProject(
            @PathVariable("id") @Parameter(description = "Project ID") Long id,
            @PathVariable("researcherId") @Parameter(description = "Researcher ID") Long researcherId) {
        enforceAllowedProjectWrite();
        enforceOwnershipForChercheur(id);
        Project project = projectService.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Project", "id", id));
        Researcher researcher = researcherService.findById(researcherId)
                .orElseThrow(() -> new ResourceNotFoundException("Researcher", "id", researcherId));
        project.removeResearcher(researcher);
        Project updated = projectService.update(id, project);
        return ResponseEntity.ok(updated);
    }

    private void enforceProjectsReadAccess() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        boolean allowed = authentication.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .anyMatch(authority -> authority.equals("ROLE_MODERATOR")
                        || authority.equals("ROLE_RESEARCHER")
                        || authority.equals("ROLE_ADMIN"));
        if (!allowed) {
            throw new AccessDeniedException("Users can only access news and publications");
        }
    }

    private void enforceOwnershipForChercheur(Long projectId) {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        boolean isChercheur = authentication.getAuthorities().stream()
                .anyMatch(a -> "ROLE_RESEARCHER".equals(a.getAuthority()));
        if (isChercheur && !projectService.isOwner(projectId, authentication.getName())) {
            throw new AccessDeniedException("RESEARCHER can only manage their own projects");
        }
    }

    private void enforceAllowedProjectWrite() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        boolean allowed = authentication.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .anyMatch(authority -> authority.equals("ROLE_ADMIN")
                        || authority.equals("ROLE_MODERATOR")
                        || authority.equals("ROLE_RESEARCHER"));
        if (!allowed) {
            throw new AccessDeniedException("You are not allowed to manage projects");
        }
    }

    private String currentUsername() {
        return SecurityContextHolder.getContext().getAuthentication().getName();
    }
}
