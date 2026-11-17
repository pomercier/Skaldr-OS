# Skaldr OS visual identity

## Canonical assets

- `assets/skaldr-logo.svg`: the source-quality, self-contained 1024 × 1024
  **vector logo**, designed for GitHub, documents, social profiles and larger
  renderings. It has a dark rounded backdrop to retain contrast in both light
  and dark viewers; paths and gradients stay crisp at any scaling factor.
- `assets/skaldr-logo.png`: **legacy 128 × 128 raster icon** retained for the
  currently deployed desktop/installer icon paths. Do **not** upscale it in a
  README or other large surface.
- `scripts/skaldr-make-wallpaper.sh`: produces independent 4K and ultrawide
  SVG wallpaper images in the staged ArchISO tree. Wallpaper layout and
  typography should not be produced by enlarging a small desktop icon.
- `scripts/skaldr-make-boot-splash.py`: creates bootloader-specific PNG
  backgrounds; the visual role differs from the full GitHub wordmark.

The new SVG is a high-resolution vector redraw inspired by the prior Nordic
raven emblem, retaining its silver feathers, cyan-purple arc, name and
Valknut-style knot. It does not import any external fonts, images or scripts.

## Export a large PNG locally

With Inkscape installed, run this **one command** at the repository root:

```sh
inkscape assets/skaldr-logo.svg --export-type=png --export-width=1024 --export-filename=skaldr-logo-1024.png
```

The SVG is the authoritative asset. Raster PNG exports are optional outputs
and do not need to be committed for the README to remain sharp. Do not replace
the 128 px system icon until the installed desktop, Calamares and boot-artwork
paths have separately been tested with the new asset.

## GitHub README guidance

Use `<img src="assets/skaldr-logo.svg" width="280" height="280">`.
Keep the image local to this repository: GitHub can render it without relying
on externally hosted files. CI checks that the README cannot accidentally
fall back to the 128 px PNG. Accessibility text and the SVG title/description
must be kept when editing the emblem.

## Bootloader screenshots in Calamares

The successful preview.2 Limine/Btrfs QEMU screenshots showed a leftover
CachyOS bootloader preview inside otherwise correctly branded Calamares.
This was an illustrative upstream static screenshot, not a runtime kernel or
loader identification error. The post-preview.2 installer now replaces all
four upstream bootloader screenshots with locally bundled, self-contained SVG
**illustrations** (GRUB, rEFInd, systemd-boot, Limine) before opening Calamares.
The bootloader names, descriptions, availability and installation logic are
kept unchanged; legitimate kernel package names and upstream credits remain.
The SVG cards explicitly say "Illustrative preview" and do not pretend to
be literal captures of the bootloader on real hardware.
