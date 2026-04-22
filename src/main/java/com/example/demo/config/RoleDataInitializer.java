package com.example.demo.config;

import com.example.demo.model.Role;
import com.example.demo.model.User;
import com.example.demo.repository.RoleRepository;
import com.example.demo.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;

@Component
public class RoleDataInitializer implements CommandLineRunner {

    private final RoleRepository roleRepository;
    private final UserRepository userRepository;

    @Autowired
    public RoleDataInitializer(RoleRepository roleRepository, UserRepository userRepository) {
        this.roleRepository = roleRepository;
        this.userRepository = userRepository;
    }

    @Override
    @Transactional
    public void run(String... args) {
        // Standard names
        List<String> standardRoles = Arrays.asList(
                "ROLE_ADMIN",
                "ROLE_USER",
                "ROLE_MODERATOR",
                "ROLE_RESEARCHER"
        );

        // 1. Ensure standard roles exist
        for (String roleName : standardRoles) {
            ensureRole(roleName);
        }

        // 2. Cleanup non-standard roles
        cleanupOldRoles(standardRoles);
    }

    private void ensureRole(String roleName) {
        if (roleRepository.findByName(roleName).isEmpty()) {
            roleRepository.save(new Role(roleName));
            System.out.println("Created standard role: " + roleName);
        }
    }

    private void cleanupOldRoles(List<String> standardRoles) {
        List<Role> allRoles = roleRepository.findAll();
        List<Role> rolesToDelete = allRoles.stream()
                .filter(role -> !standardRoles.contains(role.getName()))
                .collect(Collectors.toList());

        if (!rolesToDelete.isEmpty()) {
            System.out.println("Found " + rolesToDelete.size() + " non-standard roles. Starting cleanup...");
            
            // Get all users who might have these roles
            List<User> allUsers = userRepository.findAll();
            
            for (User user : allUsers) {
                boolean rolesRemoved = false;
                Set<Role> userRoles = user.getRoles();
                
                // Remove non-standard roles from this user
                for (Role roleToDelete : rolesToDelete) {
                    if (userRoles.contains(roleToDelete)) {
                        user.getRoles().remove(roleToDelete);
                        rolesRemoved = true;
                    }
                }
                
                if (rolesRemoved) {
                    userRepository.save(user);
                    System.out.println("Cleaned roles for user: " + user.getUsername());
                }
            }

            // Finally, delete the roles from the repository
            for (Role role : rolesToDelete) {
                try {
                    roleRepository.delete(role);
                    System.out.println("Deleted non-standard role: " + role.getName());
                } catch (Exception e) {
                    System.err.println("Could not delete role " + role.getName() + ": " + e.getMessage());
                }
            }
        }
    }
}
