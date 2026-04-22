package com.example.demo.service.impl;

import com.example.demo.exception.ResourceNotFoundException;
import com.example.demo.model.Domain;
import com.example.demo.repository.DomainRepository;
import com.example.demo.service.DomainService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Service
@Transactional
public class DomainServiceImpl implements DomainService {

    private final DomainRepository domainRepository;

    @Autowired
    public DomainServiceImpl(DomainRepository domainRepository) {
        this.domainRepository = domainRepository;
    }

    @Override
    public Domain create(Domain domain) {
        return domainRepository.save(domain);
    }

    @Override
    @Transactional(readOnly = true)
    public List<Domain> findAll() {
        return domainRepository.findAll();
    }

    @Override
    @Transactional(readOnly = true)
    public Optional<Domain> findById(Long id) {
        return domainRepository.findById(id);
    }

    @Override
    @Transactional(readOnly = true)
    public Optional<Domain> findByName(String name) {
        return domainRepository.findByName(name);
    }

    @Override
    public Domain update(Long id, Domain domainDetails) {
        Domain existingDomain = domainRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Domain", "id", id));

        if (domainDetails.getName() != null) {
            existingDomain.setName(domainDetails.getName());
        }
        if (domainDetails.getDescription() != null) {
            existingDomain.setDescription(domainDetails.getDescription());
        }

        return domainRepository.save(existingDomain);
    }

    @Override
    public void delete(Long id) {
        if (!domainRepository.existsById(id)) {
            throw new ResourceNotFoundException("Domain", "id", id);
        }
        domainRepository.deleteById(id);
    }

    @Override
    @Transactional(readOnly = true)
    public boolean existsById(Long id) {
        return domainRepository.existsById(id);
    }

    @Override
    @Transactional(readOnly = true)
    public long count() {
        return domainRepository.count();
    }
}
