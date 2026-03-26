package com.example.demo.service;

import com.example.demo.model.Domain;
import java.util.List;
import java.util.Optional;

public interface DomainService {
    Domain create(Domain domain);

    List<Domain> findAll();

    Optional<Domain> findById(Long id);

    Optional<Domain> findByName(String name);

    Domain update(Long id, Domain domainDetails);

    void delete(Long id);

    boolean existsById(Long id);

    long count();
}
