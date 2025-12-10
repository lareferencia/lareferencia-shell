
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

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.WebApplicationType;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.data.elasticsearch.ElasticsearchDataAutoConfiguration;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.boot.context.event.ApplicationEnvironmentPreparedEvent;
import org.springframework.context.ApplicationListener;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.ImportResource;
import org.springframework.core.env.ConfigurableEnvironment;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.support.ResourcePropertySource;

@SpringBootApplication(exclude = { ElasticsearchDataAutoConfiguration.class })
@ImportResource({ "classpath*:application-context.xml" }) // please configure commands scanning in the context file
@Configuration
public class MainApp {

	private static final String PROPERTIES_DIR = "config/application.properties.d";

	public static void main(String[] args) {

		SpringApplication springApplication = new SpringApplicationBuilder()
				.sources(MainApp.class)
				.web(WebApplicationType.NONE)
				.listeners(new PropertiesDirectoryListener())
				.build();

		// If arguments are provided, run the command and close
		// Otherwise, keep the shell interactive
		if (args.length > 0) {
			springApplication.run(args).close();
		} else {
			springApplication.run(args);
		}
	}

	/**
	 * Listener that loads properties from
	 * config/application.properties.d/*.properties
	 */
	private static class PropertiesDirectoryListener
			implements ApplicationListener<ApplicationEnvironmentPreparedEvent> {

		@Override
		public void onApplicationEvent(ApplicationEnvironmentPreparedEvent event) {
			Path dir = Paths.get(PROPERTIES_DIR);

			if (!Files.exists(dir) || !Files.isDirectory(dir)) {
				System.out.println("[PropertiesLoader] Directory not found: " + PROPERTIES_DIR);
				return;
			}

			try (Stream<Path> stream = Files.list(dir)) {
				ConfigurableEnvironment env = event.getEnvironment();

				List<Path> propertyFiles = stream
						.filter(p -> p.toString().endsWith(".properties"))
						.sorted()
						.collect(Collectors.toList());

				for (Path file : propertyFiles) {
					try {
						ResourcePropertySource source = new ResourcePropertySource(
								"custom-" + file.getFileName().toString(),
								new FileSystemResource(file.toFile()));
						env.getPropertySources().addLast(source);
						System.out.println("[PropertiesLoader] Loaded: " + file.getFileName());
					} catch (IOException e) {
						System.err.println("[PropertiesLoader] Failed to load: " + file + " - " + e.getMessage());
					}
				}

			} catch (IOException e) {
				System.err.println("[PropertiesLoader] Error listing directory: " + e.getMessage());
			}
		}
	}

	// @Bean
	// public SolrClient solrClient(@Value("${solr.host}") String solrHost) {
	// return new HttpSolrClient.Builder(solrHost).build();
	// }
}
