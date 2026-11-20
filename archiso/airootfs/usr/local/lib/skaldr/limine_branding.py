"""Safely rebrand the installed Skaldr Limine menu after kernel regeneration.

Only collapse a legacy CachyOS group when its Linux boot entries are proven
functionally equivalent to the Skaldr ones. Never change paths or hashes.
"""
from pathlib import Path
import re

ROOT = re.compile(r"(?m)^/(?!/)[^\r\n]+$")
CHILD = re.compile(r"(?m)^//(?!/)[^\r\n]+$")
FIELD = re.compile(r"(?m)^[ \t]*([a-z_]+):[ \t]*([^\r\n]*)$")
THEME = {
    "interface_branding": "SKALDR OS  |  PERFORMANCE BY INTENTION",
    "interface_branding_colour": "1ad7ef",
    "interface_help_colour": "8be9fd",
    "interface_help_colour_bright": "c4f5ff",
    "term_background": "000c1425",
    "term_foreground": "e5edf7",
    "term_palette": "0c1425;ef7891;61d5b0;f6d48b;6aabfa;b59af5;1ad7ef;e5edf7",
}


def _entries(group):
    matches = list(CHILD.finditer(group))
    if not matches:
        return None
    result = {}
    for i, match in enumerate(matches):
        name = match.group()[2:].lstrip("+-").strip()
        block = group[match.end():matches[i + 1].start() if i + 1 < len(matches) else len(group)]
        fields = {}
        for field in FIELD.finditer(block):
            fields.setdefault(field.group(1), []).append(field.group(2).strip())
        if (not name or name in result or fields.get("protocol") != ["linux"] or
                len(fields.get("path", [])) != 1 or
                len(fields.get("cmdline", [])) != 1 or
                not fields.get("module_path")):
            return None
        result[name] = fields
    return result


def _same_boot_images_with_safe_cmdline(legacy, modern):
    a, b = _entries(legacy), _entries(modern)
    if not a or not b or a.keys() != b.keys():
        return False
    for name, old in a.items():
        new = b[name]
        if old["path"] != new["path"] or old["module_path"] != new["module_path"]:
            return False
        before = old["cmdline"][0].split()
        after = new["cmdline"][0].split()
        old_roots = [x for x in before if x.startswith("root=")]
        new_roots = [x for x in after if x.startswith("root=")]
        if (len(old_roots) != 1 or new_roots != old_roots or
                len(set(before)) != len(before) or
                len(set(after)) != len(after) or
                not set(before).issubset(set(after)) or
                set(after).difference(before) - {"mitigations=off"}):
            return False
    return True



def _recover_verified_root_arguments(legacy, modern):
    """Recover missing root flags only from exactly matching fallback images.

    Calamares may generate a rootless Skaldr group alongside a working
    CachyOS group for the very same kernel and initramfs hashes. Copy only
    the proven fallback command line plus the already-requested mitigations
    flag. Unknown kernel options or mismatched images are never accepted.
    """
    old, new = _entries(legacy), _entries(modern)
    if not old or not new or old.keys() != new.keys():
        return None
    matches = list(CHILD.finditer(modern))
    rebuilt = [modern[:matches[0].start()]]
    for i, match in enumerate(matches):
        name = match.group()[2:].lstrip("+-").strip()
        before = old[name]
        after = new[name]
        if (before["path"] != after["path"] or
                before["module_path"] != after["module_path"]):
            return None
        previous = before["cmdline"][0].split()
        current = after["cmdline"][0].split()
        roots_previous = [s for s in previous if s.startswith("root=")]
        roots_current = [s for s in current if s.startswith("root=")]
        if (len(roots_previous) != 1 or roots_previous[0] == "root=" or
                len(roots_current) > 1 or
                len(previous) != len(set(previous)) or
                len(current) != len(set(current))):
            return None
        block = modern[match.end():
                       matches[i + 1].start() if i + 1 < len(matches)
                       else len(modern)]
        if not roots_current:
            allowed = set(previous) | {"mitigations=off"}
            if not set(current).issubset(allowed):
                return None
            repaired = previous + [s for s in current if s not in previous]
            pattern = re.compile(r"(?m)^([ \t]*cmdline:[ \t]*)[^\r\n]*$")
            if len(pattern.findall(block)) != 1:
                return None
            block = pattern.sub(lambda m: m.group(1) + " ".join(repaired),
                                block, count=1)
        rebuilt.append(match.group(0))
        rebuilt.append(block)
    result = "".join(rebuilt)
    confirmed = _entries(result)
    if (not confirmed or
            any(len([s for s in entry["cmdline"][0].split()
                     if s.startswith("root=")]) != 1
                for entry in confirmed.values())):
        return None
    return result

def _update_global(header, key, value):
    pattern = re.compile(r"(?m)^" + re.escape(key) + r":[ \t]*[^\r\n]*$")
    if len(pattern.findall(header)) > 1:
        raise ValueError("Duplicate global Limine option: " + key)
    if pattern.search(header):
        return pattern.sub(lambda _: key + ": " + value, header, count=1)
    return header.rstrip("\n") + "\n" + key + ": " + value + "\n"


def _prepare_snapper(path):
    if path.is_symlink() or not path.is_file():
        return False
    original = path.read_text(encoding="utf-8")
    key = re.compile(r"(?m)^TARGET_OS_NAME[ \t]*=[ \t]*([^\r\n]*)$")
    found = key.findall(original)
    if len(found) > 1:
        raise ValueError("Duplicate TARGET_OS_NAME keys in Snapper config")
    if found:
        value = found[0].strip().strip('"\'')
        if value not in ("CachyOS", "Arch Linux", "Skaldr OS"):
            return False  # Preserve custom snapshot integrations.
        updated = key.sub('TARGET_OS_NAME="Skaldr OS"', original, count=1)
    else:
        updated = original.rstrip("\n") + '\nTARGET_OS_NAME="Skaldr OS"\n'
    return path, original, updated


def reconcile_limine_menu(root=Path("/")):
    """Return status without deleting an unverified boot entry or snapshot."""
    root = Path(root)
    if not (root / "etc/default/limine").is_file():
        return "not-limine"
    cfg = root / "boot/limine.conf"
    if cfg.is_symlink() or not cfg.is_file():
        raise RuntimeError("Limine config is missing or an unsafe symlink")
    data = cfg.read_text(encoding="utf-8")
    roots = list(ROOT.finditer(data))
    if not roots:
        raise RuntimeError("Limine has no bootable menu sections")
    header = data[:roots[0].start()]
    sections = [data[m.start():roots[i + 1].start() if i + 1 < len(roots) else len(data)]
                for i, m in enumerate(roots)]
    labels = [x.splitlines()[0] for x in sections]
    if labels.count("/+CachyOS") > 1 or labels.count("/+Skaldr OS") > 1:
        raise RuntimeError("Ambiguous duplicate Limine OS groups")
    old = labels.index("/+CachyOS") if "/+CachyOS" in labels else None
    new = labels.index("/+Skaldr OS") if "/+Skaldr OS" in labels else None
    if new is None:
        return "no-skaldr-group"  # Keep upstream's working fallback.
    modern_entries = _entries(sections[new])
    if not modern_entries or not all(
            len([token for token in entry["cmdline"][0].split()
                 if token.startswith("root=")]) == 1
            for entry in modern_entries.values()):
        repaired = (_recover_verified_root_arguments(sections[old], sections[new])
                    if old is not None else None)
        if repaired is None:
            raise RuntimeError("Skaldr Limine entries lack exactly one root= parameter; "
                               "no verified fallback kernel to recover from")
        sections[new] = repaired
        modern_entries = _entries(repaired)
        print("Skaldr: recovered root parameters from matching legacy boot images",
              flush=True)
    if old is not None and _same_boot_images_with_safe_cmdline(sections[old], sections[new]):
        sections.pop(old)
        status = "legacy-duplicate-removed"
    elif old is not None:
        status = "legacy-preserved-unverified"
    else:
        status = "already-skaldr"
    # Keep existing choice when duplicate comparison was inconclusive.
    if status != "legacy-preserved-unverified":
        preferred = "linux-cachyos" if "linux-cachyos" in modern_entries else next(iter(modern_entries))
        header = _update_global(header, "default_entry", "Skaldr OS/" + preferred)
    for key, value in THEME.items():
        header = _update_global(header, key, value)
    updated = header + "".join(sections)
    # Validate the Snapper configuration before writing the boot menu.
    snapper = (None if status == "legacy-preserved-unverified" else
               _prepare_snapper(root / "etc/limine-snapper-sync.conf"))
    if updated != data:
        cfg.write_text(updated, encoding="utf-8")
    if snapper:
        target, original, replacement = snapper
        if original != replacement:
            target.write_text(replacement, encoding="utf-8")
    return status
