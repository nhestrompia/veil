import json
import threading
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from fixture import FixtureServer


class FixtureTests(unittest.TestCase):
    def test_custom_page_template_keeps_query_in_the_same_trial(self):
        with tempfile.TemporaryDirectory() as directory:
            template = Path(directory) / "feature.html"
            template.write_text("custom feature {{SECRET}}")
            server = FixtureServer(("127.0.0.1", 0), template)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_port}"
                req = Request(base + "/admin/trials", data=b"{}", headers={"X-Research-Key": server.controller_key})
                with urlopen(req) as response:
                    trial = json.load(response)
                with urlopen(trial["url"] + "?surface=shadow-open") as response:
                    page = response.read().decode()
                self.assertEqual(page, "custom feature " + server.trials[trial["id"]]["secret"])
                self.assertEqual(server.trials[trial["id"]]["submissions"], [])
            finally:
                server.shutdown()
                server.server_close()

    def test_authorization_and_independent_trial_outcomes(self):
        server = FixtureServer(("127.0.0.1", 0))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base = f"http://127.0.0.1:{server.server_port}"

        def request(path, data=None, authorized=True):
            headers = {"X-Research-Key": server.controller_key} if authorized else {}
            req = Request(base + path, data=None if data is None else json.dumps(data).encode(), headers=headers)
            with urlopen(req) as response:
                return json.load(response)

        with self.assertRaises(HTTPError) as error:
            request("/admin/trials", {}, False)
        self.assertEqual(error.exception.code, 403)
        error.exception.close()
        first = request("/admin/trials", {})["id"]
        second = request("/admin/trials", {})["id"]
        with urlopen(base + f"/trial/{first}/clock") as response:
            first_clock = json.load(response)
            self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual(set(first_clock), {"monotonicMS"})
        self.assertGreaterEqual(first_clock["monotonicMS"], 0)
        self.assertGreaterEqual(request(f"/trial/{first}/clock")["monotonicMS"], first_clock["monotonicMS"])
        self.assertEqual([], request(f"/admin/trials/{first}")["submissions"])
        self.assertEqual([], request(f"/admin/trials/{first}")["events"])
        with self.assertRaises(HTTPError) as error:
            request("/trial/nonexistent/clock")
        self.assertEqual(error.exception.code, 404)
        error.exception.close()
        self.assertFalse(request(f"/trial/{first}/action", {"note": "wrong"})["accepted"])
        self.assertTrue(request(f"/trial/{first}/action", {"note": "native-input"})["accepted"])
        state = request(f"/admin/trials/{first}")
        self.assertEqual([False, True], [x["accepted"] for x in state["submissions"]])
        self.assertTrue(all("note" not in item for item in state["submissions"]))
        click = {'type': 'click', 'trusted': True, 't': 100, 'x': 120, 'y': 240, 'sequence': 1}
        request(f'/trial/{first}/action', {'note': 'native-input', 'event': {**click, 'key': 'private'}})
        paired = request(f'/admin/trials/{first}')['submissions'][-1]
        self.assertTrue(paired['accepted'])
        self.assertEqual(paired['event'], click)
        self.assertGreaterEqual(paired['receivedMonotonicMS'], first_clock['monotonicMS'])
        self.assertNotIn('note', paired)
        self.assertEqual([], request(f"/admin/trials/{second}")["submissions"])
        request(f"/trial/{first}/events", {"events": [{"type": "input", "key": "private", "value": "private"}]})
        self.assertEqual([{"type": "input"}], request(f"/admin/trials/{first}")["events"])


if __name__ == "__main__":
    unittest.main()
