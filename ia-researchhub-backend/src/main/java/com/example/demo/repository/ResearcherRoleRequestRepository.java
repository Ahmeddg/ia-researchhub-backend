package com.example.demo.repository;

import com.example.demo.model.ResearcherRequestStatus;
import com.example.demo.model.ResearcherRoleRequest;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ResearcherRoleRequestRepository extends JpaRepository<ResearcherRoleRequest, Long> {
    List<ResearcherRoleRequest> findByStatus(ResearcherRequestStatus status);

    Optional<ResearcherRoleRequest> findFirstByUserIdAndStatusOrderByCreatedAtDesc(Long userId, ResearcherRequestStatus status);

    List<ResearcherRoleRequest> findByUserIdOrderByCreatedAtDesc(Long userId);
}
