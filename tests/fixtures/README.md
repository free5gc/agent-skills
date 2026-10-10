# Fixtures

core/ contains unchanged official Makefile and three YAML configurations fetched
from free5gc/free5gc at ab1280ed772ad1900a0c6c00ac4f7852eb9d491d on 2026-10-10.
They contain no subscriber credentials. Sources: the commit-pinned config and
Makefile links in skills/free5gc-deploy/references/sources.md. Upstream repository
license: Apache-2.0. No fixture Makefile is ever executed. Tests copy fixtures to
a disposable path with spaces and create inert stand-ins for build artifacts.
Command mocks deliberately prohibit system/network mutations.
