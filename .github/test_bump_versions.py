import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bump_versions as bv


def write(path, content):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


ANYVM_PY = (
    'VERSION = "x"\n'
    "DEFAULT_BUILDER_VERSIONS = {\n"
    '    "freebsd": "2.2.5",\n'
    '    "openbsd": "2.0.9",\n'
    "}\n"
)

WORKFLOW = (
    "name: Demo\n"
    "jobs:\n"
    "  test:\n"
    "    strategy:\n"
    "      matrix:\n"
    '        release: ["15.0", "15.1"]\n'
    '        arch: ["aarch64", ""]\n'
    '        sync: ["nfs", "scp"]\n'
    "  test-riscv:\n"
    "    strategy:\n"
    "      matrix:\n"
    '        release: ["15.1"]\n'
    '        arch: ["riscv64"]\n'
)


def rel(tag, release=None, arch="x86_64", desktop=False, build=True):
    return {"tag": tag, "release": release or tag, "arch": arch,
            "sync": "nfs,scp", "shutdown": "shutdown",
            "desktop": desktop, "build": build}


class Case(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        old = os.getcwd()
        self.addCleanup(os.chdir, old)
        os.chdir(tmp.name)
        write("anyvm.py", ANYVM_PY)
        write(os.path.join(".github", "workflows", "demo.yml"), WORKFLOW)
        write(os.path.join(".github", "coverage.allow"),
              "demo r1-build demo.yml\n")


class TestDefaultVersions(Case):
    def test_line_rewrite(self):
        n = bv.rewrite_default_version("freebsd", "2.2.6")
        self.assertTrue(n)
        text = open("anyvm.py").read()
        self.assertIn('    "freebsd": "2.2.6",', text)
        self.assertIn('    "openbsd": "2.0.9",', text)

    def test_unknown_os_is_not_invented(self):
        self.assertFalse(bv.rewrite_default_version("plan10", "1.0.0"))
        self.assertNotIn("plan10", open("anyvm.py").read())


class TestMatrixEdit(Case):
    def test_release_added_when_all_job_arches_ship(self):
        index = [rel("15.0"), rel("15.0", arch="aarch64"),
                 rel("15.1"), rel("15.1", arch="aarch64"),
                 rel("15.1", arch="riscv64"),
                 rel("15.2"), rel("15.2", arch="aarch64"),
                 rel("15.2", arch="riscv64")]
        changed, notes = bv.extend_matrices("demo", index)
        self.assertTrue(changed)
        text = open(".github/workflows/demo.yml").read()
        self.assertIn('release: ["15.0", "15.1", "15.2"]', text)
        self.assertIn('release: ["15.1", "15.2"]', text)

    def test_release_missing_on_one_arch_is_not_added(self):
        index = [rel("15.1"), rel("15.1", arch="aarch64"),
                 rel("15.1", arch="riscv64"),
                 rel("15.2"), rel("15.2", arch="aarch64")]  # no riscv64
        changed, notes = bv.extend_matrices("demo", index)
        self.assertTrue(changed)
        text = open(".github/workflows/demo.yml").read()
        # job with aarch64+"" gets it; riscv64 job does not
        self.assertIn('release: ["15.0", "15.1", "15.2"]', text)
        self.assertIn('release: ["15.1"]\n', text)
        self.assertTrue(any("riscv" in n for n in notes))

    def test_empty_arch_means_x86_64(self):
        index = [rel("15.0"), rel("15.1"),
                 rel("15.2")]   # x86_64 only
        changed, notes = bv.extend_matrices("demo", index)
        text = open(".github/workflows/demo.yml").read()
        # first job needs aarch64 too -> not added anywhere
        self.assertNotIn("15.2", text)
        self.assertTrue(notes)

    def test_desktop_and_variants_never_enter_matrices(self):
        index = [rel("15.0"), rel("15.0", arch="aarch64"),
                 rel("15.1"), rel("15.1", arch="aarch64"),
                 rel("15.1", arch="riscv64"),
                 rel("15.2-xfce", desktop=True),
                 rel("15.2-build")]
        changed, notes = bv.extend_matrices("demo", index)
        text = open(".github/workflows/demo.yml").read()
        self.assertNotIn("xfce", text)
        self.assertNotIn("15.2-build", text)

    def test_comments_and_excludes_survive_byte_identically(self):
        wf = (".github/workflows/demo.yml")
        extra = ("        exclude:\n"
                 "          # hand-written knowledge, never touched\n"
                 '          - release: "15.0"\n'
                 "            sync: rsync\n")
        write(wf, WORKFLOW + extra)
        before = open(wf).read()
        index = [rel("15.0"), rel("15.0", arch="aarch64"),
                 rel("15.1"), rel("15.1", arch="aarch64"),
                 rel("15.1", arch="riscv64")]
        changed, notes = bv.extend_matrices("demo", index)
        self.assertFalse(changed)
        self.assertEqual(open(wf).read(), before)

    def test_ordering_follows_natural_key(self):
        write(".github/workflows/demo.yml",
              "jobs:\n  t:\n    strategy:\n      matrix:\n"
              '        release: ["9.4", "10.0"]\n'
              '        arch: [""]\n')
        index = [rel("9.4"), rel("10.0"), rel("10.1")]
        bv.extend_matrices("demo", index)
        self.assertIn('release: ["9.4", "10.0", "10.1"]',
                      open(".github/workflows/demo.yml").read())

    def test_sentinel_default_release_list_is_never_touched(self):
        # freebsd's cross-host powerpc64 job: release: [""] means "the
        # default release only"
        wf = ("jobs:\n  t:\n    strategy:\n      matrix:\n"
              '        release: ["15.1"]\n'
              '        arch: [""]\n'
              "  hosts:\n    strategy:\n      matrix:\n"
              '        release: [""]\n'
              '        arch: ["powerpc64"]\n')
        write(".github/workflows/demo.yml", wf)
        index = [rel("15.1"), rel("15.1", arch="powerpc64"),
                 rel("15.2"), rel("15.2", arch="powerpc64")]
        bv.extend_matrices("demo", index)
        text = open(".github/workflows/demo.yml").read()
        self.assertIn('release: [""]\n', text)
        self.assertIn('release: ["15.1", "15.2"]', text)

    def test_empty_release_list_is_never_touched(self):
        wf = ("jobs:\n  t:\n    strategy:\n      matrix:\n"
              "        release: []\n"
              '        arch: [""]\n')
        write(".github/workflows/demo.yml", wf)
        changed, notes = bv.extend_matrices("demo", [rel("15.2")])
        self.assertFalse(changed)
        self.assertIn("release: []\n",
                      open(".github/workflows/demo.yml").read())

    def test_frozen_legacy_job_is_never_extended(self):
        # openbsd's testold: deliberately pinned old releases; only jobs
        # already tracking the file-wide newest release keep tracking
        wf = ("jobs:\n  test:\n    strategy:\n      matrix:\n"
              '        release: ["7.8", "7.9"]\n'
              '        arch: [""]\n'
              "  testold:\n    strategy:\n      matrix:\n"
              '        release: ["7.3", "7.4", "7.5", "7.6"]\n'
              '        arch: [""]\n')
        write(".github/workflows/demo.yml", wf)
        index = [rel("7.8"), rel("7.9"), rel("8.0")]
        bv.extend_matrices("demo", index)
        text = open(".github/workflows/demo.yml").read()
        self.assertIn('release: ["7.8", "7.9", "8.0"]', text)
        self.assertIn('release: ["7.3", "7.4", "7.5", "7.6"]\n', text)

    def test_variant_members_mirror_the_current_list(self):
        # ghostbsd's real matrix lists desktop variants next to the base
        wf = ("jobs:\n  t:\n    strategy:\n      matrix:\n"
              '        release: ["26.1", "26.1-xfce", "26.1-gershwin"]\n'
              '        arch: [""]\n')
        write(".github/workflows/demo.yml", wf)
        index = [rel("26.1"), rel("26.1-xfce", desktop=True),
                 rel("26.1-gershwin", desktop=True),
                 rel("27.0"), rel("27.0-xfce", desktop=True),
                 rel("27.0-gershwin", desktop=True)]
        changed, notes = bv.extend_matrices("demo", index)
        self.assertTrue(changed)
        self.assertIn('release: ["26.1", "26.1-xfce", "26.1-gershwin", '
                      '"27.0", "27.0-xfce", "27.0-gershwin"]',
                      open(".github/workflows/demo.yml").read())

    def test_unsorted_current_list_still_tracks(self):
        wf = ("jobs:\n  t:\n    strategy:\n      matrix:\n"
              '        release: ["26.1", "26.1-xfce"]\n'
              '        arch: [""]\n')
        write(".github/workflows/demo.yml", wf)
        # variant sorts above the base as a string; the job must still
        # count as tracking base 26.1 and receive 27.0
        index = [rel("26.1"), rel("26.1-xfce"), rel("27.0")]
        changed, notes = bv.extend_matrices("demo", index)
        self.assertTrue(changed)
        self.assertIn('"27.0"',
                      open(".github/workflows/demo.yml").read())


class TestAllowMirror(Case):
    def test_suffix_mirrored_onto_new_tag(self):
        added = bv.mirror_allow_lines("demo", ["r2", "r2-build"])
        self.assertEqual(added, ["demo r2-build demo.yml"])
        text = open(".github/coverage.allow").read()
        self.assertIn("demo r2-build demo.yml\n", text)

    def test_no_new_exemptions_invented(self):
        added = bv.mirror_allow_lines("demo", ["r2", "r2-gnome"])
        self.assertEqual(added, [])

    def test_existing_line_not_duplicated(self):
        bv.mirror_allow_lines("demo", ["r2-build"])
        again = bv.mirror_allow_lines("demo", ["r2-build"])
        self.assertEqual(again, [])
        text = open(".github/coverage.allow").read()
        self.assertEqual(text.count("demo r2-build demo.yml"), 1)


class Fetch(object):
    def __init__(self, table):
        self.table = table

    def __call__(self, url):
        for k, v in self.table.items():
            if k in url:
                return v
        raise bv.FetchError("HTTP 404")


class TestMain(Case):
    def _latest(self, tag):
        return json.dumps({"tag_name": tag}).encode()

    def _index(self, entries):
        return json.dumps({"os": "demo", "releases": entries}).encode()

    def test_noop_when_current(self):
        write("anyvm.py", 'DEFAULT_BUILDER_VERSIONS = {\n'
              '    "demo": "2.0.0",\n}\n')
        fetch = Fetch({"demo-builder/releases/latest": self._latest("v2.0.0")})
        self.assertEqual(bv.main(["--check"], fetch=fetch), 0)

    def test_bump_and_matrix_and_allow(self):
        write("anyvm.py", 'DEFAULT_BUILDER_VERSIONS = {\n'
              '    "demo": "2.0.0",\n}\n')
        index = [rel("15.0"), rel("15.0", arch="aarch64"),
                 rel("15.1"), rel("15.1", arch="aarch64"),
                 rel("15.1", arch="riscv64"),
                 rel("15.2"), rel("15.2", arch="aarch64"),
                 rel("15.2", arch="riscv64")]
        fetch = Fetch({
            "demo-builder/releases/latest": self._latest("v2.0.1"),
            "v2.0.1/releases.json": self._index(index),
        })
        self.assertEqual(bv.main([], fetch=fetch), 0)
        self.assertIn('"demo": "2.0.1"', open("anyvm.py").read())
        self.assertIn("15.2", open(".github/workflows/demo.yml").read())

    def test_missing_index_leaves_everything(self):
        write("anyvm.py", 'DEFAULT_BUILDER_VERSIONS = {\n'
              '    "demo": "2.0.0",\n}\n')
        fetch = Fetch({"demo-builder/releases/latest": self._latest("v2.0.1")})
        rc = bv.main([], fetch=fetch)
        self.assertEqual(rc, 1)
        self.assertIn('"demo": "2.0.0"', open("anyvm.py").read())

    def test_landed_out_written_on_bump(self):
        write("anyvm.py", 'DEFAULT_BUILDER_VERSIONS = {\n'
              '    "demo": "2.0.0",\n}\n')
        index = [rel("15.0"), rel("15.0", arch="aarch64"),
                 rel("15.1"), rel("15.1", arch="aarch64"),
                 rel("15.1", arch="riscv64")]
        fetch = Fetch({
            "demo-builder/releases/latest": self._latest("v2.0.1"),
            "v2.0.1/releases.json": self._index(index),
        })
        rc = bv.main(["--landed-out", "landed.txt"], fetch=fetch)
        self.assertEqual(rc, 0)
        self.assertIn("demo 2.0.0 -> 2.0.1",
                      open("landed.txt", encoding="utf-8").read())

    def test_landed_out_absent_on_noop_and_check(self):
        write("anyvm.py", 'DEFAULT_BUILDER_VERSIONS = {\n'
              '    "demo": "2.0.0",\n}\n')
        fetch = Fetch({"demo-builder/releases/latest": self._latest("v2.0.0")})
        self.assertEqual(bv.main(["--landed-out", "landed.txt"],
                                 fetch=fetch), 0)
        self.assertFalse(os.path.exists("landed.txt"))
        fetch2 = Fetch({
            "demo-builder/releases/latest": self._latest("v2.0.1"),
            "v2.0.1/releases.json": self._index([rel("15.1")]),
        })
        self.assertEqual(bv.main(["--check", "--landed-out",
                                  "landed.txt"], fetch=fetch2), 0)
        self.assertFalse(os.path.exists("landed.txt"))

    def test_check_writes_nothing(self):
        write("anyvm.py", 'DEFAULT_BUILDER_VERSIONS = {\n'
              '    "demo": "2.0.0",\n}\n')
        index = [rel("15.0"), rel("15.0", arch="aarch64"),
                 rel("15.1"), rel("15.1", arch="aarch64"),
                 rel("15.1", arch="riscv64")]
        fetch = Fetch({
            "demo-builder/releases/latest": self._latest("v2.0.1"),
            "v2.0.1/releases.json": self._index(index),
        })
        self.assertEqual(bv.main(["--check"], fetch=fetch), 0)
        self.assertIn('"demo": "2.0.0"', open("anyvm.py").read())


if __name__ == "__main__":
    unittest.main()
