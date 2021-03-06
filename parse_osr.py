from textwrap import dedent
from math import *
import struct
import lzma
import time
import sys
import json
def parse_uleb128(f):
    result = 0
    shift = 0
    while True:
        byte = struct.unpack('<B', f.read(1))[0]
        result |= ((byte & 0x7f) << shift)
        if (byte & 0x80) == 0:
            break
        shift += 7

    return result

def parse_string(f):
    head = struct.unpack('<B', f.read(1))[0]
    if head == 0x00:
        return ''
    elif head == 0x0b:
        length = parse_uleb128(f)
        return f.read(length).decode()

MODES = ['osu!', 'Taiko', 'Catch the Beat', 'osu!mania']
SHORTMODS = [None, 'NF', 'EZ', None, 'HD', 'HR', 'SD', 'DT', 'RX', 'HT', 'NC',
             'FL', 'AO', 'SO', 'AP', 'PF', '4K', '5K', '6K', '7K', '8K', 'FI',
             'RD', None, 'TP', '9K', 'CO', '1K', '3K', '2K']
MODS = ['None', 'NoFail', 'Easy', 'NoVideo', 'Hidden', 'HardRock',
        'SuddenDeath', 'DoubleTime', 'Relax', 'HalfTime', 'NightCore',
        'Flashlight', 'Autoplay', 'SpunOut', 'Autopilot', 'Perfect', 'Key4',
        'Key5', 'Key6', 'Key7', 'Key8', 'FadeIn', 'Random', 'Cinema',
        'TargetPractice', 'Key9', 'Co-op', 'Key1', 'Key3', 'Key2']

def mods_to_str(n):
    i = 1
    s = set()
    while n:
        if n & 1:
            s.add(MODS[i])
        i += 1
        n >>= 1
    return ','.join(s)

def shortmods(n):
    i = 1
    s = ''
    while n:
        if n & 1:
            s += SHORTMODS[i]
        i += 1
        n >>= 1
    return s

def to_bin(n, size):
    s = ''
    while size:
        s = s + '01'[n & 1]
        n >>= 1
        size -= 1
    return s

def keys(n):
    k1 = n & 5 == 5
    k2 = n & 10 == 10
    m1 = not k1 and n & 1 == 1
    m2 = not k2 and n & 2 == 2
    smoke = n & 16 == 16
    return ' '.join([('K1' if k1 else '  '),
                     ('K2' if k2 else '  '),
                     ('M1' if m1 else '  '),
                     ('M2' if m2 else '  '),
                     ('SMOKE' if smoke else '     ')])

import matplotlib.pyplot as plt
path = input()
out = open(path+'.txt','w')

def dis(a,b,c,d):
    return sqrt(pow(a-c,2)+pow(b-d,2))
with open(path, 'rb') as f:
    mode, version = struct.unpack('<BI', f.read(5))
    beatmap_md5 = parse_string(f)
    player_name = parse_string(f)
    replay_md5 = parse_string(f)
    n300, n100, n50, ngeki, nkatu, nmiss, score, combo, perfect, mods = struct.unpack('<HHHHHHIH?I', f.read(23))
    life_bar = parse_string(f) # ms|life
    timestamp, length = struct.unpack('<QI', f.read(12))

    data = lzma.decompress(f.read(length)).decode()
    last_w = 0
    totalDis = 0
    suspiciousDis = 0
    prevx=None
    prevy=-0.1
    previousK1 = None
    previousK2 = None
    latestK1 = 0
    latestK2 = 0
    K1Interval = []
    K2Interval = []
    for record in data.split(','):
        if record:
            w, x, y, z = record.split('|')
            w, z = int(w), int(z)
            x, y = float(x), float(y)
            last_w = last_w + w
            
            out.write('%10d %10.4f %10.4f %s \n' % (last_w, x, y, keys(z)))
            if(keys(z).find('K1')!=-1):
                latestK1 = last_w
                if(previousK1==None): previousK1 = last_w
            else:
                if(previousK1!=None):
                    K1Interval.append(last_w-previousK1)
                    if(last_w-previousK1<30): print(last_w)
                    previousK1=None
                
            if(keys(z).find('K2')!=-1):
                latestK2 = last_w
                if(previousK2==None): previousK2 = last_w
            else:
                if(previousK2!=None):
                    K2Interval.append(last_w-previousK2)
                    previousK2=None 
                
            if(prevx!=None):
                if( (x==prevx or y==prevy) and (not(x==prevx and y==prevy))):
                    suspiciousDis += dis(x,y,prevx,prevy)
                totalDis += dis(x,y,prevx,prevy)
            prevx=x
            prevy=y
            
    out.write('total:'+str(totalDis) + ' suspicious:' + str(suspiciousDis) + ' percent:' + str(int(suspiciousDis/totalDis*100)) + '%\n')
    out.write('cheat Possibility:' + str(int(100-559.017*exp(-0.20118*suspiciousDis/totalDis*100))) + '%\n')
    out.write(dedent('''
        Game mode   : %s
        Version     : %d
        Beatmap MD5 : %s
        Player      : %s
        Replay MD5  : %s
        300s        : %d
        100s        : %d
        50s         : %d
        Gekis       : %d
        Katus       : %d
        Misses      : %d
        Score       : %d
        Combo       : %d
        Perfect     : %s
        Mods        : %s
        Life        : %s
        Timestamp   : %d
        Length      : %d
    ''') % (MODES[mode], version, beatmap_md5, player_name,
        replay_md5, n300, n100, n50, ngeki, nkatu, nmiss, score,
        combo, perfect, shortmods(mods), life_bar, timestamp, length))
        

K1Interval = sorted(K1Interval)
K2Interval = sorted(K2Interval)

out.write(json.dumps((K1Interval)) )  
out.write('\n')
out.write(json.dumps((K2Interval)) ) 
out.write('\n') 

lim=50    
stK1 = [ [5*n,0] for n  in range( min(K1Interval[-1]//5 +1,lim) ) ]
stK2 = [ [5*n,0] for n  in range( min(K2Interval[-1]//5 +1,lim) ) ] 
#print (stK1       )
for i in range(len(K1Interval)):
    #print(K1Interval[i])
    if(K1Interval[i]//5>=lim): break
    stK1[ K1Interval[i]//5 ][1] +=1
    
for i in range(len(K2Interval)):
    if(K2Interval[i]//5>=lim): break
    stK2[ K2Interval[i]//5 ][1] +=1
    
import matplotlib.pyplot as plt
x = [ p[0] for p in stK1 ]
y = [ p[1] for p in stK1 ]   
x2 = [ p[0] for p in stK2 ]
y2 = [ p[1] for p in stK2 ] 

plt.subplot(2,1,1)
plt.plot(x,y,'r')
plt.subplot(2,1,2)
plt.plot(x2,y2,'g')
plt.show()

out.write(json.dumps(sorted(stK1)))
out.write('\n')
out.write(json.dumps(sorted(stK2)) )  
out.close()





















