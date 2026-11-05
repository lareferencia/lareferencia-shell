package org.lareferencia.shell.commands.harvester;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.file.Path;
import java.util.*;
import org.lareferencia.core.export.*;
import org.springframework.shell.context.*;
import org.springframework.shell.standard.*;

/** Command adapters for provenance-preserving metadata packages. */
@ShellComponent
public class MetadataExportCommands {
    private final MetadataExportService service;
    private final ShellContext context;
    private final ObjectMapper json = new ObjectMapper();
    public MetadataExportCommands(MetadataExportService service, ShellContext context) { this.service = service; this.context = context; }

    @ShellMethod(key = "export-metadata", value = "Export LGK original or processed metadata with provenance and record mapping")
    public String exportMetadata(
            @ShellOption(value = "--network", defaultValue = ShellOption.NULL, help = "Exact source acronym") String network,
            @ShellOption(value = "--networks", defaultValue = ShellOption.NULL, help = "Comma-separated exact source acronyms") String networks,
            @ShellOption(value = "--all-networks", defaultValue = "false", help = "Select every source") boolean allNetworks,
            @ShellOption(value = "--variant", defaultValue = "processed", help = "original or processed") String variant,
            @ShellOption(value = "--format", defaultValue = "jsonl", help = "xml, json or jsonl") String format,
            @ShellOption(value = "--mapping", defaultValue = ShellOption.NULL, help = "JSON mapping path; required for JSON formats") String mapping,
            @ShellOption(value = "--layout", defaultValue = "collection", help = "XML collection or per-record") String layout,
            @ShellOption(value = "--partition-by", defaultValue = "network", help = "network or none") String partitionBy,
            @ShellOption(value = "--max-records", defaultValue = ShellOption.NULL, help = "Records per batch; default 10000") Long maxRecords,
            @ShellOption(value = "--max-bytes", defaultValue = ShellOption.NULL, help = "Uncompressed bytes, KiB, MiB or GiB; default 128MiB") String maxBytes,
            @ShellOption(value = "--compression", defaultValue = "gzip", help = "none or gzip") String compression,
            @ShellOption(value = "--valid-only", defaultValue = "false", help = "Exclude active invalid records") boolean validOnly,
            @ShellOption(value = "--output", help = "Parent directory for new export package") String output) throws Exception {
        var request = request(network, networks, allNetworks, variant, format, mapping, layout, partitionBy,
                maxRecords, maxBytes, compression, validOnly, output);
        var result = service.export(request);
        String summary = result.status() + ": " + result.directory() + "\nAttempted: " + result.attempted()
                + "; exported: " + result.exported() + "; filtered: " + result.filtered() + "; errors: " + result.errors();
        if (!result.successful() && context.getInteractionMode() != InteractionMode.INTERACTIVE)
            throw new IllegalStateException(summary);
        return summary;
    }
    @ShellMethod(key = "export-mapping-validate", value = "Validate a versioned XOAI to JSON mapping")
    public String validate(@ShellOption(value = "--mapping", help = "Mapping JSON path") String mapping) throws Exception {
        var profile = service.validateMapping(Path.of(mapping)).specification();
        return "Valid mapping: " + profile.path("name").asText() + " " + profile.path("version").asText();
    }
    @ShellMethod(key = "export-metadata-preview", value = "Preview XOAI mapping and provenance without writing an export package")
    public String preview(
            @ShellOption(value = "--network", help = "Exact source acronym") String network,
            @ShellOption(value = "--variant", defaultValue = "processed", help = "original or processed") String variant,
            @ShellOption(value = "--mapping", help = "Mapping JSON path") String mapping,
            @ShellOption(value = "--limit", defaultValue = "5", help = "Maximum attempted records") int limit,
            @ShellOption(value = "--valid-only", defaultValue = "false", help = "Exclude invalid records") boolean validOnly) throws Exception {
        var request = request(network, null, false, variant, "jsonl", mapping, "collection", "network", null, null, "none", validOnly, null);
        return json.writerWithDefaultPrettyPrinter().writeValueAsString(service.preview(request, limit));
    }
    static ExportRequest request(String network, String networks, boolean allNetworks, String variant, String format,
            String mapping, String layout, String partitionBy, Long maxRecords, String maxBytes,
            String compression, boolean validOnly, String output) {
        if (network != null && networks != null) throw new IllegalArgumentException("Use exactly one network selection");
        List<String> selected = network != null ? List.of(network) : networks != null ? Arrays.asList(networks.split(",", -1)) : List.of();
        return new ExportRequest(selected, allNetworks, variant, format, mapping == null ? null : Path.of(mapping), layout,
                partitionBy, maxRecords, maxBytes == null ? null : ExportRequest.parseBytes(maxBytes), compression, validOnly,
                output == null ? null : Path.of(output));
    }
}
