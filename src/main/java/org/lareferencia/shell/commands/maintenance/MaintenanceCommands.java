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
package org.lareferencia.shell.commands.maintenance;

import com.google.common.hash.BloomFilter;
import com.google.common.hash.Funnels;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.lareferencia.core.metadata.IMetadataStore;
import org.lareferencia.core.metadata.ISnapshotStore;
import org.lareferencia.core.metadata.MetadataRecordStoreException;
import org.lareferencia.core.metadata.RecordStatus;
import org.lareferencia.core.metadata.SnapshotMetadata;
import org.lareferencia.core.repository.parquet.OAIRecord;
import org.lareferencia.core.repository.parquet.OAIRecordParquetRepository;
import org.lareferencia.core.repository.parquet.RecordValidation;
import org.lareferencia.core.repository.parquet.ValidationStatParquetRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.shell.standard.ShellComponent;
import org.springframework.shell.standard.ShellMethod;
import org.springframework.shell.standard.ShellOption;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Iterator;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Maintenance commands for cleaning orphan metadata and other housekeeping tasks.
 * 
 * <p>These commands help maintain the health of the metadata store by identifying
 * and removing metadata entries that are no longer referenced by any snapshot.</p>
 * 
 * <h2>Memory Optimization with Bloom Filter</h2>
 * <p>Uses Guava's BloomFilter for memory-efficient hash lookup (~6 MB for 5M records
 * vs ~680 MB with HashSet). The 1% false positive rate means some orphans may be
 * kept, but no valid metadata will ever be deleted (safe operation).</p>
 */
@ShellComponent
@Configuration
@ComponentScan(basePackages = {"org.lareferencia.core.repository.parquet"})
public class MaintenanceCommands {

    private static final Logger logger = LogManager.getLogger(MaintenanceCommands.class);

    /** Capacity multiplier for Bloom Filter (1.2x to reduce false positives) */
    private static final double BLOOM_FILTER_CAPACITY_FACTOR = 1.2;

    /** False positive probability for Bloom Filter (1%) */
    private static final double BLOOM_FILTER_FPP = 0.01;

    @Autowired
    private ISnapshotStore snapshotStore;

    @Autowired
    private IMetadataStore metadataStore;

    @Autowired
    private OAIRecordParquetRepository oaiRecordRepository;

    @Autowired
    private ValidationStatParquetRepository validationRepository;

    /**
     * Cleans orphan metadata entries that are not referenced by any record in the snapshot.
     * 
     * <p>This command performs the following steps:</p>
     * <ol>
     *   <li>Retrieves SnapshotMetadata for the given snapshot ID</li>
     *   <li>Iterates OAI catalog records to collect originalMetadataHash values</li>
     *   <li>Iterates validation records to collect publishedMetadataHash values</li>
     *   <li>Stores all hashes in a memory-efficient Bloom Filter</li>
     *   <li>Iterates metadata store and deletes entries not in the Bloom Filter</li>
     * </ol>
     * 
     * <h3>Memory Usage</h3>
     * <p>Uses Bloom Filter with 1.2x capacity and 1% false positive rate.
     * For 5M records: ~6 MB vs ~680 MB with HashSet.</p>
     * 
     * <h3>Safety</h3>
     * <p>False positives only mean some orphans are kept (not deleted).
     * Valid metadata is NEVER deleted due to false positives.</p>
     * 
     * @param snapshotId the snapshot ID to clean orphan metadata for
     * @param dryRun if true, only reports what would be deleted without actually deleting
     * @return summary of the cleanup operation
     */
    @ShellMethod(value = "Clean orphan metadata entries not referenced by any record in the snapshot", 
                 key = "clean-orphan-metadata")
    public String cleanOrphanMetadata(
            @ShellOption(help = "Snapshot ID to clean orphan metadata for (optional if networkId is provided)", 
                        defaultValue = ShellOption.NULL) Long snapshotId,
            @ShellOption(help = "Network ID to get last good known snapshot (optional if snapshotId is provided)", 
                        defaultValue = ShellOption.NULL) Long networkId,
            @ShellOption(help = "If true, only report without deleting", defaultValue = "false") boolean dryRun) {

        // Validate that at least one ID is provided
        if (snapshotId == null && networkId == null) {
            return "ERROR: Either snapshotId or networkId must be provided";
        }

        // Resolve effective snapshot ID: snapshotId takes priority over networkId
        Long effectiveSnapshotId = snapshotId;
        if (effectiveSnapshotId == null && networkId != null) {
            effectiveSnapshotId = snapshotStore.findLastGoodKnownSnapshot(networkId);
            if (effectiveSnapshotId == null) {
                return String.format("ERROR: No valid snapshot found for network %d", networkId);
            }
            logger.info("CLEAN ORPHAN METADATA: Using last good known snapshot {} for network {}", 
                       effectiveSnapshotId, networkId);
        }

        logger.info("CLEAN ORPHAN METADATA: Starting for snapshot {} (dryRun={})", effectiveSnapshotId, dryRun);

        try {
            // Step 1: Get SnapshotMetadata
            SnapshotMetadata snapshotMetadata = snapshotStore.getSnapshotMetadata(effectiveSnapshotId);
            if (snapshotMetadata == null) {
                String error = String.format("Snapshot %d not found", effectiveSnapshotId);
                logger.error(error);
                return "ERROR: " + error;
            }
            logger.info("Retrieved SnapshotMetadata for network: {}", 
                       snapshotMetadata.getNetwork().getAcronym());

            // Step 2: Count total records to size the Bloom Filter
            long totalOaiRecords = countOaiRecords(snapshotMetadata);
            long totalValidationRecords = countValidationRecords(snapshotMetadata);
            long totalRecords = totalOaiRecords + totalValidationRecords;

            if (totalRecords == 0) {
                return "No records found in snapshot " + effectiveSnapshotId + ". Nothing to clean.";
            }

            logger.info("Total records to process: {} (OAI: {}, Validation: {})", 
                       totalRecords, totalOaiRecords, totalValidationRecords);

            // Step 3: Create Bloom Filter with 1.2x capacity and 1% FPP
            int bloomCapacity = (int) (totalRecords * BLOOM_FILTER_CAPACITY_FACTOR);
            BloomFilter<CharSequence> activeHashes = BloomFilter.create(
                Funnels.stringFunnel(StandardCharsets.UTF_8),
                bloomCapacity,
                BLOOM_FILTER_FPP
            );
            logger.info("Created Bloom Filter with capacity {} and {}% FPP (estimated size: {} bytes)",
                       bloomCapacity, BLOOM_FILTER_FPP * 100, 
                       estimateBloomFilterSize(bloomCapacity, BLOOM_FILTER_FPP));

            // Step 4: Collect originalMetadataHash from OAI catalog
            AtomicLong oaiHashCount = new AtomicLong(0);
            collectOaiHashes(snapshotMetadata, activeHashes, oaiHashCount);
            logger.info("Collected {} originalMetadataHash values from OAI catalog", oaiHashCount.get());

            // Step 5: Collect publishedMetadataHash from validation records
            AtomicLong validationHashCount = new AtomicLong(0);
            collectValidationHashes(snapshotMetadata, activeHashes, validationHashCount);
            logger.info("Collected {} publishedMetadataHash values from validation records", 
                       validationHashCount.get());

            // Step 6: Iterate metadata store and delete orphans
            AtomicLong totalMetadataCount = new AtomicLong(0);
            AtomicLong orphanCount = new AtomicLong(0);
            AtomicLong deletedCount = new AtomicLong(0);
            AtomicLong errorCount = new AtomicLong(0);

            deleteOrphanMetadata(snapshotMetadata, activeHashes, dryRun, 
                                totalMetadataCount, orphanCount, deletedCount, errorCount);

            // Build result summary
            String mode = dryRun ? "[DRY RUN] " : "";
            StringBuilder result = new StringBuilder();
            result.append(mode).append("Orphan metadata cleanup completed for snapshot ").append(effectiveSnapshotId).append("\n");
            result.append("Network: ").append(snapshotMetadata.getNetwork().getAcronym()).append("\n");
            result.append("----------------------------------------\n");
            result.append("OAI records processed: ").append(totalOaiRecords).append("\n");
            result.append("Validation records processed: ").append(totalValidationRecords).append("\n");
            result.append("Active hashes collected: ").append(oaiHashCount.get() + validationHashCount.get()).append("\n");
            result.append("Bloom Filter capacity: ").append(bloomCapacity).append("\n");
            result.append("----------------------------------------\n");
            result.append("Total metadata entries scanned: ").append(totalMetadataCount.get()).append("\n");
            result.append("Orphan entries found: ").append(orphanCount.get()).append("\n");
            result.append(mode).append("Entries deleted: ").append(deletedCount.get()).append("\n");
            if (errorCount.get() > 0) {
                result.append("Deletion errors: ").append(errorCount.get()).append("\n");
            }

            String summary = result.toString();
            logger.info("CLEAN ORPHAN METADATA: Completed for snapshot {}", effectiveSnapshotId);
            return summary;

        } catch (IOException e) {
            String error = String.format("IO error during cleanup: %s", e.getMessage());
            logger.error(error, e);
            return "ERROR: " + error;
        } catch (MetadataRecordStoreException e) {
            String error = String.format("Metadata store error during cleanup: %s", e.getMessage());
            logger.error(error, e);
            return "ERROR: " + error;
        }
    }

    /**
     * Counts OAI records in the snapshot.
     */
    private long countOaiRecords(SnapshotMetadata snapshotMetadata) throws IOException {
        long count = 0;
        Iterator<OAIRecord> iterator = oaiRecordRepository.getIterator(snapshotMetadata);
        while (iterator.hasNext()) {
            iterator.next();
            count++;
        }
        return count;
    }

    /**
     * Counts validation records in the snapshot.
     */
    private long countValidationRecords(SnapshotMetadata snapshotMetadata) throws IOException {
        long count = 0;
        Iterator<RecordValidation> iterator = validationRepository.getLightweightIterator(
            snapshotMetadata, RecordStatus.UNTESTED);
        while (iterator.hasNext()) {
            iterator.next();
            count++;
        }
        return count;
    }

    /**
     * Collects originalMetadataHash values from OAI catalog into the Bloom Filter.
     */
    private void collectOaiHashes(SnapshotMetadata snapshotMetadata, 
                                   BloomFilter<CharSequence> activeHashes,
                                   AtomicLong hashCount) throws IOException {
        Iterator<OAIRecord> iterator = oaiRecordRepository.getIterator(snapshotMetadata);
        while (iterator.hasNext()) {
            OAIRecord record = iterator.next();
            String hash = record.getOriginalMetadataHash();
            if (hash != null && !hash.isEmpty()) {
                activeHashes.put(hash);
                hashCount.incrementAndGet();
            }
        }
    }

    /**
     * Collects publishedMetadataHash values from validation records into the Bloom Filter.
     */
    private void collectValidationHashes(SnapshotMetadata snapshotMetadata,
                                          BloomFilter<CharSequence> activeHashes,
                                          AtomicLong hashCount) throws IOException {
        Iterator<RecordValidation> iterator = validationRepository.getLightweightIterator(
            snapshotMetadata, RecordStatus.UNTESTED);
        while (iterator.hasNext()) {
            RecordValidation record = iterator.next();
            String hash = record.getPublishedMetadataHash();
            if (hash != null && !hash.isEmpty()) {
                activeHashes.put(hash);
                hashCount.incrementAndGet();
            }
        }
    }

    /**
     * Iterates metadata store and deletes orphan entries not in the Bloom Filter.
     */
    private void deleteOrphanMetadata(SnapshotMetadata snapshotMetadata,
                                       BloomFilter<CharSequence> activeHashes,
                                       boolean dryRun,
                                       AtomicLong totalCount,
                                       AtomicLong orphanCount,
                                       AtomicLong deletedCount,
                                       AtomicLong errorCount) throws MetadataRecordStoreException {
        
        metadataStore.forEachHash(snapshotMetadata, hash -> {
            totalCount.incrementAndGet();
            
            // Check if hash is NOT in Bloom Filter (definitely orphan)
            // Note: mightContain() returns true if hash MIGHT be in the filter
            // If it returns false, the hash is DEFINITELY NOT in the filter
            if (!activeHashes.mightContain(hash)) {
                orphanCount.incrementAndGet();
                
                if (!dryRun) {
                    try {
                        boolean deleted = metadataStore.deleteMetadata(snapshotMetadata, hash);
                        if (deleted) {
                            deletedCount.incrementAndGet();
                            if (deletedCount.get() % 1000 == 0) {
                                logger.info("Deleted {} orphan metadata entries...", deletedCount.get());
                            }
                        }
                    } catch (MetadataRecordStoreException e) {
                        errorCount.incrementAndGet();
                        logger.error("Failed to delete metadata with hash {}: {}", hash, e.getMessage());
                    }
                }
            }
            
            // Log progress every 10000 entries
            if (totalCount.get() % 10000 == 0) {
                logger.info("Scanned {} metadata entries, found {} orphans...", 
                           totalCount.get(), orphanCount.get());
            }
        });
    }

    /**
     * Estimates Bloom Filter size in bytes.
     * Formula: -n * ln(p) / (ln(2)^2) bits, then /8 for bytes
     */
    private long estimateBloomFilterSize(int capacity, double fpp) {
        double bits = -capacity * Math.log(fpp) / (Math.log(2) * Math.log(2));
        return (long) Math.ceil(bits / 8);
    }
}
