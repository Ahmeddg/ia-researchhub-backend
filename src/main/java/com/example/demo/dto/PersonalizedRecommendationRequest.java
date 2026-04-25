package com.example.demo.dto;

import java.util.List;

public class PersonalizedRecommendationRequest {
    private List<Long> upvotedIds;
    private List<Long> downvotedIds;
    private int limit;

    public PersonalizedRecommendationRequest() {}

    public PersonalizedRecommendationRequest(List<Long> upvotedIds, List<Long> downvotedIds, int limit) {
        this.upvotedIds = upvotedIds;
        this.downvotedIds = downvotedIds;
        this.limit = limit;
    }

    public List<Long> getUpvotedIds() { return upvotedIds; }
    public void setUpvotedIds(List<Long> upvotedIds) { this.upvotedIds = upvotedIds; }

    public List<Long> getDownvotedIds() { return downvotedIds; }
    public void setDownvotedIds(List<Long> downvotedIds) { this.downvotedIds = downvotedIds; }

    public int getLimit() { return limit; }
    public void setLimit(int limit) { this.limit = limit; }
}
