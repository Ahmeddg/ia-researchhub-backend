package com.example.demo.repository;

import com.example.demo.model.Publication;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;

@Repository
public interface PublicationRepository extends JpaRepository<Publication, Long> {
    List<Publication> findByDomainId(Long domainId);
    Optional<Publication> findByDoi(String doi);
}
