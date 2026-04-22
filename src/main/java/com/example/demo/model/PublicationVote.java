package com.example.demo.model;

import jakarta.persistence.*;

@Entity
@Table(name = "publication_votes", uniqueConstraints = {
    @UniqueConstraint(columnNames = {"user_id", "publication_id"})
})
public class PublicationVote {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "publication_id", nullable = false)
    private Publication publication;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private VoteType type;

    public enum VoteType {
        UPVOTE, DOWNVOTE
    }

    public PublicationVote() {}

    public PublicationVote(User user, Publication publication, VoteType type) {
        this.user = user;
        this.publication = publication;
        this.type = type;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }

    public Publication getPublication() { return publication; }
    public void setPublication(Publication publication) { this.publication = publication; }

    public VoteType getType() { return type; }
    public void setType(VoteType type) { this.type = type; }
}
