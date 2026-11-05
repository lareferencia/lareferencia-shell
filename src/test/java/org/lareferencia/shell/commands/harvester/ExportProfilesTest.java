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
    @Test void classificationProfileIncludesUnqualifiedDescriptionsButExcludesExplicitNotes() throws Exception {
        var file = java.nio.file.Path.of("config/exports/classification-embeddings-v1.json");
        var projection = new XoaiExportMapping(json.readTree(file.toFile()));
        var data = projection.project("""
            <metadata xmlns="http://www.lyncode.com/xoai"><element name="dc">
              <element name="title"><element name="none"><field name="value">Español</field>
                <field name="language">spa</field><field name="value">English</field><field name="language">eng</field>
              </element></element>
              <element name="description">
                <element name="none"><field name="value">Possible abstract</field><field name="value">Unqualified note</field></element>
                <element name="abstract"><field name="value">Abstract</field><field name="language">eng</field></element>
                <element name="abstractenglish"><field name="value">English abstract</field></element>
                <element name="resumen"><field name="value">Resumen</field></element>
                <element name="notes"><field name="value">Exclude notes</field></element>
                <element name="tableofcontents"><field name="value">Exclude contents</field></element>
                <element name="program"><field name="value">Exclude program</field></element>
              </element>
              <element name="subject"><element name="unesco"><field name="value">Education</field></element></element>
            </element><element name="dcterms">
              <element name="abstract"><element name="none"><field name="value">DCTERMS abstract</field></element></element>
              <element name="subject"><element name="none"><field name="value">Learning</field></element></element>
            </element></metadata>
            """);
        assertEquals(java.util.Set.of("titles", "abstracts", "keywords"), json.convertValue(data, java.util.Map.class).keySet());
        assertEquals(2, data.path("titles").size());
        assertEquals("eng", data.at("/titles/1/language").asText());
        assertEquals(6, data.path("abstracts").size());
        assertFalse(data.at("/abstracts/0").has("qualifier"));
        assertEquals("abstract", data.at("/abstracts/2/qualifier").asText());
        assertEquals(2, data.path("keywords").size());
        assertEquals("unesco", data.at("/keywords/0/qualifier").asText());
        assertFalse(data.toString().contains("Exclude"));
        assertFalse(data.toString().contains("schema"));
        var empty = projection.project("<metadata xmlns=\"http://www.lyncode.com/xoai\"/>");
        for (var name : java.util.List.of("titles", "abstracts", "keywords")) assertTrue(empty.path(name).isEmpty());
    }

}
