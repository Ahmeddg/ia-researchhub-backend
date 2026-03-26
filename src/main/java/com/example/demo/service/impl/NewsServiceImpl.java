package com.example.demo.service.impl;

import com.example.demo.exception.ResourceNotFoundException;
import com.example.demo.model.News;
import com.example.demo.repository.NewsRepository;
import com.example.demo.service.NewsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Service
@Transactional
public class NewsServiceImpl implements NewsService {

    private final NewsRepository newsRepository;

    @Autowired
    public NewsServiceImpl(NewsRepository newsRepository) {
        this.newsRepository = newsRepository;
    }

    @Override
    public News create(News news) {
        if (news.getCreatedAt() == null) {
            news.setCreatedAt(LocalDateTime.now());
        }
        return newsRepository.save(news);
    }

    @Override
    @Transactional(readOnly = true)
    public List<News> findAll() {
        return newsRepository.findAll();
    }

    @Override
    @Transactional(readOnly = true)
    public Optional<News> findById(Long id) {
        return newsRepository.findById(id);
    }

    @Override
    @Transactional(readOnly = true)
    public List<News> findLatest(int limit) {
        List<News> allNews = newsRepository.findAllByOrderByCreatedAtDesc();
        return allNews.stream().limit(limit).toList();
    }

    @Override
    public News update(Long id, News newsDetails) {
        News existingNews = newsRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("News", "id", id));

        if (newsDetails.getTitle() != null) {
            existingNews.setTitle(newsDetails.getTitle());
        }
        if (newsDetails.getContent() != null) {
            existingNews.setContent(newsDetails.getContent());
        }
        if (newsDetails.getUser() != null) {
            existingNews.setUser(newsDetails.getUser());
        }

        return newsRepository.save(existingNews);
    }

    @Override
    public void delete(Long id) {
        if (!newsRepository.existsById(id)) {
            throw new ResourceNotFoundException("News", "id", id);
        }
        newsRepository.deleteById(id);
    }

    @Override
    @Transactional(readOnly = true)
    public boolean existsById(Long id) {
        return newsRepository.existsById(id);
    }

    @Override
    @Transactional(readOnly = true)
    public long count() {
        return newsRepository.count();
    }
}
