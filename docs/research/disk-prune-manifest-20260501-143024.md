# Disk prune manifest

Approved by Ahmed after disk reached 81% and safe disk-guard cleanup reclaimed 0B.

Deletion candidates:
- /root/openclaw-backups/openclaw-pre-update-20260501-020425.tar.gz
- /root/.openclaw/backups/manual-update-20260428
- /root/openclaw-snapshot-20260430

Kept intentionally:
- /root/openclaw-backups/targeted-pre-update-20260501-020938.tar.gz
- /root/openclaw-backups/openclaw-targeted-preupdate-2026-04-30_044759.tar.gz
- /root/openclaw-backups/runtime-patches-20260501-020425
- small service/config backups under /root/.openclaw/backups

Pre-delete evidence:
2026-05-01T14:30:24+03:00
Filesystem     Type  Size  Used Avail Use% Mounted on
/dev/sda1      ext4   96G   78G   19G  81% /

12G	/root/openclaw-backups/openclaw-pre-update-20260501-020425.tar.gz
6.5G	/root/.openclaw/backups/manual-update-20260428
5.1G	/root/openclaw-snapshot-20260430

drwxr-xr-x  3 root root        4096 Apr 28 16:03 /root/.openclaw/backups/manual-update-20260428
-rw-r--r--  1 root root 12178860579 May  1 02:13 /root/openclaw-backups/openclaw-pre-update-20260501-020425.tar.gz
drwx------ 38 root root        4096 Apr 30 21:45 /root/openclaw-snapshot-20260430

Post-delete verification:
2026-05-01T14:30:39+03:00
Filesystem     Type  Size  Used Avail Use% Mounted on
/dev/sda1      ext4   96G   55G   42G  57% /

removed /root/openclaw-backups/openclaw-pre-update-20260501-020425.tar.gz
removed /root/.openclaw/backups/manual-update-20260428
removed /root/openclaw-snapshot-20260430

498M	/root/openclaw-backups
338M	/root/.openclaw/backups
12G	/root/.openclaw
4.1G	/root/openclaw
