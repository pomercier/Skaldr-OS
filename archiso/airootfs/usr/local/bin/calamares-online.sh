#!/usr/bin/env bash
# Start Calamares using the packages included in the Skaldr OS live image.
# Package signing and mirror initialization occur during installation;
# never destroy the live keyring just to launch an installer window.
set -Eeuo pipefail

log="${HOME:-/home/liveuser}/cachy-install.log"
stage="preflight"
mkdir -p "$(dirname "$log")"
exec >> "$log" 2>&1

report_failure() {
    local status=$?
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

stage="check shipped packages"
command -v calamares >/dev/null
command -v pkexec-wrapper >/dev/null
command -v sudo >/dev/null
[[ -r /usr/share/calamares/settings_online.conf ]]
[[ -r /etc/calamares/modules/pacstrap.conf ]]
[[ -r /etc/calamares/modules/shellprocess.conf ]]

stage="select Calamares online configuration"
sudo install -Dm0644 /usr/share/calamares/settings_online.conf /etc/calamares/settings.conf

stage="integrate installed-system settings"
sudo /usr/local/bin/skaldr-cal-inject

stage="start Calamares GUI"
printf '[Skaldr installer] Launching Calamares with shipped packages\n'
pkexec-wrapper calamares -D6
