import glob
import os

from fabric.api import task, local
from fabric.context_managers import lcd


class Test(object):
    def __init__(self, func, deps=[], needs_rpython=True, needs_rubyspec=False,
                 builds_release=False):
        self.func = func
        self.deps = deps
        self.needs_rpython = needs_rpython
        self.needs_rubyspec = needs_rubyspec
        self.builds_release = builds_release

    def install_deps(self):
        local("pip install --use-mirrors {}".format(" ".join(self.deps)))

    def download_rpython(self):
        local("wget https://bitbucket.org/pypy/pypy/get/default.tar.bz2 -O `pwd`/../pypy.tar.bz2")
        local("tar -xf `pwd`/../pypy.tar.bz2 -C `pwd`/../")
        [path_name] = glob.glob("../pypy-pypy*")
        path_name = os.path.abspath(path_name)
        with open("rpython_marker", "w") as f:
            f.write(path_name)

    def download_mspec(self):
        with lcd(".."):
            local("git clone --depth=100 --quiet https://github.com/rubyspec/mspec")

    def download_rubyspec(self):
        with lcd(".."):
            local("git clone --depth=100 --quiet https://github.com/rubyspec/rubyspec")

    def run_tests(self):
        env = {}
        if self.needs_rpython:
            with open("rpython_marker") as f:
                env["rpython_path"] = f.read()
        self.func(env)

    def build_release(self):
        local("python topaz/tools/make_release.py topaz.tar")
        # TODO: the part where we upload it somewhere.


@task
def install_requirements():
    t = TEST_TYPES[os.environ["TEST_TYPE"]]
    if t.deps:
        t.install_deps()
    if t.needs_rpython:
        t.download_rpython()
    if t.needs_rubyspec:
        t.download_mspec()
        t.download_rubyspec()


@task
def run_tests():
    t = TEST_TYPES[os.environ["TEST_TYPE"]]
    t.run_tests()


@task
def build_release():
    t = TEST_TYPES[os.environ["TEST_TYPE"]]
    if t.builds_release:
        t.build_release()


def run_own_tests(env):
    local("PYTHONPATH=$PYTHONPATH:{rpython_path} py.test".format(**env))


def run_rubyspec_untranslated(env):
    run_specs("bin/topaz_untranslated.py", prefix="PYTHONPATH=$PYTHONPATH:{rpython_path} ".format(**env))


def run_translate_tests(env):
    local("PYTHONPATH={rpython_path}:$PYTHONPATH python {rpython_path}/rpython/bin/rpython --batch -Ojit targettopaz.py".format(**env))
    run_specs("`pwd`/bin/topaz")
    local("PYTHONPATH={rpython_path}:$PYTHONPATH py.test --topaz=bin/topaz tests/jit/".format(**env))


def run_specs(binary, prefix=""):
    local("{prefix}../mspec/bin/mspec --config=topaz.mspec --format=dotted".format(
        prefix=prefix,
        binary=binary
    ))


def run_docs_tests(env):
    local("sphinx-build -W -b html docs/ docs/_build/")

TEST_TYPES = {
    "own": Test(run_own_tests, deps=["-r requirements.txt"]),
    "rubyspec_untranslated": Test(run_rubyspec_untranslated, deps=["-r requirements.txt"], needs_rubyspec=True),
    "translate": Test(run_translate_tests, deps=["-r requirements.txt"], needs_rubyspec=True, builds_release=True),
    "docs": Test(run_docs_tests, deps=["sphinx"], needs_rpython=False),
}
