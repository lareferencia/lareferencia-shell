package org.lareferencia.shell.commands.harvester;

import java.io.PrintWriter;
import java.io.StringWriter;
import java.nio.file.Path;
import java.util.*;
import org.junit.jupiter.api.*;
import org.jline.terminal.Terminal;
import org.lareferencia.core.export.*;
import org.springframework.context.support.GenericApplicationContext;
import org.springframework.shell.*;
import org.springframework.shell.command.*;
import org.springframework.shell.context.*;
import org.springframework.shell.exit.ExitCodeMappings;
import org.springframework.shell.standard.StandardMethodTargetRegistrar;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class MetadataExportCommandsTest {
    MetadataExportService service;
    ShellContext context;
    MetadataExportCommands commands;
    GenericApplicationContext application;
    CommandCatalog catalog;
    @BeforeEach void setup() {
        service = mock(MetadataExportService.class); context = mock(ShellContext.class);
        when(context.getInteractionMode()).thenReturn(InteractionMode.NONINTERACTIVE);
        commands = new MetadataExportCommands(service, context);
        application = new GenericApplicationContext();
        application.registerBean(MetadataExportCommands.class, () -> commands); application.refresh();
        catalog = CommandCatalog.of();
        new StandardMethodTargetRegistrar(application, CommandRegistration::builder).register(catalog);
    }
    @AfterEach void close() { application.close(); }
    @Test void registersCommandsAndDescribesOptions() {
        assertEquals(Set.of("export-metadata", "export-mapping-validate", "export-metadata-preview"), catalog.getRegistrations().keySet());
        var registration = catalog.getRegistrations().get("export-metadata");
        assertTrue(registration.getDescription().contains("provenance"));
        assertTrue(registration.getOptions().size() >= 13);
    }
    @Test void translatesSelectionAndLimitsWithoutInternalIds() {
        var request = MetadataExportCommands.request(null, "RCAAP,IBICT", false, "processed", "jsonl", "mapping.json", "collection", "network", 10L, "128MiB", "gzip", false, "exports");
        assertEquals(List.of("RCAAP", "IBICT"), request.networks()); assertEquals(134217728L, request.byteLimit());
        assertThrows(IllegalArgumentException.class, () -> MetadataExportCommands.request("A", "B", false, "original", "xml", null, "collection", "none", null, null, "gzip", false, "exports"));
    }
    private String invoke() throws Exception {
        return commands.exportMetadata("RCAAP", null, false, "processed", "jsonl", "mapping.json", "collection", "network", null, null, "gzip", false, "exports");
    }
    @Test void partialExportFailsInBatchAndReturnsSummaryInteractively() throws Exception {
        when(service.export(any())).thenReturn(new MetadataExportService.Result(Path.of("exports/exp-test"), "PARTIAL", 2, 1, 0, 1));
        assertThrows(IllegalStateException.class, this::invoke);
        when(context.getInteractionMode()).thenReturn(InteractionMode.INTERACTIVE);
        assertTrue(invoke().startsWith("PARTIAL"));
    }
    @Test void actualShellParserExecutesFlagsAndPropagatesBatchFailures() throws Exception {
        when(service.export(any())).thenReturn(new MetadataExportService.Result(Path.of("exports/exp-test"), "PARTIAL", 2, 1, 0, 1));
        Terminal terminal = mock(Terminal.class);
        when(terminal.writer()).thenReturn(new PrintWriter(new StringWriter()));
        Shell shell = new Shell(mock(ResultHandlerService.class), catalog, terminal, context, mock(ExitCodeMappings.class));
        shell.setArgumentResolvers(new CommandExecution.CommandExecutionHandlerMethodArgumentResolvers(List.of(
                new org.springframework.shell.standard.ShellOptionMethodArgumentResolver(new org.springframework.core.convert.support.DefaultConversionService(), null))));
        Input input = () -> "export-metadata --network RCAAP --variant processed --format jsonl --mapping mapping.json --all-networks false --output exports";
        java.util.concurrent.atomic.AtomicBoolean provided = new java.util.concurrent.atomic.AtomicBoolean();
        Exception error = assertThrows(Exception.class, () -> shell.run(() -> provided.getAndSet(true) ? null : input));
        assertTrue(error.getMessage().contains("PARTIAL"), () -> error.toString() + " cause=" + error.getCause());
        verify(service).export(argThat(request -> request.networks().equals(List.of("RCAAP")) && !request.allNetworks()));
    }
    @Test void actualShellDefaultsAndBareFlagsReachTheService() throws Exception {
        when(service.export(any())).thenReturn(new MetadataExportService.Result(Path.of("exports/exp-test"), "COMPLETE", 1, 1, 0, 0));
        Terminal terminal = mock(Terminal.class);
        when(terminal.writer()).thenReturn(new PrintWriter(new StringWriter()));
        Shell shell = new Shell(mock(ResultHandlerService.class), catalog, terminal, context, mock(ExitCodeMappings.class));
        shell.setArgumentResolvers(new CommandExecution.CommandExecutionHandlerMethodArgumentResolvers(List.of(
                new org.springframework.shell.standard.ShellOptionMethodArgumentResolver(new org.springframework.core.convert.support.DefaultConversionService(), null))));
        java.util.concurrent.atomic.AtomicBoolean provided = new java.util.concurrent.atomic.AtomicBoolean();
        shell.run(() -> provided.getAndSet(true) ? null : () -> "export-metadata --all-networks --valid-only --mapping mapping.json --output exports");
        verify(service).export(argThat(request -> request.allNetworks() && request.validOnly()
                && request.variant().equals("processed") && request.format().equals("jsonl")
                && request.partitionBy().equals("network") && request.recordLimit() == 10000 && request.byteLimit() == 134217728));
    }

}
