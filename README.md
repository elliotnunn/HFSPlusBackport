Backporting HFS+ to Mac OS pre-8.1
==================================

This is a project to patch early versions of the "classic" Mac OS to support the [HFS+ ("Mac OS Extended")](https://en.wikipedia.org/wiki/HFS_Plus) filesystem. HFS+ succeeded Apple's previous Hierarchical File System (plain "HFS" or "Mac OS Standard"). It was salvaged from the failed Copland OS project and shipped with Mac OS version 8.1. Its main practical benefit to users was to save space and increase the maximum file count on large volumes, by allowing disk sectors to divided among >64k "allocation blocks".

Mac OS 8.1 and later provided equal support for HFS and HFS+, until the release of Mac OS X 10.6 over ten years later. Floppy disks were never formatted with HFS+, allowing easy data exchange in most cases (the overhead with HFS+ was also too large for a floppy disk). Unfortunately, no HFS+ support was ever provided for Mac OS 8.0 and earlier. On unsupported systems, HFS+ volumes would seem to contain only one document: "Where_have_all_my_files_gone?"

HFS+ was only relatively recently deprecated by macOS 10, and can still easily be read and written on a modern Mac. HFS, by contrast, was relegated to read-only status years ago, and likely will soon be removed altogether.


Inspiration
-----------
*Disk Tools PPC*

This remarkable Disk Copy image was included with the Mac OS 8.1 install CD, to allow a user to make her own minimal bootable rescue disk. It can read, write, format and repair HFS+ volumes.

Lacking the Appearace Manager and Finder 8, it looks and feels more like System 7. On closer inspection, I found that it actually is System 7! The contents of the resource fork reveal that it is based on System 7.5.5. It must then be possible for pre-8.1 Systems to support HFS+ without a complete rewrite. This is our goal.

"Disk Tools 1", on the same CD, contains a similar minimal System for 68k Macs only. This restriction is enforced by the "Disk Tools 1/2 Enabler" file on each Disk Tools floppy. The file is misnamed: it comprises minimal code to *disable* boot on opposite-architecture Macs, by complaining in a Deep Shit error box, "This Disk Tools disk will not work with this computer. Use the disk labelled Disk Tools 2/1".

"Disk Tools 1" and "Disk Tools PPC" are versioned "8.0DT" and "8.1DT" respectively, as if to avoid confusion about which System version will read HFS+ volumes. 


How HFS+ is implemented on Mac OS
---------------------------------

Essentially, HFS+ support is provided by 68k code in the 'ptch' -20217 resource. This patch uses the "File System Manager" hooks provided by the Mac Plus and later ROMs. Mac OS 8.1 executes the patch fairly early in the boot process from the 'boot' 3 resource. (At some point before Mac OS 9.2.2, this was moved even earlier into the 'boot' 2 resource.) Additional support comes from:

- 'ptch' 41, the Disk Cache
- 'boot' 22460
- 'PACK' 2, the Disk Initialization code, and related resources

The 'ptch' -20217 resource was actually used for "MountCheck" in System 7.6.x. Repurposing it for HFS+ might have been a diplomatic way to avoid requiring System Enablers ("Gibblies") to know about HFS in their own custom 'boot' 3 resources. Instead, they would "accidentally" load it while expecting to fsck the boot disk. Happily enough, this means that we do not need to patch any 'boot' resources in System 7.6.x.

The Text Encoding Converter extension is required on at least some systems, I suppose because HFS+ does encode Unicode filenames with UTF-16.


Tooling
-------
These the prerequisites to work on this project:

- Pretty much any Unix-like system
- Python 3
- My `macresources` and `machfs` Python packages: `python3 -m pip install macresources machfs`
- Mac OS emulators: [SheepShaver](https://www.emaculation.com/doku.php/sheepshaver) (PowerPC) and [Basilisk II](https://www.emaculation.com/doku.php/basilisk_ii)

The Python packages are used to manipulate Mac OS [resource forks](https://en.wikipedia.org/wiki/Resource_fork), which contain most of the code in the Mac OS System file, and to create bootable disk images to test our work.

This repository contains an anthology of Mac OS System files under `SampleSystems`, including the Disk Tools discussed above. Systems have been dumped into the Rez-like `.rdump` format preferred by `macresources`. All resources have been decompressed (an essay in itself) and placed in a canonical order for easy browsing/diffing. `resreport.txt` shows the evolution of the resources across these System versions, and clearly illustrates the similarity between System 7.5.5 and Disk Tools PPC.

Binary-level comparisions between resources are possible by combining `rfx` (installed with `macresources`) with C.J. Madsen's `vbindiff`. E.g.: `rfx vbindiff SampleSystems/7.6.1//boot/3 SampleSystems/8.1.0//boot/3`

`make.py`, heavily commented, combines resources from various System versions to make a a series of patched Systems under `TestImages.tmp`.

This project has, so far, not required any deep exploration of the HFS or HFS+ on-disk formats.


Status of HFS+ backporting
--------------------------

Mac OS Version      | 68k Status                             | PowerPC Status
--------------------|----------------------------------------|----------------------------------------
System 7.5.3        | Does not work (Basilisk II)            | Not tested in SheepShaver (bad System file?)
System 7.5.5        | Works with gtbl hacks and DT boot 3    | Works
Mac OS 7.6          | Works with gtbl hacks                  | Works
Mac OS 7.6.1        | Works with gtbl hacks                  | Works
Mac OS 8.0          | Works with gtbl hacks                  | Works
Mac OS 8.1          | Always worked                          | Always worked
