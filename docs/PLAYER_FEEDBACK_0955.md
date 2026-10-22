# AuctionHammer — Gameplay responsiveness and combat clarity (0.9.55)

This UI-only change is intentionally independent of tutorials, cards, combat rules, AI decisions, auctions, RNG, saves, and signed audits.

## Player-visible changes

1. **Faster AI cadence:** consecutive AI commands wait 480 ms instead of 850 ms. The AI strategy, difficulty and command order are unchanged.
2. **Responsive attack targets:** hovering a currently legal attack target intensifies its cyan outline and displays the short action label `ATAKUJ`. No other target is suggested or enabled.
3. **Immediate attack recap:** after a confirmed attack, the bottom-right feedback panel prioritizes the latest committed HP and shield changes. The attacked target is listed before secondary retaliation or chained effects. At most two changes are displayed; further effects remain in **H — historia**.
4. **No stale combat backlog after an attack:** an attack clears the previously queued transient ticker messages, not the permanent event journal. The latest result remains for 2.4 s, then normal feedback resumes.
5. **Impact-aligned animation:** projectiles reach their target earlier and damage/heal/shield-break pulses are scheduled near impact; changing HP numbers are timed to match. Consumed shields render `TARCZA -N` even when zero HP is lost. All pulses reflect confirmed state deltas, with no speculative damage or invented kills.

## Acceptance / regression

- `python -m unittest discover -s tests -v`
- `tests/test_combat_feedback_0955.py`: actual attack recap, zero-damage shield block, non-death removal, delayed pulse survival, ticker precedence and journal integrity, hovered target rendering, AI pacing.
- Existing combat VFX regression `tests/test_signature_overlays_and_combat_0935.py` and journal UX tests remain authoritative.
- **Physical Windows visual acceptance PENDING:** confirm target highlights and two-line outcomes at 1366×768 and Full HD, DPI 100/125/150%; check high-frequency multi-hit combos, shield-only attacks and full-board battles.

The summary is a presentation of the last committed state transition and is **not** a per-hit combat simulator. For multi-step effects that complete inside a single Match command, the journal under **H** contains the fine-grained chronology.
