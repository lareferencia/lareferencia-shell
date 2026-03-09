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

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.lareferencia.core.domain.Network;
import org.lareferencia.core.metadata.IMetadataStore;
import org.lareferencia.core.metadata.ISnapshotStore;
import org.lareferencia.core.metadata.MetadataRecordStoreException;
import org.lareferencia.core.metadata.SnapshotMetadata;
import org.lareferencia.core.repository.catalog.OAIRecord;
import org.lareferencia.core.repository.catalog.OAIRecordCatalogRepository;
import org.lareferencia.core.repository.jpa.NetworkRepository;
import org.lareferencia.core.util.PathUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.shell.standard.ShellComponent;
import org.springframework.shell.standard.ShellMethod;
import org.springframework.shell.standard.ShellOption;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.sql.Statement;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.stream.Stream;
import java.util.zip.GZIPOutputStream;

@ShellComponent
public class DumpCommands {

    private static final Logger logger = LogManager.getLogger(DumpCommands.class);
    private static final DateTimeFormatter TIMESTAMP_FORMATTER = DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss");

    private static final String CREATE_MAPPING_TABLE_SQL = """
            CREATE TABLE IF NOT EXISTS record_mapping (
                export_key TEXT PRIMARY KEY,
                identifier TEXT NOT NULL
            )
            """;

    private static final String INSERT_MAPPING_SQL = """
            INSERT OR REPLACE INTO record_mapping (export_key, identifier)
            VALUES (?, ?)
            """;

    private static final int INSERT_BATCH_SIZE = 5000;

    @Autowired
    private NetworkRepository networkRepository;

    @Autowired
    private ISnapshotStore snapshotStore;

    @Autowired
    private OAIRecordCatalogRepository catalogRepository;

    @Autowired
    private IMetadataStore metadataStore;

    @ShellMethod(value = "Export LGK identifier mapping for all networks into a single SQLite file",
            key = "export-all-lgk-identifiers-mapping")
    public String exportLgkIdentifierMappingSqlite(
            @ShellOption(help = "Full path to the SQLite output file") String sqliteFilePath,
            @ShellOption(help = "Overwrite the output file if it already exists", defaultValue = "false") boolean overwrite)
            throws Exception {

        Path outputPath = Paths.get(sqliteFilePath).toAbsolutePath().normalize();
        prepareOutputPath(outputPath, overwrite);

        long processedNetworks = 0;
        long skippedNetworks = 0;
        long exportedRecords = 0;

        try (Connection exportConnection = openExportDatabase(outputPath)) {
            for (Network network : networkRepository.findAll()) {
                if (network == null || network.getId() == null) {
                    skippedNetworks++;
                    continue;
                }

                Long snapshotId = snapshotStore.findLastGoodKnownSnapshot(network.getId());
                if (snapshotId == null) {
                    skippedNetworks++;
                    logger.info("MAPPING EXPORT: Skipping network {} ({}) because it has no LGK snapshot",
                            network.getId(), network.getAcronym());
                    continue;
                }

                SnapshotMetadata snapshotMetadata = snapshotStore.getSnapshotMetadata(snapshotId);
                if (snapshotMetadata == null || snapshotMetadata.getNetwork() == null) {
                    skippedNetworks++;
                    logger.warn("MAPPING EXPORT: Skipping snapshot {} for network {} because metadata is unavailable",
                            snapshotId, network.getId());
                    continue;
                }

                String acronym = snapshotMetadata.getNetwork().getAcronym();
                if (acronym == null || acronym.isBlank()) {
                    skippedNetworks++;
                    logger.warn("MAPPING EXPORT: Skipping snapshot {} for network {} because acronym is blank",
                            snapshotId, network.getId());
                    continue;
                }

                logger.info("MAPPING EXPORT: Processing network {} ({}) with LGK snapshot {}",
                        network.getId(), acronym, snapshotId);

                try {
                    catalogRepository.openSnapshotForRead(snapshotMetadata);

                    long networkExportedRecords = exportSnapshotMappings(exportConnection, snapshotMetadata, acronym);
                    exportedRecords += networkExportedRecords;
                    processedNetworks++;

                    logger.info("MAPPING EXPORT: Exported {} records for network {} from snapshot {}",
                            networkExportedRecords, acronym, snapshotId);
                } catch (IOException e) {
                    skippedNetworks++;
                    logger.error("MAPPING EXPORT: Failed to open catalog for network {} snapshot {}: {}",
                            acronym, snapshotId, e.getMessage(), e);
                } finally {
                    catalogRepository.closeSnapshot(snapshotId);
                }
            }
        }

        return new StringBuilder()
                .append("LGK record mapping export completed").append("\n")
                .append("Output: ").append(outputPath).append("\n")
                .append("Networks processed: ").append(processedNetworks).append("\n")
                .append("Networks skipped: ").append(skippedNetworks).append("\n")
                .append("Records exported: ").append(exportedRecords)
                .toString();
    }

    private void prepareOutputPath(Path outputPath, boolean overwrite) throws IOException {
        Path parent = outputPath.getParent();
        if (parent != null) {
            Files.createDirectories(parent);
        }

        if (Files.exists(outputPath)) {
            if (!overwrite) {
                throw new IOException("Output file already exists: " + outputPath
                        + " (use --overwrite true to replace it)");
            }
            Files.delete(outputPath);
        }
    }

    private Connection openExportDatabase(Path outputPath) throws SQLException {
        Connection connection = DriverManager.getConnection("jdbc:sqlite:" + outputPath);

        try (Statement stmt = connection.createStatement()) {
            stmt.execute("PRAGMA journal_mode=WAL");
            stmt.execute("PRAGMA synchronous=NORMAL");
            stmt.execute(CREATE_MAPPING_TABLE_SQL);
        }

        connection.setAutoCommit(false);
        return connection;
    }

    private long exportSnapshotMappings(Connection exportConnection, SnapshotMetadata snapshotMetadata, String acronym)
            throws SQLException {

        long exported = 0;

        try (PreparedStatement insertStatement = exportConnection.prepareStatement(INSERT_MAPPING_SQL);
                Stream<OAIRecord> recordStream = catalogRepository.streamNotDeleted(snapshotMetadata)) {

            long batched = 0;

            for (OAIRecord record : (Iterable<OAIRecord>) recordStream::iterator) {
                insertStatement.setString(1, acronym + "_" + record.getId());
                insertStatement.setString(2, record.getIdentifier());
                insertStatement.addBatch();

                exported++;
                batched++;

                if (batched == INSERT_BATCH_SIZE) {
                    insertStatement.executeBatch();
                    exportConnection.commit();
                    batched = 0;
                }
            }

            if (batched > 0) {
                insertStatement.executeBatch();
                exportConnection.commit();
            }

            return exported;

        } catch (RuntimeException e) {
            exportConnection.rollback();
            throw new SQLException("Failed to export snapshot mappings for snapshot "
                    + snapshotMetadata.getSnapshotId(), e);
        }
    }

    @ShellMethod(value = "Export LGK metadata to gzipped XML files (one per network)",
            key = "export-all-lgk-metadata")
    public String exportLgkMetadataXml(
            @ShellOption(help = "Directory where output .xml.gz files will be written") String outputDirectory,
            @ShellOption(help = "Optional network ID. If omitted, exports all networks",
                    defaultValue = ShellOption.NULL) Long networkId,
            @ShellOption(help = "Overwrite output files if they already exist", defaultValue = "false") boolean overwrite)
            throws Exception {

        Path outputDir = Paths.get(outputDirectory).toAbsolutePath().normalize();
        Files.createDirectories(outputDir);

        long processedNetworks = 0;
        long skippedNetworks = 0;
        long exportedRecords = 0;
        long metadataErrors = 0;

        Iterable<Network> networks = networkId != null
                ? resolveSingleNetwork(networkId)
                : networkRepository.findAll();

        for (Network network : networks) {
            if (network == null || network.getId() == null) {
                skippedNetworks++;
                continue;
            }

            Long snapshotId = snapshotStore.findLastGoodKnownSnapshot(network.getId());
            if (snapshotId == null) {
                skippedNetworks++;
                logger.info("METADATA EXPORT: Skipping network {} ({}) because it has no LGK snapshot",
                        network.getId(), network.getAcronym());
                continue;
            }

            SnapshotMetadata snapshotMetadata = snapshotStore.getSnapshotMetadata(snapshotId);
            if (snapshotMetadata == null || snapshotMetadata.getNetwork() == null) {
                skippedNetworks++;
                logger.warn("METADATA EXPORT: Skipping snapshot {} for network {} because metadata is unavailable",
                        snapshotId, network.getId());
                continue;
            }

            String acronym = snapshotMetadata.getNetwork().getAcronym();
            if (acronym == null || acronym.isBlank()) {
                skippedNetworks++;
                logger.warn("METADATA EXPORT: Skipping snapshot {} for network {} because acronym is blank",
                        snapshotId, network.getId());
                continue;
            }

            Path outputFile = buildMetadataOutputPath(outputDir, acronym, snapshotId);
            ensureWritableOutputFile(outputFile, overwrite);

            logger.info("METADATA EXPORT: Processing network {} ({}) with LGK snapshot {} into {}",
                    network.getId(), acronym, snapshotId, outputFile);

            try {
                catalogRepository.openSnapshotForRead(snapshotMetadata);

                MetadataExportResult result = exportSnapshotOriginalMetadata(snapshotMetadata, outputFile);
                exportedRecords += result.exportedRecords();
                metadataErrors += result.metadataErrors();
                processedNetworks++;

                logger.info("METADATA EXPORT: Exported {} records for network {} from snapshot {} (errors: {})",
                        result.exportedRecords(), acronym, snapshotId, result.metadataErrors());
            } catch (IOException e) {
                skippedNetworks++;
                logger.error("METADATA EXPORT: Failed to export snapshot {} for network {}: {}",
                        snapshotId, acronym, e.getMessage(), e);
            } finally {
                catalogRepository.closeSnapshot(snapshotId);
            }
        }

        return new StringBuilder()
                .append("LGK original metadata export completed").append("\n")
                .append("Output directory: ").append(outputDir).append("\n")
                .append("Networks processed: ").append(processedNetworks).append("\n")
                .append("Networks skipped: ").append(skippedNetworks).append("\n")
                .append("Records exported: ").append(exportedRecords).append("\n")
                .append("Metadata retrieval errors: ").append(metadataErrors)
                .toString();
    }

    private Iterable<Network> resolveSingleNetwork(Long networkId) throws IOException {
        return networkRepository.findById(networkId)
                .<Iterable<Network>>map(java.util.List::of)
                .orElseThrow(() -> new IOException("Network not found: " + networkId));
    }

    private Path buildMetadataOutputPath(Path outputDir, String acronym, Long snapshotId) {
        String sanitizedAcronym = PathUtils.sanitizeNetworkAcronym(acronym);
        String timestamp = LocalDateTime.now().format(TIMESTAMP_FORMATTER);
        String fileName = String.format("lgk_%s_snapshot_%d_metadata_%s.xml.gz",
                sanitizedAcronym, snapshotId, timestamp);
        return outputDir.resolve(fileName);
    }

    private void ensureWritableOutputFile(Path outputFile, boolean overwrite) throws IOException {
        if (Files.exists(outputFile)) {
            if (!overwrite) {
                throw new IOException("Output file already exists: " + outputFile
                        + " (use --overwrite true to replace it)");
            }
            Files.delete(outputFile);
        }
    }

    private MetadataExportResult exportSnapshotOriginalMetadata(SnapshotMetadata snapshotMetadata, Path outputFile)
            throws IOException {

        long exported = 0;
        long errors = 0;

        try (BufferedWriter writer = new BufferedWriter(new java.io.OutputStreamWriter(
                new GZIPOutputStream(Files.newOutputStream(outputFile)),
                java.nio.charset.StandardCharsets.UTF_8));
                Stream<OAIRecord> recordStream = catalogRepository.streamNotDeleted(snapshotMetadata)) {

            writer.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
            writer.write("<records network=\"");
            writer.write(escapeXmlAttribute(snapshotMetadata.getNetwork().getAcronym()));
            writer.write("\" snapshotId=\"");
            writer.write(String.valueOf(snapshotMetadata.getSnapshotId()));
            writer.write("\">\n");

            for (OAIRecord record : (Iterable<OAIRecord>) recordStream::iterator) {
                String hash = record.getOriginalMetadataHash();
                if (hash == null || hash.isBlank()) {
                    errors++;
                    logger.warn("METADATA EXPORT: Record {} in snapshot {} has no original metadata hash",
                            record.getIdentifier(), snapshotMetadata.getSnapshotId());
                    continue;
                }

                try {
                    String metadata = metadataStore.getMetadata(snapshotMetadata, hash);
                    writer.write(metadata);
                    writer.write('\n');
                    exported++;
                } catch (MetadataRecordStoreException e) {
                    errors++;
                    logger.warn("METADATA EXPORT: Failed to load metadata for record {} (hash {}) in snapshot {}: {}",
                            record.getIdentifier(), hash, snapshotMetadata.getSnapshotId(), e.getMessage());
                }
            }

            writer.write("</records>\n");
        }

        return new MetadataExportResult(exported, errors);
    }

    private String escapeXmlAttribute(String value) {
        return value
                .replace("&", "&amp;")
                .replace("\"", "&quot;")
                .replace("<", "&lt;")
                .replace(">", "&gt;");
    }

    private record MetadataExportResult(long exportedRecords, long metadataErrors) {
    }
}
