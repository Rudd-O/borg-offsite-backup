# borg-offsite-backup: help back up Qubes VMs and ZFS file systems

## On the client

The Borg key will by default be stored in `~/.borg-offsite-backup.key`.

Sample configuration `/etc/borg-offsite-backup.conf` for a Qubes OS
dom0 that has ZFS volumes backing the system's qubes:

```
{
    "backup_path": "/var/backups/qubes_backup_dom0/backup",
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

Sample config file for a plain old bare metal machine that has
no ZFS datasets:

```
{
    "backup_path": "/var/backups/qubes_backup_machine/backup",
    "backup_server": "milena.dragonfear",
    "backup_user": "qubes_backup_machine",
    "ssh_from": "user"
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
        "/",
        "/boot",
        "/boot/efi"
    ],
}
```

With your config file similar to the above,
`borg-offsite-backup create` will automatically create a new backup
snapshot with the current date in YYYY-MM-DD format on the backup server.

## On the server

The backup server's login shell for the backup server's backup user
should be this program (note the use of `--restrict-to-repository`
whose argument you should change to be the actual backup path, and
you must also have the `nice`, `ionice`, `borgbackup` and `logger`
programs on the remote server):

```
#!/bin/bash -e
me=(basename "$0")
logger -p local7.notice -t "$me" "Initiating backup access as user $USER from client $SSH_CLIENT assigned to $HOME/qubes"
logger -p local7.notice -t "$me" "Original command (ignored): $SSH_ORIGINAL_COMMAND"
ret=0
nice ionice -c3 borg serve --debug --restrict-to-repository "$HOME"/backup || ret=$?
if [ "$ret" = "0" ] ; then
    logger -p local7.notice -t "$me" "Finished backup access for user $USER"
else
    logger -p local7.error -t "$me" "Error in backup access for user $USER -- return code $ret"
fi
exit $ret
```
