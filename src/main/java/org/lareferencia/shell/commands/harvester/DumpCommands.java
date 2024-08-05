
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

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
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

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.xml.XmlMapper;


@ShellComponent
public class DumpCommands {

	@Autowired
	NetworkRepository networkRepository;

	@Autowired
	IMetadataRecordStoreService storeService;

	private static Logger logger = LogManager.getLogger(HarvesterCommands.class);

	@ShellMethod("Dump LGK Snaphot Metadata to disk")
	public String lgkRecordsDump(String fullPath) throws Exception {

		for (Network network : networkRepository.findAll()) {

			Long lgkSnaphotId = storeService.findLastGoodKnownSnapshot(network);

			if (lgkSnaphotId != null) {

				IPaginator<OAIRecord> paginator = storeService.getNotInvalidRecordsPaginator(lgkSnaphotId);
				paginator.setPageSize(1000);

				// for each page in the paginator
				
				Page<OAIRecord> page = paginator.nextPage();
				int pageIndex = 0;


				while (page != null) {

					// create a file for each page of records
					// and dump the metadata of each record in the page
					File file = new File(fullPath + "/page_" + pageIndex + ".txt");
					
					try (FileWriter writer = new FileWriter(file)) {

						// Escribir los metadatos de cada registro en el archivo
						for (OAIRecord oaiRecord : page.getContent()) {
							OAIRecordMetadata metadata = storeService.getPublishedMetadata(oaiRecord);

							XmlMapper xmlMapper = new XmlMapper();
							JsonNode node = xmlMapper.readTree(metadata.toString() + '\n');
							ObjectMapper jsonMapper = new ObjectMapper();
							writer.write(jsonMapper.writeValueAsString(node));
						}

					} catch (IOException e) {
						logger.error("Error writing to file: " + file.getAbsolutePath(), e);
					}

					// Obtener la siguiente página
					page = paginator.nextPage();
					pageIndex++;

					System.out.println("Page " + pageIndex + " dumped to: " + file.getAbsolutePath());
				}

			

				

				paginator.nextPage().forEach(oaiRecord -> {
					try {
						OAIRecordMetadata metadata = storeService.getPublishedMetadata(oaiRecord);

					} catch (Exception e) {
						logger.error("Error dumping record: " + oaiRecord.getId(), e);
					}
				});

				

				
			}
		}

		return "metadata dumped to: " + fullPath;
	}

	

}
