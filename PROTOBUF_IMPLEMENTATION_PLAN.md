<!-- file: PROTOBUF_IMPLEMENTATION_PLAN.md -->
<!-- version: 1.0.0 -->
<!-- guid: 2c728c3d-59c7-4e7a-93f1-6221b100edb5 -->

# Protobuf Implementation Plan

This plan tracks progress on implementing protobuf definitions across the gcommon modules.

## Modules Overview

| Module | Files Remaining | Status |
|-------|----------------|--------|
| Metrics | 95 | Pending |
| Queue | 175 | In Progress |
| Web | 176 | Pending |
| Auth | 109 | Pending |
| Cache | 36 | Pending |
| Config | 20 | Pending |

## Recent Work

- Implemented initial `queue.proto` providing service and message definitions for queue operations.

## Next Steps

- Flesh out advanced queue message types such as delayed delivery and priority handling.
- Begin designing metrics module protobufs.
