#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""   
(c) Research Group CAMMA, University of Strasbourg, France
Website: http://camma.u-strasbg.fr
Code author: Armine Vardazaryan
"""

import json
import tkinter as tk
import tkinter.font as font

import tkinter.filedialog as filedialog

from rater import Reviewer_Gui_Rater


resource_dir = './images'
config_path = './config.json'


def main():
    root = tk.Tk()
    
    try:
        with open(config_path, 'r') as f:
            info = json.load(f)
            datapath = info['datapath']
    except:
        
        datapath = filedialog.askdirectory(title='Select folder containing the frames')
        
        with open(config_path, 'w') as f:    
            json.dump({'datapath':datapath}, f)
        
    root.update()
    tk.Grid.rowconfigure(root, 0, weight=1)
    tk.Grid.columnconfigure(root, 0, weight=1)
    
    default_font = font.nametofont("TkDefaultFont")
    default_font.configure(size=11)
    root.option_add("*Font", default_font)
    
    app = Reviewer_Gui_Rater(datapath, resource_dir, config_path)
        

    root.bind('<Left>', app.leftKey)
    root.bind('<Right>', app.rightKey)
    root.bind('<Up>', app.upKey)
    root.bind('<Return>', app.returnKey)
    root.bind('<KP_Enter>', app.returnKey)
    root.bind('<F1>', app.oneKey)
    root.bind('<F2>', app.twoKey)
    root.bind('<F3>', app.threeKey)
    
    root.bind('<Control-a>', app.ctrl_aKey) #artifact
    root.bind('<Control-n>', app.ctrl_nKey) #roi not visible
    root.bind('<Control-r>', app.ctrl_rKey) #roi visible partially 
    root.bind('<Control-i>', app.ctrl_iKey) #instrument in roi
    root.bind('<Control-d>', app.ctrl_dKey) #difficult to review
    root.bind('<Control-o>', app.ctrl_oKey) #out of body
    root.bind('<Control-p>', app.ctrl_pKey) #posterior view
    root.bind('<Control-v>', app.ctrl_vKey) #anatomical variation

    root.mainloop()  
    
if __name__ == '__main__':
    main()  
    
