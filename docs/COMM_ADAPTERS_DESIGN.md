# Communication Adapters: Redis and NATS (Design Notes)

This document outlines the intended design for production-grade communication adapters.

## RedisBus (Pub/Sub or Streams)

- Transport: redis.asyncio or aioredis
- Modes:
  - Pub/Sub: light-weight fan-out for topics
  - Streams: durable messaging via XADD/XREAD with consumer groups
- Message format: JSON with fields from Message (topic, type, payload, correlation_id, reply_to, headers)
- Backpressure:
  - Stream maxlen / eviction policies
  - Consumer groups with pending message lists
- Ordering:
  - Per-stream ordering guaranteed by Redis streams
- Observability:
  - Record publish latency; backpressure triggers; subscriber count metrics
- Security:
  - Redis ACL for channels/streams

## NatsBus (Subjects, JetStream optional)

- Transport: nats-py (async)
- Subjects: map topics -> subjects; reply_to -> inbox subject
- Request/Response:
  - Use request() for RPC pattern; timeouts; correlation id in headers
- JetStream (optional): persistence, retention policies, consumer groups
- Backpressure:
  - Flow control via jetstream; acking; durable consumers
- Ordering:
  - Per stream subject ordering with JetStream
- Observability:
  - Publish/subscribe latencies; lost messages; reconnection counts

## API Contracts

Adapters implement CommunicationBus (subscribe, unsubscribe, publish), and rely on the existing request() helper in the base class for RPC.
