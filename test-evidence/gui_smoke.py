import os, subprocess, sys, tempfile, tkinter as tk
from pathlib import Path
from unittest.mock import patch
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ui.main_page import MainPage
from ui.quality_tools import CauseEditorDialog
from ui.dialogs import position_dialog, _work_area
from tkinter import filedialog, messagebox
import logic.imr_chart as imr

appdata=tempfile.mkdtemp(prefix='sikpro-theme-restart-'); os.environ['APPDATA']=appdata
root=tk.Tk(); app=MainPage(root); root.state('normal'); root.geometry('1080x720+100+100'); root.update()
def record(name, obj): print(name,repr(obj),flush=True)
try:
    combos=[]
    for lang,mode,label in [('en','light','Data Input'),('en','dark','Data Input'),('id','dark','Masukan Data'),('id','light','Masukan Data')]:
        if app.current_lang != lang: app.set_lang(lang)
        app.set_theme(mode); root.update(); assert app.ui.workspace_title.cget('text')==label
        palette=app.theme_manager.palette
        assert root.cget('bg')==palette['window'] and app.sheet.sheet.ops.table_bg==palette['input']
        assert app.ui.context_panel.cget('bg')==palette['panel']
        assert app.ui.nav_buttons['data_input'].cget('bg')==palette['selected']
        combos.append((lang,mode,root.cget('bg')))
    record('I18N_COMBINATIONS',combos)
    app.set_lang('en');app.set_theme('light')
    app.sheet.set_sheet_data([['4']]+[[''] for _ in range(200)]);root.update()
    config=imr.IMRConfigPopup(app,app.sheet);config.column_var.set('C1');root.update();errors=[]
    with patch.object(imr.messagebox,'showerror',side_effect=lambda *a,**k:errors.append(a)):config.generate()
    assert config.winfo_exists() and config.column_var.get()=='C1' and errors
    record('DIALOG_VALIDATION',(config.winfo_exists(),errors[-1][1]))
    with patch.object(imr.messagebox,'showerror',side_effect=lambda *a,**k:errors.append(a)),patch.object(imr,'control_limits',side_effect=RuntimeError('injected chart failure')):config.generate()
    assert config.winfo_exists() and 'injected chart failure' in errors[-1][1]
    record('DIALOG_RUNTIME_FAILURE',(config.winfo_exists(),errors[-1][1]));config.destroy();root.update()
    app.sheet.set_sheet_data([[str(v)] for v in [10,11,9,12,10,13]]+[[''] for _ in range(195)]);root.update()
    config=imr.IMRConfigPopup(app,app.sheet);config.column_var.set('C1');root.update();config.generate();root.update()
    assert not config.winfo_exists() and len(app.analysis_objects)==1
    analysis=app.analysis_objects[0];view=app.ui.active_chart_view;sheet_snapshot=app.sheet.get_sheet_data()
    app.set_theme('dark');root.geometry('1250x820+110+90');root.update()
    from matplotlib._pylab_helpers import Gcf
    chart_faces=[manager.canvas.figure.get_facecolor() for manager in Gcf.get_all_fig_managers()]
    assert any(tuple(round(v,3) for v in face[:3])==(0.125,0.157,0.2) for face in chart_faces)
    record('IMR_CHART_THEME',chart_faces)
    app.set_theme('light');root.update()
    assert app.analysis_objects[0] is analysis and app.sheet.get_sheet_data()==sheet_snapshot
    record('DIALOG_GENERATE',(not config.winfo_exists(),len(app.analysis_objects),view.winfo_width(),view.winfo_height()))
    app.ui.open_fishbone();root.update();view=app.ui.active_chart_view;cause_id=view.model.add_cause(view.model.categories[0]['id'],'Pump seal leak');view.refresh()
    dialog=CauseEditorDialog(app,'Edit cause','Pump seal leak',lambda v:view._edit_cause(cause_id,v));root.update();dialog.editor.focus_force();dialog.editor.mark_set('insert','1.5');dialog.editor.event_generate('<KeyPress-BackSpace>');root.update();pending=dialog.editor.get('1.0','end-1c')
    app.set_theme('dark');root.update();assert dialog.editor.get('1.0','end-1c')==pending and dialog.editor.cget('bg')==app.theme_manager.palette['input'];dark=view.figure.get_facecolor()
    app.set_theme('light');root.update();dialog.save();root.update();assert view.model.causes[0].text==pending
    view.effect_var.set('Seal leakage');root.update();assert view.model.effect=='Seal leakage'
    second_id=view.model.add_cause(view.model.categories[0]['id'],'Alignment drift');view.refresh();view.listbox.selection_set(1);view.reorder_cause(-1)
    assert view.model.causes[0].id==second_id
    def choose_second_category():
        candidates=[w for w in root.winfo_children() if isinstance(w,tk.Toplevel) and hasattr(w,'choice')]
        if not candidates:
            root.after(10,choose_second_category);return
        candidates[0].choice.current(1);candidates[0]._ok()
    view.listbox.selection_clear(0,tk.END);view.listbox.selection_set(0);root.after(100,choose_second_category);view.move_cause()
    assert view.model.causes[0].category_id==view.model.categories[1]['id']
    view.listbox.selection_clear(0,tk.END);view.listbox.selection_set(0);view.delete_cause()
    assert all(c.id!=second_id for c in view.model.causes)
    record('FISHBONE_WORKFLOW',{'effect':view.model.effect,'edited_cause':view.model.causes[0].text,'moved_and_deleted':second_id not in [c.id for c in view.model.causes]})
    record('FISHBONE_THEME',(pending,view.model.causes[0].text,dark,view.figure.get_facecolor()))
    record('FISHBONE_THEME_SAVE',(pending,view.model.causes[0].text))
    app.ui.open_check_sheet();root.update();cs=app.ui.active_chart_view;app.set_theme('light');root.update();assert cs.figure.get_facecolor()[:3]==(1.0,1.0,1.0);check_light=cs.figure.get_facecolor();app.set_theme('dark');root.update();assert cs.figure.get_facecolor()[:3]==(32/255,40/255,51/255);check=(cs.cget('bg'),cs.summary.cget('bg'),cs.figure.get_facecolor())
    app.ui.open_defect_concentration();root.update();dc=app.ui.active_chart_view;app.set_theme('light');root.update();assert dc.figure.get_facecolor()[:3]==(1.0,1.0,1.0);defect_light=dc.figure.get_facecolor();app.set_theme('dark');root.update();assert dc.figure.get_facecolor()[:3]==(32/255,40/255,51/255)
    record('QUALITY_TOOLS_LIGHT_DARK',(check_light,check,defect_light,dc.cget('bg'),dc.figure.get_facecolor(),[p.get_facecolor() for p in dc.ax.patches]))
    app.ui.open_fishbone();root.update();view=app.ui.active_chart_view;view.model.add_cause(view.model.categories[0]['id'],'long cause description '*12);view.refresh()
    root.state('normal');root.geometry('850x640+120+110');root.update();d1=(root.winfo_width(),root.winfo_height(),view.canvas.get_tk_widget().winfo_width(),view.canvas.get_tk_widget().winfo_height());app.set_theme('dark');root.state('normal');root.geometry('1180x790+120+110');root.update();d2=(root.winfo_width(),root.winfo_height(),view.canvas.get_tk_widget().winfo_width(),view.canvas.get_tk_widget().winfo_height());app.set_theme('light');root.update();assert d1!=d2
    record('CHART_RESIZE',(d1,d2,view.figure.get_size_inches().tolist()))
    app.ui.open_help();root.update();help_view=app.ui.active_chart_view;app.set_theme('dark');root.update()
    heading_color=help_view.text.tag_cget('section','foreground')
    assert help_view.text.cget('bg')==app.theme_manager.palette['input'] and heading_color==app.theme_manager.palette['accent']
    popup_after=tk.Toplevel(root);tk.Label(popup_after,text='active theme').pack();root.update()
    assert popup_after.cget('bg')==app.theme_manager.palette['window']
    record('HELP_AND_NEW_DIALOG_THEME',(help_view.text.cget('bg'),heading_color,popup_after.cget('bg')))
    root.state('normal');root.geometry('850x620+2200+40');root.update()
    popup=tk.Toplevel(root);popup.geometry('420x240');tk.Label(popup,text='position check').pack();root.update();placed=position_dialog(popup,root);root.update()
    bounds=_work_area(root,(0,0,root.winfo_screenwidth(),root.winfo_screenheight()))
    from ui.dialogs import _windows_window_rect
    popup_rect=_windows_window_rect(popup.winfo_id())
    assert bounds[0]<=popup_rect[0] and bounds[1]<=popup_rect[1] and popup_rect[2]<=bounds[2] and popup_rect[3]<=bounds[3]
    record('DIALOG_POSITION',(popup.geometry(),placed,bounds,popup_rect));popup.destroy()
finally: root.destroy()
script='import tkinter as tk; from ui.main_page import MainPage; r=tk.Tk(); a=MainPage(r); print(a.theme_manager.mode); a.set_theme("dark"); r.destroy()'
env=os.environ.copy();first=subprocess.run([sys.executable,'-c',script],env=env,text=True,capture_output=True,timeout=30)
script2='import tkinter as tk; from ui.main_page import MainPage; r=tk.Tk(); a=MainPage(r); print(a.theme_manager.mode); r.destroy()'
second=subprocess.run([sys.executable,'-c',script2],env=env,text=True,capture_output=True,timeout=30)
assert first.returncode==second.returncode==0 and second.stdout.strip()=='dark',(first.stdout,first.stderr,second.stdout,second.stderr)
record('THEME_RESTART',(first.returncode,second.returncode,second.stdout.strip(),Path(appdata,'SIKPRO','settings.json').read_text()))
