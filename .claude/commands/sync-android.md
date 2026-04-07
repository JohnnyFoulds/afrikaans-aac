# sync-android

Sync `literature/mp3/` to the Android phone and trigger a MediaStore rescan so files appear in Samsung Music immediately.

**Usage:** `/sync-android`

No arguments. Run from repo root.

## What it does

1. `rsync` — transfers new/changed MP3s to `~/storage/music/unisa/` on the phone (port 8022, key auth)
2. `am broadcast MEDIA_SCANNER_SCAN_FILE` — tells Android to scan the unisa subfolder
3. `am broadcast MEDIA_MOUNTED` — triggers a full MediaStore remount so Samsung Music picks up the files

Both broadcasts are required — one alone does not reliably cause Samsung Music to update.

## Prerequisites (one-time setup)

- SSH key installed on phone: `ssh-copy-id -p 8022 u0_a356@192.168.1.101`
- `termux-setup-storage` run in Termux (grants `~/storage/music/` symlink)
- `rsync` installed in Termux: `pkg install -y rsync`

## Steps

```bash
bash scripts/sync-android.sh
```

When the skill is invoked, run the script and report how many files were transferred.
