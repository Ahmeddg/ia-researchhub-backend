package com.example.demo.config;

import com.example.demo.security.CustomUserDetailsService;
import com.example.demo.security.JwtAuthenticationFilter;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.dao.DaoAuthenticationProvider;
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
        DaoAuthenticationProvider authProvider = new DaoAuthenticationProvider(customUserDetailsService);
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
                        .requestMatchers(HttpMethod.GET, "/api/publications/**").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/researchers/**").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/projects/**").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/domains/**").permitAll()

                        // User profile - any authenticated user
                        .requestMatchers("/api/users/me").authenticated()

                        // Content management - MODERATEUR, CHERCHEUR, ADMIN
                        .requestMatchers(HttpMethod.POST, "/api/news/**").hasAnyRole("MODERATEUR", "CHERCHEUR", "ADMIN")
                        .requestMatchers(HttpMethod.PUT, "/api/news/**").hasAnyRole("MODERATEUR", "CHERCHEUR", "ADMIN")
                        .requestMatchers(HttpMethod.DELETE, "/api/news/**")
                        .hasAnyRole("MODERATEUR", "CHERCHEUR", "ADMIN")

                        .requestMatchers(HttpMethod.POST, "/api/publications/**")
                        .hasAnyRole("MODERATEUR", "CHERCHEUR", "ADMIN")
                        .requestMatchers(HttpMethod.PUT, "/api/publications/**")
                        .hasAnyRole("MODERATEUR", "CHERCHEUR", "ADMIN")
                        .requestMatchers(HttpMethod.DELETE, "/api/publications/**")
                        .hasAnyRole("MODERATEUR", "CHERCHEUR", "ADMIN")

                        .requestMatchers(HttpMethod.POST, "/api/projects/**")
                        .hasAnyRole("MODERATEUR", "CHERCHEUR", "ADMIN")
                        .requestMatchers(HttpMethod.PUT, "/api/projects/**")
                        .hasAnyRole("MODERATEUR", "CHERCHEUR", "ADMIN")
                        .requestMatchers(HttpMethod.DELETE, "/api/projects/**")
                        .hasAnyRole("MODERATEUR", "CHERCHEUR", "ADMIN")

                        .requestMatchers(HttpMethod.POST, "/api/domains/**")
                        .hasAnyRole("MODERATEUR", "CHERCHEUR", "ADMIN")
                        .requestMatchers(HttpMethod.PUT, "/api/domains/**")
                        .hasAnyRole("MODERATEUR", "CHERCHEUR", "ADMIN")
                        .requestMatchers(HttpMethod.DELETE, "/api/domains/**")
                        .hasAnyRole("MODERATEUR", "CHERCHEUR", "ADMIN")

                        .requestMatchers(HttpMethod.POST, "/api/researchers/**")
                        .hasAnyRole("MODERATEUR", "CHERCHEUR", "ADMIN")
                        .requestMatchers(HttpMethod.PUT, "/api/researchers/**")
                        .hasAnyRole("MODERATEUR", "CHERCHEUR", "ADMIN")
                        .requestMatchers(HttpMethod.DELETE, "/api/researchers/**")
                        .hasAnyRole("MODERATEUR", "CHERCHEUR", "ADMIN")

                        // User management - CHERCHEUR, ADMIN only
                        .requestMatchers(HttpMethod.GET, "/api/users/**").hasAnyRole("CHERCHEUR", "ADMIN")
                        .requestMatchers(HttpMethod.POST, "/api/users/**").hasAnyRole("CHERCHEUR", "ADMIN")
                        .requestMatchers(HttpMethod.PUT, "/api/users/**").hasAnyRole("CHERCHEUR", "ADMIN")
                        .requestMatchers(HttpMethod.DELETE, "/api/users/**").hasAnyRole("CHERCHEUR", "ADMIN")

                        // Role assignment - CHERCHEUR, ADMIN only
                        .requestMatchers("/api/users/*/roles").hasAnyRole("CHERCHEUR", "ADMIN")

                        // Role management (create/delete roles) - ADMIN only
                        .requestMatchers(HttpMethod.POST, "/api/roles/**").hasRole("ADMIN")
                        .requestMatchers(HttpMethod.PUT, "/api/roles/**").hasRole("ADMIN")
                        .requestMatchers(HttpMethod.DELETE, "/api/roles/**").hasRole("ADMIN")
                        .requestMatchers(HttpMethod.GET, "/api/roles/**").hasAnyRole("CHERCHEUR", "ADMIN")

                        // All other requests need authentication
                        .anyRequest().authenticated())
                .authenticationProvider(authenticationProvider())
                .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }
}
