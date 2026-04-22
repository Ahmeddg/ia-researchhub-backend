package com.example.demo.service;

import com.example.demo.model.Role;
import java.util.List;
import java.util.Optional;

public interface RoleService {
    Role create(Role role);

    List<Role> findAll();

    Optional<Role> findById(Long id);

    Optional<Role> findByName(String name);

    Role update(Long id, Role roleDetails);

    void delete(Long id);

    boolean existsById(Long id);
}
