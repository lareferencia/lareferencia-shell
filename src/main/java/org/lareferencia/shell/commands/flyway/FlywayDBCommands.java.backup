
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

package org.lareferencia.shell.commands.flyway;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.flywaydb.core.Flyway;
import org.flywaydb.core.api.MigrationInfo;
import org.flywaydb.core.api.MigrationInfoService;
import org.flywaydb.core.api.output.MigrateOutput;
import org.flywaydb.core.api.output.MigrateResult;
import org.flywaydb.core.api.output.RepairOutput;
import org.flywaydb.core.api.output.RepairResult;
import org.flywaydb.core.api.output.ValidateResult;
import org.flywaydb.core.internal.info.MigrationInfoDumper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.shell.standard.ShellComponent;
import org.springframework.shell.standard.ShellMethod;
import org.springframework.shell.standard.ShellOption;

/**
 * Please check: https://flywaydb.org/documentation/usage/api/javadoc
 * 
 * @author pgraca
 *
 */
@ShellComponent
public class FlywayDBCommands {

    private static Logger logger = LogManager.getLogger(FlywayDBCommands.class);

    @Value("${spring.flyway.url}")
    private String dbURL;

    @Value("${spring.flyway.user}")
    private String dbUsername;

    @Value("${spring.flyway.password}")
    private String dbPassword;

    @Value("${spring.flyway.locations:db/migration}")
    private String[] dbLocations;

    private Flyway flyway;

    @ShellMethod("Database info: it will display current migration information")
    String database_info() {
        flyway = Flyway.configure().locations(dbLocations).dataSource(dbURL, dbUsername, dbPassword).load();

        MigrationInfoService info = flyway.info();
        logger.info("Database migration report");

        if (info.pending().length > 0) {
            for (MigrationInfo migrationPendingInfo : info.pending()) {
                logger.warn("Migration pending:" + " Version:" + migrationPendingInfo.getVersion() + "; Type:"
                        + migrationPendingInfo.getType() + "; State:" + migrationPendingInfo.getState()
                        + "; Description:" + migrationPendingInfo.getDescription());
            }
        }

        ValidateResult validate = flyway.validateWithResult();
        if (validate.warnings.isEmpty()) {
            for (String warning : validate.warnings) {
                logger.warn("Migration warning:" + warning);
            }
        }

        return MigrationInfoDumper.dumpToAsciiTable(info.all());
    }

    @ShellMethod("Database migration: it will migrate or upgrade your database using pre-existing scripts")
    void database_migrate(
            @ShellOption(help = "If you want to migrate considering out of order migrations", defaultValue = "false") boolean outOfOrder,
            @ShellOption(help = "If you want to migrate using already existing database", defaultValue = "true") boolean baselineOnMigrate) {
        // -ignoreIgnoredMigrations=true. To allow executing this migration, set
        // -outOfOrder=true
        // spring.flyway.baselineOnMigrate=true
        flyway = Flyway.configure().outOfOrder(outOfOrder).baselineOnMigrate(baselineOnMigrate).locations(dbLocations)
                .dataSource(dbURL, dbUsername, dbPassword).load();

        logger.info("Migrating database");
        MigrateResult migrateResult = flyway.migrate();

        if (migrateResult.migrationsExecuted > 0) {
            for (MigrateOutput output : migrateResult.migrations) {
                logger.info("Migration:" + " Version:" + output.version + "; Type:" + output.type + "; Category:"
                        + output.category + "; Description:" + output.description);
            }
        }

    }

    @ShellMethod("Database repairing: it will repair and migrate or upgrade your database using pre-existing scripts")
    void database_repair() {
        // If you already have versions 1.0 and 3.0 applied, and now a version 2.0 is
        // found, it will be applied too instead of being ignored.
        flyway = Flyway.configure().locations(dbLocations).dataSource(dbURL, dbUsername, dbPassword).load();

        logger.info("Repairing database");
        RepairResult repairResult = flyway.repair();

        for (RepairOutput output : repairResult.migrationsAligned) {
            logger.info("Aligned:" + " Version:" + output.version + "; Path:" + output.filepath + "; Description:"
                    + output.description);
        }

        for (RepairOutput output : repairResult.migrationsDeleted) {
            logger.info("Deleted:" + " Version:" + output.version + "; Path:" + output.filepath + "; Description:"
                    + output.description);
        }

        for (RepairOutput output : repairResult.migrationsRemoved) {
            logger.info("Removed:" + " Version:" + output.version + "; Path:" + output.filepath + "; Description:"
                    + output.description);
        }

    }

    @ShellMethod("Database clean: ATTENTION this command will delete all data")
    void database_clean(@ShellOption(defaultValue = "false") boolean confirm) {
        flyway = Flyway.configure().locations(dbLocations).dataSource(dbURL, dbUsername, dbPassword).load();

        if (confirm) {
            logger.info("Deleting database");
            flyway.clean();
        } else {
            logger.warn("ATTENTION This command will DELETE all data");
        }
    }

}