package org.lareferencia.shell.commands.harvester;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.*;

import org.apache.poi.openxml4j.util.ZipSecureFile;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.lareferencia.core.domain.Network;
import org.lareferencia.core.domain.Transformer;
import org.lareferencia.core.domain.Validator;
import org.lareferencia.core.repository.jpa.NetworkRepository;
import org.lareferencia.core.repository.jpa.TransformerRepository;
import org.lareferencia.core.repository.jpa.ValidatorRepository;
import org.springframework.scheduling.support.CronExpression;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

/** Shared one-sheet source format used by the shell. It intentionally mirrors the v5 API. */
final class NetworkXlsxTransfer {
    static final List<String> COLUMNS = List.of("sourceId", "acronym", "name", "institutionName", "institutionAcronym", "published", "originUrl", "metadataPrefix", "metadataStoreSchema", "scheduleCronExpression", "attributeProfile", "attributesJson", "setsJson", "propertiesJson", "prevalidatorRef", "validatorRef", "transformerRef", "secondaryTransformerRef");
    private static final int MAX_ROWS = 10_000;
    private final NetworkRepository networks; private final ValidatorRepository validators; private final TransformerRepository transformers; private final ObjectMapper json;

    NetworkXlsxTransfer(NetworkRepository networks, ValidatorRepository validators, TransformerRepository transformers, ObjectMapper json) { this.networks = networks; this.validators = validators; this.transformers = transformers; this.json = json; }

    void exportTo(String filename) throws Exception {
        try (Workbook workbook = new XSSFWorkbook(); FileOutputStream output = new FileOutputStream(filename)) {
            Sheet sheet = workbook.createSheet("Fuentes"); Row header = sheet.createRow(0);
            for (int i = 0; i < COLUMNS.size(); i++) header.createCell(i).setCellValue(COLUMNS.get(i));
            int index = 1;
            for (Network network : networks.findAll().stream().sorted(Comparator.comparing(Network::getAcronym)).toList()) {
                List<String> values = new ArrayList<>(); values.add(value(network.getId())); values.add(network.getAcronym()); values.add(network.getName()); values.add(network.getInstitutionName()); values.add(network.getInstitutionAcronym()); values.add(value(network.getPublished())); values.add(network.getOriginURL()); values.add(network.getMetadataPrefix()); values.add(network.getMetadataStoreSchema()); values.add(network.getScheduleCronExpression()); values.add(profile(network)); values.add(json.writeValueAsString(map(network.getAttributes()))); values.add(json.writeValueAsString(network.getSets() == null ? List.of() : network.getSets())); values.add(json.writeValueAsString(map(network.getProperties()))); values.add(name(network.getPrevalidator())); values.add(name(network.getValidator())); values.add(name(network.getTransformer())); values.add(name(network.getSecondaryTransformer()));
                Row row = sheet.createRow(index++); for (int i = 0; i < values.size(); i++) row.createCell(i).setCellValue(safe(values.get(i)));
            }
            sheet.createFreezePane(0, 1); workbook.write(output);
        }
    }

    void importFrom(String filename) throws Exception {
        ZipSecureFile.setMinInflateRatio(0.01d);
        try (Workbook workbook = WorkbookFactory.create(new FileInputStream(filename))) {
            Sheet sheet = workbook.getSheet("Fuentes"); if (sheet == null) throw new IllegalArgumentException("Missing sheet Fuentes"); if (sheet.getLastRowNum() > MAX_ROWS) throw new IllegalArgumentException("Too many rows");
            Map<String, Integer> columns = columns(sheet.getRow(0)); DataFormatter formatter = new DataFormatter(); Set<String> seen = new HashSet<>(); List<RowData> rows = new ArrayList<>();
            for (int i = 1; i <= sheet.getLastRowNum(); i++) { Row row = sheet.getRow(i); if (row == null || empty(row, formatter)) continue; RowData data = parse(row, i + 1, columns, formatter); validate(data, seen); rows.add(data); }
            for (RowData data : rows) apply(data);
        }
    }

    private void apply(RowData row) {
        Network network = networks.findByAcronym(row.acronym); if (network == null) { network = new Network(); }
        network.setAcronym(row.acronym); network.setName(row.name); network.setInstitutionName(row.institutionName); network.setInstitutionAcronym(emptyToNull(row.institutionAcronym)); network.setPublished(row.published); network.setOriginURL(row.originUrl); network.setMetadataPrefix(emptyToNull(row.metadataPrefix)); network.setMetadataStoreSchema(emptyToNull(row.metadataStoreSchema)); network.setScheduleCronExpression(emptyToNull(row.cron)); network.setAttributes(new HashMap<>(row.attributes)); network.setSets(new ArrayList<>(row.sets)); network.setProperties(new HashMap<>(row.properties)); network.setPrevalidator(findValidator(row.prevalidator)); network.setValidator(findValidator(row.validator)); network.setTransformer(findTransformer(row.transformer)); network.setSecondaryTransformer(findTransformer(row.secondaryTransformer)); networks.save(network);
    }

    private void validate(RowData row, Set<String> seen) {
        if (row.acronym == null || !row.acronym.matches("^[A-Za-z0-9][A-Za-z0-9._-]{1,9}$")) throw new IllegalArgumentException("Invalid acronym at row " + row.row);
        if (!seen.add(row.acronym)) throw new IllegalArgumentException("Duplicate acronym at row " + row.row);
        if (blank(row.name) || blank(row.institutionName)) throw new IllegalArgumentException("Missing required source fields at row " + row.row);
        try { URI uri = URI.create(row.originUrl); if (uri.getScheme() == null || uri.getHost() == null) throw new IllegalArgumentException(); } catch (Exception e) { throw new IllegalArgumentException("Invalid originUrl at row " + row.row); }
        if (!blank(row.cron) && !CronExpression.isValidExpression(row.cron)) throw new IllegalArgumentException("Invalid cron at row " + row.row);
        findValidator(row.prevalidator); findValidator(row.validator); findTransformer(row.transformer); findTransformer(row.secondaryTransformer);
    }

    private RowData parse(Row row, int rowNumber, Map<String, Integer> columns, DataFormatter formatter) throws Exception {
        Map<String, Object> attributes = object(cell(row, columns, "attributesJson", formatter)); List<String> sets = list(cell(row, columns, "setsJson", formatter)); Map<String, Boolean> properties = boolMap(cell(row, columns, "propertiesJson", formatter));
        return new RowData(rowNumber, cell(row, columns, "acronym", formatter), cell(row, columns, "name", formatter), cell(row, columns, "institutionName", formatter), cell(row, columns, "institutionAcronym", formatter), bool(cell(row, columns, "published", formatter)), cell(row, columns, "originUrl", formatter), cell(row, columns, "metadataPrefix", formatter), cell(row, columns, "metadataStoreSchema", formatter), cell(row, columns, "scheduleCronExpression", formatter), cell(row, columns, "attributeProfile", formatter), attributes, sets, properties, cell(row, columns, "prevalidatorRef", formatter), cell(row, columns, "validatorRef", formatter), cell(row, columns, "transformerRef", formatter), cell(row, columns, "secondaryTransformerRef", formatter));
    }

    private Map<String, Integer> columns(Row header) { if (header == null) throw new IllegalArgumentException("Missing header"); Map<String, Integer> result = new HashMap<>(); DataFormatter formatter = new DataFormatter(); for (Cell cell : header) result.put(formatter.formatCellValue(cell).trim(), cell.getColumnIndex()); for (String required : List.of("acronym", "name", "institutionName", "originUrl")) if (!result.containsKey(required)) throw new IllegalArgumentException("Missing column " + required); return result; }
    private String cell(Row row, Map<String, Integer> columns, String key, DataFormatter formatter) { Integer index = columns.get(key); if (index == null) return ""; Cell cell = row.getCell(index); if (cell == null) return ""; if (cell.getCellType() == CellType.FORMULA) throw new IllegalArgumentException("Formulas are not allowed"); return formatter.formatCellValue(cell).trim(); }
    private boolean empty(Row row, DataFormatter formatter) { for (Cell cell : row) if (!formatter.formatCellValue(cell).trim().isEmpty()) return false; return true; }
    private Map<String, Object> object(String value) throws Exception { return blank(value) ? Map.of() : json.readValue(value, new TypeReference<Map<String, Object>>() {}); } private List<String> list(String value) throws Exception { return blank(value) ? List.of() : json.readValue(value, new TypeReference<List<String>>() {}); } private Map<String, Boolean> boolMap(String value) throws Exception { return blank(value) ? Map.of() : json.readValue(value, new TypeReference<Map<String, Boolean>>() {}); }
    private boolean bool(String value) { return blank(value) || Boolean.parseBoolean(value); } private Validator findValidator(String name) { if (blank(name)) return null; List<Validator> values = validators.findAll().stream().filter(item -> name.equals(item.getName())).toList(); if (values.size() != 1) throw new IllegalArgumentException("Validator reference not found or ambiguous: " + name); return values.get(0); } private Transformer findTransformer(String name) { if (blank(name)) return null; List<Transformer> values = transformers.findAll().stream().filter(item -> name.equals(item.getName())).toList(); if (values.size() != 1) throw new IllegalArgumentException("Transformer reference not found or ambiguous: " + name); return values.get(0); }
    private static String profile(Network network) { Object clazz = map(network.getAttributes()).get("@class"); if (!(clazz instanceof String)) return ""; return switch ((String) clazz) { case "org.lareferencia.backend.network.LAReferenciaNetworkAttributes" -> "lareferencia-repository"; case "org.lareferencia.backend.network.IbictRepositoryNetworkAttributes" -> "ibict-repository"; case "org.lareferencia.backend.network.RCAAPNetworkAttributes" -> "rcaap-repository"; default -> (String) clazz; }; }
    private static String name(Object value) { return value == null ? "" : value instanceof Validator ? ((Validator) value).getName() : ((Transformer) value).getName(); } private static String value(Object value) { return value == null ? "" : String.valueOf(value); } private static String emptyToNull(String value) { return blank(value) ? null : value; } private static boolean blank(String value) { return value == null || value.isBlank(); } private static String safe(String value) { if (value == null) return ""; return value.matches("^[=+@].*") ? "'" + value : value; } private static <T> Map<String, T> map(Map<String, T> value) { return value == null ? Map.of() : value; }
    record RowData(int row, String acronym, String name, String institutionName, String institutionAcronym, boolean published, String originUrl, String metadataPrefix, String metadataStoreSchema, String cron, String profile, Map<String, Object> attributes, List<String> sets, Map<String, Boolean> properties, String prevalidator, String validator, String transformer, String secondaryTransformer) { }
}
