"""Create an actual browser-interaction demo video from the fully offline Moonfix app.

No fabricated lunar images: each frame is a screenshot of the real running UI,
with explicit narration text and scientific limitation footer. Final video is
assembled by ffmpeg, no external web or services.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image,ImageDraw,ImageFont
from io import BytesIO
import subprocess, shutil

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'demo_moonfix_2026.mp4'
FR=ROOT/'scripts/_demo_frames'
if FR.exists():shutil.rmtree(FR)
FR.mkdir(parents=True)
fontbase='/usr/share/fonts/truetype/dejavu/DejaVuSans'
F=ImageFont.truetype(fontbase+'.ttf',21)
B=ImageFont.truetype(fontbase+'-Bold.ttf',26)
T=ImageFont.truetype(fontbase+'.ttf',15)
phases=[
 ('Explore NASA lunar south-pole landing candidates','Real JPL DE441 + NASA LOLA · 10 sites · 72 sampled hours'),
 ('Compare a more illuminated site against flatter terrain','Visibility is not a single-objective landing decision'),
 ('Adjust required Sun + Earth horizon clearance','See how a conservative safety margin changes the ranking'),
 ('Scrub an actual dated ephemeris window','Each point is one hourly TDB observation, not an extrapolation'),
 ('Inspect all sites and transparent model limits','Decision-support prototype, NOT certified mission operations')]

def frame_caption(data,phase,idx,total):
    from PIL import Image
    raw=Image.open(BytesIO(data)).convert('RGB')
    # Actual browser viewport 1365x768 -> 1280x720 image; dark footer overlaid.
    image=raw.resize((1280,720),Image.Resampling.LANCZOS)
    draw=ImageDraw.Draw(image)
    draw.rectangle((0,615,1280,720),fill=(5,20,32))
    draw.rectangle((0,615,1280,619),fill=(101,226,198))
    draw.text((28,632),phases[phase][0],font=B,fill='#e7f7f9')
    draw.text((28,672),phases[phase][1],font=F,fill='#a3c2cd')
    draw.text((1190,685),f'{idx+1}/{total}',font=T,fill='#6f9daf')
    return image

def build():
    html=(ROOT/'index.html').read_text()
    phasesN=5;fps=3;seconds=5;frames_total=phasesN*fps*seconds
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        page=b.new_page(viewport={'width':1365,'height':768},device_scale_factor=1)
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(html,wait_until='load')
        for i in range(frames_total):
            ph=i//(fps*seconds);q=i%(fps*seconds)
            if ph==0:
                page.evaluate('window.MOONFIX_DEBUG.selectSite("South_84E40")')
                page.evaluate('(x)=>window.MOONFIX_DEBUG.selectHour(x)',12+q//2)
            elif ph==1:
                page.evaluate('window.MOONFIX_DEBUG.selectSite("South_83E60")')
                page.evaluate('(x)=>window.MOONFIX_DEBUG.selectHour(x)',14+q)
            elif ph==2:
                page.evaluate('window.MOONFIX_DEBUG.selectSite("South_84E40")')
                page.evaluate('(x)=>window.MOONFIX_DEBUG.setMargin(x)',[0,.5,1,2,3][min(4,q//3)])
                page.evaluate('window.MOONFIX_DEBUG.selectHour(38)')
            elif ph==3:
                page.evaluate('window.MOONFIX_DEBUG.setMargin(1)')
                page.evaluate('(x)=>window.MOONFIX_DEBUG.selectHour(x)',int(q*71/(fps*seconds-1)))
            else:
                page.evaluate('window.MOONFIX_DEBUG.selectSite("South_83E60")')
                page.evaluate('window.MOONFIX_DEBUG.setMargin(1)')
                # Smoothly scroll to real data comparison table.
                page.evaluate('(x)=>window.scrollTo(0,x)',int(q*650/(fps*seconds-1)))
            page.screenshot(path=str(FR/f'{i:04d}.png'))
            actual=Image.open(FR/f'{i:04d}.png').convert('RGB')
            temp=BytesIO();actual.save(temp,format='PNG')
            frame_caption(temp.getvalue(),ph,i,frames_total).save(FR/f'{i:04d}.png')
        if errors:raise RuntimeError('Browser script errors '+repr(errors))
        b.close()
    command=['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate',str(fps),'-i',str(FR/'%04d.png'),
             '-c:v','libx264','-preset','medium','-crf','23','-pix_fmt','yuv420p','-r','24','-movflags','+faststart',str(OUT)]
    subprocess.run(command,check=True)
    print('ACTUAL BROWSER DEMO',OUT,'bytes',OUT.stat().st_size,'duration',frames_total/fps,'s')
    shutil.rmtree(FR)

if __name__=='__main__':build()
