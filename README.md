# AuctionHammer

AuctionHammer is a turn-based fantasy card game for one player against a computer opponent. The current solo prototype follows **Game Master v19** and includes 70 unique starter cards, with one copy of each card in the shared pool. Auctions and card play costs are not part of this version.

## Play on Windows

Download the latest [Windows release](https://github.com/MateuszBock0/AuctionHammer/releases/latest), extract the `AuctionHammer` folder, and open **`URUCHOM_AUCTIONHAMMER.bat`**. The Windows release includes the game executable and its runtime dependencies. No separate Python installation is needed to play.

- **`URUCHOM_AUCTIONHAMMER.bat`** checks for a newer release and then starts the game. If the update check is unavailable, it uses the installed version.
- **`GRAJ_BEZ_INTERNETU.bat`** starts the installed version without checking for updates.
- **`AuctionHammer.exe`** starts the game directly.

Keep `AuctionHammer.exe` and the `_internal` directory together. An internet connection is needed to download updates, but not to play offline.

## Controls

- Select a card in your hand, then click your board to play it. You can also drag a card onto the board.
- Select one of your ready units, then choose an enemy unit or the opposing hero to attack.
- When a skill requires a target or mode, use the **selection panel on the right**. Eligible targets are highlighted on the board; a direct click works when there is only one available mode for that target.
- Press **1–8** to select a visible choice, or use the panel's navigation controls for additional choices.
- Press **I** to open a card's full description. Mouse wheel scrolls the description.
- Press **Space** to end your turn. Press **F11** to switch between fullscreen and your previous window size.
- Resize the window at any time using its borders. The battlefield and click targets stay aligned, with the original aspect ratio preserved.

Each card displays a large family-specific emblem, a prominently bolded effect quantity where applicable, and a separate green upgrade ribbon showing exactly what improves after every three completed own turns in hand. The full card description (I) highlights the scalable number in green bold, without confusing it with durations or attack limits.

Each card identifies its activation timing: **On Play, On Attack, On Death, End of Turn,** or **Passive** (these labels currently appear in Polish in the game interface). When an On Play effect has legal selectable options, choosing one is required; when no legal option exists, the card can still be played without resolving that effect.

## Display and scaling

On Windows, AuctionHammer detects the current desktop size at launch and opens a window that fits within the screen, leaving room for Windows UI such as the taskbar. The game supports Full HD and common 125% or 150% Windows display scaling. It also adapts to manually resized windows while keeping the entire board and controls visible.

For the largest game view, press **F11** to enter fullscreen. Press **F11** again to return to the previous window size. The game does not require a specific screen resolution and does not change the Windows scaling setting.

## Project files

| Path | Purpose |
| --- | --- |
| `game/` | Game engine, AI, and Pygame client |
| `data/` | Card catalogue and structured rule data |
| `assets/` | Card artwork and other game assets |
| `tests/` | Automated regression tests |
| `AUCTIONHAMMER_MASTER.md` | Canonical project specification and implementation notes |
| `docs/GAME_MASTER_v17.md` | Full v19 rules and card descriptions |
| `.github/workflows/` | Automated tests and Windows release build |

To work on the source code, open this folder in VS Code. Source development requires Python 3.11+ and the dependencies in `requirements.txt`. The packaged Windows game does not.

## Releases and contributions

Changes merged to `main` run automated tests and build a new Windows release through GitHub Actions. Published builds are available under [Releases](https://github.com/MateuszBock0/AuctionHammer/releases/latest).

The solo engine is an MVP. Some complex chains of simultaneous effects still require additional rules-validation tests. The rules in Game Master v19 take precedence over earlier prototype behaviour.

## Game Master v19 integration

The approved v19 card changes are now implemented in the executable: **S66** chooses Quick Attack for itself or one particular hand card, **S67** grants Double Attack to itself or a selected allied unit, **S79** is 2 ATK / 6 HP with its conditional second attack, and **S114/S115** have updated HP and self-only traits. This version also implements the v18/v19 death fallbacks (S20/S82/S90/S91), the one-time S105 aura armor, and per-turn S109 quality healing. The 70-card shared pool and no-auction MVP remain unchanged.

For the original, complete rules archive, see the project Game Master v19 source package. See also `docs/V19_INTEGRATION_AND_UI.md` for the integration mapping and tests.
