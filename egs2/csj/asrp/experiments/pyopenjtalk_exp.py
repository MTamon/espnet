import pyopenjtalk  # type: ignore
import time

text = "えー研究によって示されています日本語だけでなく英語やドイツ語のＦ０パターンも良く近似できることも示されていますえーところが中国語においては各音節ごとに音調というものがありモデルの拡張が必要になります"

start = time.time()
for i in range(512):
    phones = pyopenjtalk.g2p(text)
# phones = pyopenjtalk.g2p(text)
stop = time.time()

start_d = time.time()
for i in range(512):
    phones = pyopenjtalk.g2p(text)
# phones = pyopenjtalk.g2p(text)
stop_d = time.time()

print(phones)
print(stop - start)
print(stop_d - start_d)
