# Example: log yesterday's work

**User:** "Log 1h30 on the Acme auth refactor from yesterday."

**Claude's flow:**

1. Resolve "yesterday" — today is 2026-04-27, so yesterday is 2026-04-26 (a Sunday). Flag this back to the user: "That's a Sunday — confirm you worked then?"
2. Once confirmed, search for the deal: `productive_list_deals(name="Acme")` — there's one match, deal id `42`, company "Acme Inc.".
3. List its services: `productive_list_services(deal_id=42)` — services are "Development" and "Project management". The user said "auth refactor" which sounds like development work; ask: "Should this go on the **Development** service?"
4. The user confirms.
5. Resolve self: `productive_list_people(email="kristian@primux.dk")` → person id `7`.
6. Translate "1h30" → 90 minutes.
7. Confirm: `Log 90min on "Development" (deal: Acme website) for 2026-04-26 — note: "auth refactor"?`
8. User says yes.
9. Call `productive_create_time_entry(date="2026-04-26", person_id="7", service_id="100", minutes=90, billable_minutes=90, note="auth refactor")`.
10. Respond: "Logged. Entry id 9123, 90min on Development (Acme website), 2026-04-26."
