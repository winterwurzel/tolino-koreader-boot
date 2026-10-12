# tolino-koreader-boot

Boot a **Tolino on stock firmware 5.18 straight into [KOReader](https://koreader.rocks)**.
There's no launcher icon and no stock home screen first. The stock reader stays on the device
as a fallback.

> **Status: tested on one device**, a Tolino Vision Color running firmware 5.18.264769 with
> KOReader kobov5 v2026.07.1. Other 5.x Tolinos (Shine 5, Shine Color) and Kobo-branded 5.x
> devices run the same software and will probably work, but nobody has tested them. Read
> [Recovery](#recovery) before you start.

## Why

NickelMenu and NickelHook don't support the Qt6-based 5.x firmware, so the usual ways of
starting KOReader from the stock reader are missing there. KOReader itself runs fine on 5.18,
but the stock reader normally does three things at boot that KOReader depends on. Without
them, KOReader can't connect to Wi-Fi, can't share its drive over USB, and reboots when you
exit. The start script here does those three things itself (see [Details](#details)).

## What you need

- A Tolino or Kobo running firmware **5.x**.
- KOReader's **kobov5** build in `.adds/koreader`, from
  [KOReader releases](https://github.com/koreader/koreader/releases): unzip
  `koreader-kobov5-*.zip` and copy its `koreader` folder into `.adds/`. Don't use the plain
  `kobo` build; it's for firmware 4.x.

## Install

1. Download `tolino-koreader-boot.zip` from the
   [releases](https://github.com/winterwurzel/tolino-koreader-boot/releases).
2. Connect the reader to a computer and unzip the file onto the root of its drive. That adds
   `.kobo/Kobo.tgz` and `.adds/koreader-boot/`. Both folders are hidden on most systems.
3. Eject, then restart the reader. While the stock reader starts, the hook installs itself and
   restarts the reader once more on its own. After that you're in KOReader, and from now on
   the reader boots into KOReader. `Kobo.tgz` disappears once the reader has applied it.

Each install and uninstall is noted in `.adds/koreader-boot/install.log`.

## Getting to the stock reader

| How | Effect |
|---|---|
| KOReader menu → Exit → **Exit** | Stock reader until the next boot |
| Start the reader while it's **connected to a computer** | Stock reader for that boot. A charger or power bank doesn't count. |
| Create `.adds/koreader-boot/boot-stock` (an empty file) | Stock reader on every boot until you delete the file |

To restart KOReader itself, use menu → Exit → **Restart KOReader**. Plain Exit switches to
the stock reader.

## Uninstall

1. Create an empty file `.adds/koreader-boot/uninstall`, then restart.
2. The stock reader is back for good. Delete `.adds/koreader-boot/` if you like.

One file can't come back: `/usr/local/Kobo/memorylogger`, a diagnostic memory logger in the
stock firmware. The hook takes its place, because that's the program the firmware starts just
before the stock reader. After uninstalling, the hook stays there but does nothing. The next
firmware update or reinstall brings the original back.

## SSH (optional)

Put your public key(s) in `.adds/koreader-boot/authorized_keys`. The boot hook then starts
KOReader's bundled SSH server (dropbear) on port **2222**, for `root` with key login only.
This runs at every boot, independently of KOReader. If KOReader breaks, you can still get in
once the stock reader has connected to Wi-Fi. The server runs from `/tmp`, so it doesn't block
KOReader's USB storage mode.

Don't use KOReader's own SSH server on the same port while this one runs.

## Recovery

- **KOReader exits or crashes:** the stock reader takes over.
- **KOReader doesn't come up at all:** start the reader while it's connected to a computer.
  You get the stock reader and its USB connection. Then create `boot-stock` or `uninstall`.
- **Back to the stock reader from a shell:** `mv /usr/local/Kobo/nickel.real /usr/local/Kobo/nickel`.

## Details

`/etc/init.d/ota` unpacks `.kobo/Kobo.tgz` into `/usr/local/Kobo` at boot. Then `/etc/rc.local`
starts `memorylogger` and `nickel` (the stock reader) from there. The package contains two
scripts and no files from the firmware:

| File | Installed as | Does |
|---|---|---|
| [`src/memorylogger`](src/memorylogger) | `/usr/local/Kobo/memorylogger` | Boot hook: keeps the device's own `nickel` binary as `nickel.real`, installs the start script as `nickel`, handles `uninstall`, starts SSH |
| [`src/koreader-boot`](src/koreader-boot) | `/usr/local/Kobo/koreader-boot`, then `nickel` | Starts KOReader, or the stock reader in the cases above |

The hook also handles firmware updates: when an update brings a new `nickel` binary, the hook
keeps that one as `nickel.real` and reinstalls the start script.

What the stock reader normally does at boot, and what the start script does instead:

| Gap on 5.18 | Symptom without the fix | Fix |
|---|---|---|
| `koreader.sh` falls back to `PLATFORM=freescale`. The firmware's own detection gives `mt8113t-ntx`. | USB storage mode fails while loading i.MX modules, and the device powers off after 90 s | `PLATFORM` from `/usr/libexec/platform/utils.sh` |
| The stock reader loads `wmt_drv` and starts `wmt_loader` / `wmt_launcher` (MediaTek Wi-Fi firmware) | "Failed to connect to wpa_supplicant control socket" | Load and start them before KOReader |
| Outside the stock reader, `koreader.sh` reboots on exit unless a boot menu (`kbmenu`) runs | Exit reboots straight back into KOReader | Placeholder process; Exit hands over to the stock reader |
| The stock reader reads `/tmp/nickel-hardware-status` | udev and DHCP scripts can block writing to it | Removed before KOReader starts |
| The stock reader runs `bootcount-ctl reset` once it has started. At boot, `/etc/init.d/mount-userdata` increments the counter and checks `bootcount-ctl boot-ok` (fails at 4). | After 4 boots without the stock reader, the firmware shows its **factory-reset prompt** (a warning sign with a button). Tapping the button **wipes the device**. | `bootcount-ctl reset` as soon as KOReader's process runs |
| `koreader.sh` decides whether it was started from the stock reader with `pkill -0 nickel` | The start script, installed as `nickel`, gets killed along with everything it started | The start script re-executes itself as `sh` first |

The factory-reset prompt comes up before anything else starts, and as far as I know the only
way past it is the reset. So the counter has to be reset reliably. That's why the start script
does it as early as possible, and why it was tested across 7 consecutive boots. If a later
firmware changes this mechanism, check `/etc/init.d/mount-userdata` before installing.

Detecting a computer at boot reads `/sys/class/power_supply/bd71827_bat/charger_type`
(`SDP` = computer, `DCP` = charger). That path was checked on the Vision Color. On devices
without that file the computer check does nothing; the other fallbacks still work.

Logs: `/tmp/koreader-boot.log` (cleared at every boot).

## Build

```
python3 build.py    # dist/tolino-koreader-boot.zip
```

## License

MIT. Not affiliated with Tolino, Kobo/Rakuten or the KOReader project.
