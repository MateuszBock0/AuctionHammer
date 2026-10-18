"""Acceptance tests: last-match audit contains every engine command and state diff."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")

from game.core.engine import Match
from game.core.audit import (state_snapshot, audit_path, write_last_match,
                             read_report, verify_replay, digest, make_report)
from game.core.ai import ComputerOpponent


class MatchAuditTests(unittest.TestCase):
    def test_audit_is_explicitly_enabled_in_real_client_only(self):
        ordinary=Match(1701)
        self.assertFalse(ordinary.audit_enabled)
        self.assertFalse(hasattr(ordinary,"audit_actions"))
        monitored=Match(1701,audit_enabled=True)
        self.assertTrue(monitored.audit_enabled)
        self.assertEqual(len(monitored.audit_actions),0)
        self.assertEqual(monitored.audit_initial,state_snapshot(monitored))
        self.assertEqual(len(monitored.event_journal),2)

    def test_all_mulligan_selections_and_illegal_moves_are_traced(self):
        game=Match(1702,audit_enabled=True)
        card=game.players[0].hand[0]
        game.mulligan_toggle(card)
        game.mulligan_toggle(card)
        with self.assertRaises(ValueError):
            game.attack("S01","hero:1")
        game.finish_mulligan(1,[])
        game.finish_mulligan(0,[])
        self.assertEqual([a["operation"] for a in game.audit_actions],
                         ["mulligan_toggle","mulligan_toggle",
                          "attack","finish_mulligan","finish_mulligan"])
        self.assertEqual(game.audit_actions[2]["result"],"error")
        self.assertEqual(game.audit_actions[2]["error"]["type"],"IllegalMove")
        self.assertIn("mulligan_done",game.audit_actions[-1]["changes"])
        self.assertEqual(game.audit_actions[-1]["after_sha256"],
                         digest(state_snapshot(game)))
        self.assertEqual(game.audit_actions[0]["event_seq_end"],2)

    def test_only_latest_finished_report_is_written_and_tamper_detected(self):
        with tempfile.TemporaryDirectory() as root:
            dest=Path(root)/"AuctionHammer-OSTATNI-MECZ.json"
            a=Match(1703,audit_enabled=True)
            a.phase="finished"
            a.winner=0
            write_last_match(a,dest)
            self.assertEqual(read_report(dest)["seed"],1703)
            b=Match(1704,audit_enabled=True)
            b.phase="finished"
            b.winner=1
            write_last_match(b,dest)
            contents=list(dest.parent.iterdir())
            self.assertEqual(contents,[dest])
            self.assertEqual(read_report(dest)["seed"],1704)
            raw=json.loads(dest.read_text(encoding="utf-8"))
            raw["payload"]["seed"]=1703
            dest.write_text(json.dumps(raw),encoding="utf-8")
            with self.assertRaises(ValueError):
                read_report(dest)

    def test_incomplete_game_cannot_be_exported(self):
        game=Match(1705,audit_enabled=True)
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"report.json"
            with self.assertRaises(ValueError):
                write_last_match(game,path)
            self.assertFalse(path.exists())

    def test_match_replay_and_engine_verification_from_real_full_game(self):
        game=Match(1706,audit_enabled=True)
        players=(ComputerOpponent(0),ComputerOpponent(1))
        for _ in range(1500):
            if game.phase=="finished":
                break
            if game.phase=="mulligan":
                for ai in players:
                    ai.step(game)
            elif game.pending is not None:
                players[game.pending.owner].step(game)
            else:
                players[game.active].step(game)
        self.assertEqual(game.phase,"finished","Benchmark should finish with actual engine")
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/"last.json"
            write_last_match(game,file)
            audit=read_report(file)
        self.assertTrue(audit["complete_from_start"])
        self.assertEqual(audit["summary"]["action_commands"],len(audit["actions"]))
        self.assertEqual(audit["event_journal"],game.event_journal)
        self.assertGreater(len(audit["actions"]),8)
        self.assertTrue(verify_replay(audit,
                                    lambda seed:Match(seed,audit_enabled=True)))


class ClientAuditTests(unittest.TestCase):
    def setUp(self):
        import pygame
        from game.ui.app import SoloApp
        self.pygame=pygame
        with patch.object(SoloApp,"_desktop_resolution",return_value=(1536,864)):
            self.app=SoloApp()

    def tearDown(self):
        self.pygame.quit()

    def test_completed_match_auto_exports_and_old_file_survives_new_start(self):
        with tempfile.TemporaryDirectory() as root:
            file=Path(root)/"AuctionHammer-OSTATNI-MECZ.json"
            with patch("game.ui.app.audit_path",return_value=file),patch(
                "game.ui.app.write_last_match",
                side_effect=lambda game:write_last_match(game,file)
            ):
                game=self.app.game
                self.assertTrue(game.audit_enabled)
                game.phase="finished"
                game.winner=0
                self.app._export_finished_audit_once()
                self.assertTrue(file.exists())
                initial=file.read_bytes()
                self.app._export_finished_audit_once()
                self.assertEqual(initial,file.read_bytes())
                self.app.restart()
                self.assertTrue(file.exists())
                self.assertIsNot(self.app.game,game)
                self.assertTrue(self.app.game.audit_enabled)
                self.assertIsNone(self.app._export_finished_audit_once())

    def test_finished_screen_audit_buttons_and_folder_instruction(self):
        app=self.app
        app.game.phase="finished"
        app.game.winner=0
        app._audit_notice="AUDYT ZAPISANY"
        app._draw_gameover()
        # Controls reside fully inside the visual result panel.
        panel=self.pygame.Rect(332,226,810,586)
        for r in (self.pygame.Rect(608,637,260,52),
                  self.pygame.Rect(392,702,325,46),
                  self.pygame.Rect(738,702,325,46)):
            self.assertTrue(panel.contains(r))
        app.menu_open=True
        app._draw_menu()


if __name__=="__main__":
    unittest.main()
