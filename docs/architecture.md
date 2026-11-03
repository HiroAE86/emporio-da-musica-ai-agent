# Technical decisions

The implementation and current limitations are summarized in the [README](../README.md). Without a model endpoint, the CLI retains deterministic keyword routing and local templates. With an endpoint, it uses a bounded OpenAI-compatible Chat Completions tool loop. Product tools read the CSV; policy tools read the generated Markdown wiki, with its source PDF retained in the repository. Endpoints that reject tools fall back to the earlier evidence-in-prompt call, then local answers.

Order lookups stay local. The customer must provide an order number, registered email, and registered phone. Only status and estimated delivery are returned, with the same generic message for unknown and mismatched identifiers. This is a basic demonstration check, not production authentication.

The order/customer rows and entered identifiers do not reach the model. Order verification runs locally and the tool returns only status and estimated delivery. Email and phone-like text is redacted from messages and in-memory chat history before model requests. Stock and orders are static snapshots. See the README for limitations.
