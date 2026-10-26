# Режет PNG с тремя рисунками на верх / середину / низ двумя «швами»:
# кривая слева направо, которая обходит непрозрачные места (динамическое программирование)
import sys,os
from PIL import Image, ImageFilter
src,out=sys.argv[1],sys.argv[2]
os.makedirs(out,exist_ok=True)
H_OUT={'top':900,'mid':700,'bot':720}
K=4
def seam(p,w,h,y0,y1):
  INF=10**9
  cost=[[ (1000 if p[x,y] else 0) for y in range(h)] for x in range(w)]
  dp=[[INF]*h for _ in range(w)];bk=[[0]*h for _ in range(w)]
  for y in range(y0,y1):dp[0][y]=cost[0][y]
  for x in range(1,w):
    for y in range(y0,y1):
      best=INF;by=y
      for dy in(-2,-1,0,1,2):
        yy=y+dy
        if y0<=yy<y1:
          v=dp[x-1][yy]+abs(dy)
          if v<best:best=v;by=yy
      dp[x][y]=best+cost[x][y];bk[x][y]=by
  y=min(range(y0,y1),key=lambda yy:dp[w-1][yy]);path=[0]*w;hit=dp[w-1][y]//1000
  for x in range(w-1,-1,-1):path[x]=y;y=bk[x][y]
  return path,hit
report=[]
for f in sorted(os.listdir(src)):
  if not f.endswith('.png') or 'original' in f or 'before' in f:continue
  name=f[:-4];im=Image.open(os.path.join(src,f)).convert('RGBA');W,H=im.size
  sm=im.getchannel('A').resize((W//K,H//K)).point(lambda v:255 if v>24 else 0).filter(ImageFilter.MaxFilter(3))
  w,h=sm.size;p=sm.load()
  s1,h1=seam(p,w,h,int(h*.2),int(h*.5))
  s2,h2=seam(p,w,h,int(h*.5),int(h*.82))
  # фигура, которую задел шов, целиком уходит в ту часть, где её больше
  k2=2;m=im.getchannel('A').resize((W//k2,H//k2)).point(lambda v:255 if v>24 else 0);mw,mh=m.size;mp=m.load()
  lab=[[0]*mw for _ in range(mh)];cnt={};n=0
  side=lambda x,y:(0 if y<s1[min(x*k2//K,w-1)]*K else 1 if y<s2[min(x*k2//K,w-1)]*K else 2)
  for y in range(mh):
    for x in range(mw):
      if mp[x,y] and not lab[y][x]:
        n+=1;lab[y][x]=n;st=[(x,y)];c=[0,0,0]
        while st:
          cx,cy=st.pop();c[side(cx,cy*k2)]+=1
          for nx,ny in((cx+1,cy),(cx-1,cy),(cx,cy+1),(cx,cy-1)):
            if 0<=nx<mw and 0<=ny<mh and mp[nx,ny] and not lab[ny][nx]:lab[ny][nx]=n;st.append((nx,ny))
        cnt[n]=c.index(max(c))
  parts=[Image.new('RGBA',(W,H),(0,0,0,0)) for _ in range(3)];pp=[q.load() for q in parts];s=im.load()
  for x in range(W):
    a,b=s1[min(x//K,w-1)]*K,s2[min(x//K,w-1)]*K
    for y in range(H):
      if s[x,y][3]:
        L=lab[min(y//k2,mh-1)][min(x//k2,mw-1)]
        pp[cnt[L] if L else (0 if y<a else 1 if y<b else 2)][x,y]=s[x,y]
  info=[]
  for key,part in zip(['top','mid','bot'],parts):
    bb=part.getbbox()
    if not bb:info.append(key+':empty');continue
    part=part.crop(bb);hh=H_OUT[key]
    if part.height>hh:part=part.resize((round(part.width*hh/part.height),hh),Image.LANCZOS)
    part.save(os.path.join(out,f'{name}-{key}.webp'),quality=86,method=6);info.append(f'{key}:{part.size}')
  report.append(f'{name} cut-through:{h1},{h2} '+' '.join(info))
print('\n'.join(report))
