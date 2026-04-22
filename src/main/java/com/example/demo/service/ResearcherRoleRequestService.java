package com.example.demo.service;

import com.example.demo.dto.ResearcherRoleRequestCreateRequest;
import com.example.demo.model.ResearcherRoleRequest;

import java.util.List;

public interface ResearcherRoleRequestService {
    ResearcherRoleRequest createRequest(String username, ResearcherRoleRequestCreateRequest request);

    List<ResearcherRoleRequest> getMyRequests(String username);

    List<ResearcherRoleRequest> getPendingRequests();

    ResearcherRoleRequest approveRequest(Long requestId, String adminUsername);

    ResearcherRoleRequest rejectRequest(Long requestId, String adminUsername);
}
