# Adding Adapters

Implement a new adapter by following `src/utp/adapters/raw_chat_adapter.ts`:
1. expose `kind`
2. carry `ToolRegistry`
3. add transcript capture array
4. register tool schemas

Keep implementation thin; conversion logic belongs in harness middleware.
