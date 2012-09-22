# How this works

The webapp displays data received by `git log` and other git commands. The users from the commits are associated with database users based on their eMail address.

For read/write permission control, the webapp writes a `command=$MINIGIT/gitserve $USER` option into the authorized\_keys file. The `gitserve` script can read out the user associated with the public key and redirect the git-receive-pack/git-upload-pack commands or reject them, based on their permissions found in the database.

**DO NOT EDIT THE AUTHORIZED_KEYS FILE MANUALLY**. The webapp will overwrite any changes anyway. The `gituser` will not be used for login, only for use with the webapp.

Git remote URLs will have this pattern:

    git://${gituser}@${yourserver}:${sshport}/${repo-slug}.git

The bare repositories will be created in the home directory of the git user. Each repository will have the "extionsion" .git at the folder name.
