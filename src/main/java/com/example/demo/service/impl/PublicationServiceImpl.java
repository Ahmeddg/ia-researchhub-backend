package com.example.demo.service.impl;

import com.example.demo.exception.ResourceNotFoundException;
import com.example.demo.model.Publication;
import com.example.demo.repository.PublicationRepository;
import com.example.demo.service.PublicationService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Service
@Transactional
public class PublicationServiceImpl implements PublicationService {

    private final PublicationRepository publicationRepository;

    @Autowired
    public PublicationServiceImpl(PublicationRepository publicationRepository) {
        this.publicationRepository = publicationRepository;
    }

    @Override
    public Publication create(Publication publication) {
        return publicationRepository.save(publication);
    }

    @Override
    @Transactional(readOnly = true)
    public List<Publication> findAll() {
        return publicationRepository.findAll();
    }

    @Override
    @Transactional(readOnly = true)
    public Optional<Publication> findById(Long id) {
        return publicationRepository.findById(id);
    }

    @Override
    @Transactional(readOnly = true)
    public Optional<Publication> findByDoi(String doi) {
        return publicationRepository.findByDoi(doi);
    }

    @Override
    @Transactional(readOnly = true)
    public List<Publication> findByDomainId(Long domainId) {
        return publicationRepository.findByDomainId(domainId);
    }

    @Override
    @Transactional(readOnly = true)
    public List<Publication> findByResearcherId(Long researcherId) {
        return publicationRepository.findByResearchersId(researcherId);
    }

    @Override
    @Transactional(readOnly = true)
    public List<Publication> findByCreatedByUsername(String username) {
        return publicationRepository.findByCreatedByUsername(username);
    }

    @Override
    public Publication update(Long id, Publication publicationDetails) {
        Publication existingPublication = publicationRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Publication", "id", id));

        if (publicationDetails.getTitle() != null) {
            existingPublication.setTitle(publicationDetails.getTitle());
        }
        if (publicationDetails.getAbstractText() != null) {
            existingPublication.setAbstractText(publicationDetails.getAbstractText());
        }
        if (publicationDetails.getPublicationDate() != null) {
            existingPublication.setPublicationDate(publicationDetails.getPublicationDate());
        }
        if (publicationDetails.getPdfUrl() != null) {
            existingPublication.setPdfUrl(publicationDetails.getPdfUrl());
        }
        if (publicationDetails.getDoi() != null) {
            existingPublication.setDoi(publicationDetails.getDoi());
        }
        if (publicationDetails.getDomain() != null) {
            existingPublication.setDomain(publicationDetails.getDomain());
        }
        if (publicationDetails.getResearchers() != null) {
            existingPublication.setResearchers(publicationDetails.getResearchers());
        }

        return publicationRepository.save(existingPublication);
    }

    @Override
    public void delete(Long id) {
        if (!publicationRepository.existsById(id)) {
            throw new ResourceNotFoundException("Publication", "id", id);
        }
        publicationRepository.deleteById(id);
    }

    @Override
    @Transactional(readOnly = true)
    public boolean existsById(Long id) {
        return publicationRepository.existsById(id);
    }

    @Override
    @Transactional(readOnly = true)
    public long count() {
        return publicationRepository.count();
    }

    @Override
    @Transactional(readOnly = true)
    public long countByDomainId(Long domainId) {
        return publicationRepository.countByDomainId(domainId);
    }

    @Override
    @Transactional(readOnly = true)
    public boolean isOwner(Long publicationId, String username) {
        return publicationRepository.existsByIdAndCreatedByUsername(publicationId, username);
    }
}
