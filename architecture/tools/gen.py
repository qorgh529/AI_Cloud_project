# -*- coding: utf-8 -*-
import p1, p2, p3, p4
from lib import write_file
out = '/home/user/AI_Cloud_project/architecture/gcp-3tier-petclinic-architecture.drawio'
n = write_file(out, [p1.build(), p2.build(), p3.build(), p4.build()])
print('bytes:', n, '->', out)
