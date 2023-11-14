import sys
import pyopenjtalk  # type: ignore

for line in sys.stdin:
    phonemized = pyopenjtalk.g2p(line, kana=False)
    print(phonemized)
