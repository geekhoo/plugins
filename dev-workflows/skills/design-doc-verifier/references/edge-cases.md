# Edge cases

- **The doc is an AGENTS.md or CLAUDE.md**: These often contain behavioral instructions
  rather than features. Extract them as behavioral requirements and look for evidence in
  hooks, middleware, or comments that enforce those behaviors.
- **The doc has zero structure** (free prose): Extract every sentence that contains
  "will", "must", "should", "shall", "can", or present-tense capability claims.
- **The codebase is very large**: Focus searches on the most relevant subdirectory
  first (e.g., the feature branch folder or the module named after the feature).
- **A requirement is ambiguous**: Note the ambiguity in the Evidence column and mark
  as PARTIAL rather than guessing DONE. Gerald can clarify.
- **The design doc references another doc**: Offer to read the referenced doc too.
