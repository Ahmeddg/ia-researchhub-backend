package com.example.demo.controller;

import com.example.demo.model.Role;
import com.example.demo.repository.RoleRepository;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/api/roles")
@CrossOrigin(origins = "*")
@Tag(name = "Role Management", description = "APIs for managing user roles")
public class RoleController {

    @Autowired
    private RoleRepository roleRepository;

    @PostMapping
    @Operation(summary = "Create a new role")
    public ResponseEntity<Role> createRole(@RequestBody Role role) {
        try {
            Role savedRole = roleRepository.save(role);
            return ResponseEntity.status(HttpStatus.CREATED).body(savedRole);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping
    @Operation(summary = "Get all roles")
    public ResponseEntity<List<Role>> getAllRoles() {
        try {
            List<Role> roles = roleRepository.findAll();
            return ResponseEntity.ok(roles);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get role by ID")
    public ResponseEntity<Role> getRoleById(@PathVariable @Parameter(description = "Role ID") Long id) {
        try {
            Optional<Role> role = roleRepository.findById(id);
            return role.map(ResponseEntity::ok)
                    .orElseGet(() -> ResponseEntity.notFound().build());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/name/{name}")
    @Operation(summary = "Get role by name")
    public ResponseEntity<Role> getRoleByName(@PathVariable @Parameter(description = "Role name") String name) {
        try {
            Optional<Role> role = roleRepository.findByName(name);
            return role.map(ResponseEntity::ok)
                    .orElseGet(() -> ResponseEntity.notFound().build());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update a role")
    public ResponseEntity<Role> updateRole(@PathVariable @Parameter(description = "Role ID") Long id,
                                          @RequestBody Role roleDetails) {
        try {
            Optional<Role> role = roleRepository.findById(id);
            if (role.isPresent()) {
                Role existingRole = role.get();
                if (roleDetails.getName() != null) {
                    existingRole.setName(roleDetails.getName());
                }
                Role updatedRole = roleRepository.save(existingRole);
                return ResponseEntity.ok(updatedRole);
            } else {
                return ResponseEntity.notFound().build();
            }
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a role by ID")
    public ResponseEntity<Void> deleteRole(@PathVariable @Parameter(description = "Role ID") Long id) {
        try {
            if (roleRepository.existsById(id)) {
                roleRepository.deleteById(id);
                return ResponseEntity.noContent().build();
            } else {
                return ResponseEntity.notFound().build();
            }
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
}
