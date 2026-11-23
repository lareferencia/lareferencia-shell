package org.lareferencia.shell.commands.harvester;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.lareferencia.core.domain.*;
import org.lareferencia.core.metadata.OAIRecordMetadata;
import org.lareferencia.core.repository.jpa.*;
import org.lareferencia.core.service.validation.ValidationService;
import org.lareferencia.core.worker.validation.*;
import org.springframework.test.util.ReflectionTestUtils;

class HarvesterProfileImportTest {
    @Test void importsStandardLegacyFilesWithoutChangingNamesOrLiteralText(@TempDir Path dir) throws Exception {
        var cmd = new HarvesterCommands();
        cmd.validatorRepository = mock(ValidatorRepository.class);
        cmd.transformerRepository = mock(TransformerRepository.class);
        var service = new ValidationService();
        ReflectionTestUtils.setField(service, "serializer", new RuleSerializer());
        var folder = Path.of("../Docker/config-overrides/lareferencia-shell");
        var json = new ObjectMapper();
        for (boolean migrate : new boolean[]{false, true}) {
            var export = json.readTree(folder.resolve("validator.json").toFile());
            String legacy = "org.lareferencia.backend.validation.validator.";
            var first = (com.fasterxml.jackson.databind.node.ObjectNode) export.get("rules").get(0);
            first.put("description", legacy);
            first.put("jsonserialization", first.path("jsonserialization").asText()
                    .replace("org.lareferencia.core.worker.validation.validator.", legacy));
            var file = dir.resolve("standard.json");
            json.writeValue(file.toFile(), export);
            cmd.importValidator(file.toString(), migrate);
            var validators = org.mockito.ArgumentCaptor.forClass(Validator.class);
            verify(cmd.validatorRepository).saveAndFlush(validators.capture());
            var model = validators.getValue();
            assertEquals(legacy, model.getRules().get(0).getDescription());
            assertEquals(!migrate, model.getRules().get(0).getJsonserialization().contains(legacy));
            var xml = new OAIRecordMetadata("fixture");
            xml.addFieldOcurrence("dc:title", "Title");
            xml.addFieldOcurrence("dc:creator", "Author");
            xml.addFieldOcurrence("dc:identifier", "ID");
            assertTrue(service.createValidatorFromModel(model).validate(xml, new ValidatorResult()).isValid());
            cmd.importTransformer(folder.resolve("transformer.json").toString(), migrate);
            var transformers = org.mockito.ArgumentCaptor.forClass(Transformer.class);
            verify(cmd.transformerRepository).saveAndFlush(transformers.capture());
            var chain = service.createTransformerFromModel(transformers.getValue());
            assertEquals(3, chain.getRules().size());
            clearInvocations(cmd.validatorRepository, cmd.transformerRepository);
        }
    }
}
