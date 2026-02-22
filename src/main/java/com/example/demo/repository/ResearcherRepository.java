package com.example.demo.repository;

import com.example.demo.model.Researcher;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface ResearcherRepository extends JpaRepository<Researcher, Long> {
    Optional<Researcher> findByEmail(String email);
}
