import json
import unittest
from pathlib import Path

import pandas as pd

from scripts.data_collection import anchors

DATA = Path(__file__).resolve().parent.parent / "data"


class FakeResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass

    def json(self):
        return {"output": [
            {"type": "reasoning", "summary": []},
            {"type": "message", "content": [{"type": "output_text", "text": self.text}]},
        ]}


class FakeSession:
    """Records the request instead of calling the API (no key, no cost)."""

    def post(self, url, json, timeout):
        self.url, self.payload = url, json
        return FakeResponse('{"dimensao": "D", "texto_ancora": "um dois três"}')


class AnchorsTest(unittest.TestCase):
    def test_base_text_and_anchors_have_the_same_dimensions(self):
        base = anchors.read_base_text(DATA / "texto_base.csv")
        for name in ("ancoras_v1_50_palavras.csv", "ancoras_v2_100_palavras.csv", "ancoras_v3_150_palavras.csv"):
            preserved = pd.read_csv(DATA / name, sep=";", encoding="utf-8-sig")
            self.assertEqual(list(preserved["dimensao"]), list(base["dimensao"]), name)

    def test_request_of_the_original_run(self):
        session = FakeSession()
        result = anchors.generate_anchor(session, "D", "texto", "v1_50_palavras")
        self.assertEqual(result, json.loads('{"dimensao": "D", "texto_ancora": "um dois três"}'))
        self.assertEqual(session.url, anchors.API_URL)
        self.assertEqual(session.payload["model"], "gpt-5.4-mini")
        self.assertEqual(session.payload["max_output_tokens"], 50 * 4 + 200)
        self.assertIn("entre 45 e 60 palavras", session.payload["input"])


if __name__ == "__main__":
    unittest.main()
