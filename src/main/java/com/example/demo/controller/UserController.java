package com.example.demo.controller;

import com.example.demo.dto.UserResponse;
import com.example.demo.exception.ResourceNotFoundException;
import com.example.demo.model.Role;
import com.example.demo.model.User;
import com.example.demo.service.RoleService;
import com.example.demo.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/users")
@Tag(name = "User Management", description = "APIs for managing users and their roles")
public class UserController {

    private final UserService userService;
    private final RoleService roleService;
    private final PasswordEncoder passwordEncoder;

    @Autowired
    public UserController(UserService userService, RoleService roleService, PasswordEncoder passwordEncoder) {
        this.userService = userService;
        this.roleService = roleService;
        this.passwordEncoder = passwordEncoder;
    }

    @GetMapping("/me")
    @Operation(summary = "Get current authenticated user profile")
    public ResponseEntity<UserResponse> getCurrentUser() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        String username = authentication.getName();

        User user = userService.findByUsername(username)
                .orElseThrow(() -> new ResourceNotFoundException("User", "username", username));

        return ResponseEntity.ok(convertToUserResponse(user));
    }

    @PutMapping("/me")
    @Operation(summary = "Update current authenticated user profile")
    public ResponseEntity<UserResponse> updateCurrentUser(@RequestBody com.example.demo.dto.UserUpdateRequest userDetails) {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        String username = authentication.getName();

        User currentUser = userService.findByUsername(username)
                .orElseThrow(() -> new ResourceNotFoundException("User", "username", username));

        // Use the existing update logic in service by creating a partial user object
        User partialUser = new User();
        partialUser.setEmail(userDetails.getEmail());
        partialUser.setPassword(userDetails.getPassword());
        partialUser.setEnabled(currentUser.isEnabled()); // Don't allow self-disabling via this endpoint possibly

        User updatedUser = userService.update(currentUser.getId(), partialUser);
        return ResponseEntity.ok(convertToUserResponse(updatedUser));
    }

    @PostMapping
    @Operation(summary = "Create a new user")
    public ResponseEntity<UserResponse> createUser(@Valid @RequestBody User user) {
        // Encode password before saving
        user.setPassword(passwordEncoder.encode(user.getPassword()));
        User savedUser = userService.create(user);
        return ResponseEntity.status(HttpStatus.CREATED).body(convertToUserResponse(savedUser));
    }

    @GetMapping
    @Operation(summary = "Get all users")
    public ResponseEntity<List<UserResponse>> getAllUsers() {
        List<User> users = userService.findAll();
        List<UserResponse> responses = users.stream()
                .map(this::convertToUserResponse)
                .collect(Collectors.toList());
        return ResponseEntity.ok(responses);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get user by ID")
    public ResponseEntity<UserResponse> getUserById(@PathVariable("id") @Parameter(description = "User ID") Long id) {
        return userService.findById(id)
                .map(this::convertToUserResponse)
                .map(ResponseEntity::ok)
                .orElseThrow(() -> new ResourceNotFoundException("User", "id", id));
    }

    @GetMapping("/username/{username}")
    @Operation(summary = "Get user by username")
    public ResponseEntity<UserResponse> getUserByUsername(@PathVariable("username") @Parameter(description = "Username") String username) {
        return userService.findByUsername(username)
                .map(this::convertToUserResponse)
                .map(ResponseEntity::ok)
                .orElseThrow(() -> new ResourceNotFoundException("User", "username", username));
    }

    @GetMapping("/email/{email}")
    @Operation(summary = "Get user by email")
    public ResponseEntity<UserResponse> getUserByEmail(@PathVariable("email") @Parameter(description = "Email address") String email) {
        return userService.findByEmail(email)
                .map(this::convertToUserResponse)
                .map(ResponseEntity::ok)
                .orElseThrow(() -> new ResourceNotFoundException("User", "email", email));
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update a user")
    public ResponseEntity<UserResponse> updateUser(@PathVariable("id") @Parameter(description = "User ID") Long id,
            @RequestBody com.example.demo.dto.UserUpdateRequest userDetails) {
        
        User partialUser = new User();
        partialUser.setUsername(userDetails.getUsername());
        partialUser.setEmail(userDetails.getEmail());
        partialUser.setPassword(userDetails.getPassword());
        partialUser.setEnabled(userDetails.isEnabled());
        
        User updatedUser = userService.update(id, partialUser);
        return ResponseEntity.ok(convertToUserResponse(updatedUser));
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a user")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public ResponseEntity<Void> deleteUser(@PathVariable("id") @Parameter(description = "User ID") Long id) {
        userService.delete(id);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/{id}/roles")
    @Operation(summary = "Assign roles to a user")
    public ResponseEntity<UserResponse> assignRoles(
            @PathVariable("id") @Parameter(description = "User ID") Long id,
            @RequestBody Set<String> roleNames) {

        User updatedUser = userService.updateRoles(id, roleNames);
        return ResponseEntity.ok(convertToUserResponse(updatedUser));
    }

    private UserResponse convertToUserResponse(User user) {
        return new UserResponse(
                user.getId(),
                user.getUsername(),
                user.getEmail(),
                user.isEnabled(),
                user.getRoles()
        );
    }
}
