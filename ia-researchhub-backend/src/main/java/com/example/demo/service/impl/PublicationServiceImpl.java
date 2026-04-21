package com.example.demo.service.impl;

import com.example.demo.dto.RecommendationDTO;
import com.example.demo.exception.ResourceNotFoundException;
import com.example.demo.repository.PublicationRepository;
import com.example.demo.repository.PublicationVoteRepository;
import com.example.demo.repository.UserRepository;
import com.example.demo.model.Publication;
import com.example.demo.model.PublicationVote;
import com.example.demo.model.User;
import com.example.demo.service.PublicationService;
import com.example.demo.service.ClassificationServiceClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Objects;
import java.util.stream.Collectors;

@Service
@Transactional
public class PublicationServiceImpl implements PublicationService {

    private static final Logger log = LoggerFactory.getLogger(PublicationServiceImpl.class);

    private final PublicationRepository publicationRepository;
    private final PublicationVoteRepository voteRepository;
    private final UserRepository userRepository;
    private final ClassificationServiceClient classificationServiceClient;

    @Autowired
    public PublicationServiceImpl(PublicationRepository publicationRepository,
                                 PublicationVoteRepository voteRepository,
                                 UserRepository userRepository,
                                 ClassificationServiceClient classificationServiceClient) {
        this.publicationRepository = publicationRepository;
        this.voteRepository = voteRepository;
        this.userRepository = userRepository;
        this.classificationServiceClient = classificationServiceClient;
    }

    @Override
    public Publication create(Publication publication) {
        publication.setStatus("PUBLISHED");
        return publicationRepository.save(publication);
    }

    @Override
    public Publication createDraft(Publication publication) {
        publication.setStatus("DRAFT");
        return publicationRepository.save(publication);
    }

    @Override
    public Publication confirmPublication(Long id, String aiCategories, String aiKeywords, Double aiConfidence) {
        Publication existing = publicationRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Publication", "id", id));
        existing.setStatus("PUBLISHED");
        existing.setAiCategories(aiCategories);
        existing.setAiKeywords(aiKeywords);
        existing.setAiConfidence(aiConfidence);
        return publicationRepository.save(existing);
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
        if (publicationDetails.getJournal() != null) {
            existingPublication.setJournal(publicationDetails.getJournal());
        }
        if (publicationDetails.getImageUrl() != null) {
            existingPublication.setImageUrl(publicationDetails.getImageUrl());
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

    @Override
    public Publication upvote(Long id, String username) {
        return handleVote(id, username, PublicationVote.VoteType.UPVOTE);
    }

    @Override
    public Publication downvote(Long id, String username) {
        return handleVote(id, username, PublicationVote.VoteType.DOWNVOTE);
    }

    private Publication handleVote(Long publicationId, String username, PublicationVote.VoteType type) {
        Publication publication = publicationRepository.findById(publicationId)
                .orElseThrow(() -> new ResourceNotFoundException("Publication", "id", publicationId));
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new ResourceNotFoundException("User", "username", username));

        Optional<PublicationVote> existingVote = voteRepository.findByUserIdAndPublicationId(user.getId(), publicationId);

        if (existingVote.isPresent()) {
            PublicationVote vote = existingVote.get();
            if (vote.getType() == type) {
                // TOGGLE OFF: User clicked the same button again, so remove the vote
                if (type == PublicationVote.VoteType.UPVOTE) {
                    publication.setUpvotes(Math.max(0, publication.getUpvotes() - 1));
                } else {
                    publication.setDownvotes(Math.max(0, publication.getDownvotes() - 1));
                }
                voteRepository.delete(vote);
            } else {
                // SWITCH: User changed from UP to DOWN (or vice versa)
                if (type == PublicationVote.VoteType.UPVOTE) {
                    publication.setUpvotes(publication.getUpvotes() + 1);
                    publication.setDownvotes(Math.max(0, publication.getDownvotes() - 1));
                } else {
                    publication.setDownvotes(publication.getDownvotes() + 1);
                    publication.setUpvotes(Math.max(0, publication.getUpvotes() - 1));
                }
                vote.setType(type);
                voteRepository.save(vote);
            }
        } else {
            // NEW VOTE: No previous vote exists
            if (type == PublicationVote.VoteType.UPVOTE) {
                publication.setUpvotes(publication.getUpvotes() + 1);
            } else {
                publication.setDownvotes(publication.getDownvotes() + 1);
            }
            voteRepository.save(new PublicationVote(user, publication, type));
        }

        return publicationRepository.save(publication);
    }
    @Override
    @Transactional(readOnly = true)
    public List<Publication> getPersonalizedRecommendations(String username) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new ResourceNotFoundException("User", "username", username));

        List<PublicationVote> votes = voteRepository.findByUserId(user.getId());
        
        List<Long> upvotedIds = votes.stream()
                .filter(v -> v.getType() == PublicationVote.VoteType.UPVOTE)
                .map(v -> v.getPublication().getId())
                .collect(Collectors.toList());
        
        List<Long> downvotedIds = votes.stream()
                .filter(v -> v.getType() == PublicationVote.VoteType.DOWNVOTE)
                .map(v -> v.getPublication().getId())
                .collect(Collectors.toList());

        log.info("PREPARING RECOMMENDATIONS - Upvoted count: {}, Downvoted count: {}", upvotedIds.size(), downvotedIds.size());
        
        List<RecommendationDTO> recommendations = classificationServiceClient.getPersonalizedRecommendations(upvotedIds, downvotedIds, 15);
        
        try {
            List<Long> recommendedIds = recommendations.stream()
                    .map(RecommendationDTO::getPublicationId)
                    .collect(Collectors.toList());

            log.info("Original recommended IDs from AI: {}", recommendedIds);
            
            List<Publication> allRecommended = publicationRepository.findAllById(recommendedIds);
            log.info("Found {} publications in DB for these IDs", allRecommended.size());
            
            Map<Long, Publication> pubMap = new java.util.HashMap<>();
            for (Publication p : allRecommended) {
                if (p != null && p.getId() != null) {
                    pubMap.put(p.getId(), p);
                }
            }

            // Map scores from DTOs
            Map<Long, Double> scoreMap = recommendations.stream()
                    .collect(Collectors.toMap(RecommendationDTO::getPublicationId, RecommendationDTO::getSimilarityScore, (a, b) -> a));
            
            // Map the results back to the original order of recommendedIds
            List<Publication> result = recommendedIds.stream()
                    .map(pubMap::get)
                    .filter(Objects::nonNull)
                    .distinct()
                    .peek(p -> {
                        Double rawScore = scoreMap.get(p.getId());
                        if (rawScore != null) {
                            // Premium Scaling: Use square root to boost moderate scores visually
                            // effectively mapping 0.49 -> 0.7, 0.81 -> 0.9, 1.0 -> 1.0
                            double boostedScore = Math.sqrt(rawScore);
                            // Cap at 1.0
                            p.setSimilarityScore(Math.min(1.0, boostedScore));
                        }
                        p.setUpvotedByUser(upvotedIds.contains(p.getId()));
                    })
                    .collect(Collectors.toList());
            
            // Custom Sorting: Interactive ones to the bottom, then by Score DESC
            List<Long> interactedIds = new java.util.ArrayList<>();
            interactedIds.addAll(upvotedIds);
            interactedIds.addAll(downvotedIds);

            result.sort((p1, p2) -> {
                boolean p1Int = interactedIds.contains(p1.getId());
                boolean p2Int = interactedIds.contains(p2.getId());
                if (p1Int && !p2Int) return 1;
                if (!p1Int && p2Int) return -1;
                double s1 = p1.getSimilarityScore() != null ? p1.getSimilarityScore() : 0.0;
                double s2 = p2.getSimilarityScore() != null ? p2.getSimilarityScore() : 0.0;
                return Double.compare(s2, s1);
            });
            
            log.info("Successfully prepared {} publications with PREMIUM SCALING and re-sorting", result.size());
            return result;
        } catch (Exception e) {
            log.error("CRITICAL ERROR in recommendation mapping: {}", e.getMessage(), e);
            return findAll(); 
        }
    }
    @Override
    @Transactional(readOnly = true)
    public List<Publication> getNewPublications() {
        return publicationRepository.findAllByOrderByPublicationDateDesc();
    }

    @Override
    @Transactional(readOnly = true)
    public List<Publication> getTopPublications() {
        return publicationRepository.findAllByOrderByUpvotesDesc();
    }

    @Override
    @Transactional(readOnly = true)
    public List<Publication> getHotPublications() {
        return publicationRepository.findHotPublications();
    }
}
