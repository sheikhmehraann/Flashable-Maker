#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ tests/test_gofile_resolution.py - Unit Tests for GoFile Token Generator & Resolver ⚡
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gofile_transfer.token_generator import TokenGenerator, token_generator
from gofile_transfer.resolvers.gofile import GoFileResolver
from gofile_transfer.resolvers.base import ResolvedURL


class TestGoFileTokenGenerator(unittest.TestCase):
    """Tests for the multi-tier TokenGenerator."""

    def test_wt_generation_format(self):
        sample_token = "f4c9c8a4-0e35-430b-9343-7f32a514d876"
        wt = token_generator.generate_wt(sample_token)
        self.assertIsInstance(wt, str)
        self.assertEqual(len(wt), 64, f"WT token should be a 64-character hex string, got: {wt}")
        # Verify hex format
        int(wt, 16)

    def test_node_eval_fallback(self):
        tg = TokenGenerator()
        sample_token = "test-token-12345"
        # Test Python SHA-256 fallback explicitly
        wt_py = tg._eval_with_python_sha256("", sample_token)
        self.assertIsNotNone(wt_py)
        self.assertEqual(len(wt_py), 64)


class TestGoFileResolver(unittest.TestCase):
    """Tests for URL extraction, handling, and parsing logic in GoFileResolver."""

    def setUp(self):
        self.resolver = GoFileResolver()

    def test_can_handle(self):
        self.assertTrue(self.resolver.can_handle("https://gofile.io/d/J4nM4YE3"))
        self.assertTrue(self.resolver.can_handle("https://gofile.io/c/AbcDeF"))
        self.assertTrue(self.resolver.can_handle("http://gofile.io/d/12345"))
        self.assertTrue(self.resolver.can_handle("gofile.io/d/xyz123"))
        self.assertFalse(self.resolver.can_handle("https://drive.google.com/file/d/123"))
        self.assertFalse(self.resolver.can_handle("https://sourceforge.net/projects/abc"))
        self.assertFalse(self.resolver.can_handle("https://mediafire.com/file/xyz"))

    def test_extract_content_id(self):
        self.assertEqual(self.resolver.extract_content_id("https://gofile.io/d/J4nM4YE3"), "J4nM4YE3")
        self.assertEqual(self.resolver.extract_content_id("https://gofile.io/c/Folder123"), "Folder123")
        self.assertEqual(self.resolver.extract_content_id("https://gofile.io/?c=QueryId123"), "QueryId123")
        self.assertEqual(self.resolver.extract_content_id("J4nM4YE3"), "J4nM4YE3")

    def test_extract_all_files_flat(self):
        mock_data = {
            "type": "folder",
            "children": {
                "file1": {
                    "type": "file",
                    "name": "firmware.zip",
                    "size": 5242880000,
                    "link": "https://store1.gofile.io/download/web/uuid/firmware.zip"
                },
                "file2": {
                    "type": "file",
                    "name": "checksum.md5",
                    "size": 64,
                    "link": "https://store1.gofile.io/download/web/uuid/checksum.md5"
                }
            }
        }
        files = self.resolver._extract_all_files(mock_data, "fake-token")
        self.assertEqual(len(files), 2)
        names = [f["name"] for f in files]
        self.assertIn("firmware.zip", names)
        self.assertIn("checksum.md5", names)

    def test_resolve_mocked(self):
        mock_data = {
            "type": "folder",
            "children": {
                "file1": {
                    "type": "file",
                    "name": "Infinix-GT-20-Pro-X6871-recovery.zip",
                    "size": 4294967296,
                    "link": "https://store-na-phx-1.gofile.io/download/web/uuid/Infinix-GT-20-Pro-X6871-recovery.zip"
                }
            }
        }

        with patch.object(self.resolver, '_get_account_token', return_value="mock-token-xyz"):
            with patch.object(self.resolver, 'fetch_content_data', return_value=mock_data):
                res: ResolvedURL = self.resolver.resolve("https://gofile.io/d/J4nM4YE3")
                self.assertEqual(res.filename, "Infinix-GT-20-Pro-X6871-recovery.zip")
                self.assertEqual(res.file_size, 4294967296)
                self.assertEqual(res.direct_url, "https://store-na-phx-1.gofile.io/download/web/uuid/Infinix-GT-20-Pro-X6871-recovery.zip")
                self.assertEqual(res.cookies.get("accountToken"), "mock-token-xyz")
                self.assertIn("Authorization", res.headers)


if __name__ == "__main__":
    unittest.main()
