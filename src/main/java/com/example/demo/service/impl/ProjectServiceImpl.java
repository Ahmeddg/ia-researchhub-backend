package com.example.demo.service.impl;

import com.example.demo.exception.ResourceNotFoundException;
import com.example.demo.model.Project;
import com.example.demo.repository.ProjectRepository;
import com.example.demo.service.ProjectService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Service
@Transactional
public class ProjectServiceImpl implements ProjectService {

    private final ProjectRepository projectRepository;

    @Autowired
    public ProjectServiceImpl(ProjectRepository projectRepository) {
        this.projectRepository = projectRepository;
    }

    @Override
    public Project create(Project project) {
        return projectRepository.save(project);
    }

    @Override
    @Transactional(readOnly = true)
    public List<Project> findAll() {
        return projectRepository.findAll();
    }

    @Override
    @Transactional(readOnly = true)
    public Optional<Project> findById(Long id) {
        return projectRepository.findById(id);
    }

    @Override
    @Transactional(readOnly = true)
    public List<Project> findByDomainId(Long domainId) {
        return projectRepository.findByDomainId(domainId);
    }

    @Override
    @Transactional(readOnly = true)
    public List<Project> findByAiCategory(String aiCategory) {
        return projectRepository.findByAiCategory(aiCategory);
    }

    @Override
    public Project update(Long id, Project projectDetails) {
        Project existingProject = projectRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Project", "id", id));

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

        return projectRepository.save(existingProject);
    }

    @Override
    public void delete(Long id) {
        if (!projectRepository.existsById(id)) {
            throw new ResourceNotFoundException("Project", "id", id);
        }
        projectRepository.deleteById(id);
    }

    @Override
    @Transactional(readOnly = true)
    public boolean existsById(Long id) {
        return projectRepository.existsById(id);
    }

    @Override
    @Transactional(readOnly = true)
    public long count() {
        return projectRepository.count();
    }

    @Override
    @Transactional(readOnly = true)
    public long countByAiCategory(String aiCategory) {
        return projectRepository.countByAiCategory(aiCategory);
    }
}
