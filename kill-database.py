#!/usr/bin/env python2

from minigit import db
from minigit.models import *

db.drop_all()
db.create_all()

opatut = User("opatut", "test01", False)
opatut.addEmail("opatutlol@aol.com", True, True)
opatut.addEmail("paulbienkowski@aol.com")
opatut.addPublicKey("ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDRUFLcksSX57IC7Z1yGWWYignX7tnn0c2EffImrZbUoZTtxpQPvsnkw191/NAb9ol8K0ndjLYtaaRIxYsXwAcLaT+/Cu0K+Jd7E+CKa1KzJJNhYsnEJIYH+JMFbBcq3IP+r5XI5E35SA0mjWlPHmqFDssotSPd9f0Q66OIy7MNscrJaNNUSauVkNVr/SlMpEHB0mpY0fZJZz0Qlqb2PV7OWvh332bMdM70+dl9CyxNRNruApq95gI+IUYac7gMqgtoFIsxojBvaETuMqqhcfwuc9wx++ezxqq2UgMV9KDGlv9rfrjPr+P3/ZhUD0afo75BalCLyEAVeYugCv8hRg+lD1IgT7oJy1WVPIKAHgM8KjqDKWUDBJRdnBokMQ/y8PEaGRBzpWk5YIWefDf901xosgi4L+DMr2fxb7wRJOLb88Y+MmBuaN5ODa6FGMo7Ql7xRwgbVleS+J46mr2HG7ITTSLvn5on7K3cAfvUQsFfcesYLoHGbL6Lf7VY7HxAEMxrj9QJyp3LWrHw7kTdxGsT34ZQCcbI4NM0h++LVer5yjlMgOM8yf5ehc6hMIj2s417HNBKWMeojyZG3ThvtmQmhvxVyrWdFhntNB0tB0RxMiINQEBHLV6S/OHg9TKEhcPn1csG8H2QjXf1k88cGjuFu6xzCam+0Hfk/2DDZmkRVQ== paul@newton")
db.session.add(opatut)

zetaron = User("zetaron", "test01", False)
zetaron.addEmail("fabian.stegemann@gmx.net", True, True)
zetaron.addPublicKey("ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC2YAj5i7PiANi0OuNEoi2DlPYVFhAN6pAOwm06bI1htIy2/Em0QLAHFuf5+v4Ty5AFTGdSAWK2zB3KDJOfEJ5GWgPkeIKo/MNzFD8BBYgbFC8y+jW6e0JrhaTiB6PJ0xbxepUZzqIp5NpL4i/BN3+8cCQf+Ny8J5P2tMPour03iSvsyFQAILnpThD0lljyW6a7Xc1+5ZSITLTHMfdxruyBhnUOuz8IcxHknKTwJSK1q7Yg5x3cpBz3K7IOLsnwMHSPhtPD1SuFxMUevbGYGr9A99R+zarghNZNXKCe0R7ui3l9frVLwSnMHW4/mKuQDKUMwNmpyHYpfwljTq0qnPlXNIxG46VIvfhmt9FiFNQWQQYIOCSMDIZAfLu9PJcjvHzVD5bZIMsQYfCeYAQz9IwGqhNIJKG8Cj7gFm5F7iAKHOo50wwAfZEChTGv6VWOQJmOTaBkRW6gnB/x39+WXhkYOISW/5BZYRQsUWUf9tnIBjml+cJX/7+hIUC/MG0AK+mknziISZW09gnrlD4BGZ1Fxarcv0owiK5fJy9c4KuBzBOwgvtC35XPDTlpxuqh/89b9fAoWEYjp6bW/AsWKtw6s8IpRWZzPDUBguXunjUAV16m+mgwFH2XJKM5zK1f/vJY+TXN2dpi0nL1ELztwe1SobsFQA9cq4VG1dIq0S8MlQ== fabian@zetarania")
db.session.add(zetaron)

test = Repository("Test Repository", "test")
db.session.add(test)
test.init()

db.session.commit()

test.setUserPermission(opatut, "read")
test.setUserPermission(zetaron, "read")

db.session.commit()
