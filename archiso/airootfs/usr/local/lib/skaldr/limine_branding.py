"""Safely rebrand the installed Skaldr Limine menu after kernel regeneration.

Only collapse a legacy CachyOS group when its Linux boot entries are proven
functionally equivalent to the Skaldr ones. Never change paths or hashes.
"""
from pathlib import Path
import re

ROOT = re.compile(r"(?m)^/(?!/)[^\r\n]+$")
CHILD = re.compile(r"(?m)^[ \t]*//(?!/)[^\r\n]+$")
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
        name = match.group().lstrip()[2:].lstrip("+-").strip()
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
    # Every kernel in this installation must agree on the same root device
    # and Btrfs subvolume before any cmdline is copied from the old menu.
    # One valid root per entry is not enough: inconsistent kernels can boot
    # different filesystems and must never be marked reconciled.
    old_roots = {tuple(s for s in v["cmdline"][0].split()
                       if s.startswith("root=")) for v in old.values()}
    old_flags = {tuple(s for s in v["cmdline"][0].split()
                       if s.startswith("rootflags=")) for v in old.values()}
    if len(old_roots) != 1 or len(old_flags) != 1:
        return None
    verified_root = next(iter(old_roots))
    verified_flags = next(iter(old_flags))
    if (len(verified_root) != 1 or verified_root[0] == "root=" or
            len(verified_flags) > 1):
        return None
    for entry in new.values():
        tokens = entry["cmdline"][0].split()
        roots = tuple(s for s in tokens if s.startswith("root="))
        flags = tuple(s for s in tokens if s.startswith("rootflags="))
        if (roots and roots != verified_root) or (flags and flags != verified_flags):
            return None
    matches = list(CHILD.finditer(modern))
    rebuilt = [modern[:matches[0].start()]]
    for i, match in enumerate(matches):
        name = match.group().lstrip()[2:].lstrip("+-").strip()
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


def _validated_legacy_root_fallback(legacy, modern):
    """Find a consistent previous menu without claiming its images boot."""
    a, b = _entries(legacy), _entries(modern)
    if not a or not b or a.keys() != b.keys():
        return None
    roots = set()
    rootflags = set()
    for name, prior in a.items():
        before = prior["cmdline"][0].split()
        after = b[name]["cmdline"][0].split()
        root = [token for token in before if token.startswith("root=")]
        flags = [token for token in before if token.startswith("rootflags=")]
        if len(root) != 1 or root[0] == "root=" or len(flags) > 1:
            return None
        if any(token.startswith("root=") for token in after):
            return None
        if len(set(before)) != len(before) or len(set(after)) != len(after):
            return None
        if not set(after).issubset(set(before) | {"mitigations=off"}):
            return None
        roots.add(root[0])
        rootflags.add(tuple(flags))
    if len(roots) != 1 or len(rootflags) != 1:
        return None
    return "linux-cachyos" if "linux-cachyos" in a else next(iter(a))




def _installed_root_arguments(root):
    """Read Calamares' installed Btrfs root from fstab; never invent a UUID."""
    fstab = root / "etc/fstab"
    if not fstab.is_file() or fstab.is_symlink():
        return None
    entries = []
    for line in fstab.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 4 and parts[1] == "/":
            entries.append(parts)
    if len(entries) != 1:
        return None
    source, _, fstype, opts = entries[0][:4]
    if fstype != "btrfs":
        return None
    uuid = source.removeprefix("UUID=")
    if not source.startswith("UUID=") or not re.fullmatch(
            r"[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}", uuid):
        return None
    options = opts.split(",")
    subvol = [part for part in options if part.startswith("subvol=")]
    if len(subvol) != 1 or subvol[0] != "subvol=/@":
        return None
    return "root=UUID=" + uuid, "rootflags=subvol=/@"


def _recover_root_from_installed_fstab(root, modern):
    """Repair a rootless Skaldr menu from the actual installed fstab record.

    Never change hashed kernel paths or initramfs locations. Preserve the
    already-generated kernel options verbatim, but reject emergency-mode
    overrides and mismatched root or subvolume options.
    """
    required = _installed_root_arguments(root)
    entries = _entries(modern)
    if required is None or not entries:
        return None
    rootarg, flagarg = required
    matches = list(CHILD.finditer(modern))
    rebuilt = [modern[:matches[0].start()]]
    # limine-entry-tool legitimately generates BOOT_IMAGE=, loglevel=,
    # zswap.enabled= and hardware-specific flags. The previous five-token
    # allowlist rejected those real entries, leaving a rootless menu and
    # aborting an otherwise-completed Calamares installation.
    #
    # Only root= and rootflags= are added here, taken from the installed
    # UUID and subvolume in fstab. Preserve other generated flags untouched,
    # but do not turn an emergency/debug override into a "verified" menu.
    forbidden = {"single", "s", "1", "rescue", "emergency"}
    forbidden_prefixes = ("init=", "rdinit=", "systemd.unit=",
                          "rd.break", "break=", "rootfstype=")
    equivalent_btrfs_rootflags = {flagarg, "rootflags=subvol=@"}
    for i, match in enumerate(matches):
        name = match.group().lstrip()[2:].lstrip("+-").strip()
        tokens = entries[name]["cmdline"][0].split()
        if len(tokens) != len(set(tokens)):
            return None
        roots = [token for token in tokens if token.startswith("root=")]
        flags = [token for token in tokens if token.startswith("rootflags=")]
        if (len(roots) > 1 or len(flags) > 1 or
                (roots and roots[0] != rootarg) or
                (flags and flags[0] not in equivalent_btrfs_rootflags) or
                any(token in forbidden or token.startswith(forbidden_prefixes)
                    for token in tokens)):
            return None
        if not roots:
            tokens.append(rootarg)
        if not flags:
            tokens.append(flagarg)
        block = modern[match.end():
                       matches[i + 1].start() if i + 1 < len(matches)
                       else len(modern)]
        cmdline = re.compile(r"(?m)^([ \t]*cmdline:[ \t]*)[^\r\n]*$")
        if len(cmdline.findall(block)) != 1:
            return None
        block = cmdline.sub(lambda m: m.group(1) + " ".join(tokens),
                            block, count=1)
        rebuilt.extend((match.group(0), block))
    result = "".join(rebuilt)
    return result if _entries(result) else None


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
    # Even already-populated entries must agree with the installed filesystem.
    # Otherwise a plausible-looking stale root= could silently boot another
    # partition or a wrong Btrfs subvolume.
    installed = _installed_root_arguments(root)
    if installed is not None and modern_entries:
        rootarg, flagarg = installed
        for entry in modern_entries.values():
            tokens = entry["cmdline"][0].split()
            roots = [x for x in tokens if x.startswith("root=")]
            flags = [x for x in tokens if x.startswith("rootflags=")]
            if (len(roots) > 1 or len(flags) > 1 or
                    (roots and roots[0] != rootarg) or
                    (flags and flags[0] not in
                     {flagarg, "rootflags=subvol=@"})):
                raise RuntimeError(
                    "Skaldr Limine root arguments conflict with installed Btrfs fstab")
    fstab_repaired = False
    if not modern_entries or not all(
            len([token for token in entry["cmdline"][0].split()
                 if token.startswith("root=")]) == 1
            for entry in modern_entries.values()):
        # The installed fstab is Calamares' authoritative root mount record.
        # Unlike old boot entries, it need not share initramfs hashes.
        repaired = _recover_root_from_installed_fstab(root, sections[new])
        if repaired is not None:
            fstab_repaired = True
            print("Skaldr: reconstructed root arguments from installed Btrfs fstab",
                  flush=True)
        if repaired is None:
            repaired = (_recover_verified_root_arguments(sections[old], sections[new])
                        if old is not None else None)
        if repaired is None:
            # The two groups can legitimately have different initramfs hashes
            # after the final mkinitcpio refresh. Do not invent a root UUID or
            # let nonessential branding abort a completed installation when
            # a consistently rooted, previously generated fallback remains.
            # The QEMU cold-boot test must still prove this fallback boots.
            fallback = (_validated_legacy_root_fallback(sections[old], sections[new])
                        if old is not None else None)
            if fallback is None:
                # Preserve actionable evidence in the CI serial artifact.
                # Never silently rebrand a rootless menu as install-ready.
                print("Skaldr: Limine fstab root lookup: " + repr(installed),
                      flush=True)
                for label, block in zip(labels, sections):
                    entries = _entries(block)
                    if entries:
                        print("Skaldr: Limine " + label + " cmdlines: " +
                              repr([entry["cmdline"][0]
                                    for entry in entries.values()]), flush=True)
                    elif label in ("/+Skaldr OS", "/+CachyOS"):
                        # Capture the actual generated entry structure when
                        # the strict parser cannot recognize it. The CI serial
                        # log must contain enough evidence to fix the parser.
                        print("Skaldr: unparsed Limine " + label +
                              " section (first 120 lines):", flush=True)
                        for line in block.splitlines()[:120]:
                            print("Skaldr: limine-config: " + line, flush=True)
                raise RuntimeError("Skaldr Limine entries lack exactly one root= parameter; "
                                   "no safe fallback menu with consistent roots")
            header = _update_global(header, "default_entry", "CachyOS/" + fallback)
            for key, value in THEME.items():
                header = _update_global(header, key, value)
            revised = header + "".join(sections)
            if revised != data:
                cfg.write_text(revised, encoding="utf-8")
            # Leave the Snapper OS name untouched while relying on the
            # legacy group; never point snapshots to a rootless group.
            print("Skaldr: preserving rooted legacy Limine fallback; "
                  "Skaldr entries require further reconciliation", flush=True)
            return "legacy-preserved-rootless"
        sections[new] = repaired
        modern_entries = _entries(repaired)
        print("Skaldr: recovered root parameters from matching legacy boot images",
              flush=True)
    if old is not None and _same_boot_images_with_safe_cmdline(sections[old], sections[new]):
        sections.pop(old)
        status = "legacy-duplicate-removed"
    elif old is not None:
        status = ("legacy-preserved-verified-skaldr" if fstab_repaired
                  else "legacy-preserved-unverified")
    else:
        status = "already-skaldr"
    # Prefer the new group when its root and subvolume come from the installed
    # fstab. Keep the old fallback on disk until the cold-boot tests succeed.
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
