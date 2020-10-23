import json

with open('american1.json') as f:
  data1 = json.load(f)
with open('indian1.json') as f:
  data2 = json.load(f)
with open('thai1.json') as f:
  data3 = json.load(f)
with open('mexican1.json') as f:
  data4 = json.load(f)
with open('italian1.json') as f:
  data5 = json.load(f)
with open('chinese1.json') as f:
  data6 = json.load(f)

data = dict()
for d in [data1, data2, data3, data4, data5, data6]:
    data.update(d)

print(len(data))
cnt = 0
for v in data.values():
    print(v)
    if cnt == 100:
        break
    cnt += 1

with open('restaurant_info1.json', 'w') as outfile:
    json.dump(data, outfile)
# print(data)