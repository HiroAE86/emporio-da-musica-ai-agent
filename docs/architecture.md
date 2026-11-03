# Technical decisions

The implementation and current limitations are summarized in the [README](../README.md). The CLI uses deterministic keyword routing, lexical product matching, direct PDF text extraction with `pypdf`, and an optional OpenAI-compatible chat endpoint. If no endpoint is configured or a model call fails, the CLI uses local templates where available.

Order lookups stay local. The customer must provide an order number, registered email, and registered phone. Only status and estimated delivery are returned, with the same generic message for unknown and mismatched identifiers. This is a basic demonstration check, not production authentication.

The order/customer data and entered identifiers do not reach the model. Product and policy questions, including their full message and retrieved evidence, are sent to the configured endpoint. Stock and orders are static snapshots. See the README for unsupported query types and other limitations.
