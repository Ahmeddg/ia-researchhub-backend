package com.example.demo.service;

import com.example.demo.model.Researcher;
import java.util.List;
import java.util.Optional;

public interface ResearcherService {
    Researcher create(Researcher researcher);

    List<Researcher> findAll();

    Optional<Researcher> findById(Long id);

    Optional<Researcher> findByEmail(String email);

    List<Researcher> findByAffiliation(String affiliation);

    Researcher update(Long id, Researcher researcherDetails);

    void delete(Long id);

    boolean existsById(Long id);

    long count();
}
