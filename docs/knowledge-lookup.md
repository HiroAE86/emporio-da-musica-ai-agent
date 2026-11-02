# Project knowledge lookup for AI agents

Use `tools/project_knowledge.py` to search the current project context without manually opening every source. It indexes Markdown under `docs/`, every supplied CSV row, and extracted text from the store policy PDF. Results include the source path and a row/chunk reference.

## Commands

From the repository root:

```sh
python3 tools/project_knowledge.py build
python3 tools/project_knowledge.py query "violões disponíveis até R$ 1000"
python3 tools/project_knowledge.py query "status do pedido tracking code" --limit 10
```

`query` builds the index automatically if it does not exist. Re-run `build` after changing docs, CSVs, or the policy PDF. The generated `docs/knowledge-index.json` is a local, reproducible index; it contains the source material, not model-generated answers.

## Guidance for agents

1. Search with the customer's actual terms and relevant synonyms/identifiers.
2. Ground the answer in returned excerpts. Keep operational CSV facts distinct from policy PDF rules.
3. Cite or preserve the returned source path/reference in internal traces.
4. If there are no results, say the project sources did not provide the answer; ask for needed information or hand off. Never fabricate missing facts.
5. Treat customer/order records as sensitive; only return data after the application verifies the requester.

This is a lightweight lexical lookup, not semantic retrieval. It can miss paraphrases and does not enforce authorization or generate final responses. The future agent must apply access controls before exposing customer/order information.
