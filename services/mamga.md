# MAMGA Memory Service
**Type:** Infrastructure Service - Persistent State Layer
**URL:** http://127.0.0.1:7788
**Lifecycle:** Independent - NOT started/stopped by vibestart/vibestop

## What it does
Persistent memory layer. Unlike the 44 stateless MCP agents on port 3100,
MAMGA retains state across sessions: history, decisions, context blobs.

## How agents use it
  agent (MCP :3100) -> memory_store/memory_recall -> MAMGA :7788

## Notes
- Start MAMGA BEFORE vibestart.ps1
- vibestop.ps1 does NOT stop MAMGA - manage separately
- If MAMGA is down, agents still work but lose cross-session memory
