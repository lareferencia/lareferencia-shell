package org.lareferencia.shell.commands.harvester;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.lareferencia.core.export.XoaiExportMapping;
import static org.junit.jupiter.api.Assertions.assertEquals;

class LicenseExportProfileTest {
    @Test void removesVocabularyUrisAndKeepsOtherRightsInSourceOrder() throws Exception {
        var json = new ObjectMapper();
        var file = Path.of("config/exports/licenses-v1.json");
        var profile = new XoaiExportMapping(json.readTree(file.toFile()));
        var data = profile.project("""
            <metadata><element name="dc"><element name="rights"><element name="none">
              <field> INFO:eu-repo/semantics/openAccess </field>
              <field name="value">https://creativecommons.org/licenses/by/4.0/</field>
              <field>http://purl.org/coar/access_right/c_abf2</field>
              <field>HTTPS://WWW.VOCABULARIES.COAR-REPOSITORIES.ORG#term</field>
              <field>www.purl.org/coar?term</field><field>vocabularies.coar-repositories.org</field>
              <field>https://creativecommons.org/licenses/by/4.0/</field>
              <field> CC BY (ver info:eu-repo) </field>
              <field>https://purl.org/coauthor</field>
              <field>https://vocabularies.coar-repositories.org.example/license</field>
            </element></element></element></metadata>
            """);
        assertEquals(json.readTree("""
            {"licenses":["https://creativecommons.org/licenses/by/4.0/","CC BY (ver info:eu-repo)",
                         "https://purl.org/coauthor","https://vocabularies.coar-repositories.org.example/license"]}
            """), data);
    }
}
