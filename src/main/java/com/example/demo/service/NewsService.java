package com.example.demo.service;

import com.example.demo.model.News;
import java.util.List;
import java.util.Optional;

public interface NewsService {
    News create(News news);

    List<News> findAll();

    Optional<News> findById(Long id);

    List<News> findLatest(int limit);

    News update(Long id, News newsDetails);

    void delete(Long id);

    boolean existsById(Long id);

    long count();
}
