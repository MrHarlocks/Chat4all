# Relatório de Teste de Tolerância a Falhas
**Data**: 2025-11-30 21:02:16


### Setup Environment
- [2025-11-30 21:01:59] Starting 2 workers...
- [2025-11-30 21:01:59] Started Worker 1 (PID: 16452)
- [2025-11-30 21:01:59] Started Worker 2 (PID: 19736)
- [2025-11-30 21:02:05] Created Test Conversation: 4f2d5a1e-61fe-49c5-82f7-81b753bdadec

### Scenario 1: Worker Failure under Load
- [2025-11-30 21:02:05] Sending batch of 100 messages...
- [2025-11-30 21:02:06] Sent 100/100 messages in 0.75s
- [2025-11-30 21:02:06] ⚠️ KILLED Worker (PID: 19736) while processing
- [2025-11-30 21:02:06] Waiting for 100 messages to be processed...
- [2025-11-30 21:02:06] SUCCESS: Processed 100 messages in 0.03s
- [2025-11-30 21:02:06] ✅ System recovered and processed all messages.

### Scenario 2: Service Recovery
- [2025-11-30 21:02:06] Started New Worker (PID: 2740)
- [2025-11-30 21:02:11] Sending batch of 50 messages...
- [2025-11-30 21:02:11] Sent 50/50 messages in 0.40s
- [2025-11-30 21:02:11] Waiting for 150 messages to be processed...
- [2025-11-30 21:02:16] SUCCESS: Processed 150 messages in 5.07s
- [2025-11-30 21:02:16] ✅ New worker joined and helped process messages.

### Cleanup
- [2025-11-30 21:02:16] Terminated Worker (PID: 16452)
- [2025-11-30 21:02:16] Terminated Worker (PID: 2740)