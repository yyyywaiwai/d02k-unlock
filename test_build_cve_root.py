import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class BuildCveRootTest(unittest.TestCase):
    def test_rejects_invalid_ndk_before_fetching_sources(self):
        script = Path(__file__).resolve().parent / "build_cve_root.sh"
        with tempfile.TemporaryDirectory() as directory:
            ndk = Path(directory)
            (ndk / "source.properties").write_text("Pkg.Revision = 29.0.14206865\n")
            (ndk / "ndk-build").write_text("#!/bin/sh\nexit 99\n")
            (ndk / "ndk-build").chmod(0o700)
            env = dict(os.environ, ANDROID_NDK_HOME=directory)
            result = subprocess.run(["bash", str(script)], env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("28.2.13676358 が必要", result.stderr)
        self.assertNotIn("作業ディレクトリ:", result.stdout)


if __name__ == "__main__":
    unittest.main()
