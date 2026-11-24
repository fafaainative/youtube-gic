# YouTube GIC — Engineering Design Decisions

## DD-001: Separation of Responsibilities

**Status:** Accepted

### Context

YouTube GIC needs to retrieve external YouTube data, process that data into application-specific structures, and expose functionality through an API.

Combining these responsibilities in one module would increase coupling and make testing, maintenance and future development more difficult.

### Decision

The application will separate responsibilities into three layers:

1. **Integration layer:** `app/integrations/youtube_client.py` handles communication with external services.
2. **Business logic layer:** `app/modules/trend_radar/service.py` processes retrieved data and implements TrendRadar operations.
3. **API layer:** `app/main.py` exposes application functionality through FastAPI endpoints.

### Consequences

- Each layer has a clearly defined responsibility.
- External integrations can be mocked during testing.
- Business logic can be tested independently of HTTP requests.
- API endpoints remain relatively small.
- Future modules can reuse shared integrations where appropriate.

### Trade-offs

This introduces more files and some additional architectural structure. However, the separation is justified because YouTube GIC is intended to grow into a multi-module application.

### Verification

The architecture is supported by tests covering the YouTube client, TrendRadar service behaviour and FastAPI endpoints.