"""Audit provenance: truthful build SHA, AI settings timeline, persistence.

These fields are provenance metadata, not authoritative Game Master state and
must not alter combat, RNG, replay hashes or old audit compatibility.
"""
from __future__ import annotations
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import pygame

from game.core.engine import Match
from game.core.audit import (configure_audit_context,record_ai_difficulty,
                             state_snapshot,make_report,verify_replay,write_last_match,
                             read_report,digest)
from game.core.build_info import build_identity
from game.core.persistence import save_match,load_match


class BuildInfoTests(unittest.TestCase):
    def test_ci_stamp_is_read_verbatim_and_validated_as_full_commit(self):
        with tempfile.TemporaryDirectory() as root:
            data=Path(root)/"data"
            data.mkdir()
            sha="1"*40
            (data/"BUILD_INFO.json").write_text(
                json.dumps({"commit":sha,"version":"0.9.18"}),encoding="utf-8")
            with patch("game.core.build_info._roots",return_value=[Path(root)]):
                result=build_identity()
        self.assertEqual(result,{"commit":sha,"source":"embedded-ci","version":"0.9.18"})

    def test_invalid_ci_stamp_is_not_presented_as_a_real_sha(self):
        with tempfile.TemporaryDirectory() as root:
            data=Path(root)/"data"
            data.mkdir()
            (data/"BUILD_INFO.json").write_text(
                json.dumps({"commit":"1234","version":"0.9.18"}),encoding="utf-8")
            with patch("game.core.build_info._roots",return_value=[Path(root)]),patch(
                "game.core.build_info.sys.frozen",True,create=True
            ):
                result=build_identity()
        self.assertIsNone(result["commit"])
        self.assertEqual(result["source"],"unknown")


class AuditContextTests(unittest.TestCase):
    def test_difficulty_timeline_and_sha_round_trip(self):
        game=Match(1918,audit_enabled=True)
        sha="c"*40
        orig={"commit":sha,"source":"embedded-ci","version":"0.9.18"}
        configure_audit_context(game,"normalny",build=orig,fresh=True)
        snap=digest(state_snapshot(game))
        record_ai_difficulty(game,"trudny")
        game.finish_mulligan(0,[])
        record_ai_difficulty(game,"łatwy")
        game.finish_mulligan(1,[])
        self.assertEqual(digest(state_snapshot(Match(1918,audit_enabled=True))),
                         digest(game.audit_initial))
        self.assertNotEqual(snap,digest(state_snapshot(game)))  # actual mulligan
        self.assertEqual([a["ai_difficulty"] for a in game.audit_actions],
                         ["trudny","łatwy"])
        game.phase="finished"
        game.winner=1
        package=make_report(game)
        env=package["payload"]["environment"]
        self.assertEqual(env["build"],orig)
        self.assertEqual(env["ai_difficulty_initial"],"normalny")
        self.assertEqual(env["ai_difficulty_current"],"łatwy")
        self.assertEqual([c["after_action_seq"] for c in env["ai_difficulty_history"]],[0,1])
        with tempfile.TemporaryDirectory() as folder:
            dest=Path(folder)/"last.json"
            write_last_match(game,dest)
            restored=read_report(dest)
        self.assertEqual(restored["environment"],env)

    def test_changing_difficulty_without_game_action_does_not_affect_match_snapshot(self):
        game=Match(1919,audit_enabled=True)
        configure_audit_context(game,"normalny",
                                build={"commit":"c"*40,"source":"embedded-ci","version":"0.9.18"},
                                fresh=True)
        initial=digest(state_snapshot(game))
        record_ai_difficulty(game,"normalny")
        self.assertEqual(game.audit_metadata["ai_difficulty_history"],[])
        record_ai_difficulty(game,"trudny")
        self.assertEqual(digest(state_snapshot(game)),initial)
        self.assertEqual(game.audit_metadata["ai_difficulty_history"][0]["from"],"normalny")

    def test_old_loaded_match_metadata_is_unknown_not_falsely_stamped(self):
        previous=Match(1920)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"save.json"
            save_match(previous,path)
            loaded=load_match(path)
            info=configure_audit_context(loaded,"normalny",fresh=False)
        self.assertIsNone(info["build"]["commit"])
        self.assertEqual(info["build"]["source"],"legacy-save")
        self.assertIsNone(info["ai_difficulty_initial"])

    def test_new_metadata_is_saved_and_loaded_without_reset(self):
        previous=Match(1921,audit_enabled=True)
        configure_audit_context(previous,"trudny",
                                build={"commit":"b"*40,"source":"embedded-ci","version":"0.9.18"},
                                fresh=True)
        record_ai_difficulty(previous,"normalny")
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"save.json"
            save_match(previous,path)
            loaded=load_match(path)
        context=configure_audit_context(loaded,"łatwy",fresh=False)
        self.assertEqual(context["ai_difficulty_initial"],"trudny")
        self.assertEqual(context["ai_difficulty_current"],"normalny")
        self.assertEqual(context["build"]["commit"],"b"*40)
        self.assertEqual(len(context["ai_difficulty_history"]),1)


class ClientDifficultyTests(unittest.TestCase):
    def setUp(self):
        from game.ui.app import SoloApp
        self.app_class=SoloApp
        pygame.init()
        with patch.object(SoloApp,"_desktop_resolution",return_value=(1536,864)):
            self.app=SoloApp()

    def tearDown(self):
        pygame.quit()

    def test_settings_changes_are_captured_and_restart_resets_match_timeline(self):
        app=self.app
        self.assertEqual(app.game.audit_metadata["ai_difficulty_initial"],"normalny")
        app.menu_page="settings"
        rect=pygame.Rect(535,322+2*81,420,61)
        app._menu_click(rect.center)
        self.assertEqual(app.ai.difficulty,"trudny")
        self.assertEqual(app.game.audit_metadata["ai_difficulty_current"],"trudny")
        self.assertEqual(len(app.game.audit_metadata["ai_difficulty_history"]),1)
        app.restart()
        self.assertEqual(app.game.audit_metadata["ai_difficulty_initial"],"trudny")
        self.assertEqual(app.game.audit_metadata["ai_difficulty_history"],[])

    def test_loaded_save_restores_ai_difficulty(self):
        app=self.app
        record_ai_difficulty(app.game,"trudny")
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"save.json"
            save_match(app.game,path)
            app.ai.difficulty="łatwy"
            app.menu_page="main"
            with patch("game.ui.app.load_match",side_effect=lambda:load_match(path)):
                app._menu_click(pygame.Rect(535,322+2*81,420,61).center)
        self.assertEqual(app.ai.difficulty,"trudny")
        self.assertEqual(app.game.audit_metadata["ai_difficulty_current"],"trudny")


if __name__=="__main__":
    unittest.main()
