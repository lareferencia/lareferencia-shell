
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
package org.lareferencia.shell.commands.harvester;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.commons.beanutils.BeanUtils;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.lareferencia.core.domain.Network;
import org.lareferencia.core.domain.Transformer;
import org.lareferencia.core.domain.Validator;
import org.lareferencia.core.repository.jpa.NetworkRepository;
import org.lareferencia.core.repository.jpa.TransformerRepository;
import org.lareferencia.core.repository.jpa.ValidatorRepository;
import org.lareferencia.core.metadata.IMetadataStore;
import org.lareferencia.core.metadata.ISnapshotStore;
import org.lareferencia.core.util.JSONSerializerHelper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.shell.standard.ShellComponent;
import org.springframework.shell.standard.ShellMethod;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;


import java.io.*;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.*;

@ShellComponent
public class HarvesterCommands {

	@Autowired
	NetworkRepository networkRepository;

	// @Autowired
	// ISnapshotStore snapshotStore;

	// @Autowired
	// IMetadataStore metadataStore;

	private static Logger logger = LogManager.getLogger(HarvesterCommands.class);

	@ShellMethod("Dump networks/repositories table data to excel")
	public String networksTableDump(String excelFileFullPath) throws Exception {

		dump_fields(excelFileFullPath);

		return "networks dumped to: " + excelFileFullPath;
	}

	@ShellMethod("Update networks/repositories table data from excel")
	public String networksTableUpdate(String excelFileFullPath) throws Exception {

		String backupFileFullPath = "backup." + excelFileFullPath;
		System.out.println("making backup to:" + backupFileFullPath);

		dump_fields(backupFileFullPath);

		System.out.println("Updating db from:" + excelFileFullPath);

		upload_fields(excelFileFullPath);

		return "networks updated from: " + excelFileFullPath;
	}


	private void upload_fields(String filename) throws Exception {

		File file = new File(filename);

		if ( file.exists() ) {

			InputStream inp = new FileInputStream(file);

			Workbook wb = WorkbookFactory.create(inp);
			Sheet sheet = wb.getSheetAt(0);

			// Obtiene los nombres de las celdas de la primera fila y almacena los indices
			LinkedHashMap<String, Short> columnsByName = new LinkedHashMap<String, Short>();
			Row row = sheet.getRow(0);

			for (short colIx = row.getFirstCellNum(); colIx < row.getLastCellNum(); colIx++) {
				Cell cell = row.getCell(colIx);
				if (cell == null) {
					continue;
				}
				columnsByName.put(cell.getStringCellValue(), colIx);
			}

			System.out.println("Detected fields:" + columnsByName.keySet());

			// el indice del campo id si existe
			Short networkIdIx = columnsByName.get("id");

			if (networkIdIx != null) { // solo si existe el campo id entre los nombres de campo

				// Itera sobre todas la filas de datos
				for (short rowIx = 1; rowIx <= sheet.getLastRowNum(); rowIx++) {
					Row dataRow = sheet.getRow(rowIx);

					if (dataRow == null) {
						continue;
					}

					dataRow.getCell(networkIdIx).setCellType(CellType.STRING);
					Long networkID = Long.valueOf(dataRow.getCell(networkIdIx).getStringCellValue());

					Optional<Network> optionalNetwork = networkRepository.findById(networkID);

					if (optionalNetwork.isPresent()) {

						System.out.println("Updating network id:" + networkID);
						Network network = optionalNetwork.get();

						/**
						 *  Update attributes
						 */

						Map<String, Object> attr_fields = network.getAttributes();

						for (String fieldName : attr_fields.keySet()) {

							// get columund id for this attribute (if exists)
							Short colIx = columnsByName.get(fieldName);
							if (colIx == null)
								continue;


							if (dataRow.getCell(colIx) != null) {
								try {
									dataRow.getCell(colIx).setCellType(CellType.STRING);
									String value = dataRow.getCell(colIx).getStringCellValue();

									// if value is not null
									if (value != null)
										network.getAttributes().put(fieldName, value);
								} catch (Exception e) {
									System.out.println("Error al convertir fieldName " + fieldName + " del network " + network.getId() + ": " + e.getMessage());
								}
							}
						}

						/**
						 * Update properties
						 */

						String[] properties = {"scheduleCronExpression", "institutionName", "institutionAcronym", "name"};

						for (String fieldName : properties) {
							Short colIx = columnsByName.get(fieldName);
							if (colIx == null) continue;

							dataRow.getCell(colIx).setCellType(CellType.STRING);
							String value = dataRow.getCell(colIx).getStringCellValue();

							if (value != null)
								BeanUtils.setProperty(network, fieldName, value);
						}

						// Save network
						networkRepository.save(network);

					} else System.out.println("Network id: " + networkID + " not present in db");

				}
			} else {
				System.out.println("No Network id field (id)");
			}
		} else {
			System.out.println("File not exists: " + filename);
		}


	}

	private void dump_fields(String fieldname) throws Exception {

		Workbook workbook = new XSSFWorkbook();
		Sheet sheet = workbook.createSheet("Data");

		List<Network> networks = networkRepository.findAll();

		Set<String> networkAttributesFields = new HashSet<>();
		LinkedHashSet<String> networkPropertiesFields = new LinkedHashSet<>();

		List<Map<String, Object>> networkAttributesData = new ArrayList<Map<String, Object>>();
		List<Map<String, String>> networkPropertiesData = new ArrayList<Map<String, String>>();

		for (Network network : networks) {

			// Attributes
			Map<String, Object> networkAttributesMap = network.getAttributes();
			networkAttributesData.add(networkAttributesMap);
			networkAttributesFields.addAll(networkAttributesMap.keySet());

			// Properties
			LinkedHashMap<String, String> networkPropertiesMap = new LinkedHashMap<>();
			networkPropertiesMap.put("id",network.getId().toString());
			networkPropertiesMap.put("name",network.getName());
			networkPropertiesMap.put("institutionAcronym",network.getInstitutionAcronym());
			networkPropertiesMap.put("institutionName",network.getInstitutionName());
			networkPropertiesMap.put("metadataPrefix",network.getMetadataPrefix());
			networkPropertiesMap.put("originURL",network.getOriginURL());
			networkPropertiesMap.put("metadataStoreSchema", network.getMetadataStoreSchema());
			networkPropertiesMap.put("scheduleCronExpression", network.getScheduleCronExpression());

			//System.out.println(networkPropertiesMap);
			networkPropertiesData.add(networkPropertiesMap);
			networkPropertiesFields.addAll(networkPropertiesMap.keySet());
		}

		// convert set to array to preserve order
		ArrayList<String> attrFieldNames = new ArrayList<String>(
				Arrays.asList(networkAttributesFields.toArray(new String[networkAttributesFields.size()])));
		ArrayList<String> propFieldNames = new ArrayList<String>(
				Arrays.asList(networkPropertiesFields.toArray(new String[networkPropertiesFields.size()])));

		int row = 0;

		// create header
		Row header = sheet.createRow(row++);
		int col = 0;

		for (String propFieldName : propFieldNames)
			header.createCell(col++).setCellValue(propFieldName);

		for (String attrFieldName : attrFieldNames)
			header.createCell(col++).setCellValue(attrFieldName);

		// foreach datatow put data in xls
		for (int i = 0; i < networkAttributesData.size(); i++) {

			Map<String, Object> attrData = networkAttributesData.get(i);
			Map<String, String> propData = networkPropertiesData.get(i);

			Row datarow = sheet.createRow(row++);

			col = 0;
			for (String fieldName : propFieldNames) {
				Object value = propData.get(fieldName);
				if (value != null)
					datarow.createCell(col).setCellValue(value.toString());
				col++;
			}

			for (String fieldName : attrFieldNames) {
				Object value = attrData.get(fieldName);
				if (value != null)
					datarow.createCell(col).setCellValue(value.toString());
				col++;
			}

		}

		saveWorkBook(workbook, fieldname);
	}

	private void saveWorkBook(Workbook workbook, String filename) throws IOException {

		File currDir = new File(".");
		String path = currDir.getAbsolutePath();
		String fileLocation = path.substring(0, path.length() - 1) + filename;

		FileOutputStream outputStream = new FileOutputStream(fileLocation);
		workbook.write(outputStream);
		workbook.close();
	}

	/******************************* Validator ***************************************/
	@Autowired
	ValidatorRepository validatorRepository;

	@Autowired
	TransformerRepository transformerRepository;


	@ShellMethod("List validators")
	public String listValidators() throws Exception {

		System.out.println("Listing validators: \n");

		for (Validator validator: validatorRepository.findAll() ) {
			System.out.println( validator.getId() + "\t ----> " + validator.getName() );
		}

		return "";
	}

	@ShellMethod("List transformers")
	public String listTransformers() throws Exception {

		System.out.println("Listing transformers: \n");

		for (Transformer transformer: transformerRepository.findAll() ) {
			System.out.println( transformer.getId() + "\t ----> " + transformer.getName() );
		}

		return "";
	}

	@ShellMethod("Export validator to json file")
	public String exportValidator(
			@org.springframework.shell.standard.ShellOption(value = "--id", help = "Validator ID") Long validatorId,
			@org.springframework.shell.standard.ShellOption(value = "--filename", help = "Output JSON file path") String filename) throws Exception {

		if (validatorId == null) {
			System.err.println("Error: Validator ID is required (use --id)");
			return "FAILED";
		}

		if (filename == null || filename.trim().isEmpty()) {
			System.err.println("Error: Output filename is required (use --filename)");
			return "FAILED";
		}

		Optional<Validator> optionalValidator = validatorRepository.findById(validatorId);

		if ( optionalValidator.isPresent() ) {

			System.out.println("Exporting validator: " + validatorId + " to " + filename );

			try {
				String serializedString = JSONSerializerHelper.serializeToJsonString( optionalValidator.get() );
				Files.write(new File(filename).toPath(), serializedString.getBytes(StandardCharsets.UTF_8));
				System.out.println("Validator successfully exported to: " + filename);
			} catch (Exception e) {
				System.err.println("Error exporting validator: " + e.getMessage());
				throw e;
			}

		} else {
			System.err.println("Error: Validator with id: " + validatorId + " does not exist.");
			return "FAILED";
		}

		return "OK";
	}

	@Transactional(propagation = Propagation.REQUIRES_NEW)
	@ShellMethod("Import Validator from json file")
	public void importValidator(
			@org.springframework.shell.standard.ShellOption(value = "--filename", help = "JSON file path") String filename,
			@org.springframework.shell.standard.ShellOption(value = "--migrate", help = "Migrate package references from backend.* to core.*", defaultValue = "false") boolean migrate) throws Exception {

		if (filename == null || filename.trim().isEmpty()) {
			System.err.println("Error: Input filename is required (use --filename)");
			return;
		}

		File file = new File(filename);

		if ( !file.exists() ) {
			System.err.println("Error: File not found: " + filename);
			return;
		}

		try {
			// Read JSON content from file using non-deprecated method
			byte[] jsonBytes = Files.readAllBytes(file.toPath());
			String jsonContent = new String(jsonBytes, StandardCharsets.UTF_8);
			
			// Optionally migrate package references from old backend.* to new core.* structure
			if (migrate) {
				jsonContent = migratePackageReferencesInJson(jsonContent);
				System.out.println("Package references migrated from backend.* to core.*");
			}
			
			// Deserialize using ObjectMapper
			ObjectMapper objectMapper = new ObjectMapper();
			Validator validator = objectMapper.readValue(jsonContent, Validator.class);
			
			if (validator == null) {
				System.err.println("Error: Invalid validator JSON - deserialization returned null");
				return;
			}
			
			validator.resetId();

			validatorRepository.saveAndFlush(validator);

			System.out.println("Validator: " + validator.getName() + " successfully loaded to db. ");
		} catch (IOException e) {
			System.err.println("Error reading or processing validator file: " + e.getMessage());
			e.printStackTrace();
		} catch (Exception e) {
			System.err.println("Error importing validator: " + e.getMessage());
			e.printStackTrace();
		}

	}

	@ShellMethod("Export transformer to json file")
	public String exportTransformer(
			@org.springframework.shell.standard.ShellOption(value = "--id", help = "Transformer ID") Long transformerId,
			@org.springframework.shell.standard.ShellOption(value = "--filename", help = "Output JSON file path") String filename) throws Exception {

		if (transformerId == null) {
			System.err.println("Error: Transformer ID is required (use --id)");
			return "FAILED";
		}

		if (filename == null || filename.trim().isEmpty()) {
			System.err.println("Error: Output filename is required (use --filename)");
			return "FAILED";
		}

		Optional<Transformer> optionalTransformer = transformerRepository.findById(transformerId);

		if ( optionalTransformer.isPresent() ) {

			System.out.println("Exporting transformer: " + transformerId + " to " + filename );

			try {
				String serializedString = JSONSerializerHelper.serializeToJsonString( optionalTransformer.get() );
				Files.write(new File(filename).toPath(), serializedString.getBytes(StandardCharsets.UTF_8));
				System.out.println("Transformer successfully exported to: " + filename);
			} catch (Exception e) {
				System.err.println("Error exporting transformer: " + e.getMessage());
				throw e;
			}

		} else {
			System.err.println("Error: Transformer with id: " + transformerId + " does not exist.");
			return "FAILED";
		}

		return "OK";
	}

	@Transactional(propagation = Propagation.REQUIRES_NEW)
	@ShellMethod("Import Transformer from json file")
	public void importTransformer(
			@org.springframework.shell.standard.ShellOption(value = "--filename", help = "JSON file path") String filename,
			@org.springframework.shell.standard.ShellOption(value = "--migrate", help = "Migrate package references from backend.* to core.*", defaultValue = "false") boolean migrate) throws Exception {

		if (filename == null || filename.trim().isEmpty()) {
			System.err.println("Error: Input filename is required (use --filename)");
			return;
		}

		File file = new File(filename);

		if ( !file.exists() ) {
			System.err.println("Error: File not found: " + filename);
			return;
		}

		try {
			// Read JSON content from file using non-deprecated method
			byte[] jsonBytes = Files.readAllBytes(file.toPath());
			String jsonContent = new String(jsonBytes, StandardCharsets.UTF_8);
			
			// Optionally migrate package references from old backend.* to new core.* structure
			if (migrate) {
				jsonContent = migratePackageReferencesInJson(jsonContent);
				System.out.println("Package references migrated from backend.* to core.*");
			}
			
			// Deserialize using ObjectMapper
			ObjectMapper objectMapper = new ObjectMapper();
			Transformer transformer = objectMapper.readValue(jsonContent, Transformer.class);
			
			if (transformer == null) {
				System.err.println("Error: Invalid transformer JSON - deserialization returned null");
				return;
			}
			
			transformer.resetId();

			transformerRepository.saveAndFlush(transformer);

			System.out.println("Transformer: " + transformer.getName() + " successfully loaded to db. ");
		} catch (IOException e) {
			System.err.println("Error reading or processing transformer file: " + e.getMessage());
			e.printStackTrace();
		} catch (Exception e) {
			System.err.println("Error importing transformer: " + e.getMessage());
			e.printStackTrace();
		}

	}

	/**
	 * Migrates package references in JSON content from old backend.* structure to new core.* structure.
	 * This ensures JSON exported from old versions can be imported into new versions.
	 *
	 * Mapping rules for transformer and validator rules only:
	 * org.lareferencia.backend.validation.validator.* -> org.lareferencia.core.worker.validation.validator.*
	 * org.lareferencia.backend.validation.transformer.* -> org.lareferencia.core.worker.validation.transformer.*
	 *
	 * @param jsonContent the JSON string to migrate
	 * @return the migrated JSON with updated package references
	 */
	private String migratePackageReferencesInJson(String jsonContent) {
		// Map transformer and validator rules from backend to core.worker
		jsonContent = jsonContent.replace("org.lareferencia.backend.validation.validator.", "org.lareferencia.core.worker.validation.validator.");
		jsonContent = jsonContent.replace("org.lareferencia.backend.validation.transformer.", "org.lareferencia.core.worker.validation.transformer.");
		
		return jsonContent;
	}


	

}
