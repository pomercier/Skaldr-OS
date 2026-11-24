#!/usr/bin/env python3
"""Fail-closed fix for nested BootLoaderModel resets in official Calamares.

QStandardItemModel::clear() already emits modelReset. Upstream init()/update()
wrap clear() with beginResetModel/endResetModel and block signals, causing the
invalid nested reset warnings seen immediately before a BIOS installer SIGSEGV.
"""
from pathlib import Path
import argparse

INIT_OLD = """void
BootLoaderModel::init( const QList< Device* >& devices )
{
    beginResetModel();
    blockSignals( true );

    m_devices = devices;
    updateInternal();

    blockSignals( false );
    endResetModel();
}"""
INIT_NEW = """void
BootLoaderModel::init( const QList< Device* >& devices )
{
    // updateInternal() calls clear(), which already issues modelReset.
    m_devices = devices;
    updateInternal();
}"""
UPDATE_OLD = """void
BootLoaderModel::update()
{
    beginResetModel();
    blockSignals( true );
    updateInternal();
    blockSignals( false );
    endResetModel();
}"""
UPDATE_NEW = """void
BootLoaderModel::update()
{
    // Never nest a model reset around QStandardItemModel::clear().
    updateInternal();
}"""


def patch_source(source: str) -> str:
    if "clear();" not in source or "void\nBootLoaderModel::updateInternal()" not in source:
        raise ValueError("Unexpected upstream model: clear()/updateInternal() missing")
    for original, replacement in ((INIT_OLD, INIT_NEW), (UPDATE_OLD, UPDATE_NEW)):
        if source.count(original) != 1 or replacement in source:
            raise ValueError("Upstream BootLoaderModel changed: refusing unreviewed patch")
        source = source.replace(original, replacement)
    if "beginResetModel();" in source or "endResetModel();" in source:
        raise ValueError("Unexpected nested model reset remains")
    return source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    target = parser.parse_args().source
    fixed = patch_source(target.read_text(encoding="utf-8"))
    target.write_text(fixed, encoding="utf-8")
    print("PASS: nested BootLoaderModel reset fix applied to reviewed source")


if __name__ == "__main__":
    main()
