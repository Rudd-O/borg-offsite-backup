# borg-offsite-backup: help back up Qubes VMs and ZFS file systems

Sample configuration `/etc/borg-offsite-backup.conf`:

```
{
    "backup_path": "/var/backups/dom0",
    "backup_server": "milena.dragonfear",
    "backup_user": "qubes_backup_dom0",
    "bridge_vm": "backup",
    "ssh_from": "user"
    "datasets_to_backup": [
        "tank/ROOT/os",
        "tank/home",
        "tank/varlibqubes",
        {"name": "tank/qubes/*/private", "glob": true},
        {"name": "tank/qubes/*-tpl/root", "glob": true}
    ],
    "exclude_patterns": [
        "var/lib/qubes/*/*/root-cow.img.*",
        "var/lib/qubes/*/*/private-cow.img.*",
        "var/lib/qubes/*/*/volatile.img",
        "var/lib/qubes/appvms/disp*",
        "*/.cache",
        "*/*/.cache",
        "var/cache/*/*",
        "*/.config/borg",
        "var/lib/systemd/coredump",
        "*/.Trash-*",
        "*/*/.Trash-*",
        "var/tmp/*",
        "tmp/*"
    ],
    "filesystems_to_backup": [
        "/boot",
        "/boot/efi"
    ],
}
```

The Borg key will by default be stored in `~/.borg-offsite-backup.key`.

The backup server's login shell for the backup server's backup user
should be this program (note the use of `--restrict-to-path` which
you should change to be the actual backup path, and you should also
have the `nice`, `ionice`, `borgbackup` and `logger` programs on
the remote server):

```
#!/bin/bash -e
logger -p local7.notice -t backupsh "Initiating backup access as user $USER from client $SSH_CLIENT assigned to $HOME/qubes"
ret=0
nice ionice -c3 borg serve --restrict-to-path /path/to/backup/directory || ret=$?
if [ "$ret" = "0" ] ; then
    logger -p local7.notice -t backupsh "Finished backup access for user $USER"
else
    logger -p local7.error -t backupsh "Error in backup access for user $USER -- return code $ret"
fi
exit $ret
```
