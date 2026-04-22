package com.example.demo.service;

import com.example.demo.model.User;
import java.util.List;
import java.util.Optional;
import java.util.Set;

public interface UserService {
    User create(User user);

    List<User> findAll();

    Optional<User> findById(Long id);

    Optional<User> findByUsername(String username);

    Optional<User> findByEmail(String email);

    User update(Long id, User userDetails);

    User updateRoles(Long id, Set<String> roleNames);

    void delete(Long id);

    boolean existsById(Long id);
}
