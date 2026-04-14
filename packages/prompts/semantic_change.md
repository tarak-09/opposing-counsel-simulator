You are summarizing a clause-level contract redline.

Return JSON only with this shape:
- summary: string
- changed_tokens_count: integer
- added_phrases: string[]
- removed_phrases: string[]

Original clause:
{{original_text}}

Revised clause:
{{revised_text}}

Focus on the legal/business meaning of the change, not line-by-line markup.
