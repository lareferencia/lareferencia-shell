/*
 *   Copyright (c) 2013-2025. LA Referencia / Red CLARA and others
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

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.ImportResource;

/**
 * Configuration class that conditionally loads flowable-specific bean
 * definitions.
 * 
 * These beans (mdformats.xml, fingerprint.xml) are only required when running
 * in flowable mode (workflow.engine=flowable). When running in legacy mode,
 * these beans are not needed and this configuration is skipped.
 * 
 * @author LA Referencia Team
 */
@Configuration
@ConditionalOnProperty(name = "workflow.engine", havingValue = "flowable")
@ImportResource({
        "file:${app.config.dir}/beans/mdformats.xml",
        "file:${app.config.dir}/beans/fingerprint.xml"
})
public class WorkflowConfiguration {
    // Configuration is done via @ImportResource annotation
    // No additional bean definitions needed
}
