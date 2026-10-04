package org.lareferencia.shell.commands.security;

import java.io.Console;
import java.util.Locale;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.shell.standard.ShellComponent;
import org.springframework.shell.standard.ShellMethod;
import org.springframework.shell.standard.ShellOption;
import org.springframework.transaction.annotation.Transactional;

@ShellComponent
public class LocalIdentityCommands {
    private final JdbcTemplate jdbc;
    private final BCryptPasswordEncoder passwords = new BCryptPasswordEncoder();

    public LocalIdentityCommands(JdbcTemplate jdbc) { this.jdbc = jdbc; }

    @ShellMethod(key = "security-create-admin", value = "Create the first local v5 administrator interactively")
    @Transactional
    public String createAdmin(@ShellOption(help = "Administrator username") String username) {
        Console console = System.console();
        if (console == null) throw new IllegalStateException("Run this command from an interactive terminal so the password is not echoed");
        String normalized = username == null ? "" : username.trim().toLowerCase(Locale.ROOT);
        if (!normalized.matches("[a-z0-9._@+-]{3,100}")) throw new IllegalArgumentException("Username must be 3-100 characters using letters, digits, . _ @ + or -");
        Integer admins = jdbc.queryForObject("SELECT COUNT(*) FROM local_user WHERE global_role='ADMIN' AND enabled=TRUE", Integer.class);
        if (admins != null && admins > 0) throw new IllegalStateException("An administrator already exists; refusing to create another bootstrap account");
        char[] first = console.readPassword("New administrator password: ");
        char[] second = console.readPassword("Confirm password: ");
        try {
            String password = new String(first);
            if (password.length() < 12 || password.length() > 200) throw new IllegalArgumentException("Password must contain between 12 and 200 characters");
            if (!password.equals(new String(second))) throw new IllegalArgumentException("Passwords do not match");
            jdbc.update("INSERT INTO local_user(username,password_hash,global_role,enabled) VALUES (?,?, 'ADMIN', TRUE)",
                    normalized, passwords.encode(password));
            return "Created local administrator '" + normalized + "'. Keep this terminal output private.";
        } finally {
            java.util.Arrays.fill(first, '\0');
            java.util.Arrays.fill(second, '\0');
        }
    }

    @ShellMethod(key = "security-reset-password", value = "Reset a local user's password interactively")
    @Transactional
    public String resetPassword(@ShellOption(help = "Existing local username") String username) {
        Console console = System.console();
        if (console == null) throw new IllegalStateException("Run this command from an interactive terminal so the password is not echoed");
        String normalized = username == null ? "" : username.trim().toLowerCase(Locale.ROOT);
        if (!normalized.matches("[a-z0-9._@+-]{3,100}")) throw new IllegalArgumentException("Username must be 3-100 characters using letters, digits, . _ @ + or -");
        Integer users = jdbc.queryForObject("SELECT COUNT(*) FROM local_user WHERE username=?", Integer.class, normalized);
        if (users == null || users == 0) throw new IllegalArgumentException("Local user '" + normalized + "' was not found");

        char[] first = console.readPassword("New password: ");
        char[] second = console.readPassword("Confirm password: ");
        try {
            String password = new String(first);
            if (password.length() < 12 || password.length() > 200) throw new IllegalArgumentException("Password must contain between 12 and 200 characters");
            if (!password.equals(new String(second))) throw new IllegalArgumentException("Passwords do not match");
            jdbc.update("UPDATE local_user SET password_hash=?, updated_at=CURRENT_TIMESTAMP WHERE username=?",
                    passwords.encode(password), normalized);
            jdbc.update("DELETE FROM spring_session WHERE principal_name=?", normalized);
            return "Password reset for local user '" + normalized + "'. Existing sessions have been revoked.";
        } finally {
            java.util.Arrays.fill(first, '\0');
            java.util.Arrays.fill(second, '\0');
        }
    }
}
