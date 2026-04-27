# Example: fill gaps in a week

**User:** "Help me fill in last week — I think I missed some days."

**Claude's flow:**

1. Resolve "last week" → 2026-04-20 (Mon) through 2026-04-26 (Sun).
2. Resolve self → person id `7`.
3. `productive_search_time_entries(after="2026-04-20", before="2026-04-26", person_id="7", include=["service"])`.
4. Group by date. Result:

   | Date | Day | Minutes |
   |---|---|---|
   | 2026-04-20 | Mon | 480 |
   | 2026-04-21 | Tue | 0 |
   | 2026-04-22 | Wed | 240 |
   | 2026-04-23 | Thu | 480 |
   | 2026-04-24 | Fri | 0 |
   | 2026-04-25 | Sat | 0 |
   | 2026-04-26 | Sun | 0 |

5. Flag the gaps to the user: "Tuesday and Friday look empty, and Wednesday is half a day. Want to fill those?"
6. Ask one day at a time: "What did you work on Tuesday 2026-04-21?"
7. For each gap day, run the [Log yesterday's work](log-yesterday.md) flow with the corrected date.
8. After each successful log, mark the row as filled and move on.
9. End with a one-line summary: "Filled 3 entries; total now 32h for last week."

Don't volunteer to fill weekend days unless the user asks.
