import os,sys,tkinter as tk,re
from pathlib import Path
from unittest.mock import patch
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ui.main_page import MainPage
from tkinter import filedialog,messagebox
root=tk.Tk();app=MainPage(root);root.state('normal');root.update();app.ui.open_defect_concentration();root.update();view=app.ui.active_chart_view
for ext in ('png','pdf'):
 path=Path('test-evidence')/f'EXPORT-003-defect-concentration.{ext}'
 with patch.object(filedialog,'asksaveasfilename',return_value=str(path)),patch.object(messagebox,'showinfo',return_value=None):view.export(ext)
 if ext=='png':
  img=Image.open(path);img.verify();print('DEFECT_PNG_VALID',path.stat().st_size,Image.open(path).size)
 else:
  data=path.read_bytes(); pages=len(re.findall(rb'/Type\s*/Page\b',data));assert data.startswith(b'%PDF') and pages==1;print('DEFECT_PDF_VALID',len(data),pages)
root.destroy()
