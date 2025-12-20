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
import org.lareferencia.core.flowable.WorkflowService;
import org.lareferencia.core.flowable.dto.ProcessDefinitionInfo;
import org.lareferencia.core.flowable.dto.ProcessInstanceInfo;
import org.lareferencia.core.flowable.exception.QueueFullException;
import org.lareferencia.core.repository.jpa.NetworkRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.shell.standard.ShellComponent;
import org.springframework.shell.standard.ShellMethod;
import org.springframework.shell.standard.ShellOption;

import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Shell commands for managing Flowable workflow processes.
 * 
 * @author LA Referencia Team
 */
@ShellComponent
public class WorkflowCommands {

    private static final Logger logger = LogManager.getLogger(WorkflowCommands.class);
    private static final DateTimeFormatter DATE_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    @Autowired
    private WorkflowService workflowService;

    @Autowired
    private NetworkRepository networkRepository;

    // ========== List Processes ==========

    @ShellMethod(value = "List available workflow process definitions", key = "list-processes")
    public String listProcesses() {
        List<ProcessDefinitionInfo> processes = workflowService.getAvailableProcesses();

        if (processes.isEmpty()) {
            return "No process definitions found. Make sure BPMN files are deployed.";
        }

        StringBuilder result = new StringBuilder();
        result.append(String.format("%-30s %-40s %-10s%n", "KEY", "NAME", "VERSION"));
        result.append("=".repeat(82)).append("\n");

        for (ProcessDefinitionInfo process : processes) {
            result.append(String.format("%-30s %-40s %-10d%n",
                    process.getProcessKey(),
                    truncate(process.getName() != null ? process.getName() : "-", 38),
                    process.getVersion()));
        }

        return result.toString();
    }

    // ========== Run Process ==========

    @ShellMethod(value = "Run a workflow process for a network", key = "run-process")
    public String runProcess(
            @ShellOption(help = "Process key (e.g., networkProcessing)") String processKey,
            @ShellOption(help = "Network ID") Long networkId,
            @ShellOption(help = "Incremental mode", defaultValue = "false") boolean incremental) {

        // Validate network exists
        Optional<Network> optNetwork = networkRepository.findById(networkId);
        if (optNetwork.isEmpty()) {
            return "ERROR: Network " + networkId + " not found";
        }
        Network network = optNetwork.get();

        // Build process variables
        Map<String, Object> variables = new HashMap<>();
        variables.put("networkId", networkId);
        variables.put("incremental", incremental);

        try {
            ProcessInstanceInfo instance = workflowService.submitProcess(processKey, variables);

            if (instance.getProcessInstanceId() != null) {
                return String.format("Process started successfully\n" +
                        "  Process Key: %s\n" +
                        "  Instance ID: %s\n" +
                        "  Network: %s (ID: %d)\n" +
                        "  Incremental: %s",
                        processKey,
                        instance.getProcessInstanceId(),
                        network.getAcronym(),
                        networkId,
                        incremental);
            } else {
                return String.format("Process queued (network or lane busy)\n" +
                        "  Process Key: %s\n" +
                        "  Network: %s (ID: %d)\n" +
                        "  Incremental: %s",
                        processKey,
                        network.getAcronym(),
                        networkId,
                        incremental);
            }
        } catch (QueueFullException e) {
            return "ERROR: " + e.getMessage();
        } catch (Exception e) {
            logger.error("Error starting process", e);
            return "ERROR: " + e.getMessage();
        }
    }

    // ========== Process Status ==========

    @ShellMethod(value = "Get status of a process instance", key = "process-status")
    public String processStatus(
            @ShellOption(help = "Process instance ID") String processInstanceId) {

        ProcessInstanceInfo instance = workflowService.getProcessInstance(processInstanceId);

        if (instance == null) {
            return "ERROR: Process instance " + processInstanceId + " not found";
        }

        StringBuilder result = new StringBuilder();
        result.append("Process Instance Details\n");
        result.append("=".repeat(50)).append("\n");
        result.append(String.format("Instance ID:    %s%n", instance.getProcessInstanceId()));
        result.append(String.format("Process Key:    %s%n", instance.getProcessDefinitionKey()));
        result.append(String.format("Process Name:   %s%n",
                instance.getProcessDefinitionName() != null ? instance.getProcessDefinitionName() : "-"));
        result.append(String.format("Start Time:     %s%n",
                instance.getStartTime() != null ? instance.getStartTime().format(DATE_FORMAT) : "-"));
        result.append(String.format("End Time:       %s%n",
                instance.getEndTime() != null ? instance.getEndTime().format(DATE_FORMAT) : "-"));
        result.append(String.format("Status:         %s%n", getStatusString(instance)));
        result.append(String.format("Current Task:   %s%n",
                instance.getCurrentActivityId() != null ? instance.getCurrentActivityId() : "-"));

        // Show key variables
        if (instance.getVariables() != null && !instance.getVariables().isEmpty()) {
            result.append("\nVariables:\n");
            instance.getVariables().forEach((key, value) -> {
                if (key.equals("networkId") || key.equals("incremental") ||
                        key.equals("completionRate") || key.equals("workerSuccess")) {
                    result.append(String.format("  %s: %s%n", key, value));
                }
            });
        }

        return result.toString();
    }

    // ========== List Running ==========

    @ShellMethod(value = "List running process instances", key = "list-running")
    public String listRunning() {
        List<ProcessInstanceInfo> running = workflowService.getRunningProcesses();

        if (running.isEmpty()) {
            return "No running processes";
        }

        StringBuilder result = new StringBuilder();
        result.append(String.format("%-36s %-20s %-8s %-16s %-25s%n",
                "INSTANCE ID", "PROCESS KEY", "NETWORK", "START TIME", "STATUS"));
        result.append("=".repeat(110)).append("\n");

        for (ProcessInstanceInfo instance : running) {
            Long networkId = instance.getVariables() != null ? (Long) instance.getVariables().get("networkId") : null;
            String status = workflowService.getWorkerStatus(instance.getProcessInstanceId());

            result.append(String.format("%-36s %-20s %-8s %-16s %-25s%n",
                    instance.getProcessInstanceId(),
                    truncate(instance.getProcessDefinitionKey(), 18),
                    networkId != null ? networkId.toString() : "-",
                    instance.getStartTime() != null ? instance.getStartTime().format(DATE_FORMAT) : "-",
                    status != null ? truncate(status, 23) : "-"));
        }

        result.append("\nTotal: ").append(running.size()).append(" running");
        return result.toString();
    }

    // ========== List Queued ==========

    @ShellMethod(value = "List queued processes", key = "list-queued")
    public String listQueued() {
        int queuedCount = workflowService.getTotalQueuedCount();
        List<Long> busyNetworks = workflowService.getBusyNetworks();

        StringBuilder result = new StringBuilder();
        result.append("Queue Status\n");
        result.append("=".repeat(50)).append("\n");
        result.append(String.format("Total Queued:     %d%n", queuedCount));
        result.append(String.format("Running Count:    %d%n", workflowService.getRunningCount()));

        if (!busyNetworks.isEmpty()) {
            result.append("\nBusy Networks: ");
            result.append(busyNetworks.toString());
            result.append("\n");
        }

        return result.toString();
    }

    // ========== Stop Process ==========

    @ShellMethod(value = "Stop a running process", key = "stop-process")
    public String stopProcess(
            @ShellOption(help = "Process instance ID") String processInstanceId,
            @ShellOption(help = "Reason for stopping", defaultValue = "Manual termination") String reason) {

        ProcessInstanceInfo instance = workflowService.getProcessInstance(processInstanceId);

        if (instance == null) {
            return "ERROR: Process instance " + processInstanceId + " not found";
        }

        if (instance.isCompleted()) {
            return "ERROR: Process instance " + processInstanceId + " is already completed";
        }

        try {
            workflowService.terminateProcess(processInstanceId, reason);
            return String.format("Process %s stopped successfully\nReason: %s",
                    processInstanceId, reason);
        } catch (Exception e) {
            logger.error("Error stopping process", e);
            return "ERROR: " + e.getMessage();
        }
    }

    // ========== Helper Methods ==========

    private String getStatusString(ProcessInstanceInfo instance) {
        if (instance.isCompleted()) {
            return "COMPLETED";
        } else if (instance.isSuspended()) {
            return "SUSPENDED";
        } else {
            return "RUNNING";
        }
    }

    private String truncate(String text, int maxLength) {
        if (text == null)
            return "-";
        return text.length() > maxLength ? text.substring(0, maxLength - 2) + ".." : text;
    }
}
