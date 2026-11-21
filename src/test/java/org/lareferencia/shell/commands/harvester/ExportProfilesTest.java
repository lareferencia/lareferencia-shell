package org.lareferencia.shell.commands.harvester;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.lareferencia.core.export.XoaiExportMapping;
import static org.junit.jupiter.api.Assertions.*;

/** Shell-owned example profiles are read directly from their installation directory. */
class ExportProfilesTest {
    private final ObjectMapper json = new ObjectMapper();
    @Test void commonProfileHasIdenticalFamiliesAndPreservesAuthorRoles() throws Exception {
        for (String name : java.util.List.of("publications-v1.json", "common-full-metadata-v1.json", "classification-embeddings-v1.json")) {
            var file = java.nio.file.Path.of("config/exports", name);
            new XoaiExportMapping(json.readTree(file.toFile()));
        }
        try (var input = java.nio.file.Files.newInputStream(java.nio.file.Path.of("config/exports/common-full-metadata-v1.json"))) {
            var projection = new XoaiExportMapping(json.readTree(input));
            var uy = projection.project("""
                <metadata><element name="dc"><element name="creator"><element name="none">
                <field name="value">Creator</field></element></element></element></metadata>
                """);
            var ar = projection.project("""
                <metadata><element name="dc"><element name="contributor"><element name="author">
                <field name="value">Author</field></element><element name="advisor"><field name="value">Advisor</field>
                </element></element></element><element name="lom"><element name="language"><element name="none">
                <field name="value">spa</field></element></element></element></metadata>
                """);
            assertEquals(json.convertValue(uy, java.util.Map.class).keySet(),
                         json.convertValue(ar, java.util.Map.class).keySet());
            assertEquals("Creator", uy.at("/creators/0/value").asText());
            assertFalse(uy.at("/creators/0").has("qualifier"));
            assertEquals("author", ar.at("/creators/0/qualifier").asText());
            assertEquals("advisor", ar.at("/contributors/0/qualifier").asText());
            assertEquals("lom.language.none", ar.at("/additionalMetadata/0/path").asText());
            for (var record : java.util.List.of(uy, ar)) {
                record.fields().forEachRemaining(family -> family.getValue().forEach(occurrence -> {
                    assertFalse(occurrence.has("schema"));
                    if (family.getKey().equals("additionalMetadata")) assertFalse(occurrence.has("qualifier"));
                }));
            }
        }
    }
}
