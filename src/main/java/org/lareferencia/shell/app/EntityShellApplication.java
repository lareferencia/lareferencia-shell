
/*
 *   Copyright (c) 2013-2022. LA Referencia / Red CLARA and others
 *
 *   This program is free software: you can redistribute it and/or modify
 *   it under the terms of the GNU Affero General Public License as published by
 *   the Free Software Foundation, either version 3 of the License, or
 *   (at your option) any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU Affero General Public License for more details.
 *
 *   You should have received a copy of the GNU Affero General Public License
 *   along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 *   This file is part of LA Referencia software platform LRHarvester v4.x
 *   For any further information please contact Lautaro Matas <lmatas@gmail.com>
 */

package org.lareferencia.shell.app;

import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.WebApplicationType;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.core.annotation.Order;
import org.springframework.shell.Shell;
import org.springframework.shell.Input;
import org.springframework.shell.InputProvider;
import org.springframework.stereotype.Component;

/**
 * UPGRADED for Spring Boot 3.x / Spring Shell 3.x
 * Changes:
 * - Removed InteractiveShellApplicationRunner (no longer exists in Spring Shell
 * 3.x)
 * - Using InputProvider to execute commands programmatically
 * - Direct precedence value instead of PRECEDENCE constant
 */
@Component
@Order(-1000)
public class EntityShellApplication implements ApplicationRunner {

	private final Shell shell;

	public static void main(String[] args) {

		SpringApplication springApplication = new SpringApplicationBuilder()
				.sources(EntityShellApplication.class)
				.web(WebApplicationType.NONE)
				.build();

		springApplication.run(args).close();
	}

	public EntityShellApplication(Shell shell) {
		this.shell = shell;
	}

	@Override
	public void run(ApplicationArguments args) throws Exception {

		// Skip if running via MainApp - Spring Shell will handle command execution
		// automatically
		// This prevents double execution when running commands via command line
		// arguments
		StackTraceElement[] stackTrace = Thread.currentThread().getStackTrace();
		for (StackTraceElement element : stackTrace) {
			if (element.getClassName().contains("MainApp")) {
				return; // MainApp handles command execution, skip EntityShellApplication
			}
		}

		if (args.getNonOptionArgs().isEmpty() || args.getNonOptionArgs().stream().allMatch(s -> s.startsWith("@"))) {
			// No command provided, allow interactive mode
			return;
		} else {
			/*
			 * Execute the command and exit (non-interactive mode)
			 * In Spring Shell 3.x, we use shell.run() with InputProvider
			 */

			// Disable interactive mode by setting property
			System.setProperty("spring.shell.interactive.enabled", "false");

			// Execute the command
			String command = String.join(" ", args.getSourceArgs());

			// Create an InputProvider that returns the command
			InputProvider inputProvider = new InputProvider() {
				private boolean provided = false;

				@Override
				public Input readInput() {
					if (!provided) {
						provided = true;
						return () -> command;
					}
					return null; // Signal end of input
				}
			};

			try {
				// In Spring Shell 3.x, run() executes commands but doesn't return result
				// Output is handled by the shell itself
				shell.run(inputProvider);
			} catch (Exception e) {
				System.err.println("Error executing command: " + e.getMessage());
				e.printStackTrace();
			}
		}

	}

}