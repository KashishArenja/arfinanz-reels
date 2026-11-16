import sys, json
from PIL import Image, ImageDraw, ImageFont
W,H=1080,1350; NAVY=(14,42,92); WHITE=(255,255,255); YEL=(255,208,0); GREY=(90,105,135)
FB="/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"; FM="/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"
F=lambda p,s: ImageFont.truetype(p,s)
def wrap(d,text,font,maxw):
    out=[]
    for para in text.split("\n"):
        line=""
        for w in para.split(" "):
            t=(line+" "+w).strip()
            if d.textlength(t,font=font)<=maxw: line=t
            else: out.append(line); line=w
        out.append(line)
    return out
def block(d,y,text,font,fill,maxw=900,gap=1.25,x=90):
    for l in wrap(d,text,font,maxw):
        d.text((x,y),l,font=font,fill=fill); y+=int(font.size*gap)
    return y
def slide(s,i,n,out):
    dark=s.get("dark",False)
    bg,fg,sub=(NAVY,WHITE,(200,212,235)) if dark else (WHITE,NAVY,GREY)
    im=Image.new("RGB",(W,H),bg); d=ImageDraw.Draw(im)
    y=200
    if s.get("tag"):
        f=F(FB,34); tw=d.textlength(s["tag"],font=f)
        d.rounded_rectangle((90,y,90+tw+40,y+62),12,fill=YEL); d.text((110,y+8),s["tag"],font=f,fill=NAVY); y+=110
    if s.get("num"):
        f=F(FB,150); d.text((90,y-30),s["num"],font=f,fill=YEL if dark else YEL); y+=150
    y=block(d,y,s["title"],F(FB,s.get("ts",80)),fg,gap=1.18)+30
    if s.get("big"):
        y=block(d,y,s["big"],F(FB,96),YEL if dark else NAVY,gap=1.1)+20
    for b in s.get("body",[]):
        if b.startswith("- "):
            f=F(FM,46); d.ellipse((92,y+22,108,y+38),fill=YEL); y=block(d,y,b[2:],f,fg,maxw=850,x=130)+14
        else:
            y=block(d,y,b,F(FM,46),fg)+18
    if s.get("foot"):
        block(d,1150,s["foot"],F(FM,24),sub,maxw=900)
    f=F(FB,28); d.text((90,1255),"@arfinanz",font=f,fill=sub)
    pg=f"{i}/{n}"; d.text((W-90-d.textlength(pg,font=f),1255),pg,font=f,fill=sub)
    if i<n: d.text((W-90-d.textlength("swipe »",font=F(FM,28)),1210),"swipe »",font=F(FM,28),fill=sub)
    im.save(out)
spec=json.load(open(sys.argv[1])); pre=sys.argv[2]
for i,s in enumerate(spec,1): slide(s,i,len(spec),f"{pre}_{i:02d}.png")
