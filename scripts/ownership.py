#!/usr/bin/env python3
"""Fail if you changed files owned by someone else. Used by scripts/ship.sh.
Usage: scripts/ownership.py <me> <file> [<file> ...]   (FORCE=1 downgrades errors to warnings)"""
import os, sys

def load(path="OWNERS"):
    rules = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            prefix, owner = line.split()[:2]
            rules.append((prefix, owner))
    return rules

def owner_of(path, rules):
    best, best_len = None, -1
    for prefix, owner in rules:
        match = path == prefix or (prefix.endswith("/") and path.startswith(prefix))
        if match and len(prefix) > best_len:
            best, best_len = owner, len(prefix)
    return best

def main():
    me, files = sys.argv[1], sys.argv[2:]
    rules = load()
    bad, unowned = [], []
    for f in files:
        o = owner_of(f, rules)
        if o is None:
            unowned.append(f)
        elif o != me:
            bad.append((f, o))
    for f in unowned:
        print(f"  note: no owner listed for {f} (allowed, but add it to OWNERS)")
    if bad:
        print(f"OWNERSHIP PROBLEM: you are {me} but changed files owned by others:")
        for f, o in bad:
            print(f"  {f}  (owner: {o})")
        print("Undo your change to those files, then amend and re-ship:")
        print("  edited file : git checkout origin/main -- <file>")
        print("  new file    : git rm -f <file>")
        print("  then        : git commit --amend --no-edit && ./scripts/ship.sh")
        print("Need the change? Ask the owner in the group chat with the exact lines.")
        if os.environ.get("FORCE") == "1":
            print("FORCE=1 set: continuing anyway. Tell the group chat NOW.")
            return 0
        return 1
    print("ownership ok")
    return 0

sys.exit(main())
