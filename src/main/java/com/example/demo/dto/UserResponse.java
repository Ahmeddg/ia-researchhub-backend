package com.example.demo.dto;

import java.util.Set;

public class UserResponse {

    private Long id;
    private String username;
    private String email;
    private boolean enabled;
    private Set<String> roles;

    public UserResponse() {
    }

    public UserResponse(Long id, String username, String email, boolean enabled, Set<String> roles) {
        this.id = id;
        this.username = username;
        this.email = email;
        this.enabled = enabled;
        this.roles = roles;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public boolean isEnabled() {
        return enabled;
    }

    public void setEnabled(boolean enabled) {
        this.enabled = enabled;
    }

    public Set<String> getRoles() {
        return roles;
    }

    public void setRoles(Set<String> roles) {
        this.roles = roles;
    }
}
