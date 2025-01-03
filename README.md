# borg-offsite-backup: help back up Qubes VMs and ZFS file systems

This utility will back up any arbitrary file system (without any
guarantees of consistency) and any tree of ZFS datasets (with
full crash consistency guarantees) to a remote Borg server, which
is trivial to set up.

Thanks to Borg, backups are deduplicated, they are orders of magnitude
faster than regular `rsync` or `tar` backups, and they are encrypted.

The main difference with the `borg` CLI is that the host, user and
path to the backup are assumed.  You only deal in the name of the backup,
which is always and automatically selected to be the ISO date of the
day of the backup:


```
# creates :yyyy-mm-dd
borg-offsite-backup create
# lists archives
borg-offsite-backup list
# extracts path/to/file from ::yyyy-mm-dd
borg-offsite-backup extract ::yyyy-mm-dd path/to/file
```

## How is data structured in the backup?

While regular file systems are backed up with their normal structure,
ZFS volumes are backed up as big files under `/dev/zvol`.  The utility
makes no attempt to back up or restore qube metadata, but a full backup
of the root file system should save all the Qubes OS metadata files
needed to reconstruct qubes by hand.

Restoring individual files from a regular file system backup can be
accomplished with the command line:

```
borg-offsite-backup extract ::yyyy-mm-dd path/to/file
```

Restoring individual volumes to a zvol can be accomplished with the
command line:

```
# This assumes /dev/zvol/myvolume is the same size in bytes as the
# corresponding backed-up volume.
borg-offsite-backup extract --stdout ::yyyy-mm-dd dev/zvol/myvolume | dd of=/dev/zvol/myvolume bs=10M
```

## On the client

The Borg key will by default be stored in `~/.borg-offsite-backup.key`.
This is where the tool expects it to be.  Once you have set up the
server (see below), you should be able to initialize the repository
on the server by running `borg-offsite-backup init -v -e keyfile-blake2`
on the client.  **Back the Borg key up securely to a different machine.
Without it, you can never restore from your backup**.

You must also configure the client before initializing the repository.
We also recommend you store this configuration alongside the key in
your key backup.

Sample configuration `/etc/borg-offsite-backup.conf` for a Qubes OS
dom0 that has ZFS volumes backing the system's qubes:

```json
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
        "**/node_modules",
        "**/site-packages",
        "fm:*.log",
        "fm:*.pyc",
        "fm:*.pyo",
        "fm:*/__pycache__",
        "fm:*/.asdf",
        "fm:*/.aws",
        "fm:*/.cache",
        "fm:*/.cargo",
        "fm:*/.colima",
        "fm:*/.config/borg",
        "fm:*/.cups",
        "fm:*/.docker",
        "fm:*/.docker/*",
        "fm:*/.DS_store",
        "fm:*/.keychain",
        "fm:*/.lima/colima",
        "fm:*/.local/share/containers/*",
        "fm:*/.local/share/nvim",
        "fm:*/.local/share/Trash/*",
        "fm:*/.local/share/zinit",
        "fm:*/.mono",
        "fm:*/.mypy_cache",
        "fm:*/.npm",
        "fm:*/.npm",
        "fm:*/.pyenv",
        "fm:*/.rustup",
        "fm:*/.ssh/sockets",
        "fm:*/.terraform",
        "fm:*/.terraform.d",
        "fm:*/.tmp",
        "fm:*/.Trash-*",
        "fm:*/.Trash-*/*",
        "fm:*/.Trash",
        "fm:*/.Trash/*",
        "fm:*/.venv/*",
        "fm:*/.vim/plugged",
        "fm:*/.viminfo",
        "fm:*/.virtualenvs",
        "fm:*/.vscode/extensions",
        "fm:*/*/.cache",
        "fm:*/Applications",
        "fm:*/Caches",
        "fm:*/Downloads",
        "fm:*/Library",
        "fm:*/logs/*",
        "fm:*/node_modules",
        "fm:*/npm-global",
        "fm:*/Pictures",
        "fm:*/temp",
        "fm:*/tmp/*",
        "fm:*/venv/*",
        "var/cache/*/*",
        "var/lib/systemd/coredump",
        "var/tmp/*"
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

### Needed software

You'll need an SSH server running on the backup server, and you'll
need the `borgbackup` (also known as `borg`) package installed on
that machine.

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
