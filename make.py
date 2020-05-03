#!/usr/bin/env python3

from functools import lru_cache
from os import path
from shutil import copyfile
import machfs
import machfs
import macresources
import os
import re
import shutil


@lru_cache()
def get_resource_fork(version):
    with open(path.join(SampleSystems, version) + '.rdump', 'rb') as f:
        return list(macresources.parse_rez_code(f.read()))

def get_resource(version, rtype, rid):
    if isinstance(rtype, str): rtype = rtype.encode('mac_roman')

    for resource in get_resource_fork(version):
        if (resource.type, resource.id) == (rtype, rid):
            return resource

    raise ValueError('not found: %r %r %r' % (version, rtype, rid))

# Some resource types can "own" other resources, which should be moved with them
def does_x_own_y(xtype, xid, yid):
    types = [b'DRVR', b'WDEF', b'MDEF', b'CDEF', b'PDEF', b'PACK']
    if yid & (1 << 15) and yid & (1 << 14):
        if xtype in types and types.index(xtype) == (yid >> 11) & 7:
            if (yid >> 5) & 0x3F == xid:
                return True
    return False



parent = path.dirname(__file__)
SampleSystems = path.join(parent, 'SampleSystems')
TestBed = path.join(parent, 'TestBed')

TestImages = path.join(parent, 'TestImages.tmp')
os.makedirs(TestImages, exist_ok=True)


with open(path.join(TestImages, 'Test-Blank.dsk'), 'wb') as f:
    for i in range(50):
        f.write(bytes(1024 * 1024))


base_versions = sorted(os.listdir(SampleSystems))
base_versions = [v for v in base_versions if re.match(r'^\d.\d.\d$', v)]

base_versions = [v for v in base_versions if int(v.replace('.', '')) < 810]


for base_version in base_versions:
    print('\n=== Patching System ' + base_version + ' ===')

    src_system = path.join(SampleSystems, base_version)

    dest_dir = path.join(TestImages, 'Test-' + base_version)
    dest_disk = dest_dir + '.dsk'
    dest_system = path.join(dest_dir, 'System Folder', 'System')

    try:
        shutil.rmtree(dest_dir)
    except FileNotFoundError:
        pass
    shutil.copytree(TestBed, dest_dir)

    # Copy the sample system, except the data fork
    for suffix in ['', '.idump']:
        copyfile(src_system + suffix, dest_system + suffix)

    # Get its resource fork, and copy it to another list so we don't ruin our cache
    the_resources = get_resource_fork(base_version)


    def place_resource(resource):
        the_len = len(the_resources)
        the_resources[:] = [r for r in the_resources if (r.type, r.id) != (resource.type, resource.id)]
        # if len(the_resources) < the_len:
        #     print(' replaced %s %s' % (repr(resource.type)[1:], resource.id))
        the_resources.append(resource)


    def copy_resource_and_subresources(version, rtype, rid):
        if isinstance(rtype, str): rtype = rtype.encode('mac_roman')

        for resource in get_resource_fork(version):
            if (resource.type, resource.id) == (rtype, rid):
                print('  Copying %s\'s %s %s' % (version, repr(resource.type)[1:], resource.id))
                place_resource(resource)
                break
        else:
            raise ValueError('not found: %r %r %r' % (version, rtype, rid))

        n_extra = 0
        for resource in get_resource_fork(version):
            if does_x_own_y(rtype, rid, resource.id):
                # print('+ sub-resource %s %s' % (repr(resource.type)[1:], resource.id))
                place_resource(resource)
                n_extra += 1
        if n_extra: print('    + %d owned resources' % n_extra)





    # Use ALL of these:
    print('These are the main HFS+ resources:')
    copy_resource_and_subresources('8.1.0', 'ptch', -20217)     # HFS+ patch
    copy_resource_and_subresources('8.1.0', 'boot', 22460)      # Seems to be a gatekeeper/bootloader??

    print('Disk Cache patch:')
    copy_resource_and_subresources('8.1.0', 'ptch', 41)         # Disk Cache patch

    print('Disk Init pack and things it uses:')
    copy_resource_and_subresources('8.1.0', 'PACK', 2)          # Disk Init (brings in several "owned" resources)
    copy_resource_and_subresources('8.1.0', 'p2u#', 0)          # Referenced by ptch, "Text Encodings"...
    copy_resource_and_subresources('8.1.0', 'STR#', -20574)     # "also known as" for various formats
    copy_resource_and_subresources('8.1.0', 'STR#', -20573)     # "Where_have_all_my_files_gone?"
    copy_resource_and_subresources('8.1.0', 'STR#', -20483)     # "There is a problem with the disk"
    copy_resource_and_subresources('8.1.0', 'TEXT', -20574)     # "This is the localized version of the HFSPlus Wrapper Read Me."
    copy_resource_and_subresources('8.1.0', 'TEXT', -20573)     # Wrapper readme contents


    # Use ONE of these to chain load 'ptch' -20217 (not required on 7.6.0 and later):
    MOVEW_B107_D0 = b'\x30\x3C\xB1\x07'
    if MOVEW_B107_D0 not in get_resource(base_version, 'boot', 2) and MOVEW_B107_D0 not in get_resource(base_version, 'boot', 3):
        # Mac OS 9 actually loads ptch -20217 in boot 2, which is more elegant, because unlike boot 3,
        # boot 2 is guaranteed not to be run from a separate gibbly

        print('Pre-7.6 needs some help to load ptch -20217:')
        copy_resource_and_subresources('9.2.2', 'boot', 2)
        # copy_resource_and_subresources('8.1.0', 'boot', 3)
        # copy_resource_and_subresources('DT_8.1_PPC', 'boot', 3)


    print('Rudimentary 68k support on Basilisk II\'s Quadra 900:')

    # These 3 resources have been identified by bisecting the different resources between 8.0 and 8.1
    # Use all of these for 68k, currently only Basilisk II's Quadra 900 (only works on 7.6.0/7.6.1/8.0):
    # (Still unclear what these do -- next step is to reverse-engineer the gusd/gtbl/gpch mechanism)

    # HFS+ not loaded if it is not changed (causes a crash on its own -- requires BOTH the below resources)
    copy_resource_and_subresources('8.1.0', 'gtbl', 6) # diff contents

    # Crash if it is not changed: illegal instruction (harmless on its own)
    copy_resource_and_subresources('8.1.0', 'gpch', 750) # diff contents

    # Error Type 41 if not present (harmless on its own)
    copy_resource_and_subresources('8.1.0', 'ptch', 42) # diff contents



    # Lastly, don't forget the Text Encoding Converter extension is essential to make this work





    the_resources.sort(key=lambda r: (r.type.decode('mac_roman'), r.id))
    with open(dest_system + '.rdump', 'wb') as f:
        f.write(macresources.make_rez_code(the_resources, ascii_clean=True))




    vol = machfs.Volume()
    vol.name = 'Test-' + base_version
    vol.read_folder(dest_dir, date=0xC0000000)
    vol = vol.write(10 * 1024 * 1024)


    with open(dest_disk, 'wb') as f:
        f.write(vol)
