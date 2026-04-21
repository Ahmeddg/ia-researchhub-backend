package com.example.demo.service;

import java.util.Map;

public interface StatisticsService {
    long getResearchersCount();

    long getPublicationsCount();

    long getProjectsCount();

    long getDomainsCount();

    long getNewsCount();

    long getUsersCount();

    Map<String, Long> getPublicationsCountByDomain();

    Map<String, Long> getProjectsCountByCategory();

    Map<String, Object> getDashboardStatistics();
}
