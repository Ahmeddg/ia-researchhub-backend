package com.example.demo.config;

import com.example.demo.security.CustomUserDetailsService;
import com.example.demo.security.JwtAuthenticationFilter;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.dao.DaoAuthenticationProvider;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

@Configuration
@EnableWebSecurity
@EnableMethodSecurity(prePostEnabled = true)
public class SecurityConfig {

    private final CustomUserDetailsService customUserDetailsService;
    private final JwtAuthenticationFilter jwtAuthenticationFilter;

    @Autowired
    public SecurityConfig(CustomUserDetailsService customUserDetailsService,
            JwtAuthenticationFilter jwtAuthenticationFilter) {
        this.customUserDetailsService = customUserDetailsService;
        this.jwtAuthenticationFilter = jwtAuthenticationFilter;
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public DaoAuthenticationProvider authenticationProvider() {
        DaoAuthenticationProvider authProvider = new DaoAuthenticationProvider();
        authProvider.setUserDetailsService(customUserDetailsService);
        authProvider.setPasswordEncoder(passwordEncoder());
        return authProvider;
    }

    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration authConfig) throws Exception {
        return authConfig.getAuthenticationManager();
    }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
                .cors(Customizer.withDefaults())
                .csrf(csrf -> csrf.disable())
                .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(auth -> auth
                        // Public endpoints - anyone can access
                        .requestMatchers("/api/auth/**").permitAll()
                        .requestMatchers("/swagger-ui/**", "/swagger-ui.html", "/swagger-resources/**").permitAll()
                        .requestMatchers("/v3/api-docs/**", "/api-docs/**", "/api-docs").permitAll()
                        .requestMatchers("/webjars/**").permitAll()

                        // Public GET endpoints - anonymous can view
                        .requestMatchers(HttpMethod.GET, "/api/statistics/**").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/news/**").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/publications/me").authenticated()
                        .requestMatchers(HttpMethod.GET, "/api/publications/**").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/researchers/**").authenticated()
                        .requestMatchers(HttpMethod.GET, "/api/projects/me").authenticated()
                        .requestMatchers(HttpMethod.GET, "/api/projects/**").authenticated()
                        .requestMatchers(HttpMethod.GET, "/api/domains/**").permitAll()

                        // User profile - any authenticated user (must come before general /api/users rules)
                        .requestMatchers("/api/users/me").authenticated()

                        // Content management - MODERATOR, ADMIN
                        .requestMatchers(HttpMethod.POST, "/api/news/**").hasAnyRole("MODERATOR", "ADMIN")
                        .requestMatchers(HttpMethod.PUT, "/api/news/**").hasAnyRole("MODERATOR", "ADMIN")
                        .requestMatchers(HttpMethod.DELETE, "/api/news/**")
                        .hasAnyRole("MODERATOR", "ADMIN")

                        // Voting - Any authenticated user
                        .requestMatchers(HttpMethod.POST, "/api/publications/*/upvote").authenticated()
                        .requestMatchers(HttpMethod.POST, "/api/publications/*/downvote").authenticated()

                        // Publications - MODERATOR, RESEARCHER, ADMIN
                        .requestMatchers(HttpMethod.POST, "/api/publications/**")
                        .hasAnyRole("MODERATOR", "RESEARCHER", "ADMIN")
                        .requestMatchers(HttpMethod.PUT, "/api/publications/**")
                        .hasAnyRole("MODERATOR", "RESEARCHER", "ADMIN")
                        .requestMatchers(HttpMethod.DELETE, "/api/publications/**")
                        .hasAnyRole("MODERATOR", "RESEARCHER", "ADMIN")

                        .requestMatchers(HttpMethod.POST, "/api/projects/**")
                        .hasAnyRole("MODERATOR", "RESEARCHER", "ADMIN")
                        .requestMatchers(HttpMethod.PUT, "/api/projects/**")
                        .hasAnyRole("MODERATOR", "RESEARCHER", "ADMIN")
                        .requestMatchers(HttpMethod.DELETE, "/api/projects/**")
                        .hasAnyRole("MODERATOR", "RESEARCHER", "ADMIN")

                        .requestMatchers(HttpMethod.POST, "/api/domains/**")
                        .hasAnyRole("MODERATOR", "ADMIN")
                        .requestMatchers(HttpMethod.PUT, "/api/domains/**")
                        .hasAnyRole("MODERATOR", "ADMIN")
                        .requestMatchers(HttpMethod.DELETE, "/api/domains/**")
                        .hasAnyRole("MODERATOR", "ADMIN")

                        .requestMatchers(HttpMethod.POST, "/api/researchers/**")
                        .hasAnyRole("MODERATOR", "ADMIN")
                        .requestMatchers(HttpMethod.PUT, "/api/researchers/**")
                        .hasAnyRole("MODERATOR", "ADMIN")
                        .requestMatchers(HttpMethod.DELETE, "/api/researchers/**")
                        .hasAnyRole("MODERATOR", "ADMIN")

                        // Role assignment - ADMIN only
                        .requestMatchers("/api/users/*/roles").hasRole("ADMIN")

                        // User management - ADMIN only (General pattern last)
                        .requestMatchers(HttpMethod.GET, "/api/users/**").hasRole("ADMIN")
                        .requestMatchers(HttpMethod.POST, "/api/users/**").hasRole("ADMIN")
                        .requestMatchers(HttpMethod.PUT, "/api/users/**").hasRole("ADMIN")
                        .requestMatchers(HttpMethod.DELETE, "/api/users/**").hasRole("ADMIN")

                        // Role management - ADMIN only
                        .requestMatchers(HttpMethod.POST, "/api/roles/**").hasRole("ADMIN")
                        .requestMatchers(HttpMethod.PUT, "/api/roles/**").hasRole("ADMIN")
                        .requestMatchers(HttpMethod.DELETE, "/api/roles/**").hasRole("ADMIN")
                        .requestMatchers(HttpMethod.GET, "/api/roles/**").hasRole("ADMIN")

                        // Researcher role request workflow
                        .requestMatchers(HttpMethod.POST, "/api/researcher-requests").hasRole("USER")
                        .requestMatchers(HttpMethod.GET, "/api/researcher-requests/me").authenticated()
                        .requestMatchers(HttpMethod.GET, "/api/researcher-requests/pending").hasRole("ADMIN")
                        .requestMatchers(HttpMethod.POST, "/api/researcher-requests/*/approve").hasRole("ADMIN")
                        .requestMatchers(HttpMethod.POST, "/api/researcher-requests/*/reject").hasRole("ADMIN")

                        // All other requests need authentication
                        .anyRequest().authenticated())
                .authenticationProvider(authenticationProvider())
                .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }
}
