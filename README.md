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
    "keep_daily": 7,
    "keep_monthly": 3,
    "keep_weekly": 2
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

`keep_daily` defaults to 7, `keep_weekly` to 4, and `keep_monthly` to 12.
`borg-offsite-backup` does a prune after each backup automatically.
However, prunes do not recover disk space.  For that, you have to run
`borg-offsite-backup compact`.  Otherwise, your server will fill up
eventually.

### systemd units

Sample service unit:

```
[Unit]
Description=Back up using borg-offsite-backup
After=qubesd.service

[Service]
User=root
ExecStart=/usr/bin/borg-offsite-backup create
Environment="QUIET=yes"
```

Sample timer unit (which you must `systemctl enable` and `systemctl start`
after `systemctl daemon-reload`):

```
[Unit]
Description=Schedule Back up using borg-offsite-backup
After=network-online.target

[Timer]
OnCalendar=Mon,Tue,Wed,Thu,Fri,Sat,Sun 09:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

## On the server

You'll need a backup user on the backup server, which the client
will use to connect to the server and deposit backups into.

The backup server's login shell for the backup server's backup user
should be this program (note the use of `--restrict-to-repository`
whose argument you should change to be the actual backup path, and
you must also have the `nice`, `ionice`, `borgbackup` and `logger`
programs on the remote server):

```
#!/bin/bash -e
# typically stored as /usr/local/bin/backupsh with chmod +x
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

As you can see from the "shell", the backup will be stored in the
subfolder `qubes` of the server's user.

### Key authentication for clients

You should add the authorized key of the client (or, if a Qubes OS machine,
the authorized key of the `user` account of the backup VM) to the SSH
`~/.ssh/authorized_keys` of the user account used to back stuff up in the
server (remember that the folder `.ssh` must be mode 0700).  Here is a sample
`authorized_keys` file:

```
no-agent-forwarding,no-port-forwarding,no-X11-forwarding,no-pty,restrict,command="/usr/local/bin/backupsh" ssh-rsa <HERE GOES THE KEY> client@clienthost
```

That way, the client can execute the `borg serve` command that the shell
spawns on behalf of the client, but the client is not allowed to execute
any other command on the server.

**Strongly recommended**: create a separate user account per client.
It's more work, and you don't get to deduplicate across clients,
but it ensures a client cannot screw another client's backups.
