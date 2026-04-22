package com.example.demo.service.impl;

import com.example.demo.exception.ResourceNotFoundException;
import com.example.demo.model.Researcher;
import com.example.demo.repository.ResearcherRepository;
import com.example.demo.service.ResearcherService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Service
@Transactional
public class ResearcherServiceImpl implements ResearcherService {

    private final ResearcherRepository researcherRepository;

    @Autowired
    public ResearcherServiceImpl(ResearcherRepository researcherRepository) {
        this.researcherRepository = researcherRepository;
    }

    @Override
    public Researcher create(Researcher researcher) {
        return researcherRepository.save(researcher);
    }

    @Override
    @Transactional(readOnly = true)
    public List<Researcher> findAll() {
        return researcherRepository.findAll();
    }

    @Override
    @Transactional(readOnly = true)
    public Optional<Researcher> findById(Long id) {
        return researcherRepository.findById(id);
    }

    @Override
    @Transactional(readOnly = true)
    public Optional<Researcher> findByEmail(String email) {
        return researcherRepository.findByEmail(email);
    }

    @Override
    @Transactional(readOnly = true)
    public List<Researcher> findByAffiliation(String affiliation) {
        return researcherRepository.findByAffiliation(affiliation);
    }

    @Override
    public Researcher update(Long id, Researcher researcherDetails) {
        Researcher existingResearcher = researcherRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Researcher", "id", id));

        if (researcherDetails.getFullName() != null) {
            existingResearcher.setFullName(researcherDetails.getFullName());
        }
        if (researcherDetails.getEmail() != null) {
            existingResearcher.setEmail(researcherDetails.getEmail());
        }
        if (researcherDetails.getAffiliation() != null) {
            existingResearcher.setAffiliation(researcherDetails.getAffiliation());
        }
        if (researcherDetails.getBiography() != null) {
            existingResearcher.setBiography(researcherDetails.getBiography());
        }

        return researcherRepository.save(existingResearcher);
    }

    @Override
    public void delete(Long id) {
        if (!researcherRepository.existsById(id)) {
            throw new ResourceNotFoundException("Researcher", "id", id);
        }
        researcherRepository.deleteById(id);
    }

    @Override
    @Transactional(readOnly = true)
    public boolean existsById(Long id) {
        return researcherRepository.existsById(id);
    }

    @Override
    @Transactional(readOnly = true)
    public long count() {
        return researcherRepository.count();
    }
}
