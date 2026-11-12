#!/usr/bin/env bash
# shellcheck disable=SC2034

iso_name="skaldr"
iso_label="SKALDR_$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y%m)"
iso_publisher="Skaldr OS <https://github.com/pomercier/Skaldr-OS>"
iso_application="Skaldr OS Live/Rescue System"
iso_version="$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y.%m.%d)"
install_dir="arch"
buildmodes=('iso')
## GRUB
bootmodes=('bios.syslinux' 'uefi.grub')
## systemd-boot
#bootmodes=('bios.syslinux' 'uefi.systemd-boot')
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'zstd' '-Xcompression-level' '12' '-b' '1M')
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/etc/gshadow"]="0:0:400"
  ["/root"]="0:0:750"
  ["/etc/polkit-1/rules.d"]="0:0:750"
  ["/etc/sudoers.d"]="0:0:750"
  ["/etc/sudoers.d/g_wheel"]="0:0:440"
  ["/root/.automated_script.sh"]="0:0:755"
  ["/root/.gnupg"]="0:0:700"
  ["/usr/local/bin/choose-mirror"]="0:0:755"
  ["/usr/local/bin/dmcheck"]="0:0:755"
  ["/usr/local/bin/calamares-online.sh"]="0:0:755"
  ["/usr/local/bin/remove-nvidia"]="0:0:755"
  ["/usr/local/bin/removeun"]="0:0:755"
  ["/usr/local/bin/removeun-online"]="0:0:755"
  ["/usr/local/bin/prepare-live-desktop.sh"]="0:0:755"
  ["/usr/local/bin/nvidia-module-loader"]="0:0:755"
  ["/usr/local/bin/pkexec-wrapper"]="0:0:755"
  ["/usr/local/bin/skaldr-artcraft"]="0:0:755"
  ["/usr/local/bin/skaldr-cal-inject"]="0:0:755"
  ["/usr/local/bin/skaldr-center"]="0:0:755"
  ["/usr/local/bin/skaldr-doctor"]="0:0:755"
  ["/usr/local/bin/skaldr-gpu-assistant"]="0:0:755"
  ["/usr/local/bin/skaldr-numlock"]="0:0:755"
  ["/usr/local/bin/skaldr-postinstall"]="0:0:755"
  ["/usr/local/bin/skaldr-profile"]="0:0:755"
  ["/usr/local/bin/skaldr-theme"]="0:0:755"
  ["/usr/local/bin/skaldr-version"]="0:0:755"
  ["/usr/local/bin/skaldr-welcome"]="0:0:755"
)
