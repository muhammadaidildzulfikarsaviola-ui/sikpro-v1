import os,sys,tempfile,tkinter as tk,re
from pathlib import Path
from unittest.mock import patch
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ui.main_page import MainPage
from tkinter import filedialog,messagebox
root=tk.Tk();app=MainPage(root);root.state('normal');root.update();app.ui.open_fishbone();root.update();view=app.ui.active_chart_view;view.model.effect='Seal leakage';view.model.add_cause(view.model.categories[0]['id'],'Pump seal leak after prolonged operation');view.refresh();root.update()
for mode in ('light','dark'):
 app.set_theme(mode);root.update()
 for ext in ('png','pdf'):
  suffix='' if mode=='light' else '-dark'
  path=Path('test-evidence')/f'EXPORT-{1 if ext=="png" else 2:03d}-fishbone{suffix}.{ext}'
  with patch.object(filedialog,'asksaveasfilename',return_value=str(path)),patch.object(messagebox,'showinfo',return_value=None):view.export(ext)
  if ext=='png':
   im=Image.open(path);im.verify();print('PNG_VALID',mode,path.stat().st_size,Image.open(path).size)
  else:
   data=path.read_bytes();pages=len(re.findall(rb'/Type\s*/Page\b',data));assert data.startswith(b'%PDF') and pages==1;print('PDF_VALID',mode,len(data),pages)
 expected=(32/255,40/255,51/255) if mode=='dark' else (1,1,1)
 assert view.figure.get_facecolor()[:3]==expected
root.destroy()
