
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

import org.apache.solr.client.solrj.SolrClient;
import org.apache.solr.client.solrj.impl.HttpSolrClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.WebApplicationType;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.data.elasticsearch.ElasticsearchDataAutoConfiguration;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.ImportResource;


@SpringBootApplication(exclude={ ElasticsearchDataAutoConfiguration.class})
@ImportResource({"classpath*:application-context.xml"}) // please configure commands scanning in the context file
@Configuration
public class MainApp {
	
	
	public static void main(String[] args) {
		
		 SpringApplication springApplication = 
	                new SpringApplicationBuilder()
	                .sources(MainApp.class)
	                .web(WebApplicationType.NONE)
	                .build();
		 

	     springApplication.run(args).close();	
	}

	@Bean
	public SolrClient solrClient(@Value("${solr.host}") String solrHost) {
		return new HttpSolrClient.Builder(solrHost).build();
	}
}
