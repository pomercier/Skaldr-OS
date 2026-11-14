#!/usr/bin/env bash
# Start Calamares using the packages included in the Skaldr OS live image.
# Package signing and mirror initialization occur during installation;
# never destroy the live keyring just to launch an installer window.
set -Eeuo pipefail

log="${HOME:-/home/liveuser}/skaldr-install.log"
stage="preflight"
mkdir -p "$(dirname "$log")"
exec >> "$log" 2>&1

report_failure() {
    local status=$?
    # Preserve diagnostics locally; do not publish installation logs to paste.
    local session_log="${HOME:-/home/liveuser}/.cache/calamares/session.log"
    if [[ -r "$session_log" ]]; then
        cp -- "$session_log" "${HOME:-/home/liveuser}/skaldr-calamares-session.log" || true
    fi
    if (( status == 0 )); then
        return
    fi
    printf '[Skaldr installer] Failed at %s (exit %s)\n' "$stage" "$status" >&2
    if command -v logger >/dev/null 2>&1; then
        logger -t skaldr-installer "Failed at ${stage}; exit ${status}; log ${log}" || true
    fi
    if command -v kdialog >/dev/null 2>&1; then
        kdialog --title "Skaldr OS installer" --error \
            "Calamares could not start. Stage: ${stage}; error: ${status}.

Last error:
$(tail -n 12 "$log" 2>/dev/null || true)

Full log: ${log}" || true
    fi
}
trap report_failure EXIT

printf '\n[Skaldr installer] Started at %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
printf 'ISO version: %s\n' "$(cat /etc/version-tag 2>/dev/null || printf 'development')"

# Make Calamares debug output available to CI through the existing QEMU
# serial socket only when explicitly marked by the disposable test VM.
# Never send installation logs from real machines or ordinary VMs.
if [[ -c /dev/ttyS0 && "$(cat /sys/class/dmi/id/product_name 2>/dev/null || true)" == "Skaldr-CI" ]]; then
    printf '[Skaldr CI] Starting serial diagnostics\\n'
    (tail -n +1 -F "$log" > /dev/ttyS0 2>/dev/null) &
fi

stage="check shipped packages"
command -v calamares >/dev/null
command -v pkexec-wrapper >/dev/null
command -v sudo >/dev/null
[[ -r /usr/share/calamares/settings_online.conf ]]
[[ -r /etc/calamares/modules/pacstrap.conf ]]
[[ -r /etc/calamares/modules/shellprocess.conf ]]

stage="select Calamares online configuration"
sudo install -Dm0644 /usr/share/calamares/settings_online.conf /etc/calamares/settings.conf

stage="prepare Skaldr KDE-only installer branding"
sudo /usr/local/bin/skaldr-cal-config

stage="integrate installed-system settings"
sudo /usr/local/bin/skaldr-cal-inject

stage="start Calamares GUI"
printf '[Skaldr installer] Launching Calamares with shipped packages\n'
pkexec-wrapper calamares -D6
