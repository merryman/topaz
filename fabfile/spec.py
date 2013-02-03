from fabric.api import task, local

mspec = "bin/topaz spec/mspec/bin/mspec -t $(pwd)/bin/topaz"

@task
def run_specs():
    local("%s run -G fails spec/rubyspec/core" % mspec)

@task
def tag_specs():
    local("%s tag -G fails -f spec -V spec/rubyspec/core" % mspec)
