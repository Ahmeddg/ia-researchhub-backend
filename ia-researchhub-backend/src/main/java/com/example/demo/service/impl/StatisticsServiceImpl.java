package com.example.demo.service.impl;

import com.example.demo.model.Domain;
import com.example.demo.repository.*;
import com.example.demo.service.StatisticsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@Transactional(readOnly = true)
public class StatisticsServiceImpl implements StatisticsService {

    private final ResearcherRepository researcherRepository;
    private final PublicationRepository publicationRepository;
    private final ProjectRepository projectRepository;
    private final DomainRepository domainRepository;
    private final NewsRepository newsRepository;
    private final UserRepository userRepository;

    @Autowired
    public StatisticsServiceImpl(
            ResearcherRepository researcherRepository,
            PublicationRepository publicationRepository,
            ProjectRepository projectRepository,
            DomainRepository domainRepository,
            NewsRepository newsRepository,
            UserRepository userRepository) {
        this.researcherRepository = researcherRepository;
        this.publicationRepository = publicationRepository;
        this.projectRepository = projectRepository;
        this.domainRepository = domainRepository;
        this.newsRepository = newsRepository;
        this.userRepository = userRepository;
    }

    @Override
    public long getResearchersCount() {
        return researcherRepository.count();
    }

    @Override
    public long getPublicationsCount() {
        return publicationRepository.count();
    }

    @Override
    public long getProjectsCount() {
        return projectRepository.count();
    }

    @Override
    public long getDomainsCount() {
        return domainRepository.count();
    }

    @Override
    public long getNewsCount() {
        return newsRepository.count();
    }

    @Override
    public long getUsersCount() {
        return userRepository.count();
    }

    @Override
    public Map<String, Long> getPublicationsCountByDomain() {
        Map<String, Long> result = new HashMap<>();
        List<Domain> domains = domainRepository.findAll();
        for (Domain domain : domains) {
            long count = publicationRepository.countByDomainId(domain.getId());
            result.put(domain.getName(), count);
        }
        return result;
    }

    @Override
    public Map<String, Long> getProjectsCountByCategory() {
        Map<String, Long> result = new HashMap<>();
        List<String> categories = List.of(
                "Machine Learning",
                "Deep Learning",
                "Natural Language Processing",
                "Computer Vision",
                "Robotics",
                "Other");
        for (String category : categories) {
            long count = projectRepository.countByAiCategory(category);
            if (count > 0) {
                result.put(category, count);
            }
        }
        return result;
    }

    @Override
    public Map<String, Object> getDashboardStatistics() {
        Map<String, Object> stats = new HashMap<>();

        // Total counts
        stats.put("totalResearchers", getResearchersCount());
        stats.put("totalPublications", getPublicationsCount());
        stats.put("totalProjects", getProjectsCount());
        stats.put("totalDomains", getDomainsCount());
        stats.put("totalNews", getNewsCount());
        stats.put("totalUsers", getUsersCount());

        // Breakdowns
        stats.put("publicationsByDomain", getPublicationsCountByDomain());
        stats.put("projectsByCategory", getProjectsCountByCategory());

        return stats;
    }
}
