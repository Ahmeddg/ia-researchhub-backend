package com.example.demo.service.impl;

import com.example.demo.dto.ResearcherRoleRequestCreateRequest;
import com.example.demo.exception.BadRequestException;
import com.example.demo.exception.ResourceNotFoundException;
import com.example.demo.model.Researcher;
import com.example.demo.model.ResearcherRequestStatus;
import com.example.demo.model.ResearcherRoleRequest;
import com.example.demo.model.Role;
import com.example.demo.model.User;
import com.example.demo.repository.ResearcherRepository;
import com.example.demo.repository.ResearcherRoleRequestRepository;
import com.example.demo.repository.RoleRepository;
import com.example.demo.repository.UserRepository;
import com.example.demo.service.ResearcherRoleRequestService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Service
@Transactional
public class ResearcherRoleRequestServiceImpl implements ResearcherRoleRequestService {

    private final ResearcherRoleRequestRepository requestRepository;
    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final ResearcherRepository researcherRepository;

    @Autowired
    public ResearcherRoleRequestServiceImpl(ResearcherRoleRequestRepository requestRepository,
            UserRepository userRepository,
            RoleRepository roleRepository,
            ResearcherRepository researcherRepository) {
        this.requestRepository = requestRepository;
        this.userRepository = userRepository;
        this.roleRepository = roleRepository;
        this.researcherRepository = researcherRepository;
    }

    @Override
    public ResearcherRoleRequest createRequest(String username, ResearcherRoleRequestCreateRequest request) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new ResourceNotFoundException("User", "username", username));

        boolean alreadyResearcher = user.getRoles().stream().anyMatch(r -> "CHERCHEUR".equals(r.getName()));
        if (alreadyResearcher) {
            throw new BadRequestException("User already has CHERCHEUR role");
        }

        requestRepository.findFirstByUserIdAndStatusOrderByCreatedAtDesc(user.getId(), ResearcherRequestStatus.PENDING)
                .ifPresent(existing -> {
                    throw new BadRequestException("A pending researcher request already exists for this user");
                });

        ResearcherRoleRequest entity = new ResearcherRoleRequest();
        entity.setUser(user);
        entity.setFullName(request.getFullName());
        entity.setAffiliation(request.getAffiliation());
        entity.setBiography(request.getBiography());
        entity.setMotivation(request.getMotivation());
        entity.setStatus(ResearcherRequestStatus.PENDING);

        return requestRepository.save(entity);
    }

    @Override
    @Transactional(readOnly = true)
    public List<ResearcherRoleRequest> getMyRequests(String username) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new ResourceNotFoundException("User", "username", username));
        return requestRepository.findByUserIdOrderByCreatedAtDesc(user.getId());
    }

    @Override
    @Transactional(readOnly = true)
    public List<ResearcherRoleRequest> getPendingRequests() {
        return requestRepository.findByStatus(ResearcherRequestStatus.PENDING);
    }

    @Override
    public ResearcherRoleRequest approveRequest(Long requestId, String adminUsername) {
        ResearcherRoleRequest request = requestRepository.findById(requestId)
                .orElseThrow(() -> new ResourceNotFoundException("ResearcherRoleRequest", "id", requestId));

        if (request.getStatus() != ResearcherRequestStatus.PENDING) {
            throw new BadRequestException("Only pending requests can be approved");
        }

        User admin = userRepository.findByUsername(adminUsername)
                .orElseThrow(() -> new ResourceNotFoundException("User", "username", adminUsername));
        User user = request.getUser();

        Role chercheurRole = roleRepository.findByName("CHERCHEUR")
                .orElseGet(() -> roleRepository.save(new Role("CHERCHEUR")));
        user.addRole(chercheurRole);
        userRepository.save(user);

        researcherRepository.findByEmail(user.getEmail())
                .orElseGet(() -> {
                    Researcher researcher = new Researcher(
                            request.getFullName(),
                            user.getEmail(),
                            request.getAffiliation());
                    researcher.setBiography(request.getBiography());
                    return researcherRepository.save(researcher);
                });

        request.setStatus(ResearcherRequestStatus.APPROVED);
        request.setReviewedAt(LocalDateTime.now());
        request.setReviewedBy(admin);
        return requestRepository.save(request);
    }

    @Override
    public ResearcherRoleRequest rejectRequest(Long requestId, String adminUsername) {
        ResearcherRoleRequest request = requestRepository.findById(requestId)
                .orElseThrow(() -> new ResourceNotFoundException("ResearcherRoleRequest", "id", requestId));

        if (request.getStatus() != ResearcherRequestStatus.PENDING) {
            throw new BadRequestException("Only pending requests can be rejected");
        }

        User admin = userRepository.findByUsername(adminUsername)
                .orElseThrow(() -> new ResourceNotFoundException("User", "username", adminUsername));

        request.setStatus(ResearcherRequestStatus.REJECTED);
        request.setReviewedAt(LocalDateTime.now());
        request.setReviewedBy(admin);
        return requestRepository.save(request);
    }
}
