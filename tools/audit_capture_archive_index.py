"""Compare one index inside an archive with a local index without extracting files."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def compare(archive, member_name, local):
    listing=subprocess.run(['tar','-tf',str(archive)],capture_output=True,check=True,text=True).stdout.splitlines()
    matches=[name for name in listing if name.replace('\\','/').rsplit('/',1)[-1]==member_name]
    if len(matches)!=1: raise ValueError(f'Expected exactly one index, found {len(matches)}')
    data=subprocess.run(['tar','-xOf',str(archive),matches[0]],capture_output=True,check=True).stdout
    other=local.read_bytes()
    return {'archive':archive.as_posix(),'archive_entries':len(listing),'member':matches[0],
            'member_bytes':len(data),'member_sha256':hashlib.sha256(data).hexdigest(),
            'local':local.as_posix(),'local_sha256':hashlib.sha256(other).hexdigest(),
            'identical':data==other}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path)
    p.add_argument('member');p.add_argument('local',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=compare(a.archive,a.member,a.local)
    result['limitations']=['Only the index was compared; graphical members were not validated.',
                           'Archive listing and extraction use the system tar without writing extracted files.']
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Index identical:',result['identical'])
