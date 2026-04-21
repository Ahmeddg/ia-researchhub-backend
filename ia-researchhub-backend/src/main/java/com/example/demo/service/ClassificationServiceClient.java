package com.example.demo.service;

import com.example.demo.dto.ClassificationRequestDTO;
import com.example.demo.dto.ClassificationResponseDTO;
import com.example.demo.dto.PersonalizedRecommendationRequest;
import com.example.demo.model.Publication;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.Collections;
import java.util.List;
import com.example.demo.dto.RecommendationDTO;
import java.util.Map;

/**
 * HTTP client for the Python classification microservice.
 * Calls POST /classify and maps the response back to a
 * ClassificationResponseDTO.
 *
 * The Python service uses the SAME PostgreSQL database, so after this call:
 * - The publication embedding is stored in publication_embeddings
 * - publications.cluster_id / cluster_label are updated directly by Python
 */
@Service
public class ClassificationServiceClient {

    private static final Logger log = LoggerFactory.getLogger(ClassificationServiceClient.class);

    private final RestTemplate restTemplate;
    private final String classificationServiceUrl;

    public ClassificationServiceClient(
            @Value("${classification.service.url:http://localhost:8000}") String classificationServiceUrl) {
        this.restTemplate = new RestTemplate();
        this.classificationServiceUrl = classificationServiceUrl;
    }

    /**
     * Classify a publication by calling the Python service.
     *
     * @param publication The saved publication entity (must have a real ID
     *                    already).
     * @return The classification result, or null if the service is unavailable.
     */
    public ClassificationResponseDTO classify(Publication publication) {
        String domainName = publication.getDomain() != null ? publication.getDomain().getName() : null;

        ClassificationRequestDTO request = new ClassificationRequestDTO(
                publication.getId(),
                publication.getTitle(),
                publication.getAbstractText(),
                domainName,
                publication.getPdfUrl());

        String url = classificationServiceUrl + "/classify";
        log.info("Calling classification service at {} for publication id={}", url, publication.getId());

        try {
            ResponseEntity<ClassificationResponseDTO> response = restTemplate.postForEntity(url, request,
                    ClassificationResponseDTO.class);

            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                log.info("Classification successful for publication id={}: cluster='{}', confidence={}",
                        publication.getId(),
                        response.getBody().getClusterLabel(),
                        response.getBody().getConfidence());
                return response.getBody();
            }

            log.warn("Classification service returned status {} for publication id={}",
                    response.getStatusCode(), publication.getId());
            return null;

        } catch (RestClientException e) {
            log.error("Classification service unavailable ({}): {}. Publication {} will be saved without AI metadata.",
                    url, e.getMessage(), publication.getId());
            return null;
        }
    }

    /**
     * Get personalized recommendations from the Python service.
     */
    public List<RecommendationDTO> getPersonalizedRecommendations(List<Long> upvotedIds, List<Long> downvotedIds, int limit) {
        String url = classificationServiceUrl + "/recommend/personalized";
        PersonalizedRecommendationRequest request = 
            new PersonalizedRecommendationRequest(upvotedIds, downvotedIds, limit);

        try {
            // Using parameterized type reference to properly handle List<RecommendationDTO>
            ResponseEntity<RecommendationDTO[]> response = restTemplate.postForEntity(url, request, RecommendationDTO[].class);
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                RecommendationDTO[] body = response.getBody();
                log.info("Received {} recommendations with scores from AI service", body.length);
                return java.util.Arrays.asList(body);
            }
        } catch (RestClientException e) {
            log.error("Failed to get personal recommendations from AI service ({}): {}", url, e.getMessage());
        }
        return java.util.Collections.emptyList();
    }
}
