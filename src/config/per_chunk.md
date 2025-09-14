# Per-Chunk Analysis Prompt

You are processing part of a conference talk transcript. This is only one segment; produce complete outputs for this segment alone.

Output ONLY these four sections, markdown-formatted:

## 1) **Approach Script (3 sentences)**
- Verbatim hallway opener referencing one timestamped moment.
- Tone: warm, precise, curious.

## 2) **Five High-Signal Questions**
- Each ≤ 2 lines.
- Each tied to a timestamp or claim from this chunk.
- Outcome-oriented, decision-focused, no generic filler.

## 3) **Timeline Highlights (8–12 bullets)**
- `[mm:ss] + key moment` in order.

## 4) **Key Claims, Assumptions, Trade-offs**
- Three lists:
  - Claims (assertions)
  - Assumptions (constraints implied)
  - Trade-offs (gains vs sacrifices)

## Rules:
- Use only info in this chunk.
- Keep total length ≤ 400 words.