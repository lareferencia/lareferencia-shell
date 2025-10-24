
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
package org.lareferencia.shell.commands.harvester;


import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

import org.apache.jena.base.Sys;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.eclipse.jetty.util.MultiMap;
import org.lareferencia.backend.domain.Network;
import org.lareferencia.backend.domain.OAIRecord;
import org.lareferencia.backend.repositories.jpa.NetworkRepository;
import org.lareferencia.core.metadata.IMetadataRecordStoreService;
import org.lareferencia.core.metadata.OAIRecordMetadata;
import org.lareferencia.core.worker.IPaginator;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.shell.standard.ShellComponent;
import org.springframework.shell.standard.ShellMethod;
import org.springframework.shell.standard.ShellOption;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.xml.XmlMapper;
import com.fasterxml.jackson.datatype.guava.GuavaModule;
import com.google.common.collect.ArrayListMultimap;
import com.google.common.collect.Multimap;


@ShellComponent
public class DumpCommands {

	@Autowired
	NetworkRepository networkRepository;

	@Autowired
	IMetadataRecordStoreService storeService;

	private static Logger logger = LogManager.getLogger(HarvesterCommands.class);

	private static final String[] dcFields = { "dc.title", "dc.creator", "dc.subject", "dc.description", "dc.publisher",
			"dc.contributor", "dc.date", "dc.type", "dc.format", "dc.identifier", "dc.source", "dc.language",
			"dc.relation", "dc.coverage", "dc.rights" }; 

	private static final String DefaultNetworkAcronym = "00";

	@ShellMethod("Dump LGK Snaphot Metadata to disk")
	public String lgkRecordsDump(String fullPath, @ShellOption(defaultValue=DefaultNetworkAcronym)String networkAcronym) throws Exception {

		ObjectMapper jsonMapper = new ObjectMapper();
		jsonMapper.registerModule(new GuavaModule());

		Multimap<String, String> mdMap = null;

		// creata string with the present date for put in the file name
		// and increment the number of the file, avoid spaces in the name
		String date = java.time.LocalDate.now().toString();

		for (Network network : networkRepository.findAll()) {

			System.out.println("Dumping metadata for network: " + network.getName());
			String acronym = network.getAcronym();

			// if the networkAcronym is not the default and the network acronym is different
			if (networkAcronym != DefaultNetworkAcronym && !network.getAcronym().equals(networkAcronym)) {
				continue;
			}

			Long lgkSnaphotId = storeService.findLastGoodKnownSnapshot(network);

			if (lgkSnaphotId != null) {

				IPaginator<OAIRecord> paginator = storeService.getNotInvalidRecordsPaginator(lgkSnaphotId);
				paginator.setPageSize(10000);

				// for each page in the paginator
				
				Page<OAIRecord> page = paginator.nextPage();
				int pageIndex = 0;
				int totalPages = paginator.getTotalPages();	


				while (pageIndex < totalPages) {

					// create a file for each page of records
					// and dump the metadata of each record in the page
					
					File file = new File(fullPath + "/lr_" + acronym + "_" + date + String.format("-%04d", pageIndex) + ".json");
					
					try (FileWriter writer = new FileWriter(file)) {

						// Escribir los metadatos de cada registro en el archivo
						for (OAIRecord oaiRecord : page.getContent()) {
							OAIRecordMetadata metadata = storeService.getPublishedMetadata(oaiRecord);
							mdMap = ArrayListMultimap.create();

							// for each field in the metadata dcFields
							for (String field : dcFields) {
								// for each value in the field
								for (String value : metadata.getFieldOcurrences(field + ".*")) {
									// add the field and value to the map
									mdMap.put(field, value);
								}
							}

							writer.write( jsonMapper.writeValueAsString( mdMap ) + "\n" );
						}

					} catch (IOException e) {
						logger.error("Error writing to file: " + file.getAbsolutePath(), e);
					}

					System.out.println("Page " + pageIndex + " dumped to: " + file.getAbsolutePath());
					
					if (pageIndex == totalPages - 1) {
						break;
					}

					try {
						// Obtener la siguiente página
						page = paginator.nextPage();
					} catch (Exception e) {
						logger.error("Error getting next page", e);
					}
					
					pageIndex++;

				}		
			}
		}

		return "metadata dumped to: " + fullPath;
	}

	

}
