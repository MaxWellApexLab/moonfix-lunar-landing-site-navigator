"""Generate a short, silent video from real browser interactions in Moonfix V2."""
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image,ImageDraw,ImageFont
from io import BytesIO
import subprocess,shutil
ROOT=Path(__file__).resolve().parents[1]
FR=ROOT/'scripts/_v2_frames'
OUT=ROOT/'demo_moonfix_v2_window_explorer.mp4'
PHASES=[
 ('REAL NASA SCIENCE','Lunar landing site comparison · 10 locations · 720 hourly observations'),
 ('PHYSICAL TRADE-OFFS','Sun and Earth clearances vs. 80 m LOLA local terrain slope'),
 ('MISSION-WINDOW EXPLORER','Linear and PCHIP event roots · joint clearance proxy, not flight certification'),
 ('SENSITIVITY + EXPORT','Choose skyline margin · export model-derived windows in CSV')]
if FR.exists():shutil.rmtree(FR)
FR.mkdir(parents=True)
f='/usr/share/fonts/truetype/dejavu/DejaVuSans'
font=ImageFont.truetype(f+'-Bold.ttf',24)
font2=ImageFont.truetype(f+'.ttf',18)

def overlay(raw,phase):
 im=Image.open(BytesIO(raw)).convert('RGB').resize((1280,720),Image.Resampling.LANCZOS)
 d=ImageDraw.Draw(im)
 d.rectangle((0,617,1280,720),fill=(4,18,30));d.rectangle((0,617,1280,622),fill=(87,225,191))
 d.text((23,638),PHASES[phase][0],font=font,fill='#edfaf8')
 d.text((23,676),PHASES[phase][1],font=font2,fill='#b1d1d6')
 return im

def main():
 html=(ROOT/'index.html').read_text()
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
  page=b.new_page(viewport={'width':1365,'height':768},device_scale_factor=1)
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(html,wait_until='load')
  fps=3;frames_each=12
  for i in range(4*frames_each):
   phase=i//frames_each;pos=i%frames_each
   if phase==0:
    page.evaluate('window.scrollTo(0,0)')
    page.evaluate('(h)=>window.MOONFIX_DEBUG.selectHour(h)',12+pos)
   if phase==1:
    page.evaluate('window.MOONFIX_DEBUG.selectSite("South_83E60")')
    page.evaluate('window.MOONFIX_DEBUG.setMargin(1)')
    page.evaluate('(h)=>window.MOONFIX_DEBUG.selectHour(h)',45+pos)
    page.evaluate('window.scrollTo(0,0)')
   if phase==2:
    page.evaluate('window.MOONFIX_DEBUG.selectSite("South_84E40")')
    page.evaluate('window.MOONFIX_DEBUG.setMargin(1)')
    page.locator('#windowExplorer').scroll_into_view_if_needed()
   if phase==3:
    page.evaluate('window.MOONFIX_DEBUG.selectSite("South_84E40")')
    page.evaluate('(m)=>window.MOONFIX_DEBUG.setMargin(m)',[0,.5,1,2,3][min(4,pos//3)])
    page.locator('#windowExplorer').scroll_into_view_if_needed()
   im=overlay(page.screenshot(),phase)
   im.save(FR/f'{i:04d}.png')
  if errors:raise RuntimeError(errors)
  b.close()
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','3','-i',str(FR/'%04d.png'),'-c:v','libx264','-preset','veryfast','-crf','23','-pix_fmt','yuv420p','-r','24','-movflags','+faststart',str(OUT)],check=True)
 print('Browser-recorded video:',OUT,'bytes',OUT.stat().st_size,'seconds',4*frames_each/3)
 shutil.rmtree(FR)
if __name__=='__main__':main()
