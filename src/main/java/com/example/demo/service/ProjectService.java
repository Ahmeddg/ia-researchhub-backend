package com.example.demo.service;

import com.example.demo.model.Project;
import java.util.List;
import java.util.Optional;

public interface ProjectService {
    Project create(Project project);

    List<Project> findAll();

    Optional<Project> findById(Long id);

    List<Project> findByDomainId(Long domainId);

    List<Project> findByAiCategory(String aiCategory);

    List<Project> findByCreatedByUsername(String username);

    Project update(Long id, Project projectDetails);

    void delete(Long id);

    boolean existsById(Long id);

    long count();

    long countByAiCategory(String aiCategory);

    boolean isOwner(Long projectId, String username);
}
