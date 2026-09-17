"""Marketing PM (Scribe extension) — deterministic Python cores.

The model never touches the captured-data path: these modules parse, resolve,
classify, compute, and store. The agent (Scribe Tick) does MCP I/O and
orchestration only, plus bounded conversational phrasing in replies.
Determinism is the tenet: same inputs, same rows, every run.
"""
